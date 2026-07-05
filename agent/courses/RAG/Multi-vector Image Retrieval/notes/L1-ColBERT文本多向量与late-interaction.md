# L1 · ColBERT：文本多向量检索与 late interaction（MaxSim）

> 课程：Multi-vector Image Retrieval（DeepLearning.AI × Qdrant，C2）
> 本课任务：从文本入手打底——先复盘 Bi-encoder / Cross-encoder 各自的取舍，再用 **ColBERT** 这条"late interaction"路线拿到"可预计算 + token 级细粒度匹配"的两全其美，最后在 Qdrant 里把 dense 与 multi-vector 两种检索并排跑一遍。

## 0. 本课定位

图像多向量（下一课的 ColPali）的直觉全部来自文本多向量。所以本课先把 **ColBERT** 讲透：它是文本领域最常见的多向量技术，理解它 = 理解整门课的内核。路线：**检索三种架构对比 → ColBERT 原理（token 向量 + MaxSim）→ 代价（HNSW 失效、内存爆炸）→ 代码实操**。

## 1. 三种检索架构：为什么需要"第三条路"

RAG 的本质是给 LLM 配一个可检索的知识库：收到 prompt 先搜库、取最相关文档、拼进 prompt 再生成。检索这一步有三种做法，取舍互不相同。

### Bi-encoder（双编码器，最常见的 dense 检索）

每个文档由 embedding model 编成**一个向量**；query 也编成一个向量；搜库 = 找向量离 query 最近的文档。

- **优点：快、可扩展**。文档向量可**离线预计算**——哪怕十亿文档也只编一次；搜索时只对 query 编一个向量，配合 ANN 算法轻松扩到十亿级。
- **缺点：信息压扁**。把整个文档/prompt 的含义压进一个向量，会丢掉细节、错过 query 与文档间的微妙关联。

### Cross-encoder（交叉编码器）

把 query 与文档的**全文一起**喂进一个神经网络，直接输出一个相关性分数用于排序。

- **优点：质量极高**。因为 query 和文档同时进网络，能捕捉两者之间细腻的交互关系。
- **缺点：扩展性极差**。要拿全文才能算分 → **无法预计算**；每评一个文档都要跑一次昂贵的前向传播。所以只适合 100 个以内的文档，最佳用法是给别的技术**重排（rerank）**——比如 bi-encoder 从百万里快速捞 50 个，再用 cross-encoder 精排出前 5。

> **对比 3-retrieval 的检索器架构**：这正是我资产里 BiEncoder / CrossEncoder / ColBERT 三分法的原始出处。Bi-encoder = 可预计算但只有一个"整体印象"；Cross-encoder = token 级交互但每次都得现算。理想是"既能像 bi-encoder 预计算、又能像 cross-encoder 做 token 级深度交互"——多向量技术就是为了同时拿到这两点而生。

### 三者取舍一览

| | Bi-encoder | Cross-encoder | ColBERT（late interaction） |
|---|---|---|---|
| 表示 | 每文档 1 个向量 | 不产生可存向量 | 每 token 1 个向量 |
| 预计算 | ✅ | ❌ | ✅（文档侧向量可离线算） |
| 交互粒度 | 整体向量 | token 级（全网络） | token 级（仅算相似度） |
| 扩展性 | 十亿级 | ≤100 文档 | 受限（HNSW 失效，见 §3） |
| 典型角色 | 一级召回 | 精排 reranker | 精排 reranker / 中间地带 |

## 2. ColBERT 原理：保留每个 token 的向量 + MaxSim

**ColBERT** 是最常见的文本多向量技术。它和 bi-encoder 前半段一样：文本切 token，每个 token 拿到一个既反映自身含义、又反映其在整篇文档语境中含义的 embedding 向量。

**关键分叉**：bi-encoder 下一步会 **pooling**（最常见是把所有 token 向量求平均）压成一个文档向量；**ColBERT 把所有 token 向量都留着**。query 侧同理，每个 query token 也各得一个向量。

### 打分：MaxSim（maximum similarity，late interaction）

给一对 (query, 文档) 打分的方法叫 **MaxSim**：

```
对 query 里每个 token：
    在文档所有 token 里找与它最相似的那个（用 dot product 或 cosine）
    记下这个最大相似度
MaxSim 分数 = 所有 query token 的最大相似度之和
```

