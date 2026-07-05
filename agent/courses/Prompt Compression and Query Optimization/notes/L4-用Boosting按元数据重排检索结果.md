# L4 · 用 Boosting 按元数据重排检索结果（$addFields + 加权 + $sort）

> 课程：Prompt Compression and Query Optimization（DeepLearning.AI × MongoDB，讲师 Richmond Alake）
> 本课任务：在向量检索之后，用文档自带的**定性/定量元数据**（评分、评论数）计算一个 combinedScore，重新排序检索结果——让"语义相似"之外的"客观质量"也参与排名。这就是 boosting。

## 0. 承上：L3 之后排序还是纯语义

L3 让返回文档变瘦了，但**排名 100% 由 vector search score 决定**，也就是纯语义相似度。问题在于：一个 Airbnb listing 语义上跟 query 很像，不代表它就是好选择——它可能评分很低、或只有 1 条评论。

L4 的核心命题：

> 文档里常有一些字段能影响它在结果里的位置。拿 Airbnb listing 举例，**rating（评分）和 number of reviews（评论数）** 这些定性、定量指标，能补充文档相对于用户 query 的相关性。把这些字段的值纳入考量、去影响文档在返回列表中的位置——这个技术叫 **boosting**。

为什么要 boosting（讲师给的三条理由）：

1. vector search 按语义相似度排序有效，但**元数据也贡献相关性**；
2. 用额外的定性/定量指标排序，让结果**更可信、更贴合 query**；
3. boosting 还能保证结果满足用户的**特定要求**，从而引入**个性化**。

## 1. 三个阶段拼出 boosting

boosting 在 aggregation pipeline 里由**三个连续阶段**实现，全部跑在向量检索**之后**：

```
$vectorSearch (pre-filter 检索，同 L2/L3)
   ▼
① review_average_stage   —— $addFields 算出 averageReviewScore + reviewCountBoost
   ▼
② weighting_stage        —— $addFields 用权重合成 combinedScore
   ▼
③ sorting_stage          —— $sort 按 combinedScore 降序重排
```

关键点：**阶段有先后依赖**。②要引用①算出的字段，③要引用②算出的字段——所以顺序不能乱。

## 2. 阶段①：算定性 + 定量两个新字段（$addFields）

`$addFields` 阶段给每个文档**添加新字段**（不删旧的）。这里加两个：

```python
review_average_stage = {
    "$addFields": {
        # 定性指标：把 6 个分项评分求和再除以 6，得到平均评分
        "averageReviewScore": {
            "$divide": [
                {"$add": [
                    "$review_scores.review_scores_accuracy",
                    "$review_scores.review_scores_cleanliness",
                    "$review_scores.review_scores_checkin",
                    "$review_scores.review_scores_communication",
                    "$review_scores.review_scores_location",
                    "$review_scores.review_scores_value",
                ]},
                6   # 除以分项数量 → 平均
            ]
        },
        # 定量指标：直接把 number_of_reviews 的值传给一个新字段
        "reviewCountBoost": "$number_of_reviews"
    }
}
```

两点语法要记住：

- **数学运算用 `$` 操作符**：`$add`（求和）、`$divide`（相除）。`$add` 把 6 个 review 分项加起来，`$divide` 除以 6 得平均——这是**定性**（qualitative）度量。
- **`$字段名` 是取值语法**：`"reviewCountBoost": "$number_of_reviews"` 表示"把 `number_of_reviews` 字段的值，赋给新字段 `reviewCountBoost`"。这是把一个字段的值传给另一个字段的标准写法——这是**定量**（quantitative）度量。

## 3. 阶段②：加权合成 combinedScore

有了两个度量，还得决定**它们各自对排名影响多大**——这就是权重（weighting）：

```python
weighting_stage = {
    "$addFields": {
        "combinedScore": {
            "$add": [
                {"$multiply": ["$averageReviewScore", 0.9]},  # 定性 × 权重
                {"$multiply": ["$reviewCountBoost", 0.1]}     # 定量 × 权重
            ]
        }
    }
}
```

机制：

- **`$multiply` 乘权重**：平均评分 × 0.9，评论数 × 0.1。权重用 **0～1 之间的数**分配。
- **`$add` 合并**：把两个乘积相加，得到 combinedScore，再用 `$addFields` 挂回每个文档。
- weighting_stage 必须排在 review_average_stage **之后**，才能引用到 `averageReviewScore` 和 `reviewCountBoost`。

**权重就是这套逻辑的旋钮**。L4 演示改权重看效果（见 §5），L5 里同一段代码权重换成了 `0.3 / 0.7`——权重是可调策略，不是硬编码常量。

## 4. 阶段③：$sort 重排

