# L2 · 从零手搓语义缓存，再用 RedisVL 生产化

> 课程：Semantic Caching for AI Agents（DeepLearning.AI × Redis）
> 本课任务：先**从零构建**一个能跑的语义缓存（看清每个零件怎么工作），再用 Redis 开源 SDK 与数据库**重写成生产形态**，最后端到端接 LLM 实测延迟差。

## 0. 本课目标与素材

场景仍是客服——Agent 加速常见问题/工单的解决。数据集两块：一份客服系统的 **FAQ 数据集**（CSV，问答对 + 测试数据），一份支撑 Agentic 检索的**知识库**。

流程回顾：先用语义搜索查缓存——过去处理过的问题里有没有和当前问题**足够相似**的？足够相似 → 命中，直接返回；miss → 走 Agentic RAG 流程，把结果返给用户并**回填缓存**。

## 1. 从零手搓：embedding + 余弦距离 + 阈值

### 1.1 加载 FAQ 与生成 embedding

FAQ 每条形如：question = "How do I get a refund?"，answer = "To request a refund, visit our orders page and select..."。

用 **SentenceTransformers** 库、经典的 **all-mpnet-base-v2** 模型，把 FAQ 的问题列表编码成 embedding（首次运行需下载模型权重）：

```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-mpnet-base-v2")
faq_embeddings = model.encode(faqs["question"].tolist())  # FAQ 问题 → 向量矩阵
```

### 1.2 两个函数实现语义搜索

```python
def cosine_distance(a, b):
    ...  # 计算两组向量间的余弦距离

def semantic_search(query):
    query_embedding = model.encode(query)                       # 查询 → 向量
    dists = cosine_distance(query_embedding, faq_embeddings)    # 与 FAQ 矩阵逐条比
    idx = dists.argmin()                                        # 最相似条目的下标
    return idx, dists[idx]                                      # 返回下标 + 距离值
```

试跑：query = "How long will it take to get a refund for my order?" → 最相似 FAQ 是 "How do I get a refund?"，余弦距离 **0.331**。

### 1.3 语义搜索 → 语义缓存：只差一个阈值

```python
def check_cache(query: str, distance_threshold: float):
    idx, dist = semantic_search(query)
    if dist < distance_threshold:   # 距离小于阈值 → Cache Hit
        return faqs.iloc[idx]       # 返回缓存条目（问答对）
    return None                     # 否则 Cache Miss
```

测试：三个查询里 "Is it possible to get a refund" 以距离 **0.262** 命中，另两个 miss。

### 1.4 缓存扩容

新数据随时间进来，加一个 helper：接收问答对 → 拼进 DataFrame → 生成新 embedding 追加进 `faq_embeddings`。加入 3 条新 entry 后缓存从 **8 条 → 11 条**，重跑测试**三个查询全部命中**。

> **架构师视角**：手搓版揭示了语义缓存的本质——**它就是"向量检索 top-1 + 距离阈值判决"**，没有更多魔法。所有工程复杂度（TTL、多租户、重排、评测）都是围绕这条 if 语句长出来的。也因此它继承向量检索的一切弱点：embedding 认为近的不一定真的同义——阈值 0.3 是"敢不敢直接拿旧答案回复用户"的风险闸门，值多少要靠 L3 的指标来定，而不是拍脑袋。

## 2. 走向生产：Redis 与 RedisVL

**Redis**（Remote Dictionary Server）：开源、快速的**内存 KV 数据库**——在 Redis 服务器上存各种数据结构、跨多节点分布，应用可大规模读写。常用于缓存，但也支持**二级索引（secondary indexing）**：可存储并检索**向量、文本、数值、标签、甚至地理空间数据**——这些性质使它能做语义缓存。

本课用到的三样：

1. **低延迟向量搜索**：为检索与建索引优化，快速插入、快速查相似问题；
2. **RedisVL 开源 SDK**：对缓存配置与各种 CRUD 操作的符合工效的（ergonomic）控制；
3. **TTL / 逐出（eviction）/ 命名空间（namespacing）策略**：配置数据如何在缓存中流动、租户之间如何隔离。

### 2.1 连接 Redis + 缓存专用 embedding 模型

```python
REDIS_URL = "redis://localhost:6379"   # 多数情况下的本地默认地址
client.ping()                          # 先测连通

# 缓存优化的 embedding 模型：langcache-embed-v1
# 开源开放权重、托管在 Hugging Face、专为语义缓存操作微调
vectorizer = HFTextVectorizer(model="redis/langcache-embed-v1")  # 拉取权重到本地
```

