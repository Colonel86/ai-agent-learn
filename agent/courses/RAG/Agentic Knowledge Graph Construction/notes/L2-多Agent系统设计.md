# L2 · 多 Agent 系统设计：把构图流程编排成一队 Agent

> 课程：Agentic Knowledge Graph Construction（DeepLearning.AI × Neo4j，C2）
> 本课任务：给出 Agent 的工程定义、多 Agent 系统的协作方式，然后展开本课要构建的**完整 Agent 架构大图**——从顶层对话 Agent 到 User Intent / File Suggestion / Schema Proposal 等专职子 Agent，以及它们的产出物如何拼成图谱。

## 1. Agent 的工程定义："一种花哨的控制流算子"

讲师从工程视角定义 Agent：**一个循环，循环里调一次 LLM，LLM 决定想做什么，把决定传回代码侧（client），落到一个 switch 语句执行相应动作**。智能行为来自 LLM 调用，但**执行仍然由代码完成**。

**优点**：
- 强大——LLM 做推理 + 调工具，工具能做任何代码能做的事；
- 自适应——LLM 有 memory，能从对话或存入 memory 的信息里学习，影响后续决策；
- 上手快——基本上就是用自然语言 prompt 描述 Agent 该干什么。

**代价**：
- 慢——远程 LLM 调用又贵又慢；
- 非确定性——因为 LLM 本身非确定；
- token 成本累积——生产环境成千上万次调用，成本涨得飞快。

> **架构师视角**："agent = loop + LLM + switch" 这个还原论定义值得钉在脑子里：它提醒你 Agent 的**不确定性和成本都集中在 LLM 调用那一格**。因此优化方向很清楚——能用确定性代码/工具做的就别让 LLM 反复推理，把 LLM 只用在"需要判断"的节点。这也正是下面**用多 Agent 拆分**的动机之一。

## 2. 多 Agent 系统：分层 + 两种交互方式

**多 Agent 系统 = 多个 Agent 协作于单一目标**，典型排成**层级**：顶层 Agent 管总流程，下面挂任意多个子 Agent，各管一个工作阶段或一个具体任务。讲师明确：**转向多 Agent 恰恰能改善上面单 Agent 的那些缺点**（把大任务拆小、各用合适的小模型/短上下文，降低成本和错误传播）。

交互有两种方式：

```
                 ┌──────────────┐
   user ───────▶ │  Root Agent  │   主对话线程
                 └──────┬───────┘
             delegate   │   delegate
          ┌─────────────┴─────────────┐
          ▼                           ▼
    ┌───────────┐               ┌───────────┐
    │  Agent A  │               │  Agent B  │
    │  (tools)  │               │  tools:   │
    └───────────┘               │   ...     │
                                │   p() ────┼──▶ 其实是一个 Agent
                                └───────────┘     被当作 tool 调用
```

1. **Agent Delegation（委派）**：主对话线程和用户跑着，每个 Agent 判断"这活我能干还是该交给别人" → root 可委派给 Agent A 或 B；
2. **Agent-as-Tool（Agent 当工具）**：Agent B 的某个"工具" `p()` 其实本身是个 Agent，只是**被当成工具来调用**。

每次这类转移（transition）处都可以设**与用户的检查点（checkpoint）**。

> **对比 11-design-patterns.md 的多 Agent 模式**：本课把资产库里抽象讲的两种组合方式落到了实处——**hierarchical delegation**（root→sub）对应"编排者/工作者"，**agent-as-tool** 对应"把子 Agent 封装成可调用能力"。资产里的判断依据在这里得到印证：**delegation 适合"换个专家接管整段对话"，agent-as-tool 适合"我主导流程、只借它算一步"**。后面 Schema Proposal 的 Critic 对则是第三种——同层两 Agent 互相制衡的循环。

## 3. 要构建的完整 Agent 架构

本课构建的是一个 **Knowledge Graph Agent** 的若干部分，重点在**执行图谱构建的子 Agent**。你会学到：用 ADK 造 Agent 的基础、什么是 memory 及如何用它记录关键信息、定义工具，以及**如何从开放式对话收敛到可执行代码**。

### 3.1 顶层：对话向导 Agent

最上层 Agent **自己不干活**，只负责把用户引导过整个工作流——从知识图谱构建一路到 graph retrieval，让用户理解"这里能做什么、Agent 的职责边界在哪"。

### 3.2 中层：三条工作流

```
                    ┌─────────────────────────┐
                    │   Top-level 对话向导 Agent │
                    └───────────┬─────────────┘
        ┌───────────────────────┼───────────────────────┐
        ▼                       ▼                       ▼
┌────────────────┐   ┌──────────────────┐   ┌────────────────┐
│ Structured Data│   │ Unstructured Data│   │  GraphRAG Agent│
│    Agent       │   │     Agent        │   │  (用图谱答问)   │
│ (workflow)     │   │  (workflow)      │   └────────────────┘
└────────────────┘   └──────────────────┘
```

