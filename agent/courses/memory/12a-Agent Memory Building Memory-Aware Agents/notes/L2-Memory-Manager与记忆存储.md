# L2 · Memory Manager 与记忆存储：把分类学落成物理表

## 1. 智能体的三层栈（Agent Stack）

| 层 | 职责 | 本课对应 |
|---|---|---|
| **Application 层** | 智能体逻辑、agent loop | L5 的 `call_agent` |
| **Memory 层** | CRUD 抽象、记忆类型管理 | `MemoryManager` / `StoreManager` |
| **Infrastructure 层** | 存储、索引、向量检索 | Oracle AI Database 26ai |

> **架构师视角**：这三层分离是本课最值钱的架构决策。Application 层不该直接写 SQL，Memory 层不该关心业务语义。这跟分层架构选型（[[project_selection_matrix]]）的思路一致——**记忆的 CRUD 要有独立抽象层**，换存储底座时上层 agent loop 不动。

## 2. 两个核心类

### StoreManager —— 存储的统一入口
把所有存储（向量存储 + SQL 表）收口到一个对象，通过 getter 方法拿：

```python
store_manager = StoreManager(
    client=database_connection,
    embedding_function=embedding_model,
    table_names={'knowledge_base':..., 'workflow':..., 'toolbox':..., 'entity':..., 'summary':...},
    distance_strategy=DistanceStrategy.COSINE,   # 余弦距离
    conversational_table=CONVERSATION_HISTORY_TABLE,
    tool_log_table=TOOL_LOG_HISTORY_TABLE,
)
knowledge_base_vs = store_manager.get_knowledge_base_store()  # 向量存储
conversation_table = store_manager.get_conversational_table() # SQL 表
```

### MemoryManager —— CRUD 抽象
在 StoreManager 之上暴露语义化读写：`write_knowledge_base()` / `read_knowledge_base()` / `write_conversational_memory()` / `read_workflow()` …。**Application 层只跟它打交道**。

## 3. 物理表设计：分类学 → schema

L1 的记忆分类学在这里一一落表（注意注释里的认知类型标注）：

```python
CONVERSATIONAL_TABLE = "CONVERSATIONAL_MEMORY"  # Episodic 情景
KNOWLEDGE_BASE_TABLE = "SEMANTIC_MEMORY"        # Semantic 语义
WORKFLOW_TABLE       = "WORKFLOW_MEMORY"        # Procedural 程序性
TOOLBOX_TABLE        = "TOOLBOX_MEMORY"         # Procedural 程序性
ENTITY_TABLE         = "ENTITY_MEMORY"          # Semantic 语义
SUMMARY_TABLE        = "SUMMARY_MEMORY"         # Semantic 语义
TOOL_LOG_TABLE       = "TOOL_LOG_MEMORY"        # 工具执行日志
```

**关键区分：谁用 SQL、谁用向量？**
- **对话表 / 工具日志表 → 纯 SQL 表**：因为它们靠 `thread_id`、`timestamp` 精确检索、按时间排序，不需要语义相似度。
- **知识库/工作流/工具箱/实体/摘要 → 向量存储（OracleVS）**：靠语义相似度检索。

> **架构师视角**：这个"SQL 表 vs 向量存储"的分工是记忆系统设计的核心权衡。**精确/结构化/时序检索用 SQL，模糊/语义检索用向量**。很多人无脑全上向量库，结果"按 thread_id 拉最近 10 条"这种精确查询又慢又贵。Oracle 26ai 的价值正在于**同一个库里两种能力都有**（呼应 L1 的"记忆核心=数据库"）。

对话表的 schema 里有个关键字段 **`summary_id`**（默认 NULL）——它是 L4「上下文压实」的钩子：一旦某几行被总结过，就打上 summary_id 标记，避免重复总结。

## 4. Memory Unit（记忆单元）

**最小原子数据单元**——一条对话、一篇论文、一个工具定义，都是一个 Memory Unit。整个记忆系统就是对 Memory Unit 的增删改查。L3 的「Memory Unit Augmentation」就是对工具这种 Memory Unit 做 LLM 增强。

## 5. 两组关键概念

### Context Engineering vs Memory Engineering
- **Context Engineering**：策展高信噪比的上下文（curate high signal-to-noise context）——决定"这一次调用塞什么"
- **Memory Engineering**：是 **数据库工程 ∩ 智能体工程 ∩ ML 工程 ∩ 信息检索工程** 的交叉学科——决定"整个系统怎么存取记忆"

### 记忆操作的两种触发方式（贯穿全课的重要区分）
| 触发方式 | 谁决定 | 例子 |
|---|---|---|
| **Deterministic（确定性/程序性）** | 代码逻辑 | 上下文超 80% 自动总结 |
| **Agent-triggered（智能体触发）** | LLM 自己决定 | 把总结当工具调用 |

> **记忆点**：同一个操作（如 summarize）可以既是确定性的、又是智能体触发的——这在 L4/L5 会反复出现，是本课设计哲学的核心。

## 6. 基础设施落地要点

```python
# 嵌入模型：本地 HuggingFace，非 OpenAI
embedding_model = HuggingFaceEmbeddings(
    model_name="sentence-transformers/paraphrase-mpnet-base-v2")
# 距离策略：余弦；向量索引：IVF（safe_create_index 建 *_ivf 索引）
```

- **数据集**：从 HuggingFace 拉 `nick007x/arxiv-papers`（streaming），取 100 篇灌进知识库做 demo——把 title+subjects+abstract 拼成一段文本再 `write_knowledge_base`。
- **嵌入模型选型注记**：用了本地小模型 `paraphrase-mpnet-base-v2`（句向量、轻量），不是 OpenAI embedding。教学场景省钱省网；生产里是否换成更强的 embedding，是 [[project_selection_matrix]] 检索层要单独评的一格。

## 7. 记忆感知智能体的四要素（本课定义）

一个"memory-aware agent"需要：
1. **系统提示层面的记忆感知**——system prompt 告诉 LLM 它有哪些记忆
2. **记忆操作作为工具**——LLM 能主动调用读写
3. **推理**——基于记忆做决策
4. **上下文窗口分区（partitioning）**——不同记忆类型占不同段落

第 4 点在 L5 的 `AGENT_SYSTEM_PROMPT` 里体现得淋漓尽致（用 markdown 二级标题切分记忆段）。
