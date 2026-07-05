# L5 · 用 A2A Client 发现并调用远程 Agent（ClientFactory + 双形态响应处理）

> 课程：A2A: The Agent2Agent Protocol（DeepLearning.AI × Google）
> 本课任务：写一个 A2A Client，连上 L4 跑起来的 Policy Agent server——拉 AgentCard 完成**发现**，发 Message 完成**通信**，并把 Message / Task 两种响应形态都处理掉。至此协议的 client/server 两半闭环。

## 0. 前置：确认 server 还活着

先重开 Terminal 1 检查 L4 的 server（课程环境 30 分钟不活动或每 2 小时会重置；死了就重跑 `uv run a2a_policy_agent.py`，不用回上一课）。然后加载环境变量拿到目标地址：

```python
host = os.environ.get("AGENT_HOST", "localhost")
port = os.environ.get("POLICY_AGENT_PORT")
# port = os.environ.get("RESEARCH_AGENT_PORT")   ← 注释掉的代码是给 L6 的
prompt = "How much would I pay for mental health therapy?"   # 沿用 L3 的问题
```

**这个 client 是通用的**——notebook 里那几行注释就是伏笔：换个 port（换个 AgentCard），同一套 client 代码将原样调用 L6 的 Research Agent。

## 1. 连接：httpx.AsyncClient + ClientFactory

```python
async with httpx.AsyncClient(timeout=100.0) as httpx_client:  # 承载 HTTP 连接
    client: Client = await ClientFactory.connect(
        f"http://{host}:{port}",                # 只需要一个 URL
        client_config=ClientConfig(
            httpx_client=httpx_client,          # 注入自己的 HTTP 客户端
        ),
    )
```

分工很清晰：`httpx.AsyncClient` 管传输（超时、连接池），`ClientFactory.connect` 管协议（握手、能力协商）。整个 client 栈是纯 async。

## 2. 发现：get_card() 拉取 AgentCard

```python
agent_card = await client.get_card()    # 从 well-known URL 拉名片(L2)
display_agent_card(agent_card)          # 课程 helper:渲染成 Markdown 表格
```

拉回来的 Card 包含：name、description、version、url、**protocol_version**、全部 skills（含 examples）——正是 L4 在 server 侧声明的那份元数据，现在被另一个进程以机器可读方式读到了。

讲师特别声明：**手动 `get_card()` 打印是教学动作，生产系统不会这么用**。真实多 Agent 系统里，由一个 **supervisor / coordinator agent** 收集所有候选 Agent 的 Card（名字 + 描述 + skills），据此**决定把任务路由给谁**——后面课程会实作。

> **架构师视角**：AgentCard 在这一刻完成了它的本职——client 代码里**没有任何一处知道对端是"Claude + PDF 全文注入"**，它只知道 URL 和 Card 上的能力声明。对端明天换成 Gemini、换成 RAG 管线、甚至换团队重写，只要 Card 契约不变，client 零改动。这就是 A2A 版的"面向接口编程"；而 Card 里的 `version` / `protocol_version` 字段，就是这份接口契约做治理（灰度、兼容性检查）的抓手。

## 3. 发送：Message 对象 + send_message

```python
message = create_text_message_object(content=prompt)  # 文本 → A2A Message(带 message_id)
responses = client.send_message(message)              # 返回异步迭代器,不是单个响应
```

注意 `send_message` 返回的是 **async iterator**——协议允许一次请求对应多个事件（任务状态更新、增量产物……），所以消费端统一写成 `async for`。

## 4. 响应处理：Message 与 Task 两种形态

L2 讲过：远端 Agent 可以直接回 **Message**（快活儿），也可以回 **Task**（慢活儿，带生命周期）。健壮的 client 两条分支都要写：

```python
async for response in responses:
    if isinstance(response, Message):        # 形态①:直接回消息(本课的 policy agent)
        print(f"Message ID: {response.message_id}")
        text_content = get_message_text(response)

    elif isinstance(response, tuple):        # 形态②:ClientEvent = (Task, UpdateEvent)
        task: Task = response[0]             # 只取 Task;不处理 SSE,忽略 update event
        if task.artifacts:                   # 任务产物在 artifacts 字段(L2)
            artifact: Artifact = task.artifacts[0]
            text_content = get_message_text(artifact)

# 错误兜底:一个事件都没给出文本时,明确提示而不是静默空白
if text_content: display(Markdown(text_content))
else:            display(Markdown("**No final text content received ...**"))
```

