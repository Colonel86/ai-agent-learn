# L7 · 用 SequentialAgent 把两个 A2A 服务器串成链

> 课程：A2A: The Agent2Agent Protocol（DeepLearning.AI × Google）
> 本课任务：让 L4 的 Insurance Policy Agent 和 L6 的 Health Research Agent **协作完成同一个任务**——用 ADK 的 `SequentialAgent` 编排、`RemoteA2aAgent` 充当 A2A client，把一个 agent 的结果喂给下一个，一次提问得到两段合成回答。

## 0. 本课目标与前置

手上已有两个同时运行的 A2A server：

- **Terminal 1**：Insurance Policy Agent（裸 a2a-sdk + Claude Haiku on Vertex + 保单 PDF），`uv run a2a_policy_agent.py`；
- **Terminal 2**：Health Research Agent（ADK LlmAgent + Gemini + google_search），`uv run a2a_research_agent.py`。

本课在 notebook 里（编排端不需要长驻 server，不用写 .py 文件）构建第三个 agent：ADK 的 **SequentialAgent**，它负责 A2A 通信、**按顺序调用两个 agent，把上一个的结果作为上下文喂给下一个**。开工前先确认两个 terminal 里的 server 还活着，挂了就重跑 `uv run` 命令。

环境变量这次要**同时**取两个端口：

```python
host = os.environ.get("AGENT_HOST")
policy_port = os.environ.get("POLICY_AGENT_PORT")      # L4 的 server
research_port = os.environ.get("RESEARCH_AGENT_PORT")  # L6 的 server
```

## 1. RemoteA2aAgent：把远端 A2A server 伪装成本地 sub-agent

连接 A2A agent 只需要实例化 `RemoteA2aAgent`——给个名字，传入 **agent card 的托管 URL**：

```python
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent

policy_agent = RemoteA2aAgent(
    name="policy_agent",
    agent_card=f"http://{host}:{policy_port}",     # 指向 card，不是指向"接口文档"
)
health_research_agent = RemoteA2aAgent(
    name="health_research_agent",
    agent_card=f"http://{host}:{research_port}",   # 两个远端 agent 各建一个代理
)
```

课程强调：**这个类就是你的 A2A client**——它把与 A2A agent 交互的全部 boilerplate（HTTP 连接、tasks、messages）都处理掉了。对照 L5 手写 client 的步骤，映射关系如下：

| L5 手写 A2A Client | RemoteA2aAgent 内部代劳 |
|---|---|
| httpx + `A2ACardResolver` 拉取 agent card | 从 `agent_card` URL 自动解析 |
| 构造 `Message` / `MessageSendParams` | 自动构造 |
| `client.send_message()` 发 JSON-RPC | 自动发送 |
| `Task` / `Message` 双分支解析响应 | 自动解析（L6 的 Task 响应也接得住） |

> **架构师视角**：`RemoteA2aAgent` 的精髓是**接口归一**——远端 agent 被包装成和本地 sub-agent 同一个抽象，编排层代码里两者不可区分。这意味着"先进程内多角色、真跨边界再拆成 A2A server"的演进路径在 ADK 里几乎零重构：把本地 `LlmAgent` 换成 `RemoteA2aAgent`，`sub_agents` 列表不用动。**先定协作拓扑，部署形态留作可延迟决策**——这是把 deployment 从 architecture 里解耦出来的教科书示范。

## 2. SequentialAgent：顺序由代码定，不由模型定

```python
from google.adk.agents import SequentialAgent

root_agent = SequentialAgent(
    name="root_agent",
    description="Healthcare Routing Agent",
    sub_agents=[
        health_research_agent,   # 第一步：通用健康研究（Google 搜索）
        policy_agent,            # 第二步：结合研究结果查保单覆盖
    ],  # ⚠️ 列表顺序 = 调用顺序
)
```

课程给了一个关键辨析：

| | SequentialAgent | LlmAgent（带 sub_agents） |
|---|---|---|
| 谁决定调用顺序 | **代码**：`sub_agents` 列表顺序即执行顺序 | **模型**：LLM 自己决定何时调哪个 sub-agent |
| 确定性 | 每次都是 research → policy | 每次路由可能不同 |
| 适用 | 步骤可预先枚举的固定流水线 | 需要动态路由/自主决策的任务 |

执行拓扑（notebook 附了 sequential.png，等价 ASCII）：

```
用户 prompt
   │
   ▼
┌────────────────────── root_agent (SequentialAgent, 本地进程) ──────────────────────┐
│                                                                                    │
│  ① health_research_agent ──A2A/JSON-RPC──▶ :RESEARCH_PORT  (ADK+Gemini+搜索)       │
│         │ 研究结果注入共享上下文                                                     │
│         ▼                                                                          │
│  ② policy_agent ──────────A2A/JSON-RPC──▶ :POLICY_PORT    (裸SDK+Claude+保单PDF)   │
│                                                                                    │
└──────────────────────────────────┬─────────────────────────────────────────────────┘
                                   ▼
                     合成回答：通用治疗途径 + 本保单的覆盖细节
```

