# L4 · 多 Agent 团队与会话记忆（ADK 委派 + Session State）

> 课程：Agentic Knowledge Graph Construction（DeepLearning.AI × Neo4j，C2）
> 本课任务（对应课程 Lesson 3 Part II）：把 L3 里的单个 ADK Agent 扩展成一个「root + 两个 sub-agent」的多 Agent 团队，跑通**自动委派（delegation）**，再引入 **Session State** 让工具跨轮记住信息。这是后面所有 KG 构建 Agent 的地基。

## 0. 承接 L3：从单 Agent 到 Agent 团队

L3 用 Google ADK 建了一个只会 `say_hello` 的单 Agent（Part I），并封装了 `AgentCaller` 执行环境和工厂函数 `make_agent_caller`。本课（Part II）不重复造轮子，直接 `from helper import make_agent_caller`，把注意力放在**多 Agent 编排**和**记忆**两件事上。技术栈仍是 `google.adk`（`Agent` / `Runner` / `InMemorySessionService`）+ LiteLlm 接 `openai/gpt-4o` + Neo4j（`say_hello` 底层其实是发一条 Cypher `RETURN`）。

路线三步：**① 定义 sub-agent 的工具 → ② 定义 root + 两个 sub-agent 跑委派 → ③ 加 Session State 让记忆跨轮**。

## 1. 三个角色：root（coordinator）+ 两个 sub-agent

| 角色 | 名字 | 职责 | 工具 |
|---|---|---|---|
| root / coordinator | `friendly_agent_team_v1` | 接收用户输入，决定自己答还是委派 | **无**（只能聊天或委派） |
| greeting sub-agent | `greeting_subagent_v1` | 只负责打招呼 | `say_hello(person_name)` |
| farewell sub-agent | `farewell_subagent_v1` | 只负责告别 | `say_goodbye()`（无参数，返回常量） |

术语澄清：root agent 也叫 **orchestrator / coordinator / top-level agent**，本质是"包住另外几个 agent 并管理它们执行"的那个 agent。

## 2. delegation 的关键：description 给别人看，instruction 给自己看

这是本课反复强调的最佳实践，也是委派能否生效的命门：

- **`description`**：写给**其他 agent**看的——"我是干什么的、什么时候该调我"。root 就是靠 sub-agent 的 description 决定委派给谁，等价于工具选择时的工具描述。
- **`instruction`**：写给**agent 自己**看的——"我的目的是什么、有哪些工具、何时用"。

```python
farewell_subagent = Agent(
    model=llm,
    name="farewell_subagent_v1",
    instruction="You are the Farewell Agent. Your ONLY task is to provide a polite goodbye "
                "message. Use the 'say_goodbye' tool when the user indicates they are leaving "
                "(e.g. 'bye', 'goodbye', 'thanks bye', 'see you'). Do not perform any other actions.",
    description="Handles simple farewells and goodbyes using the 'say_goodbye' tool.",  # 委派的依据
    tools=[say_goodbye],
)
```

注意 instruction 里那句括号例子（bye / goodbye / thanks bye / see you）——这是在 agent 指令里做的一小段 **few-shot learning**。讲师说大多数 LLM 其实不需要这几个例子，但把它当习惯养成："想想怎么帮 LLM 理解这个 agent 的用途和触发时机"。

root 的 instruction 则"加倍下注"：明确告诉它有哪两个 sub-agent、各自何时用、并且**收到 hello/goodbye 时要委派而不是自己直接回**：

```python
root_agent = Agent(
    name="friendly_agent_team_v1",
    model=llm,
    description="The main coordinator agent. Delegates greetings/farewells to specialists.",
    instruction="""You are the main Agent coordinating a team. Your primary responsibility is to be friendly.
        You have specialized sub-agents:
        1. 'greeting_agent': Handles simple greetings like 'Hi','Hello'. Delegate to it for these.
        2. 'farewell_agent': Handles simple farewells like 'Bye','See you'. Delegate to it for these.
        For anything else, respond appropriately or state you cannot handle it.""",
    tools=[],                                    # coordinator 自己没有工具
    sub_agents=[greeting_subagent, farewell_subagent],   # 关键：挂上 sub-agent 列表
)
```

> **架构师视角**：`sub_agents=[...]` 一挂上，ADK 就开启**自动委派**——用户输入更适合某个 sub-agent（按其 description）时，root 自动把控制权移交过去。这比手写 if/else 路由值钱的地方在于：加一个新专家只需新增一个 agent + 一句好 description，不动 root 的编排代码。委派的质量 100% 取决于 description/instruction 的措辞，讲师原话"搭好多 agent 系统后，你大部分时间都花在打磨这些指令上"——这就是经典 prompt engineering，不是框架能替你做的。

## 3. 委派 ≠ 工具调用：整段对话历史被传递

委派"类似工具调用"，但有本质区别：**agent 知道自己在跟另一个 agent 说话，整段 conversation history 会被传过去**（而不是像工具那样只传几个参数）。开 `verbose=True` 看幕后，一次 "Hello I'm ABK" → "Thanks, bye!" 的完整轨迹：

```
[friendly_agent_team]  → action: transfer_to_agent(greeting_subagent)   # coordinator 决定委派
[greeting_subagent]    → FunctionCall: say_hello(person_name="ABK")     # sub-agent 抽出名字、调工具
                       ← "Hello to you, ABK"                            # final=True，事件循环终止
--- 第二条 user 消息 "Thanks, bye!" ---
[greeting_subagent]    → transfer_to_agent(farewell_subagent)          # 当前还在 greeting 手里，它自己转交
[farewell_subagent]    → FunctionCall: say_goodbye()                    # 无参数
                       ← "Goodbye from Cypher!"                         # final response
```

