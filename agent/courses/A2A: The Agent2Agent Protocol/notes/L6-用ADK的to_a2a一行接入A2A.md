# L6 · 用 ADK 的 to_a2a 一行接入 A2A（Health Research Agent）

> 课程：A2A: The Agent2Agent Protocol（DeepLearning.AI × Google）
> 本课任务：用 Google **ADK（Agent Development Kit）** + Gemini 3 Pro（Vertex AI）构建第二个 agent——Health Research Agent（Google 搜索做健康研究），并用 `to_a2a` 一个方法把它包成 A2A Server——**不再手写 AgentCard / AgentExecutor**。

## 0. 本课目标与定位

L3-L5 用**裸 a2a-sdk** 走完了闭环：QA agent（读保险 PDF 的 Policy Agent）→ 手写五件套包成 A2A Server → 手写 A2A Client 调用。本课扩充 agent 集合：加入第二个 agent，换一条路线——**用带 A2A 内置集成的框架**。

- **能力**：用 Google 搜索研究用户的健康状况（symptoms / conditions / treatments / procedures），返回研究结果；
- **技术栈**：Google ADK 的 `LlmAgent` + Gemini 3 Pro（Vertex AI）+ ADK 内置 `google_search` 工具；
- **关键卖点**：ADK 和若干其他框架都对 A2A 有 built-in integration，让 agent 变 A2A compliant 容易得多——这正是协议生态成熟的信号。

代码仍存成独立 Python 文件 `a2a_research_agent.py`（和 L4 的 policy agent 一样，server 要长驻运行，不适合放 notebook cell）。

## 1. 对照 L4：裸 SDK 五件套 vs ADK 一个方法

先复习 L4 裸 SDK 把 Policy Agent 包成 A2A Server 要手写的东西：

| 裸 a2a-sdk（L4） | 作用 | ADK `to_a2a`（本课） |
|---|---|---|
| `AgentSkill` | 声明能力（id/描述/示例） | 自动：从 agent 的 name/tools/description 生成 |
| `AgentCard` | 名片（url/版本/输入输出模式/capabilities） | 自动生成 |
| `AgentExecutor.execute()` | 请求 → 调 agent → 结果入 EventQueue | 自动：ADK 已替你写好 |
| `DefaultRequestHandler` + `InMemoryTaskStore` | JSON-RPC 请求分发 + 任务存储 | 自动 |
| `A2AStarletteApplication` | HTTP 应用组装 | 自动：`to_a2a()` 直接返回可运行的 app |

> **架构师视角**：`to_a2a` 省掉的不只是代码量，更是**声明的重复**——裸 SDK 里 agent 的能力要在 prompt（给模型看）和 AgentCard/AgentSkill（给对端 agent 看）各写一遍，两处会漂移；ADK 把 name/description/tools 当**单一事实来源**，agent card 由此推导。代价是：card 长什么样由框架决定，想精调 skill 的 tags/examples（L4 里可以逐字段控制）就要接受框架的默认。**快速接入选 to_a2a，名片即产品（要精细控制发现语义）选裸 SDK**。

## 2. 定义 ADK LlmAgent

```python
# a2a_research_agent.py（%%writefile 写出）
import uvicorn
from google.adk.a2a.utils.agent_to_a2a import to_a2a   # A2A 集成入口
from google.adk.agents import LlmAgent                  # ADK 的 LLM 驱动 agent
from google.adk.tools import google_search              # ADK 内置 Google 搜索工具

logging.disable(level=logging.WARNING)   # ADK 的 A2A 集成还是 experimental，
warnings.filterwarnings('ignore', ...)   # 警告很吵，先静音

load_dotenv()
credentials, project_id = authenticate(location="global")  # 认证到 Google Cloud

PORT = int(os.environ.get("RESEARCH_AGENT_PORT"))  # 注意：与 policy agent 不同端口
HOST = os.environ.get("AGENT_HOST")                # 两个 server 要在同机同时跑

research_agent = LlmAgent(
    model="gemini-3.1-pro-preview",   # 视频中是 gemini-3-pro-preview，notebook 已更新
    name="HealthResearchAgent",       # ↓ 这三项会被 to_a2a 用来自动填 agent card 和 skills
    tools=[google_search],            # Gemini 内置 Google 搜索（ADK 封装）
    description="Provides healthcare information about symptoms, health "
    "conditions, treatments, and procedures using up-to-date web resources.",
    instruction="""You are a healthcare research agent ... Use the google_search
    tool to find information on the web ... Cite your sources ...""",  # 系统指令
)
```

要点：

1. **`LlmAgent`**：ADK 的基础 agent 类——模型 + 工具 + 描述 + 指令，一次声明；
2. **`google_search`**：Gemini 的内置搜索工具经 ADK 直接可用，不用自己写 tool schema（对照 L3 的 Policy Agent——那是把 PDF 塞进 prompt 的文档 QA，没有外部工具）；
3. **端口纪律**：`RESEARCH_AGENT_PORT` ≠ `POLICY_AGENT_PORT`——两个 A2A server 要在同一系统上**同时运行**，这是 L7 编排的前提。

## 3. to_a2a：一个方法完成 A2A 化

