# L06 Human in the Loop（人在回路）

> 原始字幕：`subtitles/langchain_c5_06.vtt`
> 原始代码：`code/Lesson_6_Student.md`

---

## 一、本节目标

在 agent 执行的关键节点**插入人工干预**，包括：
1. 在工具执行前**暂停**并让人类批准；
2. 在断点处**修改 state**；
3. **时间旅行（Time Travel）**：回溯到任意历史状态并继续 / 分支；
4. **手动注入消息**：模拟 tool 执行结果。

这些模式的基础全部依赖 L05 的 **Persistence（checkpointer）**。

---

## 二、关键改造 1：自定义 Reducer（消息合并函数）

### 为什么要改？
前面都用 `Annotated[list, operator.add]`——**只追加，不替换**。
在 Human-in-the-Loop 中我们可能需要**替换已有消息**（比如修改 LLM 决定的 tool call 参数）。

### 实现

```python
from uuid import uuid4

def reduce_messages(left: list[AnyMessage], right: list[AnyMessage]) -> list[AnyMessage]:
    # 给没 id 的新消息分配 id
    for message in right:
        if not message.id:
            message.id = str(uuid4())

    merged = left.copy()
    for message in right:
        for i, existing in enumerate(merged):
            if existing.id == message.id:
                merged[i] = message        # 同 id → 替换
                break
        else:
            merged.append(message)          # 不同 id → 追加
    return merged

class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], reduce_messages]
```

**核心规则**：
- 同 `id` → 替换
- 新 `id` → 追加

---

## 三、关键改造 2：interrupt_before

在 `graph.compile` 里加一个参数：

```python
self.graph = graph.compile(
    checkpointer=checkpointer,
    interrupt_before=["action"]        # ← 在 action 节点执行前暂停
)
```

效果：
> 每次 LLM 决定调用工具后，流程**停在 action 节点之前**，等待外部（人类）批准才继续。

---

## 四、模式 1：人工批准

### 1. 启动执行
```python
messages = [HumanMessage(content="Whats the weather in SF?")]
thread = {"configurable": {"thread_id": "1"}}

for event in abot.graph.stream({"messages": messages}, thread):
    for v in event.values():
        print(v)
```
流程在 LLM 输出 tool_call 后**停下**（因为 `interrupt_before=["action"]`）。

### 2. 查看当前状态
```python
abot.graph.get_state(thread)         # 当前完整状态
abot.graph.get_state(thread).next    # 下一个要执行的节点 → 'action'
```

### 3. 继续执行：`stream(None, thread)`
```python
for event in abot.graph.stream(None, thread):
    for v in event.values():
        print(v)
```

**关键点**：`input=None` 告诉 graph"接着上次 checkpoint 继续"，而不是提供新输入。

### 4. 交互式批准循环

```python
while abot.graph.get_state(thread).next:
    _input = input("proceed?")
    if _input != "y":
        print("aborting")
        break
    for event in abot.graph.stream(None, thread):
        for v in event.values():
            print(v)
```

这就是一个**可审批的 agent**：每次要调用工具前，问一次人。

---

## 五、State Memory 与访问 API

### 1. 每个 state snapshot 里有什么

| 字段 | 含义 |
|---|---|
| `values` | 你定义的 `AgentState`（这里即 messages） |
| `config` | 包含 `thread_id` 和 `thread_ts`（快照唯一 ID） |
| `next` | 下一个要执行的节点名 |

### 2. 常用 API

| 方法 | 作用 |
|---|---|
| `get_state(thread)` | 获取**当前**状态 |
| `get_state(state_config)` | 获取某个**特定快照**（通过 `thread_ts`） |
| `get_state_history(thread)` | 迭代所有历史快照（最近的在前） |
| `update_state(thread, values)` | 修改状态 → **生成新的 checkpoint** 作为当前态 |
| `update_state(config, values, as_node=...)` | 以某个节点身份写入 state（影响 `next` 计算） |

### 3. 控制流

| 入口形式 | 效果 |
|---|---|
| `graph.stream({"messages": ...}, thread)` | 新输入，从头 |
| `graph.stream(None, thread)` | 从 thread 当前快照继续 |
| `graph.stream(None, past_state.config)` | 从指定历史快照恢复（**time travel**） |

---

## 六、模式 2：修改当前状态（Modify State）

场景：LLM 把"LA"理解成了 Los Angeles，但用户本意是 Louisiana，想在工具执行前纠正。