两种形态的对照：

| | 形态① Message | 形态② Task + Artifact |
|---|---|---|
| SDK 返回类型 | `Message` | `tuple(Task, UpdateEvent)`（ClientEvent） |
| 适用场景 | 快速同步回答（本课 policy agent） | 长任务、有生命周期状态（后面课程的 agent 会用到） |
| 取结果 | `get_message_text(response)` | `task.artifacts[0]` → `get_message_text(artifact)` |
| 关联字段 | `message_id` | `task.id` + 状态（submitted/working/completed/failed，L2） |

运行结果：依次打印 Agent Card 详情表、发送的 prompt、Message ID、最终回答——与 L3 直接调 `PolicyAgent` 得到的内容一致，但这次**跨越了进程边界、走的是标准协议**。

> **对比课程 10-MCP L5 的 client**：两边 client 的骨架惊人相似——都是"工厂/会话建连接 → 发现（MCP `list_tools` / A2A `get_card`）→ 调用"。但**控制权分布**相反：MCP client 把工具清单交给**自己进程里的 LLM**决策，工具调用循环（LLM 选工具 → 执行 → 回填结果）跑在 client 侧，对端只是被动执行函数；A2A client 只发一句自然语言，**推理循环整个跑在对端**，client 拿到的直接是结论。一句话：**MCP 是调用（invoke），A2A 是委派（delegate）**。这也解释了响应模型的差异——函数调用天然同步单值，所以 MCP 简单；委派的任务可长可短，所以 A2A 必须有 Message/Task 双形态和生命周期。06-protocols.md 的 2026 参考架构"MCP 接工具(L1) + A2A 接 agent(L4)"，落到代码上就是这两种 client 并存于同一个系统。

> **架构师视角**：`async for` + `isinstance` 双分支这段样板代码，是 A2A client 的**最小完备消费者**——哪怕你今天只对接一个"秒回 Message"的 Agent，也应把 Task 分支和空结果兜底写全，因为**响应形态是 server 的自由，不是 client 的假设**（同一个 client 下节课就会遇到走 Task 的 agent）。把它抽成团队公共的 `consume_a2a_response()` 工具函数，是接入第二个 Agent 前就该做的资产沉淀。

## 5. 本课总结

| 要点 | 一句话 |
|---|---|
| 连接 | `httpx.AsyncClient`（传输）+ `ClientFactory.connect`（协议），只需一个 URL |
| 发现 | `get_card()` 拉 AgentCard；生产上由 supervisor agent 汇集全部 Card 做路由 |
| 发送 | `create_text_message_object` → `send_message`，返回异步事件迭代器 |
| 双形态 | Message 直接取文本；Task 从 `artifacts` 取产物、忽略 update event（不处理 SSE） |
| 复用 | 同一 client 换 port/Card 即可调用任何 A2A Agent（L6 伏笔） |

> **记忆点（引出 L6）**：闭环虽成，但系统里只有一个 Agent，而且是我们**手写 Executor 裸包**出来的。L6 引入第二个 Agent——用 **Google ADK + Gemini 3 Pro** 构建、带 Google Search 的 Research Agent，并且 ADK **内置 A2A 集成**，不用再手写 AgentExecutor；notebook 里注释掉的 `RESEARCH_AGENT_PORT` 和第二条 prompt，就是留给它的座位。异构框架 + 异构模型 + 同一协议，A2A 的卖点从这里才真正开始兑现。

## 与我的资产映射

- 协议层：`agent/skills/agent-selection/2-framework/06-protocols.md`（A2A"运行时发现对端"的具体形态就是 get_card；supervisor 汇集 Card 做路由 = 该页 L4 轴的标准玩法）
- MCP 对照：`agent/courses/10-MCP: Build Rich-Context AI Apps with Anthropic/notes/L5-构建MCP客户端.md`（client 侧黄金对比：invoke vs delegate、控制权在谁的进程里）
- 多 Agent 层：`agent/skills/agent-selection/2-framework/`（supervisor/coordinator 路由模式；进程内多角色 vs 跨进程 A2A 的分界）
- 面试复习包：`agent/interview/jd-senior-agent-engineer/`（多 Agent 协作与协议互操作是高频考点，Message/Task 双形态 + 生命周期可作答题素材）
- [[project_selection_matrix]]
