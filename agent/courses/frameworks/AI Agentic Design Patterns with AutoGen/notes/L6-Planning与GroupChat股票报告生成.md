# L6 · Planning 与 GroupChat：群聊协作生成股票报告（含课程收官）

> 课程：AI Agentic Design Patterns with AutoGen（DeepLearning.AI × Microsoft × Penn State，讲师 Chi Wang & Qingyun Wu，AutoGen 创始人）
> 本课任务：学最后一个 agentic 设计模式 **Planning**，和一个新会话模式 **GroupChat**——五个 agent 组成群聊，在没有人工编排步骤的前提下协作完成"写一篇 Nvidia 近一个月股价表现的博客"。

## 0. 本课目标与定位

L2 的 sequential chat 也能做多步任务，但它要求**人来设计**具体步骤和每步涉及的 agent。本课换一个思路：**只定义 agent（角色），不定义步骤**，让它们自己协作把任务解出来。两件新事：

1. **Planning 模式**：往群里加一个 Planner agent，由它把复杂任务分解成子任务、分派给别人、检查进度；
2. **GroupChat 会话模式**：GroupChatManager 用 LLM 动态挑选下一个发言者，无需开发者预设发言顺序——以及当动态选择失控时，如何用 `allowed_or_disallowed_speaker_transitions` 加约束。

```python
llm_config = {"model": "gpt-4-turbo"}   # 本课任务复杂，用 GPT-4 Turbo

task = "Write a blogpost about the stock price performance of "\
       "Nvidia in the past month. Today's date is 2024-04-23."
```

## 1. 按角色定义五个 agent（而不是按步骤）

设计群聊的思考方式变了：不再问"第一步谁干什么"，而是问"**解这个任务需要哪些角色**"。答案是五个：

| Agent | 类型 | 职责 | 关键配置 |
|---|---|---|---|
| Admin (user_proxy) | ConversableAgent | 发任务、对博客给反馈让 Writer 改 | `human_input_mode="ALWAYS"`，不执行代码 |
| Planner | ConversableAgent | 分解任务、检查进度、指示剩余步骤 | 有 `description` 供 manager 选人 |
| Engineer | AssistantAgent | 按 Planner 的计划写 Python 代码 | 复用 AutoGen 默认写码 system message |
| Executor | ConversableAgent | 执行 Engineer 写的代码并报告结果 | `last_n_messages: 3`，`human_input_mode="NEVER"` |
| Writer | ConversableAgent | 按执行结果写 markdown 博客、按 Admin 反馈改 | 输出放 ```md``` 代码块 |

```python
user_proxy = autogen.ConversableAgent(
    name="Admin",
    system_message="Give the task, and send instructions "
    "to writer to refine the blog post.",
    code_execution_config=False,
    llm_config=llm_config,
    human_input_mode="ALWAYS",   # 轮到它发言时总是先问人；人跳过则由 LLM 代拟反馈
)

planner = autogen.ConversableAgent(
    name="Planner",
    system_message="Given a task, please determine what information "
    "is needed to complete the task. ... information will all be "
    "retrieved using Python code. Please only suggest information "
    "that can be retrieved using Python code. "        # 约束计划可被 Engineer 落地
    "After each step is done by others, check the progress and "
    "instruct the remaining steps. If a step fails, try to workaround",
    description="Planner. Given a task, determine what information "
    "is needed to complete the task. After each step is done by "
    "others, check the progress and instruct the remaining steps",
    llm_config=llm_config,
)

engineer = autogen.AssistantAgent(       # 用默认 AssistantAgent——自带详细写码指令
    name="Engineer",
    llm_config=llm_config,
    description="An engineer that writes code based on the plan "
    "provided by the planner.",
)

executor = autogen.ConversableAgent(
    name="Executor",
    system_message="Execute the code written by the engineer "
    "and report the result.",
    human_input_mode="NEVER",
    code_execution_config={
        "last_n_messages": 3,    # 从群聊历史倒着找最近 3 条里第一条含代码的消息去执行
        "work_dir": "coding",
        "use_docker": False,
    },
)

writer = autogen.ConversableAgent(
    name="Writer",
    llm_config=llm_config,
    system_message="Writer. Please write blogs in markdown format "
    "(with relevant titles) and put the content in pseudo ```md``` "
    "code block. You take feedback from the admin and refine your blog.",
    description="Writer. Write blogs based on the code execution "
    "results and take feedback from the admin to refine the blog.",
)
```

