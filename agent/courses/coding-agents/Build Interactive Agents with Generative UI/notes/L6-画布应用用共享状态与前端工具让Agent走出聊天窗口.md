# L6 · 画布应用：用共享状态 + 前端工具让 Agent 走出聊天窗口（收官）

> 课程：Build Interactive Agents with Generative UI（DeepLearning.AI × CopilotKit）
> 本课任务：造一个「Agentic 待办板」全栈应用——Agent 从后端建/改待办，用户在前端勾选，两侧**自动双向同步**。用到两个新原语：**Shared State 同步**与 **Frontend Tool 调用**。这是造 Claude Code / Cursor 式应用（across 法律/会计/营销任意垂直）的地基。末尾并入 Conclusion，收全课。

## 0. 承上：从「聊天窗口内」到「聊天窗口外」

L3–L5 造的富 UI 都活在聊天框里。L6 冲出去，做**真正像「同事」的全栈 Agent**：Agent 从后端创建待办，用户在前端编辑/完成，**两侧自动保持同步**。

## 1. 什么是「好的全栈 Agentic 应用」（产品视角）

写代码前，字幕先退一步问：从产品角度，什么算好？

- **直觉的 UX 是地基**。不要逃离 chat 模态——但 chat ≠ 纯文本，要做**增强型 chat**（叠加 generative UI、语音、甚至视频）。
- **给用户看见 Agent 在干什么**：既为保持参与，更为**赢得信任**、给用户**引导（steer）Agent** 的机会。
- **chat 不能孤立存在**：Agent 应像大应用的**原生一部分**，能用到应用的任何 data / context / connectors / actions。经验法则：**凡用户在大应用里能做的动作 / 能获知的事实，也应能通过 chat 做到 / 获知**。
- **Agent 要深访实时上下文**：用户当前在看什么、当前有哪些可用动作。

三个标杆例子：**Cursor / GitHub Copilot**（Agent 融进工作区本身，读代码、改文件、跑命令，不用离开编辑器）；**Notion AI**（自动知道页面上有什么，嵌在文档里而非旁边）；**Harvey**（法律 AI，与律师并肩起草文档、分析合同，是协作者而非 chatbot）。

**关键洞察**：跨极不同领域的 Agentic 应用，最终都建在**同一小撮核心原语**上——其一是前几课的生成式 UI 光谱，本课再补两块：**前端工具调用** + **共享状态同步**。

## 2. 原语一：前端工具调用（Frontend Tool Calling）

与你熟悉的后端工具调用**直接类比**，唯一区别：**动作在前端应用里执行**，而不只在 Agent 运行处。

- React 里用 `useFrontendTool` hook 注册：给 name、description、参数（Zod schema）、以及被调用时执行的 handler。
- handler **可以是异步的**；若返回结果，该结果作为标准 tool call result **回传给 Agent**。
- 注册可**集中**（应用初始化时）或**分散**（散在各处，随用户在应用里穿行**自动加载/卸载**）。

**底层时序**（开发者无需操心，只管调 hook）：

```
Agent 决定调某前端工具
  → AG-UI 识别到、暂停后端执行
  → 把控制权交给前端、执行 handler
  → 前端产出结果 → 回传后端
  → agentic loop 继续
```

## 3. 原语二：共享状态同步（Shared State）

**默认 Agent 与前端是断连的**：Agent 不知道用户看到啥，前端不知道 Agent 知道啥。Shared State 就是解这个的原语。

- 用 Agent 的**标准状态抽象**（本课用 LangChain agent state）；
- 前端用 `useAgent` hook，拿到一个**响应式更新的、带类型的 state 对象**。

**底层机制**：

```
Agent 运行时更新自己的 state
  → emit「state delta 事件」（增量，因常由 LLM 生成而被流式推送）
  → 前端 state 随之同步
前端也能 emit state delta 事件（承载用户侧的修改）
需要时，两侧状态的冲突消解由 AG-UI middleware 处理
```

字幕收束：这些都是**日常开发无需感知的实现细节，你只管用 `useAgent`**。

## 4. 代码：Agentic 待办板

### 4.1 后端：状态 schema + 两个操作状态的工具

```python
class Todo(TypedDict):
    id: str; title: str; completed: bool

class AgentState(BaseAgentState):     # 继承 LangChain 的 AgentState
    todos: list[Todo]

@tool
def manage_todos(todos: list[Todo], runtime: ToolRuntime) -> Command:
    """整体替换待办列表（增/改/删都走这个）"""
    for t in todos:                                  # 没 id 的补一个
        if not t.get("id"): t["id"] = str(uuid.uuid4())
    # Command 让工具「更新图状态」+「返回工具结果」一步完成
    return Command(update={
        "todos": todos,
        "messages": [ToolMessage("Successfully updated todos",
                                 tool_call_id=runtime.tool_call_id)],
    })

@tool
def get_todos(runtime: ToolRuntime):
    """读当前待办（改之前先看一眼）"""
    return runtime.state.get("todos", [])

todo_tools = [manage_todos, get_todos]
```

