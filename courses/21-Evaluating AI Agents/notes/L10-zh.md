# L10：评估驱动开发——把所有评估器组装成结构化实验

前面建好了 Trace、Skills 评估、Router 评估、Convergence 评估，本节把这些拧成一根绳——**评估驱动开发（Evaluation-Driven Development, EDD）**。

## 什么是评估驱动开发

> 用评估结果**指导**你把时间花在哪儿改进、用什么模型、改什么 Prompt、调什么逻辑。

四步循环：

1. **筛选一组测试用例（Dataset）**
2. **跑多个智能体变体**（换模型、换 Prompt、换工具描述、改路由逻辑）
3. **用同一套评估器**度量每个变体
4. **对比分数**做出改动决策

> 这看起来是线性的，**实际上是个飞轮**：上线后用真实数据扩充测试集和评估器，再回到开发期持续迭代。

## 数据集设计：求"代表性"，不求"穷尽"

- 关键是**覆盖不同类型的输入**——每类有 1~2 条代表样本即可
- 不要追求成百上千条；相似样本意义不大
- 来源：人工构造、生成模型合成、或**生产真实样本回流**
- **尽量带 expected output**——很多代码评估器需要 ground truth；不过 LLM-as-a-judge 不一定需要

## 可以变更的智能体维度

- Prompt
- 工具定义（描述、参数说明）
- 路由器逻辑
- 技能的内部结构
- 模型本身

把"用某个数据集跑某个智能体变体"叫一次 **Experiment（实验）**。

## 例：评估 Router

测试用例：

```
input: "Which stores had the best sales performance in 2021?"
expected_output: "lookup_sales_data"  # 期望调用的工具
```

实验维度：**改不同的工具描述**。
评估器：

- Code-based 比对 ground truth 工具名
- LLM-as-a-judge 函数调用评估（无需 ground truth）

## 例：评估数据库查询工具

测试用例：

```
input: "Which stores had the best sales performance in 2021?"
expected_output: "SELECT Store_Number, SUM(Total_Sale_Value) ... ORDER BY ... LIMIT 1"
```

> 这里的 expected_output 是 SQL 生成步骤的中间产物——证明**评估可以落在工具内部的某一步**。

实验维度：换 SQL 生成 Prompt、换模型。
评估器：Code-based vs ground truth SQL。

## 例：评估数据分析工具（无 ground truth）

测试用例只有 `input + 检索到的数据`，**没有 expected output**——开放式分析没法预先写答案。
评估器：**Analysis Clarity** + **Entity Correctness**（两个 LLM-as-a-judge）。

## 评估总览：HUD（Heads-Up Display）

把多次运行 × 多个评估器排成表格，每一行是一次实验，每一列是一个评估指标——你能**整体性**看到每个改动的影响：

```
| Experiment        | Tool Calling | SQL Gen | Clarity | Entity | Code Runnable |
|-------------------|-------------:|--------:|--------:|-------:|--------------:|
| v1 baseline       |         0.85 |    0.60 |    1.00 |   0.83 |          1.00 |
| v2 new SQL prompt |         0.85 |    0.45 |    0.71 |   0.83 |          1.00 |
```

## 上线后形成飞轮

进入生产后：

- 发现新的失败模式 → 加入测试集
- 用户反馈 → 衍生新评估器
- CI/CD 持续跑实验，确保每次部署不引入回归

这样开发期的工具自然延伸到生产期，**整套评估资产是可复用的**。

## 小结

本节你掌握了 EDD 的全貌：从数据集、实验到评估器，再到 HUD 式的对比视图。下一节将用代码把它落到本课程的智能体上，构造一张完整的"评估仪表盘"。
