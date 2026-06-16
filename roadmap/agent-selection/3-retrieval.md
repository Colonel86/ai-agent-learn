# 检索栈选型方案对比(向量库 / Embedding / Chunking / Retriever / Reranker)

> **用途**:为 RAG / 知识检索类 Agent 选整条检索栈的各个环节。
> **适用**:Spec-Kit `/plan`;或由 `stack-selector` skill 路由进来。
> **最后核对:2026-06**。结论分级 ✅稳定 / ⚠️快照 / ❓待验证。
> **边界**:本包是「**知识检索**」(检索文档喂给 LLM);`roadmap/agent-selection/4-tools.md` 是「**工具检索**」(在 100+ 工具里选对工具)——两层不同,别混。

---

## 一、何时需要这层选型

- 业务是"问知识库/文档"(RAG-first),检索质量决定成败。
- 朴素 RAG 召回不准、答非所问、或 LLM 拿自有知识硬答。
- 数据规模/更新频率/语言变化,需要重选向量库或 embedding。

> 👉 **核心问题:"Similarity ≠ Relevance"**(课程 06)。通用 embedding 缺任务感知;三类修法分别作用于不同阶段——**检索前**(Query Expansion)、**检索后**(Cross-Encoder 重排)、**嵌入空间**(Embedding Adapter)。

检索栈有 5 个**子决策**,逐节给方案。

---

## 二、子决策 1:向量数据库

| 向量库 | 形态 | 规模 | 部署 | 适合 |
|---|---|---|---|---|
| **Chroma** ⭐ | 轻量/内存 | 小-中 | 零依赖 | 原型、教学、单机小项目 |
| **FAISS** | 库(非服务) | 中 | 单机/可 GPU | 单机高性能、自己管持久化 |
| **pgvector** ⭐ | Postgres 扩展 | 中 | 已有 PG 时 | 已用 Postgres、想少加组件 |
| **Qdrant / Weaviate / Milvus** | 分布式服务 | 大 | 独立服务/集群 | 生产、海量、需过滤+水平扩展 |
| **Pinecone** | 托管 SaaS | 大 | 全托管 | 不想运维、快速上生产(锁定+成本) |

```
原型/教学 → Chroma
已有 Postgres → pgvector(少加组件)
单机要快/可 GPU → FAISS
生产海量+元数据过滤 → Qdrant / Weaviate / Milvus
不想运维、接受锁定 → Pinecone
```
回溯:`courses/04`、`courses/专业名词解释/向量数据库-FAISS与Milvus.md`。

## 三、子决策 2:Embedding 模型

| 模型 | 类型 | 特点 | 适合 |
|---|---|---|---|
| OpenAI `text-embedding-3-small` ⭐ | API | 便宜、够用 | 默认起步 |
| OpenAI `text-embedding-3-large` | API | 更准、更贵 | 召回质量优先 |
| BGE `bge-small/large-en-v1.5` | 本地 | 开源、可自托管 | 数据不出域、控成本 |
| BGE `bge-m3` ⭐ | 本地 | 跨语言、多粒度 | 中英混合/多语种 |
| Cohere embed | API | 多语种强 | 多语种商用 |

> 选 embedding 看:**语言**(中英→bge-m3/Cohere)、**是否出域**(不出域→本地 BGE)、**成本**(高频→小模型或本地)。换 embedding 必须**重建索引**——属高成本变更,早定。
回溯:`courses/04/notes/04-vectorstores-and-embeddings.md`、`courses/专业名词解释/向量相似度与归一化.md`。

## 四、子决策 3:Chunking 策略

| 策略 | 做法 | 适合 |
|---|---|---|
| **两级切分** ⭐ | `RecursiveCharacterTextSplitter`(语义边界)+ token splitter(`tokens_per_chunk≈256` 兜底) | 通用默认 |
| **SentenceWindow** | 按句嵌入,合成时带前后窗口(`MetadataReplacementPostProcessor`) | 嵌入精度与上下文连贯解耦 |
| **Auto-merging 层级** | 父子分块,命中子块自动合并父块 | 长文档、结构化文档 |

> chunking 常被低估:**先按语义边界切,再用 token 上限兜底**;SentenceWindow 把"嵌入粒度"和"喂给 LLM 的粒度"分开。
回溯:`courses/05`、`courses/18`。

## 五、子决策 4:Retriever 架构(三层谱)

