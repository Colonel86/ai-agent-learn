# L10 · 用 BeeAI 把多框架 Agent 编排成一个多 Agent 系统（RequirementAgent + HandoffTool）

> 课程：A2A: The Agent2Agent Protocol（DeepLearning.AI × Google Cloud × IBM Research）
> 本课任务：用 IBM Research 开源的 **BeeAI Framework** 创建一个 Healthcare Concierge 编排 Agent，动态调用前面各课用**不同框架**构建的三个 A2A agent——跨框架互操作的收官实证；最后把这个编排 Agent 自己也注册成 A2A server。

## 0. 本课目标与全景架构

前九课攒下的三个 agent 各说各的"方言"（不同框架、不同模型），但都已包成 A2A server——**协议同一，方言无碍**（"speaking the same language, even if they have different accents"）。本课的 BeeAI 编排层把它们编成一支队伍：

```
                        User
                          │ A2A
                          ▼
        ┌─────────────────────────────────────┐
        │  Healthcare Concierge (BeeAI        │
        │  RequirementAgent, port 9996)       │
        └───────┬───────────┬───────────┬─────┘
            A2A │       A2A │       A2A │
                ▼           ▼           ▼
        Policy Agent   Research Agent  Provider Agent
        (Claude + 裸    (Google ADK,   (LangGraph,
        A2A SDK, 9999)  9998)          9997)
                │           │              │
             Policy PDF  Google Search  FastMCP Server
                                        (doctors.json, stdio)
```

四个 agent、四种技术栈（裸 A2A SDK / ADK / LangGraph / BeeAI）、两种协议分工（agent 间 A2A、agent 到数据 MCP），一个系统。

## 1. BeeAI Framework：为可靠性而生的编排框架

BeeAI 定位是"production-ready agent"开发工具，核心卖点是 **agent reliability**——不止把 agent 造出来，还要确信它**不会越出你设定的约束**。字幕列出的特性清单：

| 特性 | 说明 |
|---|---|
| 规则强制（rule enforcement） | 声明式约束驱动 agent 行为（本课主角 ConditionalRequirement） |
| Event Driven Middleware | 钩入 agent 事件流，可注入内容安全过滤、prompt injection 检测 |
| 可插拔观测（pluggable observability） | trajectory middleware 展示执行轨迹 |
| 内置记忆管理 | 多种 memory 策略开箱即用 |
| MCP 与 A2A 原生支持 | 一行抽象把 agent 包成 A2A server / 把 A2A server 包成本地对象 |

推理供应商用 Vertex AI（编排 agent 跑 `gemini-2.5-flash`），BeeAI 内置 15+ providers 且可扩展自定义。

## 2. 把远程 A2A server 包成本地 Agent 对象

前置条件：三个 agent server 各自在终端里跑着（L4/L6/L8 的 `uv run a2a_*_agent.py`）。然后每个远程 server 用 `A2AAgent` 抽象包一层：

```python
from beeai_framework.adapters.a2a.agents import A2AAgent
from beeai_framework.memory import UnconstrainedMemory

policy_agent = A2AAgent(
    url=f"http://{host}:{policy_agent_port}",  # 指向运行中的 A2A server
    memory=UnconstrainedMemory()               # 由它管理会话历史
)
# 探活 + 拉取 AgentCard（名称/描述/能力 = agent 的元数据档案）
asyncio.run(policy_agent.check_agent_exists())
```

两个要点：

1. **`A2AAgent` 就是 A2A client**：负责把请求经 A2A 协议转发给 server agent，编排层拿到的是一个普通的本地 agent 对象；
2. **`check_agent_exists()` 拉回 AgentCard**：验证 server 在跑，并取回 name / description / capabilities——下一步编排器全靠这份元数据知道每个专家 agent 能干什么。

顺带的 memory 策略速览（讲师强调这是要实验调优的大杠杆）：

| 策略 | 机制 |
|---|---|
| UnconstrainedMemory | 全量保留会话历史 |
| Sliding Window | 只留最近 K 条 |
| Token Memory | 按 token 预算裁剪，守住模型上下文上限 |
| Summarize Memory | 维护一份对话的单一摘要 |

## 3. RequirementAgent：把"规则"从 system prompt 搬进框架层

