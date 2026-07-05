# L4 · 用信息检索指标度量检索质量（WANDS + ranx）

> 课程：Retrieval Optimization: Tokenization to Vector Quantization（DeepLearning.AI × Qdrant，讲师 Kacper Łukawski）
> 本课任务：**先学会度量，再谈优化**——搭一个 ground truth 数据集，用 precision/recall/MRR/DCG/NDCG 这些经典信息检索（IR）指标，客观比较两条语义检索管线谁更好。

## 0. 本课定位：优化的前提是可度量

L1-L3 讲的是"embedding 怎么来"（模型内部、tokenizer 训练、向量检索的盲区）。从 L4 起转入**优化**，而优化的第一条铁律是：

> You can't improve what you don't measure.

开场讲师甚至说：如果你不在乎 RAG 检索质量，这节可以跳过——反过来说，**在乎质量 = 必须先把质量变成一个数**。搜索引擎的相关性度量已有几十年历史，语义检索只是 IR 的一种新实现，那套度量工具原样可用。

## 1. Ground truth：一切从参考数据集开始

要判断"改动之后是不是更好了"，必须有一个不变的参照系——**ground truth 数据集**：一组 query + 每个 query 的最佳匹配文档。

构建它的现实困难（讲师明确点出）：

- **极耗人力**：需要人工标注 query 与文档的相关性；
- **意图错位**：人写出的 query 很少完美反映真实意图；
- **人群差异**：同一条 query，对不同人群相关的文档也不同。

即便如此，**一个虽小但精心标注的 ground truth 数据集是项目成熟度的标志**——它让你能追踪每次改动对质量的影响。

标注相关性有两种方式：

| 标注方式 | 含义 | 适配指标 |
|---|---|---|
| Binary（二元） | 文档"相关 / 不相关" | relevancy-based 指标 |
| Numerical（数值） | 相关性打分，越高越相关 | score-based 指标 |

## 2. WANDS 数据集：现成的带标注基准

自建成本太高，本课直接用 **WANDS（Wayfair Annotation Data Set）**——专门用来评测不同搜索方法有效性的基准，提供多个 CSV：

| CSV | 作用 | 关键列 |
|---|---|---|
| product.csv | 产品库 | product_name、product_description |
| query.csv | 测试 query（**不含**理想答案） | query |
| label.csv | ground truth：query → 文档的相关性 | label = Exact / Partial / Irrelevant |

对语义检索来说，`product_name` 和 `product_description` 都是天然的编码候选。**本课设计了两条对照管线：一条只检索 name，一条只检索 description，最后用指标裁决谁更好。**

```python
# 用同一个 sentence transformer 分别编码 name 和 description（各取前 5000 条）
model = SentenceTransformer("all-MiniLM-L6-v2")
product_name_embeddings        = model.encode(products_df["product_name"][:5000].tolist())
product_description_embeddings = model.encode(products_df["product_description"][:5000].tolist())
# description 更长 → token 更多 → 编码更慢（呼应 L2：模型吃的是 token 序列）
```

Qdrant collection 用**命名向量（named vectors）**在一个 point 上同时挂两条向量：

```python
client.create_collection(
    collection_name="wands-products",
    vectors_config={
        "product_name":        models.VectorParams(size=384, distance=models.Distance.COSINE),
        "product_description": models.VectorParams(size=384, distance=models.Distance.COSINE),
    },
    optimizers_config=models.OptimizersConfigDiff(
        default_segment_number=2,     # 分段数（L5 会讲 segment 的意义）
        indexing_threshold=1000,
    ),
)
```

把文本相关性标签映射成分数，并给 id 加前缀避免混淆：

```python
relevancy_scores = {"Exact": 10, "Partial": 5, "Irrelevant": 0}
labels_df["score"]      = labels_df["label"].map(relevancy_scores.get)
labels_df["query_id"]   = labels_df["query_id"].map(lambda x: f"query_{x}")
labels_df["product_id"] = labels_df["product_id"].map(lambda x: f"doc_{x}")
```

> **架构师视角**：`indexing_threshold` 和"上传完 ≠ 索引好"这个细节是生产坑。`client.count()` 返回满数不代表可高质量检索——向量库要在后台建 HNSW 等辅助结构，必须**轮询 collection 状态到 GREEN** 才算就绪。CI 里跑检索评测若不等 GREEN，指标会偏低且不可复现。

## 3. 三类 IR 指标：先分清再选择

每条 query 都会返回一批**按相关性（距离函数，如 cosine）排序**的结果。指标分三大类，选哪类取决于你的 ground truth 形态和业务诉求：

| 类别 | 只看什么 | 代表指标 | 适用场景 |
|---|---|---|---|
| Relevancy-based | 文档相关 / 不相关（不看位置） | precision@k、recall@k | ground truth 是二元的 |
| Ranking-related | 相关项**在结果里的位置** | MRR | 在乎"第一条就要对" |
| Score-related | 位置 + ground truth 的**相关性分值** | DCG、NDCG | 有数值标注、要综合评分 |

## 4. 五个核心指标的一句话定义