例：query token `puppy` 会和文档 token `dog` 匹配得最紧。对每个 query token 都做一次 max，再全部相加。这被称为 **late interaction（后期交互）**——文档和 query 各自独立编码（可预计算），只在最后"打分"这一步才让两边 token 交互，从而模拟 cross-encoder 的深度交互效果。

### MaxSim 是非对称的 —— 这不是细节，是硬约束

MaxSim **不对称**：距离(A→B) ≠ 距离(B→A)。把上例的 query 和文档互换，原来是 3 个 dot product 之和，换过来就变成 5 个之和。

> **架构师视角**：非对称直接掐死了 ANN。HNSW 索引建图依赖"A 是 B 的最近邻 ⟺ B 是 A 的最近邻"这种对称的邻接关系；MaxSim 下"A 是 B 的最近邻，但 B 不一定是 A 的最近邻"，图根本建不起来。所以**多向量检索通常要关掉 HNSW**（Qdrant 里设 `m=0`）。这是选型时必须记住的连锁反应：选了 late interaction，就等于放弃了 ANN 索引这条快速通道。

## 3. ColBERT 的代价与正确用法

### 代价一：HNSW 失效 → 不能单独用于大库

HNSW 用不了，若单用 ColBERT 搜索就得对全库做 **brute force 全扫描**，规模一大就太慢。

### 代价二：内存爆炸

每 token 存一个向量，一篇文档轻松几百上千个向量。算一笔账：

```
文档 1000 token × 128 维 × 4 字节(float32) ≈ 0.5 MB / 文档
对比 bi-encoder：每文档仅 1 个向量，即便高维通常也 < 10 KB / 文档
```

百万级文档时差距是量级性的。ColBERT/late interaction 是**单向量模型与 cross-encoder 之间的中间地带**：比任何 embedding 模型都更吃内存、更贵，但仍保留了"文档侧可预计算、不必每个 query 都过一遍网络"的关键优势。

### 正确用法：oversampling + rerank

> **对比课程 06 Advanced Retrieval 的 reranker**：和 cross-encoder 一样，late interaction 模型最常见的用法是**当 reranker**——先用快的 bi-encoder **过采样（oversampling，召回比最终想要的更多的候选）**，再用多向量的 MaxSim 只在这批有限候选上精排。这与 06 课里"向量召回 → reranker 精排"的两段式管线同构，只不过这里的 reranker 是 token 级 late interaction 而非一个 cross-encoder 打分模型。

## 4. 代码实操：ColBERT v2 + Qdrant

### 4.1 加载模型、看维度

```python
from fastembed import LateInteractionTextEmbedding

# ColBERT v2（Stanford），每个 token 编成 128 维向量
colbert_model = LateInteractionTextEmbedding("colbert-ir/colbertv2.0")
colbert_model.embedding_size          # -> 128
```

### 4.2 分词与嵌入：文档 vs query 不一样

ColBERT 用 **WordPiece 分词**，加特殊 token：开头 `CLS`、文档编码用的占位 token、结尾 `SEP`。普通词多为单 token，个别词会被拆成子词（示例里 `decibels` 被拆成 3 个 subword token）。

```python
document = "...electric bus fleets... 40 decibels."   # 示例文档
document_tokens = tokenize_late_interaction(colbert_model, document)
len(document_tokens)                                  # 55 个 token

# 文档嵌入：用 passage_embed —— 每个 token 一个向量
document_embeddings = next(colbert_model.passage_embed([document]))
# shape = (55, 128) —— 55 个 token，各 128 维
```

**query 侧的差异**：ColBERT 对 query 做**定长填充到 32 个 token**（保证不同 query 可一致比较，也意味着 query 不能更长，否则会被截断）。所以哪怕 query 很短：

```python
query = "advantages of EV cars"
query_embeddings = next(colbert_model.query_embed([query]))
query_embeddings.shape                                # (32, 128) —— 含大量 padding token
```

> **架构师视角**：注意调用的是 `query_embed` 而非 `passage_embed`——很多模型对 query 和 document 的处理不同（query 补 padding、document 不补）。检索管线里把这两条路径混用是常见 bug。

### 4.3 手算 MaxSim

```python
import numpy as np

# 32×55 相似度矩阵：每个 query token 对每个 document token 的 dot product
similarity_matrix = np.dot(query_embeddings, document_embeddings.T)

# 每个 query token 取一行最大值(axis=1)，再全部相加 = MaxSim
maxsim_score = similarity_matrix.max(axis=1).sum()    # 约 17
```