两个细节值得注意：Planner 的 system message 里"只建议能用 Python 代码获取的信息"是在**约束计划的可执行性**——计划再好，群里没有 agent 能落地就是空转；Executor 沿用 L5 的 dict 版 `code_execution_config`（也可换 `LocalCommandLineCodeExecutor`），`last_n_messages: 3` 决定了它回看多远去找代码。

## 2. system_message vs description：两套受众不同的文案

Planner 是本课第一个同时给了 `system_message` 和 `description` 的 agent，讲师专门解释了区别：

| 字段 | 受众 | 用途 | 写法 |
|---|---|---|---|
| `system_message` | **这个 agent 自己**（且只有它） | 指导它怎么干活 | 详细的操作指令 |
| `description` | **其他 agent**（尤其 GroupChatManager） | 让别人知道它是干嘛的 | 简短、"从别人视角能看懂这是什么角色" |

Manager 就是**根据 description 决定何时该让谁发言**的。所以 description 写得好不好，直接决定群聊会不会点错人。

> **架构师视角**：这是"一个 agent、两份接口文档"——system_message 是**实现**（内部 prompt），description 是**对外契约**（供路由决策的元数据）。这个分离与 MCP 工具的 description 字段、crewAI 的 `role`/`goal` 是同一件事：**在 LLM 驱动的动态路由系统里，agent 的自描述就是它的可发现性**。路由错乱时，第一个该查的不是路由逻辑，而是各 agent 的 description 有没有歧义/重叠。

## 3. GroupChat + GroupChatManager：组装与运行机制

角色齐了，组装只要两步——这正是"group chat 不需要多少设计步骤"的含义：

```python
groupchat = autogen.GroupChat(
    agents=[user_proxy, engineer, writer, executor, planner],  # 五个 agent 进群
    messages=[],      # 初始消息列表为空
    max_round=10,     # 最多 10 轮，到轮数即停
)

manager = autogen.GroupChatManager(   # AutoGen 的特殊 agent，管理这个群
    groupchat=groupchat, llm_config=llm_config   # 它自己也要 LLM 来选发言人
)

groupchat_result = user_proxy.initiate_chat(   # 由 user_proxy 对 manager 发起
    manager, message=task,                     # 首条消息 = 任务本身
)
```

运行机制（manager 的每一轮循环）：

```
user_proxy ──task──▶ GroupChatManager
                          │ ① broadcast：把消息广播给群里每个 agent（人人可见）
                          │ ② select：用 LLM 看「当前会话历史 + 各 agent 的
                          │    description/角色」，挑最合适的下一个发言者
                          ▼
                     被选中的 agent 发言 ──▶ 回到 ① ……直到 max_round
```

关键点：**发言顺序不是开发者写的，是 manager 的 LLM 每轮现场决策的**——依据是会话历史 + 各 agent 的角色描述。

> **对比 11-design-patterns.md**：这一课把 Ng 四大模式的最后两个（Planning、Multi-Agent）一次收齐——GroupChat 是 Multi-Agent 拓扑（manager ≈ supervisor），Planner agent 是 Planning 能力（≈ orchestrator-workers / plan-and-execute，"LLM 自主定步骤序列而非开发者硬编码"）。也要记住那份文档的成熟度立场：这两个模式最强但可控性最差，**复杂度证明值得了再上**——本课下半场演示的恰恰就是"可控性差"的实况。

> **对比课程 13 crewAI**：GroupChatManager 与 crewAI hierarchical process 的 manager agent 是同构角色——都是"一个 LLM 决定下一个干活的是谁"。差别在默认形态：crewAI 的一等公民是 sequential process（任务链是显式的，hierarchical 是可选项），AutoGen 反过来——动态群聊是主推形态，固定顺序（L2 sequential chat）才是特例。同一根轴的两端：**crewAI 从确定性出发按需加自主，AutoGen 从自主出发按需加约束**。

## 4. 运行轨迹：Planner 主导的 plan-and-execute 循环

第一次运行（无任何顺序约束），manager 自发选出的轨迹：

| 轮次 | 发言者（manager 选） | 干了什么 |
|---|---|---|
| 1 | Admin → manager | 发出任务（广播给所有人） |
| 2 | **Planner** | 给出初始计划：① 取股票数据 ② 分析数据 ③ 调研背景事件 ④ 起草博客 ⑤ 迭代 |
| 3 | Engineer | 按步骤①写取数代码 |
| 4 | Executor | 执行，输出股价数据 |
| 5 | **Planner**（再次） | 检查进度，指示后续步骤，还给了步骤②的代码起手式 |
| 6 | Engineer | 补全数据分析代码 |
| 7 | Executor | 执行，输出股价 + 日涨跌幅 |
| 8 | Writer | 认为信息够了，直接起草 markdown 博客（引言/股价分析/表现/重大事件影响/结论） |
| 9 | Admin | 轮到人给反馈；讲师跳过输入 → LLM 代拟改进意见（加视频、更细分析、交互元素等） |
| 10 | Writer | 按反馈修订博客并总结增强点，到 `max_round=10` 停止 |