```python
# 运行到 interrupt 后
current_values = abot.graph.get_state(thread)

# 定位要修改的 tool_call
_id = current_values.values['messages'][-1].tool_calls[0]['id']

# 重写 tool_calls（查询词改为 Louisiana）
current_values.values['messages'][-1].tool_calls = [
    {'name': 'tavily_search_results_json',
     'args': {'query': 'current weather in Louisiana'},
     'id': _id}        # ← 保留原 id，这样 reducer 会"替换"而非追加
]

# 提交修改
abot.graph.update_state(thread, current_values.values)

# 继续执行
for event in abot.graph.stream(None, thread):
    ...
```

**机制**：
- 改完的消息 `id` 不变 → 自定义 reducer 识别为"替换";
- `update_state` 产生新的 checkpoint；
- `stream(None, thread)` 继续执行，走的是改后的 tool_call。

---

## 七、模式 3：时间旅行（Time Travel）

### 1. 拉出历史快照
```python
states = []
for state in abot.graph.get_state_history(thread):
    states.append(state)
```
> 注意：最近的快照排在最前（`states[0]` = 最新）。
> 录制时示例用 `states[-1]`，新版 LangGraph 因为多存了几条初始快照，需要用 `states[-3]`。

### 2. 从某个历史点恢复
```python
to_replay = states[-3]
for event in abot.graph.stream(None, to_replay.config):
    ...
```

用历史快照的 `config` 当作起点，agent 会从那个 state "重新执行"后续流程。

### 3. 回到过去并分支编辑

```python
# 选一个历史点
to_replay = states[-3]

# 在那个点修改 tool_calls
_id = to_replay.values['messages'][-1].tool_calls[0]['id']
to_replay.values['messages'][-1].tool_calls = [{
    'name': 'tavily_search_results_json',
    'args': {'query': 'current weather in LA, accuweather'},
    'id': _id
}]

# 用历史快照的 config + 修改后的值更新 → 得到一条新"分支"
branch_state = abot.graph.update_state(to_replay.config, to_replay.values)

# 从分支继续
for event in abot.graph.stream(None, branch_state):
    ...
```

**与模式 2 的区别**：
- 模式 2 是修改**最新**状态；
- 模式 3 是**回到过去**再修改，产生**新分支**，原历史仍保留。

---

## 八、模式 4：伪造工具结果（`as_node` 手动更新）

场景：不真正调用 Tavily，而是**手动 mock 一个工具响应**注入 state，让 agent 基于此继续推理。

```python
_id = to_replay.values['messages'][-1].tool_calls[0]['id']

state_update = {"messages": [ToolMessage(
    tool_call_id=_id,
    name="tavily_search_results_json",
    content="54 degree celcius",        # 我们伪造的"观察"
)]}

# 关键：as_node="action"
branch_and_add = abot.graph.update_state(
    to_replay.config,
    state_update,
    as_node="action"
)

for event in abot.graph.stream(None, branch_and_add):
    ...
```

### 为什么必须 `as_node="action"`

| 不指定 as_node | 指定 `as_node="action"` |
|---|---|
| state 改了，但 next 还是 "action"（会再去执行工具） | 告诉 graph："这个 update 是 action 节点的输出"，next 自然推进到下一节点（回到 LLM） |

这样 agent 会跳过真实的 tool 执行，直接相信我们写入的 ToolMessage，回到 LLM 生成最终回答。

运行结果：
> *"The current weather in Los Angeles is 54°C"* —— 用的是我们伪造的观测值。

---

## 九、四种 Human-in-the-Loop 模式汇总

| 模式 | 做什么 | 核心 API |
|---|---|---|
| **1. 人工批准** | 工具执行前暂停等批准 | `interrupt_before=["action"]` + `stream(None, thread)` |
| **2. 修改当前状态** | 在断点处改 tool_calls / 消息内容 | `update_state(thread, new_values)` |
| **3. 时间旅行 + 分支** | 回到任意历史快照再执行或改 | `stream(None, past.config)`、`update_state(past.config, ...)` |
| **4. 伪造工具结果** | 不调工具，手工注入观察 | `update_state(..., as_node="action")` |

---

## 十、完整 Agent 代码（L05 → L06 新增项）

```python
class Agent:
    def __init__(self, model, tools, system="", checkpointer=None):
        self.system = system
        graph = StateGraph(AgentState)
        graph.add_node("llm", self.call_openai)
        graph.add_node("action", self.take_action)
        graph.add_conditional_edges(
            "llm", self.exists_action,
            {True: "action", False: END}
        )
        graph.add_edge("action", "llm")
        graph.set_entry_point("llm")

        # ↓ 本课关键：interrupt_before
        self.graph = graph.compile(
            checkpointer=checkpointer,
            interrupt_before=["action"]
        )
        self.tools = {t.name: t for t in tools}
        self.model = model.bind_tools(tools)
```

