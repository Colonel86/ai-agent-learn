# L8：评估智能体走过的路径——轨迹与收敛度

除了评估技能和路由器，还要确保智能体**用合适数量的步骤**完成任务。本节介绍**轨迹（Trajectory）**与**收敛度（Convergence）**评估。

## 什么是 Agent Trajectory

**Trajectory（轨迹）**就是智能体针对一个输入，走过的"路由器 → 工具 → 其他逻辑步骤"的完整路径。

### 例 1：简单查询

> "Which store had the most sales in 2021?"

路径：`User → Router → [lookup_sales_data + analyze_sales_data] → Router → User`

> 注意本课的智能体允许路由器**一次返回多个工具调用**，所以两个工具并排在一个步骤里。有的架构会限制一次只能调一个工具——这只是架构选择问题。

### 例 2：复杂查询

> "Plot sales data volume over time"

路径：`User → Router → [lookup_sales_data + analyze_sales_data] → Router → generate_visualization → Router → User`

到了**多智能体系统（Multi-agent Systems）**，轨迹会迅速复杂化。

## 轨迹为什么重要？效率

> "只要输出对了，路径对不对要紧吗？"

**要紧**——尤其是生产场景：

- 用 6 步完成 vs 用 11 步完成 = 更少 LLM 调用 = **更低成本**
- 更短轨迹 = **更低延迟**、更稳定
- 短轨迹意味着**更少非确定性**累积

业余项目 / 一次性研究当然可以不关心效率，但任何面向用户的智能体都得关心。

## Convergence：度量"路径效率"的方法

**Convergence（收敛度）**：衡量智能体在某类查询上有多接近"最优路径"。

### 计算流程

1. 准备一批**意思相近但表述各异**的查询——它们理应走相同路径，但实际可能有偏差
2. 把每条查询喂给智能体，记录步数（path length）
3. 找出这批运行中**最少的步数**——视为该任务的"最优路径长度"
4. 公式：
   ```
   convergence_score = mean(optimal_steps / actual_steps_per_run)
   ```
   完美收敛 = 1.0，总在 0~1 之间

> 也可以理解为：**有多大比例的运行走了最优路径**。

## 使用 Convergence 的两个坑

1. **如果每次运行都多了同一个"无用步骤"，Convergence 评估抓不住**——因为最优路径取的是这批运行的最小值，所有运行同步多余的话最小值也跟着多余
2. **只统计完整跑完的运行**——中途报错的运行步数不要计入，否则会严重歪曲数据

## 小结

本节你学到了**轨迹**与**收敛度**的概念，以及为什么效率值得追踪。下一节用 Phoenix 的实验机制具体实现 Convergence 评估。