复盘：Planner 确实履行了"出计划 → 步骤完成后复查 → 指示剩余步骤"的角色。**但计划没有被完全遵守**——Writer 跳过了步骤③（调研背景事件）直接开写。讲师点明：这是**用 LLM 全权决定发言顺序的固有缺点**。

> **架构师视角**：注意这个失败模式的位置——不是某个 agent 能力不行，而是**编排层（谁该说话）的决策错了**。LLM 路由的错误率会乘在每一轮上：10 轮群聊里只要 manager 选错一次人，整个计划就短路。这就是为什么"全自主编排"的 demo 惊艳、上生产却难：你需要把关键转移收敛为确定性规则——正是下一节的内容。

## 5. 加约束：allowed_or_disallowed_speaker_transitions

修复方式：重新定义同一批 agent（description 微调），建 GroupChat 时传入**发言转移约束**——一个"当前发言者 → 允许的下一个发言者列表"的字典：

```python
groupchat = autogen.GroupChat(
    agents=[user_proxy, engineer, writer, executor, planner],
    messages=[],
    max_round=10,
    allowed_or_disallowed_speaker_transitions={
        user_proxy: [engineer, writer, executor, planner],  # Admin 之后谁都能接
        engineer:   [user_proxy, executor],          # 写完代码 → 只能 Admin 或 Executor 接
        writer:     [user_proxy, planner],           # 写完博客 → 只能 Admin 或 Planner 接
        executor:   [user_proxy, engineer, planner], # 执行完 → Admin/Engineer/Planner，没有 Writer！
        planner:    [user_proxy, engineer, writer],
    },
    speaker_transitions_type="allowed",   # 声明这份字典是"允许表"（也可给"禁止表"）
)
```

设计意图看 `executor` 那行：**Executor 之后 Writer 不在允许列表里**——代码刚跑完不许直接开写博客，必须先经 Planner（或 Admin/Engineer），这就把"Planner 复查计划"的机会用硬约束保住了。重跑后的轨迹：前几步相同，但第二步执行完后**Planner 如期接管**，复盘已完成步骤、指示下一步——上一节的问题被修复。

三个观察：

1. **约束 ≠ 线性化**：加了约束后任务完成过程依然是非线性的，agent 仍可来回穿插、按需插话——比 sequential chat 灵活；
2. 这种转移约束**等价于在群聊里模拟有限状态机（FSM）**的状态转移——manager 的 LLM 只在允许集合内选人；
3. 代码文件的尾注提醒：实际运行可能出现 Engineer 写错代码 → Executor 报错 → 打回修改的多轮循环——错误恢复回路是这套机制天然自带的。

> **对比课程 11 LangGraph**：`allowed_or_disallowed_speaker_transitions` 本质上是在**事后给群聊补一张图**——节点 = agent，允许表 = 边，manager 的 LLM 在出边集合里做条件路由。LangGraph 则是把这张图**一开始就显式画出来**（`add_edge` / `add_conditional_edges`），控制流是一等公民。同一目标（约束控制流）的两个方向：AutoGen 是"自由群聊 − 减掉不许走的路"，LangGraph 是"空白图 + 加上允许走的路"。审计要求高的场景，后者的图定义本身就是文档；快速原型阶段，前者少写一半代码。

## 6. 控制力谱系：三档递进

讲师总结了给 GroupChat 加控制的三条路，控制力递增：

| 档位 | 手段 | 控制粒度 |
|---|---|---|
| ① 硬约束 | `allowed_or_disallowed_speaker_transitions`（FSM 式转移表） | 限定"谁能接谁"，选择仍由 LLM |
| ② 软引导 | 在 agent 的 `description` 里写自然语言转移提示 | 告诉 manager"何时该转给谁"的细节 |
| ③ 全接管 | 用编程语言定义精确的转移顺序（本课未展开，见 AutoGen 官网） | 完全确定性，LLM 不参与选人 |

本课小结：group chat 提供了一种**更动态**的多 agent 协作方式，无需开发者设计详细执行计划；再配一个 Planner agent 负责计划与任务分解。任务分解与 planning 有多种做法，本课只展示了其中一种。