配套 `visualize_maxsim_matrix` 画热力图：每格是某 query token 与某 doc token 的相似度，红框标最高分。能直观看到 `advantages`↔`benefits`、`cars`↔`fleets` 这类语义对齐。（padding/mask token 在图里被隐去，但仍参与最终打分。）

### 4.4 在 Qdrant 里同存 dense + multi-vector

一个 collection 里配两种命名向量，dense 走 COSINE，ColBERT 走特殊配置：

```python
client.create_collection(
    collection_name,
    vectors_config={
        dense_vector_name: models.VectorParams(
            size=dense_model.embedding_size,
            distance=models.Distance.COSINE,
        ),
        colbert_vector_name: models.VectorParams(
            size=colbert_model.embedding_size,          # 单个 token 向量的维度 128
            distance=models.Distance.DOT,
            multivector_config=models.MultiVectorConfig(
                comparator=models.MultiVectorComparator.MAX_SIM,   # 告诉 Qdrant 用 MaxSim 打分
            ),
            hnsw_config=models.HnswConfigDiff(m=0),     # 关掉 HNSW（§2 的非对称约束）
        ),
    },
)
```

upsert 时同一文档同时写入 dense 与 ColBERT 两种向量。查询各写一个 helper：`colbert_query` 用 `colbert_model.query_embed`，`dense_query` 用 dense 模型，都调 `client.query_points(..., using=<vector_name>)`。

### 4.5 关键实验：专有名词 `Qdrant`

query 特意选 `"search performance in Qdrant"`。原因：公司名这类专有名词常被拆成多个单字母 token——`Qdrant` 被拆成 `Q`/`dran`/`t` 三个 token，证明 ColBERT 训练时没见过这个词。

- **dense 模型**里，这种 token 混进 pooling 后基本沦为**噪声**；
- **ColBERT** 的 token 级交互能让这种多 token 序列在 query 与文档间**更好地对上**——所有 ColBERT 结果都提到了 Qdrant，dense 结果则不然。热力图显示 `perform`↔`performance` 最近，但 `Q`/`dran`/`t` 也对 MaxSim 有显著贡献。

> **架构师视角**：这就是多向量能做**关键词/专名匹配**的机制——即便模型不"理解" Qdrant 是什么，token 级交互也把它当字符序列精确对齐，等效于把 keyword matching 塞进了语义检索。讲师同时提醒：肉眼对比结果（eyeballing）不够，真实场景要建 **ground truth 数据集**量化质量。

## 本课总结

| 要点 | 一句话 |
|---|---|
| 三种检索架构 | Bi-encoder 快但压扁；Cross-encoder 准但不可预计算；多向量取中间地带 |
| ColBERT 内核 | 保留每个 token 的向量，不做 pooling |
| MaxSim / late interaction | 每个 query token 取与文档 token 的最大相似度再求和；仅打分时交互 |
| 非对称 → 关 HNSW | MaxSim 不对称，ANN 图建不起来，`m=0` 关索引 |
| 内存代价 | 每 token 一向量，百万级文档吃内存量级性上升 |
| 正确用法 | 过采样召回 + 多向量 rerank，而非单独大库检索 |
| 专名匹配 | token 级交互把 keyword matching 塞进语义检索 |

> **记忆点（引出 L2）**：ColBERT 把"每个 token 一个向量 + MaxSim"这套 late interaction 玩法在**文本**上跑通了。L2 的 **ColPali** 做的正是同一件事的图像版——把文档/图片切成 **patch**（相当于图像的 token），每个 patch 一个向量，query 文本 token 与图像 patch 之间做 MaxSim。于是无需 OCR、无需版面解析，直接"把文档当图片"检索。

## 与我的资产映射

- 检索层选型：`agent/skills/agent-selection/3-retrieval.md`（BiEncoder / CrossEncoder / ColBERT 三分法——本课是 ColBERT 一支的完整拆解，含"选 late interaction = 放弃 ANN"这条连锁取舍）
- 已学课程 06《Advanced Retrieval》的 reranker 一节（多向量作为 oversampling 后的 rerank 步骤）
- Qdrant C1《Retrieval Optimization》（HNSW / ANN 的公共底座，本课"为何关 HNSW"接在其后）
- [[project_selection_matrix]]