- **precision@k**：top-k 里相关文档的比例。若相关文档总数 < k，满分不可达，但仍能横比不同管线。按 query 算，再对全部 query 取平均。
- **recall@k**：top-k 覆盖了多少比例的相关文档。若相关文档 > k，满分很难。同样取平均。
- **MRR（Mean Reciprocal Rank）**：只看**第一个相关项的位置**，不管返回多少相关项。想"结果第一条就相关"就优化它——Google 首位结果点击率最高就是这个诉求。
- **DCG（Discounted Cumulative Gain）**：累计相关性，且**越往下的位置贡献越打折**，奖励"把相关项排前面"。
- **NDCG**：DCG 未归一化，除以 **IDCG（理想排序的 DCG）**归一到 0~1，便于跨 query 比较。

```
DCG 直觉：相关项越靠前得分越高，靠后有折扣
  位置:   1      2      3      4    ...
  折扣:  /log2  /log2  /log2  /log2   （越往下分母越大 → 贡献越小）
NDCG = DCG / IDCG  →  归一到 [0,1]
```

## 5. ranx：Qrels vs Run 两个核心对象

指标不要自己实现——用 `ranx`。它只有两个概念：

| 对象 | 含义 | 分值来源 |
|---|---|---|
| **Qrels** | query relevance judgments = ground truth | 整数，越大越相关（来自人工标注） |
| **Run** | 检索系统的实际输出 | 向量库返回的相似度分数 |

```python
from ranx import Qrels, Run, compare

qrels = Qrels.from_df(labels_df, q_id_col="query_id",
                      doc_id_col="product_id", score_col="score")

# 对每条 query 检索 name 向量，把 (doc_id -> score) 塞进 Run
name_run_dict = defaultdict(dict)
for id, row in queries_df.iterrows():
    results = client.search(
        "wands-products",
        query_vector=models.NamedVector(name="product_name", vector=row["query_embedding"]),
        limit=100, with_payload=False, with_vectors=False,
    )
    for p in results:
        name_run_dict[f"query_{id}"][f"doc_{p.id}"] = p.score
product_name_run = Run(name_run_dict, name="product_name")
# description 同理构造 product_description_run …
```

## 6. 裁决：name 完胜 description

```python
compare(
    qrels=qrels,
    runs=[product_name_run, product_description_run],
    metrics=["precision@10", "recall@10", "mrr@10", "dcg@10", "ndcg@10"],
)
```

**结论：所有指标都指向 product_name 是更好的语义检索候选。** 讲师提醒：你自己跑可能数值略有出入，因为不同向量库内部结构构建方式不同——这本身就是"为什么要有可复现评测"的注脚。

一个反直觉点：更长、信息更多的 description 反而不如短短的 name。这印证 L3 的主题——**更多文本 ≠ 更好向量**，噪声会稀释语义；也呼应 L2"覆盖测试集所需 token 越少可能越好"的经验。

> **对比 3-retrieval.md 的检索评测**：选型矩阵里"检索层"反复强调 offline eval 要先于任何调参。本课把它落到最小可执行形态——**ranx 的 Qrels/Run 就是检索版的单元测试**。关键裁决点：测检索比测整条 RAG 简单得多，因为端到端 RAG 通常还要引入 LLM-as-judge（另一个不确定源、另一份成本）。**能在检索层用确定性指标卡住的质量，就不要推迟到生成层用 LLM 裁判去兜底。**

## 7. 为什么这对 RAG 生死攸关

RAG 的核心假设是"把相关信息塞进 prompt 能提升 LLM 处理私有数据的能力"。但：

- prompt 里塞非本质信息 = 帮倒忙；
- 检索给不出有意义的内容 = 整条链路失败。

所以讲师的忠告是：**认真的项目从第一天就该建参考数据集**，把它当成 CI 里的一组测试用例，防止检索质量随时间悄悄退化。

## 本课总结

| 要点 | 一句话 |
|---|---|
| 度量先行 | 不能度量就不能优化，优化前先把质量变成数 |
| Ground truth | 小而精的参照集是项目成熟度标志，当成 CI 测试用例 |
| 三类指标 | relevancy（precision/recall）/ ranking（MRR）/ score（DCG/NDCG） |
| ranx | Qrels=真值、Run=系统输出，别自己实现指标 |
| name > description | 更长文本反而更差，呼应 L3"更多 token ≠ 更好向量" |

> **记忆点（引出 L5）**：本课度量的是"embedding 模型 + 检索管线"的绝对质量。但生产向量库跑的是**近似**最近邻（ANN），近似本身会掉质量。L5 把参照系换成 exact KNN，用同一套 precision@k 去量化"HNSW 近似离理论上限差多少"，并通过调 M / ef 把这个差距收窄。

## 与我的资产映射

- 检索层：`agent/skills/agent-selection/3-retrieval.md`（offline eval 是检索选型/调参的前置门；ranx Qrels/Run 是最小落地形态）
- 观测·Eval 层：`agent/skills/agent-selection/5-observability-eval.md`（检索指标 vs LLM-as-judge 的取舍：能在检索层确定性卡住的别推给生成层）
- 面试包：检索质量度量、precision/recall/MRR/NDCG 概念区分是高频考点
- [[project_selection_matrix]]