- 左侧两条是 **workflow agent**：Structured Data Agent 和 Unstructured Data Agent，各自把用户从"想做什么"带到"构建出图"；
- 右侧 **GraphRAG Agent** 在前两者建好图之后，帮用户**用图谱回答问题**。
- 两条 workflow 的**前两步是共用的**（下面 3.3 的 User Intent + File Suggestion 两侧相同）。

### 3.3 结构化数据工作流的子 Agent

把你自己当成被指派干这活的数据工程师，这几个子 Agent 就是你会依次做的事：

| 子 Agent | 干什么 | 产出物 |
|---|---|---|
| **User Intent Agent** | 对话式澄清："你到底想让我做什么、目标是什么、要什么分析"——先把方向钉死 | 用户目标（user goal） |
| **File Suggestion Agent** | 基于已确立的目标，看磁盘上有哪些数据文件，挑出对达成目标有用的 | 一份**经用户批准**的建议文件清单 |
| **Schema Proposal Agent** | **一对 Agent，Critic Pattern**：一个提 schema 方案，一个批评"这里不太对、这样改" | **Graph Construction Plan** |

**Critic Pattern 细节**：这对 Agent 内部循环遍历可能性、自我批评，最终产出一个好的 graph schema——既用上一阶段批准的文件，又符合第一阶段设定的用户目标，能回答对用户有用的问题。注意产出的 **Graph Construction Plan 不是图本身，而是"如何构建这张图"的说明**。

### 3.4 非结构化数据工作流的差异

前两步（User Intent + File Suggestion）和结构化侧**完全一样**，只是处理的是 Markdown 文件。**第三步不同**：手上只有文本，怎么建图？——用两个专职 Agent 通读文本，识别 **entities**（人、地点、事物）和描述这些 entity 的 **facts**（如"abk 爱喝 Phil's 的咖啡"）。

关键：这个 Agent 的目标是**找出"能抽哪些类型的事实"，而不是真的去抽**——只描述可能性，产出 **Knowledge Extraction Plan**。

### 3.5 收口：一个"多合一"的构建工具

**Graph Construction Plan（结构化侧）+ Knowledge Extraction Plan（非结构化侧）合在一起，就是构图所需的全部规则**。架构图角落里那个红盒子是**一个对外单一、内部多工具**的 tool，它真正执行：

- 遍历所有 construction rule → 建出 domain graph；
- 遍历所有 Markdown → chunk 化 → 向量嵌入；
- 抽取 entities 和 facts → 连回结构化数据。

**分工要点**：前面那些 Agent 做的是**"该做什么工作"的推理**，这个工具做的是**"真正动手"的重活**。推理与执行分离。

## 4. 课程后续安排

- **L4–L8**：走完整条结构化数据工作流——user intent → file suggestions → schema proposal；
- 然后跳到非结构化数据，只做 **entity 和 fact type 的 proposal**；
- **L8**：那个真正做图谱构建的工具。
- 下一课（L3）先动手写代码，用 **Google ADK** 造第一个 Agent（已熟 ADK 者可跳过，但推荐看，能理解讲师的实现思路）。

## 本课总结

| 要点 | 一句话 |
|---|---|
| Agent 定义 | loop + LLM 决策 + 代码侧 switch 执行；强大但慢/非确定/贵 |
| 多 Agent 动机 | 分层拆任务，正好缓解单 Agent 的慢/贵/错误传播 |
| 两种交互 | delegation（委派整段）+ agent-as-tool（当工具借一步） |
| 三条工作流 | 结构化 / 非结构化 workflow + GraphRAG Agent；前两步共用 |
| 关键产出物 | Graph Construction Plan + Knowledge Extraction Plan = 全部构图规则 |
| 推理/执行分离 | Agent 推理"该做什么"，红盒子工具做"真正建图"的重活 |

> **记忆点（引出 L3）**：L2 是纯设计蓝图——知道了要造一队分层 Agent、每个 Agent 的职责和产出物。L3 落到最小可运行单元：用 **Google ADK** 的 `Agent` / `Runner` / `SessionService` 亲手造并跑一个带工具的 hello_agent，把"agent = loop + LLM + switch"这个定义在事件循环（event loop）代码里看个明白。

## 与我的资产映射

- 设计模式：`agent/skills/agent-selection/11-design-patterns.md`（hierarchical delegation / agent-as-tool / Critic Pattern——本课把三种多 Agent 模式一次性落到构图任务）
- 检索层：`agent/skills/agent-selection/3-retrieval.md`（GraphRAG Agent 是这套架构的检索出口）
- [[project_selection_matrix]]（框架层：Google ADK 的 workflow agent / 子 Agent 编排能力评估）