| 架构 | 原理 | 速度 | 精度 | 用在哪 |
|---|---|---|---|---|
| **Bi-Encoder**(双塔)⭐ | 查询/文档各自编码,可离线建索引 | 快 | 中 | 召回/粗排(Stage 1) |
| **Cross-Encoder** | 查询+文档拼接进 attention,逐对打分 | 慢 | 高 | 精排/重排(Stage 2) |
| **ColBERT** | token 级向量 + late-interaction(MaxSim) | 中 | 高 | 精度与可索引折中(存储贵) |

> **生产标准 = 两阶段**:Bi-Encoder 宽召回(top 50-200)→ Cross-Encoder 精排(top 8-12)。
回溯:`courses/专业名词解释/检索器架构-BiEncoder-CrossEncoder-ColBERT.md`、`courses/06`。

## 六、子决策 5:Reranker + 进阶技术

| 技术 | 作用 | 何时加 |
|---|---|---|
| **Reranker**(`bge-reranker-v2-m3`)⭐ | 两阶段精排 | 召回有了但 top 不准 |
| **Query Expansion / HyDE / Multi-Query** | 检索前扩写查询 | 查询太短/口语化 |
| **Hybrid(BM25 + 向量)** | 关键词+语义并用 | 有专有名词/术语精确匹配 |
| **Embedding Adapter** | 嵌入后线性变换到任务空间(±1 标注,MSE) | 有反馈数据、想低成本提质 |

---

## 七、组合决策树(整条栈)

```
Step 1 向量库:原型→Chroma;有PG→pgvector;生产海量→Qdrant/Weaviate/Milvus
Step 2 Embedding:默认 text-embedding-3-small;多语种→bge-m3;不出域→本地BGE
Step 3 Chunking:默认两级切分;长/结构化文档→Auto-merging;要连贯→SentenceWindow
Step 4 召回不准?→ 加两阶段(Bi-Encoder召回 + Cross-Encoder/bge-reranker 精排)
Step 5 仍不准?→ 查询侧加 HyDE/Multi-Query;有术语→Hybrid;有反馈数据→Embedding Adapter
Step 6 用 RAG Triad 验收(见下)
```

---

## 八、验收指标:RAG Triad(课程 05)

| 指标 | 查什么 | 失败信号 |
|---|---|---|
| **Context Relevance** | 检索到的是否相关 | 低 → 检索环节出问题 |
| **Groundedness** | 答案是否基于检索内容 | 低 → LLM 在用自有知识硬答 |
| **Answer Relevance** | 答案是否回应问题 | 低 → 端到端跑偏 |

> 选型不是拍脑袋:每改一个环节,用 Triad 跑一遍看哪个指标动了。详见 `roadmap/agent-selection/5-observability-eval.md`。

---

## 九、场景推荐

| 场景 | 推荐栈 |
|---|---|
| 原型/demo | Chroma + 3-small + 两级切分 |
| 已有 Postgres 的生产 | pgvector + 3-small/large + 两阶段重排 |
| 多语种知识库 | Qdrant + bge-m3 + Hybrid + reranker |
| 数据不能出域 | 本地 BGE + FAISS/Qdrant 自托管 |
| 长文档/合同/手册 | Auto-merging + SentenceWindow + reranker |

---

## 十、接入 Spec-Kit(可复制 prompt 块)

```
请用 roadmap/agent-selection/3-retrieval.md 为本 RAG feature 选检索栈。
- 数据:规模 <…> / 结构 <…> / 更新频率 <…> / 语言 <…>
- 约束:是否出域 <…> / 延迟 <…> / 已有基础设施(有无 Postgres 等)<…>
请逐子决策给方案(向量库/embedding/chunking/retriever架构/reranker+进阶),
每项:推荐 + 备选 + 理由 + 代价,并给出用 RAG Triad 验收的方式。
```

---

## 十一、课程回溯 + 相关资产

- 回溯:`courses/04`、`courses/05`、`courses/06`、`courses/18`、`courses/RAG/RAG.md`、`courses/专业名词解释/{向量数据库-FAISS与Milvus, 检索器架构-BiEncoder-CrossEncoder-ColBERT, 向量相似度与归一化}.md`。
- 相关层:`roadmap/agent-selection/2-framework/`(LlamaIndex/Haystack 作为编排框架在那边)、`roadmap/agent-selection/5-observability-eval.md`(RAG Triad 评估)、`roadmap/agent-selection/4-tools.md`(工具检索,不同层)。
- 总览:`roadmap/agent-selection/README.md`。沉淀:`skills/adr-writer`。
