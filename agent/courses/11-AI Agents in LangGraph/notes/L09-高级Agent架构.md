# L09 高级 Agent 架构（Advanced Agent Flows / Conclusion）

> 原始字幕：`subtitles/langchain_c5_09.vtt`

---

## 一、本节目的

课程收官。在你已掌握基础的情况下，Harrison 介绍**本课程没覆盖、但你应当知道**的几种前沿 agent 架构。

---

## 二、架构 1：Multi-Agent（多智能体共享状态）

> 多个不同的 agent **操作同一份共享状态**。

### 特点
- 每个 agent 可以是：
  - 只有 prompt + LLM（像 L07 Essay Writer 里的 planner / writer / critic）
  - prompt + LLM + tools
  - 内部本身还有循环的 sub-agent
- 本质：**同一个 state 在 agent 之间传递**。

### 示意
```
[ Agent A ]──►[ Agent B ]──►[ Agent C ]
     \_________________________/
            共享 State
```

L07 的 Essay Writer 就是这种模式的朴素实现——所有节点读写同一个 `AgentState`。

---

## 三、架构 2：Supervisor Agent（监督者模式）

> 有一个 **supervisor（监督者）** 负责**调度多个 sub-agent**。

### 与 Multi-Agent 的关键差异

| 维度 | Multi-Agent | Supervisor |
|---|---|---|
| 状态 | **共享同一 state** | sub-agent **各自有内部 state**（它们是独立的图） |
| 调度 | 节点之间固定 / 条件边传递 | **supervisor 决定**调谁、传什么输入 |
| 核心角色 | 无中心控制 | 中心化 supervisor 做**路由 + 协调** |

### 什么时候选 Supervisor
> 当你能给 supervisor 配一个**非常强大的 LLM** 时。
> 因为 supervision 和 planning 本身需要极高的推理能力。

### 示意
```
           ┌─────────────┐
           │ Supervisor  │ ←── 强 LLM，做路由
           └──────┬──────┘
        ┌────────┼────────┐
        ▼        ▼        ▼
   [Sub-Agent] [Sub-Agent] [Sub-Agent]
   （各自独立的 graph，有自己的 state）
```

---

## 四、架构 3：Flow Engineering（流程工程）

> 概念来自 **AlphaCodium** 论文——在编程基准上取得 SOTA 表现。

### 核心思想
- **流水线（pipeline）为主**，关键节点**嵌入小循环**；
- 典型循环点：
  - 初始代码方案的迭代
  - 公开测试上的迭代
  - AI 任务上的迭代
- 形态上：**前半是有向线性流，后半是关键节点上的迭代**。

### 更广义的定义
> Flow Engineering = 思考 **agent 应该按什么样的信息流来行动和思考**。

即：不要把 agent 的"自由度"设得太高让它乱走，而是精心设计**信息如何在节点间流动**。

---

## 五、架构 4：Plan-and-Execute（先规划后执行）

### 流程
```
1. Planner 先明确列出要做的所有步骤
2. 依次派给 sub-agent 执行
3. 每步完成后：
   - 要么继续执行下一步
   - 要么根据结果 update plan（有些变体会重规划）
4. 全部完成后检查：
   - 如果计划成功 → 返回用户
   - 如果不够 → replan
```

### 为什么重要
- 把"思考"和"行动"**明确分开**
- 对长任务比"边走边想"稳定得多
- L07 的 Essay Writer 里的 `planner` → `research_plan` → ... 本质上就是这个思路

---

## 六、架构 5：Language Agent Tree Search (LATS)

> 来自论文 *Language Agent Tree Search*。

### 核心思想
> 对"可能动作的状态空间"做**树搜索**，类似 MCTS（蒙特卡洛树搜索）。

### 过程
```
1. 生成一个 action（节点）
2. 反思（reflect）评估这个 action
3. 根据评估展开子 action（子节点）
4. 继续反思 → 继续展开
5. 反思过程中可以决定"跳回树上某个祖先节点"
6. 反向传播（backprop）更新祖先节点的信息
   → 让未来的展开用到更丰富的经验
```

### 关键依赖
> **Persistence 极其重要** —— 因为要能"回到历史状态"，这正是 L05、L06 学过的能力。

这是 LangGraph 这类图式架构能很自然表达的模式，也是它相比其它框架的优势。

---

## 七、五种架构对照

| 架构 | 核心特征 | 典型用途 | 依赖基础能力 |
|---|---|---|---|
| **Multi-Agent** | 多角色 + 共享 state | 团队式协作（写作、研究） | State / 节点 / 条件边 |
| **Supervisor** | 中心调度多子 agent | 复杂任务分派 | 多层图嵌套 |
| **Flow Engineering** | 有向流 + 关键节点循环 | 代码生成等高要求任务 | 条件边 + 循环 |
| **Plan-and-Execute** | 先规划后执行 + 可重规划 | 长任务（出差计划、多步运维） | 状态存储 + 条件边 |
| **LATS（树搜索）** | 对动作空间做反思 + 回溯 | 需探索大量方案的高难度任务 | **Persistence** + 回退 |

---

## 八、LangGraph 的定位总结

Harrison 的收官观点：

> **LangGraph 的核心差异化 = Controllability（可控性）。**

- 允许创建**循环 / 非循环**的任意控制流
- **高度可控** —— 区别于其他框架
- Harrison 认为：
  > "高可控性是做出 **真正能跑起来** 的 agent 的关键。"

---

## 九、课程总览（Week 1 的 9 节）

| 节次 | 主题 | 关键产出 |
|---|---|---|
| L01 | 课程介绍 | 五大设计模式 + LangGraph 的由来 |
| L02 | 从零 ReAct Agent | 理解 LLM 与 runtime 的分工 |
| L03 | LangGraph 组件 | Nodes / Edges / Conditional Edges / State |
| L04 | Agentic Search | Tavily，结构化给 agent 用 |
| L05 | Persistence & Streaming | Checkpointer + thread_id + token stream |
| L06 | Human in the Loop | 批准 / 改状态 / 时间旅行 / 伪造结果 |
| L07 | 项目实战 Essay Writer | 融合所有概念的多节点循环 agent |
| L08 | 延伸资源 | 生态文档、LangServe、LangSmith |
| L09 | 高级架构 | Multi-agent / Supervisor / Flow / Plan-Execute / LATS |

---

## 十、课程收获清单（你现在会做什么）

- [x] 用裸 Python + LLM 手写 ReAct Agent
- [x] 用 LangGraph 定义状态图、条件边、循环
- [x] 把 Tavily 作为 agent 的工具使用
- [x] 实现多会话、可恢复、带流式输出的 agent
- [x] 在关键节点插入人工审批、修改状态、回到历史
- [x] 用结构化输出（Pydantic）保证 LLM 输出可被解析
- [x] 组装多节点 + 多角色 + 多轮迭代的复杂 agent
- [x] 了解 Multi-agent / Supervisor / Flow Engineering / Plan-Execute / LATS 等前沿模式

> **下一步**：动手把这些概念用到你自己的业务场景——或继续学 Multi AI Agent Systems with crewAI / AutoGen 等多 agent 框架。