传统 agent 的不可预测性是生产落地最大障碍之一：测试完美，上了生产却跳步骤、用错工具、任务没完就终止；同一任务换个模型执行模式天差地别。把规则写进 system prompt 只是**建议（suggestion）**，不可强制执行（not enforceable）。

RequirementAgent 的解法是声明式的 **ConditionalRequirement**：**每次 LLM 调用前检查条件规则，只把当前时点满足条件的工具暴露给 LLM 作为可选项**。比如 agent 有 10 个工具，第三轮按你的逻辑只该用 4 个，那 LLM 就只看得见这 4 个。三重收益：

1. **框架层强制**而非 prompt 层建议——换任何底层模型规则都成立；
2. **减少上下文膨胀**——不相关工具不进 context，省性能省钱；
3. **降低模型推理负担**——不必在"什么时候能用哪个工具"上消耗推理能力。

> **架构师视角**：这是"把控制流放在 prompt 还是放在代码"这条老光谱上的一个精确刻度——ConditionalRequirement 不是 LangGraph 那种把整条控制流画死成图，也不是纯 prompt 放任自由，而是**保留 LLM 的动态选择权、只在边界上做硬约束**（谁先谁后、最多几次、不许连发）。生产 agent 的规则分两类：该被强制的（安全/流程硬约束）进框架层，该被理解的（业务语境）留 prompt——混在 system prompt 里一锅炖，是"测试通过、生产翻车"的典型根因。

## 4. 配置编排器：ThinkTool + 三个 HandoffTool + 条件规则

```python
healthcare_agent = RequirementAgent(
    name="Healthcare Agent",
    description="A personal concierge for Healthcare Information...",  # 之后暴露成 A2A server 时的元数据
    llm=VertexAIChatModel(
        model_id="gemini-2.5-flash",
        allow_parallel_tool_calls=True,   # 可同时并行调多个专家 agent（如同时问保险+找医生）
    ),
    tools=[
        thinktool := ThinkTool(),          # 推理工具：配合规则可拼出 ReAct / Planning 等模式
        policy_tool := HandoffTool(        # 每个专家 agent 一个 HandoffTool
            target=policy_agent,
            name=policy_agent.name,
            description=policy_agent.agent_card.description,  # 工具描述直接用 AgentCard 描述！
        ),
        research_tool := HandoffTool(target=research_agent, ...),
        provider_tool := HandoffTool(target=provider_agent, ...),
    ],
    requirements=[
        # 第 1 步强制 think（planning），之后每次工具调用后强制 think 但不许连发（ReAct）
        ConditionalRequirement(
            thinktool, force_at_step=1, force_after=Tool,
            consecutive_allowed=False
        ),
    ],
    role="Healthcare Concierge",
    instructions="""...保险问题交给 Policy Agent；医生信息只准出自
    Provider Agent、保险信息只准出自 Policy Agent；注明信息来源...""",
)
```

四个设计点：

1. **HandoffTool ≠ 普通 tool**：普通工具是"孤立函数执行、返回结果"；HandoffTool 还会把**状态和上下文一并移交**给接手的 agent，移交逻辑不用自己写；
2. **AgentCard.description 直接当工具描述**——L2 讲的"发现"机制在这里闭环：编排器对专家 agent 能力的全部认知都来自协议标准化的元数据，而非硬编码；
3. **同一个 ThinkTool，换条规则就是换推理模式**：`force_at_step=1` 是 Planning，`force_after=Tool` 是 ReAct，这里两者叠加；
4. **system prompt 因此变干净**：规则已被 ConditionalRequirement 强制，不必再用自然语言复述一遍，减轻 LLM 推理负担。其他可用参数还有 min/max invocations、`consecutive_allowed`、只许在某工具之前/之后、自定义条件等。

## 5. 运行与观测：trajectory middleware

```python
response = await healthcare_agent.run(
    "I'm based in Austin, TX. How do I get mental health therapy "
    "near me and what does my insurance cover?"
).middleware(ConciseGlobalTrajectoryMiddleware())   # 中间件打印执行轨迹
display(Markdown(response.last_message.text))
```

轨迹里能看到完整循环：检查各 ConditionalRequirement → 确定本轮可用工具 → 调 VertexAIChatModel → 第一步被强制调 ThinkTool → 循环往复直到产出 final answer。最终答案汇总了 **Provider Agent**（网络内的心理健康提供者）和 **Policy Agent**（门诊/住院覆盖与个人保单注意事项）。

