# L3 · 用 Projection 在数据库侧裁字段（$project 投影阶段）

> 课程：Prompt Compression and Query Optimization（DeepLearning.AI × MongoDB，讲师 Richmond Alake）
> 本课任务：在 MongoDB aggregation pipeline 里加一个 **projection（投影）阶段**，让向量检索返回的文档只带需要的字段，把"裁字段"这件事从应用层下沉到数据库层。

## 0. 承上：L2 留下的问题

L2 讲的是用 **metadata（元数据）** 做多阶段 aggregation pipeline——给向量 embedding 配上 title/artist/location 这类附加信息，用 `$match` 之类的阶段在检索时按元数据过滤，提升效率和相关性。到 L2 结束，检索能返回"对的文档"了，但返回的**每个文档还是整条**——所有字段原封不动带回来。

L3 要解决的正是这个"字段太肥"的问题。上一课（L2/L1）里，裁掉不要的字段是靠 **Pydantic 模型**在应用层做的：定义一个 model，只声明你想要的属性，多余字段在 Python 侧被丢弃。这有个隐性代价：

> 不想要的数据**仍然要经过网络传输、仍然要在应用层被处理**，然后才被过滤掉。增加网络流量、增加处理时间。

一句话概括 L3 的立场：**过滤应该发生在数据最早能被丢弃的地方——数据库里**，而不是等它千里迢迢传到应用层再扔。

## 1. 什么是 Projection

Projection 是 MongoDB 里"选择性包含/排除字段"的技术，作为 aggregation pipeline 的**又一个阶段**加进去。它的定义性特征：

- **输出文档数量 = 上一阶段的文档数量**（不改变行数）；
- **只减少每个文档里返回的字段数**（改变列数）。

对照 L2 那张 Mona Lisa 文档，projection 可以把一条包含 title/artist/location/embedding/... 的完整文档，砍成只剩你点名的几个字段。

三条好处（讲师明确列出）：

| 好处 | 机制 |
|---|---|
| 降低应用层内存占用 | 数据库操作返回的数据更少，应用层要装的东西就少 |
| 降低查询执行时间 | 更少数据传输 = 更快返回 |
| 安全与隐私 | 敏感字段（如金融应用里的个人信息）可以在数据库层就剥离，不流向下游 |

第三点是架构上最值钱的：让**数据库承担"发出去之前先脱敏"的逻辑**，下游进程根本拿不到敏感字段，整体安全性提升——这不是应用层"我拿到了但我不用"能比的。

> **架构师视角**：Projection 的本质是**把过滤器推到离数据源最近的地方（predicate pushdown 的思想）**。Pydantic 在应用层裁字段是"防御式"的——数据已经传过来了，你只是不看它；Projection 是"根治式"的——数据压根不出库。对隐私合规（数据不离开可信边界）和成本（网络/内存/RAG 下游的 token 都省），后者是唯一正确答案。判断准则：**只要能在源头裁，就不要在下游裁**。

## 2. `$project` 阶段：包含 vs 排除

Projection 阶段用 `$project` 操作符定义，接收一个"描述哪些字段要投影"的文档：

```python
projection_stage = {
    "$project": {
        "_id": 0,                    # 排除：0 表示不要这个字段
        "name": 1,                   # 包含：1 表示保留
        "accommodates": 1,
        "address.street": 1,         # 支持点号访问嵌套字段
        "address.government_area": 1,
        "address.market": 1,
        "address.country": 1,
        "address.location.coordinates": 1,
        "summary": 1,
        "space": 1,
        "neighborhood_overview": 1,
        "notes": 1,
        "score": {"$meta": "vectorSearchScore"}   # 见 §3
    }
}
additional_stages = [projection_stage]   # 放进列表，作为附加阶段传给向量检索
```

两条必须记住的规则：

1. **`_id` 是自动返回的**。aggregation pipeline 返回的每个文档都会带 `_id` 字段——除非你显式 `"_id": 0` 排除它。
2. **包含即排除**：一旦你点名了要包含的字段（用 `1`），**所有没点名的字段自动被排除**。你不需要把不要的字段一个个写 `0`。

### 关键坑：包含模式和排除模式不能混用

这是 L3 现场演示的一个报错。规则：**同一个 projection 里，要么全用 `1`（inclusion 模式），要么全用 `0`（exclusion 模式），不能混**。唯一的例外是 `_id`——它可以在 inclusion 模式里单独写 `0` 来排除。

演示：把上面某个本该是 `1` 的字段改成 `0`，运行 → **database operation failure**。往下滚看原因：`invalid $project document`，因为"你不能在一个 inclusion projection 里做 exclusion"。修复方法：把它改回 `1`，遵守 inclusion 模式。

