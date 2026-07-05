# L5 · 调优 HNSW 近似检索（M / ef 与近似质量的取舍）

> 课程：Retrieval Optimization: Tokenization to Vector Quantization（DeepLearning.AI × Qdrant）
> 本课任务：理解 HNSW 这张多层图怎么做近似最近邻（ANN），用 **exact KNN 当参照系**量化近似掉了多少质量，再通过调 **M / ef** 把差距收窄——同时看清调参的延迟与内存代价。

## 0. 本课定位：优化第一站——把近似做得更准

L4 度量的是"模型 + 管线"的绝对质量。但几乎所有向量库都用 **HNSW 做近似**最近邻，近似天然带来质量损耗。本课的问题变成：**在不动 embedding 模型的前提下，怎么让近似更接近理论上限？**

## 1. HNSW 结构回顾：分层的小世界图

HNSW = Hierarchical Navigable Small World，一张**多层堆叠的图**，节点是向量、边按相似度连接（所以相似度度量必须建库前选定）：

```
Layer 2 (最稀疏)   ●········●              少量向量、长跳边
                   |        |   ← 层间边（同一向量在不同层的连接）
Layer 1            ●···●···●···●
                   |   |   |   |
Layer 0 (最稠密)   ●●●●●●●●●●●●●●●        全部向量都在底层
```

规则：**上层的向量一定也出现在下层**；顶层最稀疏（只含一小撮向量），底层最稠密（含全部向量）。除了相似度边，还有**层间边**帮助在层之间跳转。

**两个可调参数：**

| 参数 | 含义 | 调高的效果 | 代价 |
|---|---|---|---|
| **M** | 每个节点建多少条边 | 近似质量↑，越接近 exact KNN | 图更大 → 内存↑；搜索更慢 |
| **ef** | 每层保留多少个候选点 | 结果更好 | 更慢 |

关键澄清（讲师反复强调）：**M/ef 只能改善"近似"的好坏，改不了 embedding 模型的天花板。** 如果表示本身太弱，调图参数不会变魔术般变出语义。调高 M 只是让你**更接近 exact KNN 的结果**而已。

## 2. 搜索流程：从顶层贪心下沉

```
query 向量化（同一 embedding 模型）
  └→ 从顶层进入，找 ef 个最近点
      └→ 顺层间边下沉到下一层，只看"上一步选中点 + 其直接邻居"，再选 ef 个
          └→ 逐层重复，作用域不断收窄
              └→ 到底层取 top-k 返回（k 通常 < ef）
```

每一步只检查"上一层选中的点及其直接邻居"，这就是它高效的原因——**不遍历全图，只沿图贪心逼近**。

## 3. ANN vs exact KNN：参照系的切换

Qdrant 默认跑近似搜索；打开 `exact=True` 强制纯 KNN——**慢，但给出该 embedding 模型下能达到的最高质量**：

```python
# 近似（默认）
client.search("wands-products",
    query_vector=models.NamedVector("product_name", vector=vec),
    search_params=models.SearchParams(exact=False))

# 精确 KNN：暴力全量，作为质量上限
client.search("wands-products",
    query_vector=models.NamedVector("product_name", vector=vec),
    search_params=models.SearchParams(exact=True))
```

**本课的巧妙之处：ground truth 不再是"人工标注的完美答案"，而是 exact KNN 的输出。** 因为我们要度量的不是模型好坏，而是"近似离精确差多少"：

```python
# 用 exact KNN 结果构造 Qrels（近似质量的参照系）
knn_qrels_dict = defaultdict(dict)
for id, row in queries_df.iterrows():
    results = client.search("wands-products",
        query_vector=models.NamedVector("product_name", vector=row["query_embedding"]),
        limit=100, search_params=models.SearchParams(exact=True))
    for p in results:
        # ranx 要整数分值 → 相似度 ×100 取整
        knn_qrels_dict[f"query_{id}"][f"doc_{p.id}"] = int(p.score * 100)
qrels = Qrels(knn_qrels_dict)
```

由于 embedding 不变、变的只是"哪些结果可能漏掉"，**只有 precision@k 有意义**（分数和文档集合本身不会变）。默认配置（M=16, ef=100）实测：