Agent 挂上状态 schema、工具、中间件：

```python
agent.graph = create_agent(
    model=ChatOpenAI(model="gpt-4.1"),
    state_schema=AgentState,           # ← 声明共享状态结构
    tools=todo_tools,
    middleware=[CopilotKitMiddleware()],  # ← 让 CopilotKit/AG-UI 栈易与 LangChain 交互
    checkpointer=MemorySaver(),
    system_prompt=("你管理一份共享待办。用 manage_todos 增改删、get_todos 查看。"
                   "被要求管理待办时，先调 openOrCloseTodos 前端工具 open=true。回复 1-2 句。"),
)
```

### 4.2 前端：`useFrontendTool` + `useAgent` 双向绑状态

```tsx
export default function App() {
  const [todosOpen, setTodosOpen] = useState(false);

  // 🪁 注册一个前端工具，让 Agent 能开/关面板（浏览器侧执行）
  useFrontendTool({
    name: "openOrCloseTodos",
    description: "Open or close the todo panel.",
    parameters: z.object({ open: z.boolean() }),
    handler: async ({ open }) => { setTodosOpen(open); return `Todos are ${open?'open':'closed'}.`; },
  });

  // 🪁 订阅共享 agent state
  const { agent } = useAgent();

  return <TodoAppLayout chat={<CopilotChat />} open={todosOpen} onOpenChange={setTodosOpen}
    panel={(onClose) => (
      <TodoList
        todos={agent.state.todos || []}                      // 🪁 读共享状态
        onUpdate={(updated) => agent.setState({ todos: updated })}  // 🪁 写共享状态
        isRunning={agent.isRunning} onClose={onClose} />
    )} />;
}
```

字幕感叹此处「相当深刻」：**`useAgent` 提供了前后端全功能状态同步**——像本地标准 React state 一样响应式，可直接在应用里用；而每一次状态更新、流式、上下文消解都自动处理。开发者**把它当本地 state 用即可**，底层自动与 agentic 后端保持同步。

### 4.3 演示：双向同步跑通

`Add three todos about learning CopilotKit` → Agent **先开面板**（前端工具）**再填数据**（`manage_todos` 改状态）；在面板里直接勾选一条 → 问 `What's on my list?` Agent 读到最新状态答对；`Remove all completed todos` → Agent 用过滤后的列表调 `manage_todos`。**同步双向成立**。

> **架构师视角**：`useAgent` 把「跨进程的分布式状态一致性」这个**本该很脏的问题**（增量流式、冲突消解、断流重连）压缩成一句「像本地 React state 一样用」。这是一种典型的**抽象杠杆**——但架构师要清醒：抽象没消灭复杂度，只是把它挪进了 middleware。生产环境的问号仍在——LLM 生成的 state delta 与用户的本地编辑撞车时，AG-UI 的冲突消解策略是什么？多用户并发编辑同一 state 怎么办？断线重连后如何对齐？课程演示是单用户、内存态；把它抬到生产，这些正是要压测的地方。**便利越大，越要知道抽象在替你藏什么。**

> **对比 LangGraph 后端的原生状态**：本课的「共享状态」不是 CopilotKit 另造的东西——它**直接复用 LangGraph 的 agent state**（`AgentState` 继承自 LangChain `BaseAgentState`），工具用 LangGraph 原生的 `Command(update={...})` 改状态。CopilotKit/AG-UI 做的只是**把这份后端状态「投射」到前端**（`useAgent`）并维持双向同步。这印证了 `10-agent-ux.md` 的「反向约束」：**选了 AG-UI/CopilotKit 呈现层，后端最好用有 AG-UI 适配的框架**——正因为 shared state 靠的是后端框架的原生状态抽象 + Command/checkpointer 机制，换个没有细粒度状态与中断-恢复能力的后端，这套双向同步就接不上。呈现层与编排框架在此**强耦合**，必须 plan 期一起拍。

## 全课收官

### ① Conclusion 要点

字幕结语的核心一句：**「没有一种方案能统治全部（no one approach to rule them all）」**——生成式 UI 光谱每一段服务不同需求，你现在有工具在自己应用里**混搭（mix and match）**。因为一切都建在**开源 AG-UI 协议**上，这些模式**通行整个 agentic 生态，不止 CopilotKit**（AG-UI 已被 Google / Microsoft / Amazon / LangChain / Oracle 采纳）。

本课只探了**agentic 前端栈的第一层**。后面还有：**持久层**（沉淀这些富交互）、**洞察层**（理解用户在生产中如何与 Agent 交互）、直到**自我改进层**（Agent 跨交互学习、随时间自行提升）。