两个观察点：① `transfer_to_agent` 的返回值是 `None`，它只是移交控制权，真正干活的是接手的 sub-agent；② 第二轮时控制权还在 greeting sub-agent 手里，是它自己判断"这不归我管"再转交给 farewell——**sub-agent 之间也能互相 aware 并转交**，不必回到 root。讲师建议至少完整走读一次 verbose 输出，这是调试 agent 交互的基本功。

## 4. Session State：给团队装上共享记忆

多 agent 系统最后一块拼图是**记忆**。ADK 的 Session State 默认就是一个**跨整个 session、跨所有参与 agent 共享的 dict**；你改 key，ADK 追踪 delta 并异步同步给所有 agent（无论并行还是串行）。两种访问方式：

| 方式 | 机制 | 适用 |
|---|---|---|
| **ToolContext**（讲师首选） | 工具函数最后一个参数声明为 `tool_context: ToolContext`，ADK 自动注入；工具内读写 `tool_context.state` | 工具执行途中读写记忆 |
| **output_key** | agent 定义时设 `output_key="k"`，其 final 响应文本自动存进 `state["k"]` | 把 agent 输出直接落进状态（L7 的 critic 会用到） |

把两个工具升级成 stateful 版：

```python
from google.adk.tools.tool_context import ToolContext

def say_hello_stateful(user_name: str, tool_context: ToolContext):
    """打招呼，同时把名字写进 state"""
    tool_context.state["user_name"] = user_name          # 写记忆
    return graphdb.send_query("RETURN 'Hello to you, ' + $user_name + '.' AS reply",
                              {"user_name": user_name})

def say_goodbye_stateful(tool_context: ToolContext) -> dict:
    """告别，从 state 读回名字（自己没有 user_name 参数）"""
    user_name = tool_context.state.get("user_name", "stranger")   # 读记忆，带默认值
    return graphdb.send_query("RETURN 'Goodbye, ' + $user_name + ...", {"user_name": user_name})
```

关键点：`say_goodbye_stateful` **不接收任何名字参数**，却能叫出用户名——因为 `say_hello_stateful` 早先把 `user_name` 写进了共享 state。跑一遍"Hello, I'm ABK!"→"Thanks, bye!"，初始 `state={}`，结束时 `state={'user_name':'ABK'}`，告别语正确带出 ABK。

> **对比 C1《Knowledge Graphs for RAG》**：C1 里"记忆"其实是**知识图谱本身**——事实沉淀成节点/边，跨 session 长存，是 semantic/领域记忆。本课的 Session State 是**易失的工作记忆（working memory）**，只在单个 session 内、in-memory（讲师明说生产要换持久化后端）。两者正交：KG 是 agent 要构建的产物 + 长期知识底座，Session State 是构建过程中 agent 之间传递中间态的临时黑板。选型上对应 `6-memory.md` 的"记忆类型"子决策——先分清你要的是长期语义记忆还是短期会话状态，别用一个后端硬扛两件事。

> **对比 4-tools.md 的读写分离**：注意 `set_*` / `get_*` 成对出现的苗头——本课还只是 hello/goodbye，但 L5/L6/L7 会把它固化成 pattern：**只有工具能写 state，agent 通过 get 工具读 state 而不是靠 conversation history 脑补**。这是把"工具当作记忆的唯一合法入口"，用来对抗 LLM 的幻觉与漂移。

## 5. 本课总结

| 要点 | 一句话 |
|---|---|
| 多 Agent 团队 | root(coordinator) + sub-agents，`sub_agents=[...]` 开启自动委派 |
| description vs instruction | 前者给别人看决定"何时调我"，后者给自己看决定"我怎么干" |
| 委派 ≠ 工具调用 | 传整段对话历史；sub-agent 之间也能互相转交控制权 |
| Session State | 跨 agent 共享 dict，`ToolContext` 读写 / `output_key` 落输出 |
| 工具是记忆入口 | 用 set/get 工具封装 state 访问，为后续 KG Agent 打样 |

> **记忆点（引出 L5）**：本课的 hello/goodbye 只是 ADK 机制的"教学脚手架"。L5 起进入真正的业务——构建 **Structured Data Agent 工作流**的第一环 **User Intent Agent**：用 `set_perceived_user_goal` / `approve_perceived_user_goal` 两个工具做 human-in-the-loop 的目标确认，把"用户到底想建什么图"写进 `approved_user_goal`，为整条流水线定方向。你会看到本课的 ToolContext 读写记忆、trust-but-verify 的 set/approve 双工具模式全部被复用。

## 与我的资产映射

- 编排层：`agent/skills/agent-selection/11-design-patterns.md`（+Multi-Agent 叠加维度、routing 路由——ADK 自动委派是 routing 的 LLM 驱动实现）
- 记忆层：`agent/skills/agent-selection/6-memory.md`（会话工作记忆 vs 长期语义记忆的分层；控制权子决策——谁触发写入，本课答案是"只有工具"）
- 框架层：`agent/skills/agent-selection/2-framework/`（Google ADK 作为多 Agent 框架的一个样本：内建 delegation + session state + LoopAgent）
- 面试包：`agent/interview/jd-senior-agent-engineer/`（多 Agent 委派 vs 工具调用的区别、description 驱动路由，是常见追问点）
- [[project_selection_matrix]]