> **对比 3-retrieval 的 embedding 选型**：那边的核心命题是 "Similarity ≠ Relevance"——通用 embedding 缺任务感知，修法之一是改嵌入空间。`langcache-embed-v1` 正是这个思路的产品化：不用通用 all-mpnet-base-v2，而是**针对"两个问题是否同义"这一特定任务微调**的模型——缓存判同义比开放域检索窄得多，专用模型在窄任务上更准。选型启示同款：任务够窄且量大时，微调小专模 > 通用大模型。

### 2.2 创建 SemanticCache 并灌数据

```python
cache = SemanticCache(
    name="faq_cache",              # 名字 → 数据库里的唯一命名空间
    vectorizer=vectorizer,         # 刚创建的缓存专用 embedding 模型
    redis_client=client,           # Redis 连接对象
    distance_threshold=0.3,        # 缓存判决的基线距离阈值
)

for _, row in faqs.iterrows():     # 逐条把 FAQ 灌进缓存（hydrate）
    cache.store(prompt=row["question"], response=row["answer"])
```

验证：问 "I need a refund for my purchase" → 返回缓存条目 prompt = "How do I get a refund?"、完整已验证答案、余弦距离 **0.25 < 阈值 0.3**——符合预期的正常命中。

### 2.3 TTL：让缓存保持新鲜

TTL（time to live）告诉数据库何时**逐出**在缓存里待了太久的数据，常用于系统数据变化/演进时保持缓存新鲜。RedisVL 一行搞定：

```python
cache.set_ttl(24 * 60 * 60)   # TTL 设为一整天（单位：秒）
```

## 3. 端到端实测：cache hit ~65ms vs LLM 1s+

用 LangChain OpenAI SDK 的 `ChatOpenAI` 接 **gpt-4o-mini**，helper 函数发 prompt："你是有帮助的客服助手，简洁专业地用 1–2 句话回答"。

```python
for q in test_questions:          # 课程自带 PerformanceEvaluation 类做细粒度计时
    result = cache.check(q)       # ① 先查缓存
    if result:
        ...                       # ② 命中：直接返回缓存答案（记为 hit）
    else:
        answer = ask_llm(q)       # ③ miss：调 LLM（记为 miss）
        cache.store(q, answer)
```

结果：测试问题命中/未命中混合出现（符合预期）；计时对比——

| 路径 | 平均耗时 |
|---|---|
| Cache Hit | **~65 毫秒** |
| LLM 调用 | **1 秒以上** |

约 **15 倍以上**的延迟差，这还只是一种度量形式。收尾可清空缓存，为下一课清理工作区。

## 4. 本课总结

| 要点 | 一句话 |
|---|---|
| 手搓内核 | 语义缓存 = 向量检索 top-1 + 距离阈值 if 判决 |
| 缓存可增长 | 新问答对 → 新 embedding 追加，8 条到 11 条后测试全命中 |
| Redis 能力 | 内存 KV + 二级索引（向量/文本/数值/标签/地理），低延迟向量搜索 |
| RedisVL 生产件 | SemanticCache（命名空间 + vectorizer + 阈值）、TTL/逐出/租户隔离 |
| 专用 embedding | langcache-embed-v1——为缓存判同义微调的开放权重模型 |
| 延迟实证 | hit ~65ms vs LLM 1s+，少量命中即大幅省时 |

> **记忆点（引出 L3）**：缓存跑通了、也快了 15 倍，但"跑通"不等于"可靠"——阈值 0.3 是拍的，命中的答案对不对没人背书。L3 用机器学习模型评测的方式给缓存做体检：**Hit Rate、Precision、Recall、延迟 + 混淆矩阵**，把"缓存失效的两种方式——质量差 vs 性能差"量化出来，让阈值从拍脑袋变成有据可调。

## 与我的资产映射

- 检索层：`agent/skills/agent-selection/3-retrieval.md`（embedding 选型/换 embedding 重建索引；Similarity ≠ Relevance 与专用微调模型）
- 成本经济学：`agent/skills/agent-selection/8-cost-economics.md`（语义缓存的省钱账：hit rate × 单次 LLM 成本；65ms vs 1s 的延迟账同理）
- 记忆层：`agent/skills/agent-selection/6-memory.md` + memory 课程 12a（Semantic Cache 作为短期记忆组件；TTL/逐出即短期记忆的遗忘机制）
- 面试包：`agent/interview/jd-senior-agent-engineer/05-context-engineering-and-caching.md`（本课直接对口：可现场手写 check_cache 内核 + RedisVL 生产化路径）
- [[project_selection_matrix]]
