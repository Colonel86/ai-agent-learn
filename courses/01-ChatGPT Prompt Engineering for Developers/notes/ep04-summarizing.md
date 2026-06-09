# EP04: Summarizing（文本摘要）

> 学习日期：2026-04-15
> 所属阶段：Phase 1 · 基石构建
> 课程来源：DeepLearning.AI × OpenAI（Andrew Ng + Isa Fulford）

---

## 应用场景

现代人信息过载，LLM 的摘要能力可以帮助快速处理大量文本——电商评论、新闻、报告等。

## 基础摘要

```python
prompt = f"""
你的任务是生成一段电商产品评论的简短摘要。
用不超过 30 个词总结以下评论。
评论：{review}
"""
```

## 定向摘要（面向特定受众）

同一篇评论，针对不同部门可以生成不同侧重的摘要：

**面向物流部门：**
```python
prompt = f"...重点关注任何提到运输和配送的方面。评论：{review}"
# 输出：产品比预期早一天到达
```

**面向定价部门：**
```python
prompt = f"...重点关注与价格和感知价值相关的任何方面。评论：{review}"
# 输出：价格相对尺寸可能偏高
```

## Extract vs Summarize（提取 vs 摘要）

| 方式 | 指令 | 结果 |
|---|---|---|
| 摘要（Summarize） | "总结评论" | 包含多方面信息，全面但有噪音 |
| 提取（Extract） | "提取与配送相关的信息" | 只给出"比预期早一天到达"，精准无噪音 |

根据下游任务的需求选择合适的方式。

## 批量处理多条评论

```python
reviews = [review_1, review_2, review_3, review_4]  # 熊猫玩具、台灯、电动牙刷、搅拌机

for i, review in enumerate(reviews):
    prompt = f"用最多20个词总结以下评论：{review}"
    response = get_completion(prompt)
    print(f"评论 {i+1}：{response}")
```

适用于电商后台仪表盘，让运营人员快速浏览大量评论。