课程正文最后还点了 AutoGen 未覆盖的进阶方向：**Teachability**（agent 随时间被教会、持续改进）、**多模态/视觉**（理解图像）、**OpenAI Assistant 作为 agent 后端**、**agent 评估与 benchmark 工具**、以及"如何为特定任务设计 agent"等新研究——见官网与博客。

## 全课收官

### 结语要点（Conclusion）

- 本课程覆盖了 AutoGen 中的几个 agentic 设计模式：**multi-agent collaboration、reflection、tool use、code generation、planning**；
- 这些是**积木（building blocks）**——组合它们可以构建有创意的应用、解决非常复杂的任务；
- 更多进阶特性见官网；感谢开源社区，Discord 社区已超 16,000 名成员。

### L1–L6 六课回顾

| 课 | 案例 | 设计模式 / 会话模式 | 一句话 |
|---|---|---|---|
| L1 | 单口喜剧对话 | ConversableAgent 两 agent 对话 | 一切的原语：agent 之间靠"发消息-回消息"协作 |
| L2 | 客户入职流程 | Sequential chat + carryover | 人工编排的多步任务链，前序摘要作为上下文接力 |
| L3 | 博客写作评审 | Reflection（嵌套评审） | 用嵌套 chat 让评审员团队批判-改进，质量换 token |
| L4 | 对话象棋 | Tool Use | 工具注册给 LLM 选、执行归 executor，两端分离 |
| L5 | 财务分析 | Code Generation & Execution | 让 agent 现场写代码并沙箱执行，代码即万能工具 |
| L6 | 股票报告博客 | **Planning + GroupChat（Multi-Agent）** | 只定义角色不定义步骤，manager 动态选人 + FSM 约束兜底 |

前五课的模式在 L6 全部会师：GroupChat 里有 L1 的对话原语、L5 的代码执行（Engineer+Executor 对）、L3 式的反馈修订回路（Admin→Writer），Planner 补上最后一块 Planning——这门课的结构本身就是"积木→组合"的示范。

> **架构师的裁决**：AutoGen 的 conversation-first 编排范式——一切协作皆对话、控制流是对话的涌现属性、约束是事后往对话上加的——**适合**：任务分解方式无法预先枚举的开放探索型任务（研究、数据分析→报告）、快速原型验证"多 agent 到底有没有增益"、以及人随时要插进对话的场景（human_input_mode 是一等公民）。**不适合**：步骤可枚举、失败成本高、要审计回放的生产流水线——LLM 选人的每一轮都是一个不可复现的分支点，10 轮就是 10 次路由赌博。取舍判据就一条轴：**控制流的确定性要求**。步骤已知走 crewAI sequential / 简单 chaining；控制流复杂但可画成图（分支/循环/checkpoint/HITL 审批）走 LangGraph；真正"不知道要几步、谁先谁后"的任务才轮到 AutoGen GroupChat——而且一旦从 demo 走向生产，第一件事就是像本课下半场那样，把跑出来的隐式秩序固化成 transition 约束，向 FSM/图那端回收控制权。

## 本课总结

| 要点 | 一句话 |
|---|---|
| GroupChat 会话模式 | 只定义角色不定义步骤，五 agent 进群 + `max_round` 封顶 |
| GroupChatManager | 特殊 agent：广播消息 + 用 LLM 按"历史+description"选下一个发言者 |
| system_message vs description | 前者给 agent 自己（实现），后者给别人尤其 manager（路由契约） |
| Planning 模式 | Planner agent 出计划→复查进度→指示剩余步骤，且计划受"Python 可落地"约束 |
| 失控与修复 | LLM 选人会跳步；`allowed_or_disallowed_speaker_transitions` + `speaker_transitions_type="allowed"` 以 FSM 式转移表兜底 |
| 控制力谱系 | 硬约束转移表 → description 软引导 → 编程定义精确顺序，三档递进 |

## 与我的资产映射

- 设计模式层：`agent/skills/agent-selection/11-design-patterns.md`——Planning（≈ orchestrator-workers）与 Multi-Agent（supervisor 拓扑）两个叠加维度的活教材；"最强但可控性差、复杂度证明值得了再上"的立场在 L6 的跳步事故里有了实证
- 框架层：`agent/skills/agent-selection/2-framework/03-framework-profiles.md`——AutoGen conversation-first vs LangGraph 图编排 vs crewAI 角色编排的三方对照，本课补齐 AutoGen 一侧的第一手细节
- 面试包：`agent/interview/jd-senior-agent-engineer/01-agent-run-loop-and-orchestration`——GroupChatManager 的"广播+LLM 选人"循环、FSM 转移约束、控制力三档谱系都是编排题的高频素材
- [[project_selection_matrix]]