外加自定义的 `reduce_messages` + `AgentState` 替换掉 `operator.add`。

---

## 十一、本节要点速记

- **`interrupt_before=[node]`** 让执行在进入某节点前暂停，是人工审批的基石。
- **`stream(None, thread)`** 表示"继续跑"，不是新输入。
- **`update_state`** 产生新的 checkpoint；若要让 graph 知道这是某节点的输出，用 `as_node=...`。
- **自定义 reducer**（同 id 替换、新 id 追加）支撑了"改写历史消息"。
- `get_state_history` + 历史快照的 `config` = **时间旅行**和**分支**。
- 可以用 `ToolMessage` + `as_node="action"` **完全绕过真实工具执行**，注入 mock observation。
- 所有这些能力共享一个底座：**Persistence / Checkpointer**。

> 下一节：课程**终章项目** —— 构建一个更复杂的多 LLM 调用、多阶段状态的 agent。

---

## 十二、面试速答总结

**一句话**：Human-in-the-Loop 的所有花样都建立在 **Persistence（checkpointer）** 这一个底座上——用 `interrupt_before` 在关键节点前**暂停**，用 `stream(None, thread)` **续跑**，用 `update_state`（必要时带 `as_node`）**改状态/伪造观察**，用 `get_state_history` + 历史快照 config **时间旅行与分支**；而"能改写历史消息"又依赖一个**自定义 reducer**（同 id 替换、新 id 追加）。

### 面试回答骨架（问"agent 怎么加人工审批 / 怎么纠错 / 怎么回溯调试"）

> 1. **底座先亮明**：四种模式共享一个基础——**checkpointer 持久化**。没有"每步存 state + 可恢复任意快照"，人工干预无从谈起（这也是 L05 → L06 的连贯逻辑）。
> 2. **模式1 人工批准**：`compile(interrupt_before=["action"])` 让流程在**工具执行前停下**；`get_state(thread).next` 看下一步；`stream(None, thread)`（`input=None` = 续跑而非新输入）放行。套个 `while state.next: input('proceed?')` 就是可审批 agent。
> 3. **模式2 改当前状态 / 模式4 伪造结果**：`update_state(thread, values)` 会产生**新 checkpoint**。改 tool_call 参数（如把误解的 LA 改成 Louisiana，**保留原 id** 让 reducer 替换）；或用 `update_state(..., as_node="action")` **注入一条 ToolMessage 冒充工具输出**，让 agent 跳过真实调用、next 自然推进回 LLM。
> 4. **模式3 时间旅行 + 分支**：`get_state_history` 拿历史快照，用某个快照的 `config` 当起点 `stream(None, past.config)` 就能**回到过去重跑**；在历史点改值再 `update_state` 就得到**新分支**，原历史仍在。

### 关键判断（加分点）

- **为什么要自定义 reducer**：默认 `operator.add` 只追加，无法"改写已存在的消息"。HITL 要**替换** LLM 已决定的 tool_call，所以换成「同 id 替换 / 新 id 追加」的 reducer——**id 是替换与追加的开关**。
- **`as_node` 是最容易答漏的点**：不指定 as_node，state 改了但 `next` 仍是 "action"，会再去真跑工具；指定 `as_node="action"` 等于告诉图"这是 action 的输出"，next 才推进——用于 mock 工具、离线调试、绕过昂贵/危险调用。
- **HITL 的工程价值**：高风险动作（下单、发邮件、删数据）前插审批；LLM 误解参数时人工纠正;时间旅行让 agent 缺陷**可复现、可分支对比**——这三点直接对应生产安全与可调试性。

### 为什么这是高分答法

- 把四种看似零散的模式收敛到**一个底座（persistence）+ 三个 API（interrupt_before / stream(None) / update_state）**，结构清晰可复述；
- 答出 reducer 的 id 语义和 `as_node` 这两个"魔鬼细节"，证明是真写过而非背概念。

**一句话收尾**：Human-in-the-Loop 不是给 agent 加个确认框，而是靠持久化把 agent 的**每一步 state 变成可暂停、可修改、可回溯、可伪造**的对象——审批、纠错、时间旅行本质是同一套 checkpoint 能力的不同用法，这正是"可控 agent"落到生产的关键。

> 关联：`L05-持久化与流式输出.md`（checkpointer 底座）、`L07-项目实战-Essay-Writer.md`（GUI 里把这些 API 可视化）、`L09-高级Agent架构.md`（LATS 回溯同源）。