```python
sorting_stage_sort = {
    "$sort": {"combinedScore": -1}   # -1 = 降序（高分在前）；1 = 升序
}
```

最简单的一步：按 combinedScore 降序，让综合分高的排前面。

三阶段合成一个列表，作为附加阶段接在向量检索后：

```python
additional_stages = [review_average_stage, weighting_stage, sorting_stage_sort]
# 所有阶段在 vector search 之后按顺序执行
# 注意：这里用的仍是 L2 的 pre-filter 向量检索（vector_index_with_filter）
```

配套的 Pydantic 模型也要加上新字段才能接住：

```python
class SearchResultItem(BaseModel):
    name: str
    accommodates: Optional[int] = None
    address: custom_utils.Address
    averageReviewScore: Optional[float] = None   # L4 新增
    number_of_reviews: Optional[float] = None     # L4 新增
    combinedScore: Optional[float] = None         # L4 新增
```

## 5. 权重实验：同一批文档，两种排名

跑默认权重（0.9 定性 / 0.1 定量）后观察到一个反直觉现象：

> 有个文档**评分很高，却排在下面**——因为它**评论数少**。这就是加权的效果。

然后现场调权重，**给评论数高权重、给平均评分低权重**，重跑：

> 现在一个**评论数多**的文档，排在了一个**评分高但评论少**的文档前面。

这个对照实验说明 boosting 的价值不在公式本身，而在**权重是产品/业务决策的显式表达**——"我们更看重口碑规模还是绝对评分"这种取舍，被写成了两个可调数字。

```
默认 (0.9 / 0.1)：高评分但少评论 → 被压到后面
调后 (偏向评论数)：多评论 → 顶到前面
                    └─ 同一批召回文档，排名随权重翻转
```

## 6. boosting vs re-ranking：这是"穷人的重排"

L4 的 boosting 用**确定性数学公式**在数据库内重排，跟专门的 re-ranking（如 cross-encoder / LLM re-ranker）是两条路：

| 维度 | L4 boosting（$addFields+$sort） | 专用 re-ranker（cross-encoder / LLM） |
|---|---|---|
| 排序依据 | 结构化元数据（评分/评论数）的加权公式 | query-文档对的深层语义相关性 |
| 算力/延迟 | 几乎零，在库内完成（亚毫秒） | 需额外模型推理，延迟高 |
| 可解释性 | 完全透明（权重可读可调） | 黑盒 |
| 适用 | 元数据信号强、权衡明确的场景 | 纯语义、无好用元数据的场景 |

两者不互斥：真实系统常是"vector 粗召 → boosting 按业务元数据调 → 可选 re-ranker 精排"。

## 7. 本课总结

| 要点 | 一句话 |
|---|---|
| Boosting | 用元数据重排检索结果，让"客观好"影响排名 |
| 三阶段 | $addFields 造字段 → $addFields 加权合成 → $sort 重排 |
| 定性/定量 | averageReviewScore（评分平均）/ reviewCountBoost（评论数） |
| 数学操作符 | `$add` `$divide` `$multiply`；`$字段名` 取值 |
| 权重是旋钮 | 0～1 分配，表达"更看重哪个信号"的业务取舍 |
| 阶段有依赖 | 加权引用造字段的结果，顺序不可乱 |

> **对比 3-retrieval.md 的 re-ranking 一节**：`3-retrieval.md` 把召回后处理分成"filter → re-rank → compress"三档。L4 的 boosting 恰是 **re-rank 档里最轻量的实现**——不引入额外模型，纯靠数据库自带的元数据和 `$sort`。选型判断：**当你的文档带有强业务信号（评分、销量、时效、权限等级）且排序权衡是明确的产品决策时，boosting 比上 cross-encoder 更划算**；只有当排序纯粹取决于 query-文档的深层语义、且没有好用的结构化信号时，才值得为专用 re-ranker 付延迟和算力。

> **记忆点（引出 L5）**：到 L4 为止，检索侧的优化（filter → project → boost）都做完了——召回准、字段瘦、排序合理。但这批文档最终还是要**拼成 prompt 塞给 LLM**，而这个 prompt 可能有几千 token，按 REST API 计费会很贵。L5 转向**生成侧**：用 prompt compression（LLM Lingua）把几千 token 的 prompt 压到几百 token，直接砍 LLM 调用成本。

## 与我的资产映射

- 检索层：`agent/skills/agent-selection/3-retrieval.md`（re-ranking 一节——boosting 是元数据驱动的轻量重排）
- 选型矩阵：`agent/skills/agent-selection/`（检索后处理的取舍：数据库内 boosting vs 外挂 re-ranker）
- [[project_selection_matrix]]