```python
def main() -> None:
    a2a_app = to_a2a(research_agent, host=HOST, port=PORT)  # agent → A2A 应用
    uvicorn.run(a2a_app, host=HOST, port=PORT)              # 和 L4 一样跑在 uvicorn 上
```

课程原话："All you need to do to make this agent A2A-compatible is call the `to_a2a` method"——不需要创建 agent card 或 agent executor，**ADK 已经替你写好了这些代码**，并用 agent 的 name / tools / description 填出 card 和 skills。

运行方式与 L4 相同——在 Terminal 2（Terminal 1 还跑着 policy agent）：

```
uv run a2a_research_agent.py
```

> **对比 2-framework/06-protocols.md（协议层决策页）**：那页把 A2A 的采纳成本列为顾虑之一；本课演示的正是成本曲线的另一端——**当框架内置了协议适配器，「A2A 化」从 L4 的五件套手工装配降到一次函数调用**。这也是协议标准化的复利：MCP 被各框架内置后工具接入变成配置项，A2A 正在走同一条路（ADK、LangGraph 等都有集成）。选型时「目标框架是否原生支持该协议」应当进入 scorecard。

## 4. 复用 L5 的 Client 访问它（Task vs Message）

server 跑起来后，**L5 手写的那个 A2A Client 原样可用**——它本来就是按协议写的，与对端 agent 的实现框架无关。只需换 query 和 host/port。

但有一个协议层的差异值得记：

| | L4 Policy Agent（裸 SDK） | L6 Research Agent（ADK） |
|---|---|---|
| 响应类型 | 直接回 **Message** | 回 **Task**（而非立即的 message） |
| Client 处理 | 从 message parts 取文本 | 走任务分支：从 task 的产出里取结果 |

L5 的 client 已经写了 `Task` / `Message` 两个分支（`isinstance` 判断），所以无需改代码——这正是当时"响应可能是两种类型都要处理"的伏笔兑现。ADK 包装的 agent 内部有工具调用等多步执行，天然更适合 Task 这种有生命周期的抽象。

## 5. 全景：两个异构 A2A Server 并存

至此系统里有两个技术栈完全不同、但对外协议一致的 agent：

```
Terminal 1                              Terminal 2
┌─────────────────────────────┐         ┌─────────────────────────────┐
│ InsurancePolicyCoverageAgent│         │ HealthResearchAgent          │
│ 裸 a2a-sdk 手工五件套        │         │ ADK LlmAgent + to_a2a        │
│ Claude Haiku (Vertex) + PDF │         │ Gemini 3 Pro + google_search │
│ :POLICY_AGENT_PORT          │         │ :RESEARCH_AGENT_PORT         │
└──────────────┬──────────────┘         └──────────────┬──────────────┘
               └───────── 对外都是标准 A2A ─────────────┘
                    （agent card + JSON-RPC + Task/Message）
```

> **对比 2-framework/03-framework-profiles.md 的 ADK 条目**：那里给 ADK 的定性是"单厂商官方路线"⚠️——全程 Gemini/Vertex，换省心付可移植性代价。本课恰好展示了这笔交易的两侧：**买到的省心**是 `google_search` 内置工具和 `to_a2a` 一行 A2A 化；**付出的绑定**是模型字段只认 Gemini 家族、认证走 Google Cloud。但注意 A2A 在这里起了**止损作用**——绑定被封在 server 进程内部，对外是中立协议，消费方（L5 client、L7 编排器）不感知 ADK 的存在。协议边界就是厂商绑定的隔离舱。

## 6. 本课总结

| 要点 | 一句话 |
|---|---|
| ADK LlmAgent | model + tools + description + instruction 一次声明式定义 agent |
| to_a2a | 一个方法完成 A2A 化，card/skills 从 agent 元数据自动生成 |
| 免五件套 | AgentCard / AgentSkill / Executor / RequestHandler / Starlette 全部由 ADK 代劳 |
| 端口纪律 | 与 policy agent 不同端口，两 server 同机并存是 L7 前提 |
| Task 响应 | ADK agent 回 Task 而非 Message，L5 client 的双分支正好接住 |
| 协议隔离舱 | ADK/Gemini 的厂商绑定被封在 server 内，对外仍是中立 A2A |

> **记忆点（引出 L7）**：现在有两个同时在跑的 A2A server——裸 SDK 的 Policy Agent 和 ADK 的 Research Agent。L7 让它们**协作完成同一个任务**：用 ADK 的 `SequentialAgent` + `RemoteA2aAgent`（充当 A2A client）把两个 agent 串成 sequential workflow，一个 query 得到"通用研究 + 保单适配"的合成回答。

## 与我的资产映射

- 框架层：`agent/skills/agent-selection/2-framework/03-framework-profiles.md`（§10 Google ADK——"单厂商官方路线"的省心/绑定交易，本课是实例）
- 协议层：`agent/skills/agent-selection/2-framework/06-protocols.md`（A2A 采纳成本——框架内置适配器把五件套降为一行，可补进决策页）
- 面试包：`agent/interview/jd-senior-agent-engineer/`（A2A 落地路线二选一：裸 SDK 精细控制 vs 框架 to_a2a 快速接入）
- [[project_selection_matrix]]