### ② L1–L6 全课回顾表

| 课 | 主题 | 一句话 | 光谱定位 |
|---|---|---|---|
| **L1** | 生成式 UI 光谱心智模型 | 三支柱：受控 / 声明式 / 开放式，及各自何时用（AG-UI 协议贯穿全课） | 全景 |
| **L2** | Agent Chat UI 地基 | 把 React 前端接到 LangChain Deep Agent（及 Google ADK agent），生产级起点 | — |
| **L3** | 受控生成式 UI | 程序员定全自定义组件，Agent 填数据；控外观、Agent 控意图；光谱的「主力」 | ◀ 最可控 |
| **L4** | 声明式生成式 UI（A2UI） | 建组件目录让 Agent 自己拼；dynamic（Agent 搭结构）vs fixed（程序员写死） | 中段 |
| **L5** | 开放式生成式 UI | MCP Apps 挂第三方应用 + `openGenerativeUI` 当场手写界面；最灵活最不可控 | 最灵活 ▶ |
| **L6** | 画布应用（共享状态） | 走出聊天窗口：`useFrontendTool` + `useAgent` 让前后端共享实时状态、双向同步 | 超越光谱 |

### ③ 架构师的裁决

> **架构师的裁决**：
>
> **生成式 UI 何时值得做？** 判据不是「炫不炫」，而是「**Agent 的产出需不需要被看见/被操作**」。纯后台批处理、单轮问答——一个打字机文本流就够，别引入这层。一旦要「过程透明（工具调用/检索/审批）」或「产出可交互（表单/图表/画布）」，才动它。且**按界面重要性分层混用**，而非全站一种：
> - **高频 + 品牌门面**（航班卡、结账页）→ **受控式(L3)**，吃像素级可控 + 可预测，值得手写；
> - **长尾 + 内部工具**（退款、找丢失设备、临时报表）→ **声明式(L4)**，一份目录覆盖、省 token；
> - **有现成第三方应用的工具型任务**（白板、设计、规划）→ **MCP Apps(L5)**，外包给成熟应用；
> - **无先例、无需每次可靠的创意界面** → **Open-Ended(L5)**，当探索性投资，回报吃 prompt/skill。
>
> **AG-UI/CopilotKit 这类框架 vs 手写前端？** 框架的真正价值不在「能渲染组件」——那手写也行——而在**把三件脏活标准化**：① 前后端**事件协议**（约 16 个 AG-UI 事件）；② **流式 + 状态双向同步 + 冲突消解**（`useAgent` 一行搞定，手写要造一套分布式一致性）；③ **中断-恢复 / HITL 控制权交接**（前端工具那套 pause-handoff-resume）。**选框架**当：要做协作型 agentic 前端、后端已在 LangGraph 这类有 AG-UI 适配的栈、且看重跨生态可迁移（AG-UI 开源、多厂采纳）。**手写前端**当：界面极简（纯文本流打字机就够）、或有硬性理由不吃 CopilotKit runtime 抽象与其事件模型绑定。取舍本质是——**框架替你藏了分布式状态与协议复杂度，代价是把你绑在它的抽象上；界面越简单，这笔交易越不划算；交互越像「真同事」，这笔交易越值。**

## 本课总结

| 要点 | 一句话 |
|---|---|
| 走出聊天窗口 | 让 Agent 像「同事」：融入大应用、深访实时上下文、能做用户能做的一切 |
| 两个新原语 | Frontend Tool（`useFrontendTool`，浏览器侧执行、结果回传）+ Shared State（`useAgent`，前后端双向同步） |
| 后端 | `Command(update={...})` 一步「改状态 + 回工具结果」；`state_schema=AgentState`（LangGraph 原生状态） |
| 前端 | `agent.state.todos` 读、`agent.setState({todos})` 写，当本地 React state 用，同步自动 |
| 抽象与代价 | `useAgent` 藏起流式/冲突消解/重连；生产要压测并发与冲突策略 |

## 与我的资产映射

- 呈现层选型：`agent/skills/agent-selection/10-agent-ux.md`（③工具调用可视化 + ④HITL 维度；「呈现层反向约束编排框架」的第一手实证——shared state 靠 LangGraph 原生状态）
- 记忆/状态：`agent/skills/agent-selection/6-memory.md`（agent state 作为 shared state 载体，与 checkpointer 持久化）
- 面试包：`agent/interview/1.md`（前后端 Stream 事件模型全景——`STATE_DELTA` 双向、前端工具的 pause-handoff-resume）；本全课可作「Agentic 前端栈」JD 素材
- 设计模式：`agent/skills/agent-selection/11-design-patterns.md`（生成式 UI 光谱按界面重要性分层混用的裁决表）
- [[project_selection_matrix]] · [[project_interview_prep]]