> **对比 11-design-patterns.md（Anthropic workflow 谱）**：`SequentialAgent` 就是谱系最左端 **prompt chaining** 档的框架化身——代码定控制流、线性依赖、最可预测；`LlmAgent` 派单则落在最右端 **autonomous agent** 档（模型定控制流）。课程这个二选一恰好复刻了那页的核心纪律：**workflow 优先、agent 兜底**——"研究 → 查保单"步骤天然可枚举，用 SequentialAgent 拿到确定性、可调试性、成本三赢，没必要让 LLM 每次现场决定路由。往右挪档要有"链不够用"的证据。

## 3. InMemoryRunner：运行链并取最终响应

```python
from google.adk.runners import InMemoryRunner

prompt = "How can I get mental health therapy?"

runner = InMemoryRunner(root_agent)          # 内存版 Runner，存放 agent state/session

for event in await runner.run_debug(prompt, quiet=True):   # 逐事件流式返回
    if event.is_final_response() and event.content:
        display(Markdown(event.content.parts[0].text))      # 只打印最终响应
```

- **InMemoryRunner**：ADK 的执行器，负责 session/state 存储（内存版，教学够用；生产可换持久化实现）；
- **事件流**：`run_debug` 产出事件序列，用 `is_final_response()` 过滤出各 agent 的最终响应；
- **输出**：一次提问得到**两段**回答——先是 health research agent 的通用研究（心理治疗的获取途径，带引用来源），随后是 policy agent **针对我们这份保险单**的覆盖答复（哪些心理健康服务在保、自付多少）。等待几秒是正常的：背后是两次真实的跨进程 A2A 调用 + 一次 Google 搜索。

至此，课程原话："You've successfully built a **chained multi-agent system using A2A**." 而且这条链是**异构**的——两个 sub-agent 分别由裸 SDK+Claude 和 ADK+Gemini 实现，编排层完全无感。

> **对比 2-framework/06-protocols.md（A2A 决策页）**：那页的冷水要照泼——**同进程多角色不必上 A2A**，框架内的 handoff/sub-agent 就够。本课如果三个 agent 都写在一个 notebook 里，正确做法是三个本地 `LlmAgent` 直接进 `sub_agents`，零协议开销。这里 A2A 的回本点在于两个 server **本来就是独立进程、独立技术栈**（一个还是别家模型），编排方不该也不能 import 它们的代码——这才踩中"跨进程/跨栈、运行时发现对端"的真实需求。升级路径复述：单 agent+MCP → 进程内多角色（框架原生）→ 真跨边界才上 A2A。

## 4. 本课总结

| 要点 | 一句话 |
|---|---|
| RemoteA2aAgent | ADK 的 A2A client：传 name + agent card URL，HTTP/tasks/messages 全代劳 |
| 接口归一 | 远端 agent 与本地 sub-agent 同一抽象，部署形态与协作拓扑解耦 |
| SequentialAgent | sub_agents 列表顺序 = 执行顺序，代码定控制流（prompt chaining 档） |
| vs LlmAgent 派单 | LlmAgent 由模型决定调谁，是 agent 档；本课任务可枚举，选 workflow |
| InMemoryRunner | 存 state、跑事件流，`is_final_response()` 取各 agent 最终响应 |
| 异构合成 | 一个 prompt → Gemini 的通用研究 + Claude 的保单适配，跨栈无感 |

> **记忆点（引出 L8）**：本课证明了 A2A 链的**跨框架**能力——裸 SDK 和 ADK 的 agent 在同一条链里协作。L8 把版图再扩一块：用 **LangGraph + MCP** 构建 Provider Agent（A2A 管 agent 间通信、MCP 管 agent 到工具/数据），三大件同框，验证"MCP 接工具、A2A 接 agent"的两层参考架构。

## 与我的资产映射

- 设计模式层：`agent/skills/agent-selection/11-design-patterns.md`（SequentialAgent = prompt chaining 档的框架实现；SequentialAgent vs LlmAgent 派单 = workflow vs agent 的档位选择）
- 协议层：`agent/skills/agent-selection/2-framework/06-protocols.md`（A2A 回本点：跨进程/跨栈才上协议；本课是正例，同 notebook 三 agent 则是反例）
- 框架层：`agent/skills/agent-selection/2-framework/03-framework-profiles.md`（§10 ADK 编排原语：SequentialAgent/LlmAgent/Runner，可补充进条目）
- 面试包：`agent/interview/jd-senior-agent-engineer/`（多 agent 编排三问：谁定控制流、上下文怎么传递、协议何时回本）
- [[project_selection_matrix]]