```
inclusion 模式：{name:1, summary:1, _id:0}   ✓  （_id 是唯一可混的例外）
exclusion 模式：{summary:0, notes:0}         ✓
混用：         {name:1, notes:0}            ✗  OperationFailure
```

## 3. 顺手把 vector search score 取出来

`$project` 里有一行特殊写法：

```python
"score": {"$meta": "vectorSearchScore"}
```

这不是投影已有字段，而是用 `$meta` 把**向量检索的相似度分数**"物化"成文档里的一个真实字段 `score`。这样分数就能跟着文档一起返回、被 Pydantic 模型接住、最终展示出来。

分数范围 **0～1**，越接近 1 表示语义相似度越高。这是 L4 boosting 的伏笔——L4 要在这个 vector score 之外，再叠加评分/评论数等元数据来重排。

## 4. 让 Pydantic 模型和 projection 对齐

投影出来的字段，要和接住结果的 Pydantic 模型**一一对应**（代码注释明写：`Ensure that the projection document in the projection stage matches the search result model`）：

```python
class SearchResultItem(BaseModel):
    name: str
    accommodates: Optional[int] = None
    address: custom_utils.Address
    summary: Optional[str] = None
    space: Optional[str] = None
    neighborhood_overview: Optional[str] = None
    notes: Optional[str] = None
    score: Optional[float] = None      # L3 新增：接住 vectorSearchScore
```

`handle_user_query` 里加了一句调试打印，专门观察"projection 放行了哪些字段"：

```python
# 取第一条结果、遍历它的 keys —— 看 projection 之后、送进 Pydantic 之前
# 文档到底剩哪些字段
print(get_knowledge[0].keys())
```

跑完观察到两件事：① 向量检索操作在**不到 1 毫秒**内完成；② 返回文档里的字段，正好就是 projection 里点名的那些（name / summary / space / ...），加上带出来的 `score`。**结果集不变、命中的还是同样的文档**——只是每个文档瘦了一圈。

## 5. 数据流全景

```
用户 query
   │  embedding
   ▼
┌─────────────── aggregation pipeline ───────────────┐
│  $vectorSearch (带 pre-filter，见 L2)               │
│      → 返回 N 条完整文档（字段全、体积大）           │
│  $project  ← 本课新增                                │
│      → 仍是 N 条，但每条只剩点名字段 + score         │
└─────────────────────────────────────────────────────┘
   │  更小的结果集
   ▼
Pydantic SearchResultItem（应用层，字段已对齐）
   ▼
拼进 prompt → 送 LLM（gpt-3.5-turbo）
```

对照 L2：pipeline 从"检索 + 元数据过滤"变成"检索 + 元数据过滤 + 投影裁字段"。每加一课，pipeline 就多接一节。

## 6. 本课总结

| 要点 | 一句话 |
|---|---|
| Projection = 数据库侧裁字段 | `$project` 阶段，行数不变、列数变少 |
| 三大收益 | 省内存、省查询时间、能在库内脱敏 |
| 包含/排除不可混 | 一个 projection 全 `1` 或全 `0`，`_id` 是唯一例外 |
| 包含即排除 | 点名了要保留的，其余自动丢弃 |
| `$meta` 取分数 | `{"$meta": "vectorSearchScore"}` 把相似度物化成字段 |
| 与 Pydantic 对齐 | 投影字段集必须匹配 SearchResultItem |

> **对比 8-cost-economics.md 的成本分层**：`8-cost-economics.md` 把 RAG 成本拆成"检索成本 + 上下文 token 成本 + 生成成本"。Projection 精准打在**中间那层**——它不减少检索次数，但直接减少每条召回文档塞进 prompt 的字段量，等于在源头压缩了 context token。这和 L5 的 prompt compression 是**同一目标的两级火箭**：L3 在结构化层面砍掉整个不需要的字段（无损、零算力），L5 在自然语言层面压缩保留字段的措辞（有损、需小模型算力）。先做 L3 再做 L5，顺序不能反。

> **记忆点（引出 L4）**：L3 让返回的文档"更瘦"，但**排序还完全由 vector search score 决定**——纯语义相似度。可现实里一个 Airbnb listing 的好坏还取决于**评分高不高、评论多不多**。L4 引入 **boosting**：用 `$addFields` 把这些定性（rating）/定量（review count）元数据算进一个 combinedScore，再 `$sort` 重排，让"语义像"之外的"客观好"也能影响排名。

## 与我的资产映射

- 检索层选型：`agent/skills/agent-selection/3-retrieval.md`（向量检索后处理——projection 是 retrieval 结果整形的第一手段）
- 成本层：`agent/skills/agent-selection/8-cost-economics.md`（context token 成本——数据库侧裁字段是压 token 的最便宜一招）
- [[project_selection_matrix]]