```
precision@25 ≈ 0.998   # 近似已经很接近精确了
```

## 4. 调参实验：拉高 M 与 ef_construct

```python
client.update_collection(
    collection_name="wands-products",
    hnsw_config=models.HnswConfigDiff(m=64, ef_construct=200),  # 16→64, 100→200
)
# 必须轮询到 GREEN，否则还在用旧图，测出的是旧质量
while collection.status != models.CollectionStatus.GREEN:
    time.sleep(1.0); collection = client.get_collection("wands-products")
```

调高后 precision@25 进一步上升（本就 0.998，提升空间有限）。**讲师的现实提醒：也许根本没必要提这么多。**

## 5. 代价：高参数不是免费的

调参不是单调向好，M/ef 越高代价越大：

| 代价维度 | 机制 |
|---|---|
| 延迟↑ | 每层查更多候选、每节点更多边 → 搜索更慢 |
| 内存↑ | 边数增加直接放大图的体积 |

所以生产原则是：**把 M/ef 保持在"够用的最小值"**，而不是一味拉满。也可以反向——若首要诉求是速度，甚至可以**调低**参数，牺牲一点质量换更快检索。

**一个关键实现细节：HNSW 不是一张全局大图，而是分段（segment）的。** 向量被切成互不重叠的 segment，每段各建一张 HNSW：

- **可扩展**：segment 可分散到整个机器集群；
- **并发**：单机也能用多 CPU 核并行；
- **易重建**：一段一段重建，不必推倒全局图。

（这个 segment 设计在 L6 的 scalar quantization 里会再次派上用场——每段可独立测量数值范围。）

> **架构师视角**：本课最反直觉的一课是"近似已经 0.998 了"。这说明**在很多真实场景，HNSW 调参不是收益最高的旋钮**——默认配置往往够好，把工程时间砸在把 0.998 抬到 0.999 上是低 ROI 的。真正的杠杆通常在上游（embedding 选型、L4 揭示的 name vs description）或下游（L6 用量化换内存/速度）。**先量化"当前近似离上限差多少"，再决定值不值得调参**，这才是架构师而非调参工的姿势。

> **对比 Qdrant C2「Multi-vector」检索**：本课在单条命名向量上调 HNSW；C2 的多向量（如 ColBERT 式 late-interaction、图文多向量）把检索精度问题推到"一个 point 多个向量"的层面。取舍分野：**HNSW 调参是在既定表示下榨近似质量的上限，多向量是换一种更强的表示去抬高上限本身。** 当调参已顶到天花板（如这里的 0.998），继续调无意义，该考虑的是换表示，而不是继续拧 M/ef。

## 本课总结

| 要点 | 一句话 |
|---|---|
| HNSW | 多层小世界图，顶稀疏底稠密，贪心下沉搜索 |
| M / ef | 只调近似质量，调不动 embedding 天花板；越高越慢越占内存 |
| exact KNN 参照 | 近似质量 = 与 exact KNN 结果比 precision@k |
| 最小够用 | 生产里 M/ef 取"够用最小值"，甚至可为速度调低 |
| segment 分段 | HNSW 非全局单图，分段利于扩展/并发/重建/量化 |

> **记忆点（引出 L6）**：L5 调 HNSW 是在**质量维度**做优化，但没碰"每条向量占多少内存"。float32 × 1500+ 维 = 单块 6KB，百万级就吃满内存。L6 引入 **vector quantization**（PQ/SQ/BQ），用可控的质量损失换 4~32 倍内存压缩、乃至最高 40 倍检索提速——优化从质量维度切到成本/速度维度。

## 与我的资产映射

- 检索层：`agent/skills/agent-selection/3-retrieval.md`（HNSW M/ef 是 ANN 索引的核心旋钮；"先量化差距再决定调不调"的 ROI 判断）
- 成本经济：`agent/skills/agent-selection/8-cost-economics.md`（M/ef 拉高 = 内存与延迟成本，最小够用原则）
- 服务·部署：`agent/skills/agent-selection/9-serving-deployment.md`（segment 分段 → 水平扩展与并发的实现基础）
- 面试包：HNSW 分层结构、M/ef 语义、ANN vs KNN 是向量检索必考题
- [[project_selection_matrix]]
