# L9 · 用 Microsoft Agent Framework 做 A2A 客户端（跨框架互操作收官）

> 课程：A2A: The Agent2Agent Protocol（DeepLearning.AI × Google）
> 本课任务：A2A 的核心卖点是**互操作性（interoperability）**——本课用 **Microsoft Agent Framework** 内建的 A2A client 连上 L8 用 LangGraph 建的 Healthcare Provider Agent，微软框架 × Google 栈 server，一次跨厂商实证。

## 0. 本课在互操作拼图里的位置

到本课为止，课程已经把"谁当 client、谁当 server、各用什么框架"排列了一轮：

| 课次 | Server 侧 | Client 侧 | 集成方式 |
|---|---|---|---|
| L3-L5 | PolicyAgent（裸 A2A SDK） | 裸 A2A SDK client | 手写全套 |
| L6-L7 | ADK agent → A2A | Google ADK（RemoteA2aAgent） | ADK 内建集成 |
| L8 | LangGraph + MCP → 裸 SDK 包装 | —（本课补上） | 手写包装 |
| **L9** | **沿用 L8 的 LangGraph server** | **Microsoft Agent Framework（A2AAgent）** | **MAF 内建集成** |

本课代码量极小（一个 import、一个对象、一次 `run`），但语义分量最重：**client 侧完全不知道也不需要知道 server 是 LangGraph 写的**。

## 1. 前置：确认 Provider Agent 还活着

L8 的 server 跑在 Terminal 3（`uv run a2a_provider_agent.py`，端口 9997）。本课先检查它是否仍在运行——挂了就重启，**不需要回到 L8 的 notebook**，因为 server 已经落成独立文件。这本身就是一个小注脚：agent 是常驻服务，不是 notebook 里的临时对象。

## 2. 三行接入：A2AAgent

```python
from agent_framework.a2a import A2AAgent   # Microsoft Agent Framework 的 A2A 客户端类

load_dotenv()
host = os.environ.get("AGENT_HOST")
port = os.environ.get("PROVIDER_AGENT_PORT")

healthcare_provider_agent = A2AAgent(      # 只需名字 + URL，直连配置
    name="HealthcareProviderAgent",
    url=f"http://{host}:{port}",           # 指向 L8 跑在 Terminal 3 的 server
)
```

`A2AAgent` 的机制与 ADK 的 `RemoteA2aAgent` 同一个思路：**一个包着 HTTP client 的 agent 类**——对外走 HTTP 与 A2A 兼容 agent 通信，对内把远端 agent 伪装成 Microsoft Agent Framework 的本地 agent。

```
Microsoft Agent Framework 侧              LangGraph/Google 侧
┌─────────────────────────┐              ┌──────────────────────┐
│ A2AAgent("Healthcare…") │   A2A 协议    │ a2a_provider_agent.py │
│  ├ 对内：MAF 原生 agent  │ ──HTTP──────▶ │  AgentCard + Executor │
│  └ 对内含 HTTP client   │ ◀──响应────── │  └ LangGraph + MCP    │
└─────────────────────────┘              └──────────────────────┘
   client 不感知对端实现                      server 不感知调用方框架
```

## 3. 跨框架调用与结果

用 L8 一模一样的 prompt 验证：

```python
prompt = "I'm based in Austin, TX. Are there any Psychiatrists near me?"

result = await healthcare_provider_agent.run(prompt)   # MAF 原生的 run 接口
display(Markdown(result.text))                         # 响应与 L8 直连 LangGraph 时一致
```

调用链上发生的事对使用者完全透明：MAF client 把请求**序列化成 A2A 协议**→ 发给 server → server 侧 LangGraph agent 调 MCP 工具查 doctors.json → 响应原路返回，`result.text` 拿到与 L8 相同的答案（Austin 的精神科医生）。

从此这个远端 agent 就是一个**全功能的 Microsoft Agent Framework agent**——可以直接放进任何用该框架搭的多 agent 系统里，与 ADK 处理 remote A2A agent 的方式基本相同。

> **对比 L6-L7 的 ADK 路线**：两家框架对 A2A client 的抽象殊途同归——ADK 叫 `RemoteA2aAgent`，MAF 叫 `A2AAgent`，都是"**远端 agent 本地代理化**"：给个 URL，框架负责读 AgentCard、序列化请求、处理响应，把协议细节全部藏掉。这说明 A2A 生态的收敛点很清晰：server 侧包装各显神通（内建集成或裸 SDK 手写，见 L8），client 侧则统一成"URL in, native agent out"的一行式体验。

> **架构师视角**：本课是选型矩阵 03-framework-profiles.md 里 MAF 条目"**原生 MCP/A2A**"这一格的实景——AutoGen + Semantic Kernel 合并后的 MAF 把协议支持做成一等公民，跨框架接 agent 不再需要胶水代码。更大的启示是**组织层面的**：A2A 让"provider 团队用 LangGraph、consumer 团队用 MAF"成为合法架构，框架选型从"全公司统一"降级为"团队局部决策"，接口收敛在协议而不是框架上——这正是 06-protocols.md 说 A2A 只在"跨团队/跨进程/跨组织"才回本的正面例子：本课两端分属两个生态，协议的钱花得值；若两个 agent 本来就在同一进程同一框架里，这层 HTTP + 协议序列化就纯是开销。

## 4. 本课总结

| 要点 | 一句话 |
|---|---|
| 互操作实证 | Microsoft 框架 client 调 Google 栈 LangGraph server，双方互不感知对端实现 |
| A2AAgent | MAF 内建 A2A client：包 HTTP client 的 agent 类，`name + url` 即完成接入 |
| 透明协议翻译 | `run(prompt)` 内部自动完成 A2A 序列化/反序列化，使用者零协议代码 |
| 本地代理化模式 | 与 ADK RemoteA2aAgent 同构：远端 A2A agent → 框架原生 agent，可进多 agent 系统 |
| Server 常驻 | L8 的 server 是独立进程，client 课次随时重启重连，不依赖原 notebook |

> **记忆点（引出 L10）**：现在手里有三个各说各框架方言、但都持 A2A 名片的 agent——PolicyAgent（裸 SDK/Claude）、ADK agent、Provider Agent（LangGraph+MCP）。下一课 Sandy 用 **BeeAI 框架**把它们全部编排进一个**多 agent 系统**：A2A 从"两两互通"升级为"异构 agent 组队"，这才是协议的终局形态。

## 与我的资产映射

- 框架档案：`agent/skills/agent-selection/2-framework/03-framework-profiles.md`——MAF 条目（AutoGen+SK 合并、原生 MCP/A2A、多 agent 生产新项目的微软栈选项）；本课验证其 A2A 集成成色
- 协议层：`agent/skills/agent-selection/2-framework/06-protocols.md`——A2A 回本判据"跨团队/跨组织、运行时发现"；本课是跨生态正面样例，同时反衬"同进程多角色别套 A2A"
- 面试叙事：跨框架互操作 = "框架选型局部化、接口收敛到协议"的架构论点，可直接用于 `agent/interview/jd-senior-agent-engineer/` 的多 agent 议题
- [[project_selection_matrix]]