**Research Agent 没被调用**——因为没有规则强制它，编排器自己判断这个问题用不上它。想强制？给它加一条 `min invocations` 的 ConditionalRequirement 即可。这正是"动态编排 + 边界约束"的行为示范。middleware 除了观测，还能钩进事件流注入 content safety filter、prompt injection 检测。

## 6. 递归收官：编排 Agent 自己也是 A2A server

把 notebook 逻辑用 `%%writefile` 写成 `a2a_healthcare_agent.py`，然后**只需追加一条注册语句**：

```python
from beeai_framework.adapters.a2a.serve.server import A2AServer, A2AServerConfig
from beeai_framework.serve.utils import LRUMemoryManager

A2AServer(
    config=A2AServerConfig(port=healthcare_agent_port,
                           protocol="jsonrpc", host=host),
    memory_manager=LRUMemoryManager(maxsize=100),  # 会话级记忆（最多缓存100个session），
).register(healthcare_agent,                      # 区别于单个 agent 的上下文记忆
           send_trajectory=True).serve()
```

`uv run a2a_healthcare_agent.py` 启动后，客户端还是那个熟悉的 `A2AAgent` 包装：

```python
agent = A2AAgent(url="http://127.0.0.1:9996", memory=UnconstrainedMemory())
response = await agent.run("...同一个问题...")
```

至此完成递归闭环：**A2A client 调一个 A2A server，这个 server 里的 agent 又作为 client 调另外三个 A2A server**。"由 A2A agent 组成的 agent，本身也能暴露成 A2A agent"——这是 A2A 可组合性（composability）的完整实证。

> **对比 2-framework/06-protocols.md 的 A2A/MCP 分工**：本课一张图把两个协议的边界钉死——**MCP 是 agent 到工具/数据的纵向协议**（Provider Agent → doctors.json 走 MCP stdio），**A2A 是 agent 到 agent 的横向协议**（Concierge → 三个专家、User → Concierge 全走 A2A）。判据就一条：对端有没有自主推理能力——有，A2A；没有（纯函数/数据源），MCP。

> **对比 2-framework/03-framework-profiles.md**：L3-L10 等于活体跑了一遍框架选型矩阵——裸 SDK（全控制、全手工）、ADK（内置 A2A 集成 + SequentialAgent 编排原语）、LangGraph（图控制流 + MCP 生态）、BeeAI（规则强制 + reliability 导向）。A2A 的战略含义是**让这道选型题从"一次性全局决策"降级为"每个 agent 的局部决策"**：每个团队按自己的场景选框架，协议层负责拼装——选错一个框架不再殃及整个系统。

## 7. 本课总结

| 要点 | 一句话 |
|---|---|
| A2AAgent 抽象 | 远程 A2A server → 本地 agent 对象，`check_agent_exists()` 拉 AgentCard |
| RequirementAgent | LLM 调用前按条件规则过滤可见工具，框架层强制而非 prompt 建议 |
| HandoffTool | agent 即工具，且自动移交状态与上下文；描述直接用 AgentCard.description |
| ConditionalRequirement | force_at_step / force_after / consecutive_allowed 拼出 Planning+ReAct |
| 递归组合 | 编排 agent 加一条 A2AServer 注册语句，自己也成为 A2A server |

> **记忆点（引出 L11）**：多 agent 系统在笔记本里已经跑通，但四个 server 全靠四个终端手工拉起、密钥放本地 env、没有持久化没有 UI 没有鉴权。L11 直面这个"被讨论得太少的问题"——**把 agent 部署到生产出乎意料地难**，并用自托管的 Agent Stack 平台给出一条不锁框架、不锁云的路。

## 与我的资产映射

- 协议层：`agent/skills/agent-selection/2-framework/06-protocols.md`（A2A 横向 / MCP 纵向的分工在本课一图闭环）
- 框架层：`agent/skills/agent-selection/2-framework/03-framework-profiles.md`（BeeAI 的差异化定位：ConditionalRequirement 式规则强制；A2A 把框架选型降级为局部决策）
- 安全护栏：`agent/skills/agent-selection/7-safety-guardrails.md`（框架层强制 vs prompt 层建议，是 guardrail 落点选择的同一命题）
- [[project_selection_matrix]]
