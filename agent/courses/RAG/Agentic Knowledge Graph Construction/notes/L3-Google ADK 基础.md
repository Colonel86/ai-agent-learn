# L3 · Google ADK 基础：造并跑第一个带工具的 Agent

> 课程：Agentic Knowledge Graph Construction（DeepLearning.AI × Neo4j，C2）
> 本课任务：用 **Google ADK** 亲手造一个 Agent——定义一个操作 Neo4j 的工具、配置 `Agent`、搭执行环境（`Runner` + `SessionService`）、手写一遍事件循环（event loop）看清内部机理，最后封成 `AgentCaller` 助手类供全课复用。
> 代码：`code/intro_to_adk_1.md`

## 1. Setup：导入与模型

```python
import os
from google.adk.agents import Agent                 # 描述"一个 Agent 是什么"的核心类
from google.adk.models.lite_llm import LiteLlm       # 用 LiteLLM 让 ADK 接 OpenAI
from google.adk.sessions import InMemorySessionService  # 内存版 memory
from google.adk.runners import Runner                # Agent 的执行器
from google.genai import types                       # 造 message 的 Content/Parts
from typing import Optional, Dict, Any

MODEL_GPT = "openai/gpt-4o"        # 本课用 OpenAI 的 GPT-4o
llm = LiteLlm(model=MODEL_GPT)     # LiteLLM 作为 ADK ↔ OpenAI 的适配壳
```

要点：**ADK 本是 Google 的框架，但通过 LiteLLM 这层薄封装就能驱动 OpenAI**——模型是可插拔的。

## 2. `neo4j_for_adk`：让 Neo4j 结果对 ADK 友好

实验环境给了个 helper `neo4j_for_adk`，从中导入单例 `graphdb`，它包住 Neo4j Python driver，把结果整成 ADK 喜欢的形状：

```python
from neo4j_for_adk import graphdb

# send_query 跑一条 Cypher，结果统一成带 status 的 dict
neo4j_is_ready = graphdb.send_query("RETURN 'Neo4j is Ready!' as message")
print(neo4j_is_ready)
# → {'status': 'success', 'query_result': [{'message': 'Neo4j is Ready!'}]}
```

`neo4j_for_adk.py` 内部的关键设计（讲师带读了源码）：

- 结果**必须**回成 dict，带 `status`：`success` 或 `error`——两个 helper `tool_success` / `tool_error` 负责格式化；
- 一个 `to_python` 函数把 Neo4j 各种返回类型转成**易序列化**的形式（ADK 要能持久化结果）；
- 上层类 `Neo4jForADK` 包住 driver、初始化环境变量、暴露 `send_query`；
- 最后导出**单例 `graphdb`**（只用一个 driver / 一个连接），全课 notebook 复用。

> **架构师视角**：这个 helper 的全部价值就一句——**把外部系统的返回，收敛成框架统一的 `{status, ...}` 契约**。工具返回结构一致（success/error + 数据），Agent 才能可靠地判断"这一步成没成、要不要重试或上报"。这是给 Agent 写工具时最容易被忽略、却最影响鲁棒性的一环：**别把裸异常或异构结果甩给 LLM，先规约成契约**。

## 3. 定义工具：一个函数就是一个 tool

```python
def say_hello(person_name: str) -> dict:
    """Formats a welcome message to a named person.

    Args:
        person_name (str): the name of the person saying hello
    Returns:
        dict: 带 'status'（'success'/'error'）；success 时含 'query_result' 行数组，
              error 时含 'error_message'。
    """
    return graphdb.send_query(
        "RETURN 'Hello to you, ' + $person_name AS reply",   # $person_name 是查询参数
        {"person_name": person_name}
    )
```

两个不能省的细节：

1. **docstring 不是给人看的，是给 LLM 看的**。ADK 把 docstring 连同工具一起传给 LLM，LLM 靠它理解"这工具干什么、参数是什么、返回什么"——写工具时 docstring 是**功能规格**，不是注释。
2. **用查询参数 `$person_name`，不要字符串拼接**。`$` 在 Cypher 里表示查询参数，值作为变量传入而非模板替换，**防注入攻击**。演示：

```python
print(say_hello("RETURN 'injection attack avoided'"))
# 恶意串只是被当成普通名字拼进问候语，不会被当 Cypher 执行
```

## 4. 定义 Agent：name / model / description / instruction / tools

```python
hello_agent = Agent(
    name="hello_agent_v1",          # 唯一标识；带版本号便于调试/并存多版本
    model=llm,                       # 前面定义的 LiteLLM→OpenAI
    description="Has friendly chats with a user.",   # 给"别的 Agent"看：何时该委派给我
    instruction="""You are a helpful assistant, chatting with a user.
                Be polite and friendly, introducing yourself and asking who the user is.
                If the user provides their name, use the 'say_hello' tool to get a custom greeting.
                If the tool returns an error, inform the user politely.
                If the tool is successful, present the reply.""",   # 给"自己"看：等同 system prompt
    tools=[say_hello],               # 直接传函数名数组
)
```

`description` vs `instruction` 是两个易混但关键的参数：

- **`description`**：Agent 的对外简介，**给其他 Agent / ADK 看的"公开文档"**，决定别人**何时把任务委派（delegate）给它**；
- **`instruction`**：给 LLM 的详细行为指引，**等同 prompt engineering 里的 system prompt**——人格、目标、**何时/如何用哪个工具**。

## 5. 跑 Agent：Runner + SessionService + 事件循环

Agent 光有定义还不能跑，需要**执行环境**和 **memory**。

### 5.1 建 Runner 和 Session

```python
app_name = hello_agent.name + "_app"
user_id = hello_agent.name + "_user"
session_id = hello_agent.name + "_session_01"

session_service = InMemorySessionService()          # 简单内存实现，适合测试
await session_service.create_session(
    app_name=app_name, user_id=user_id, session_id=session_id)

runner = Runner(                                     # 编排引擎
    agent=hello_agent, app_name=app_name, session_service=session_service)
```

- **`SessionService`**：管对话历史和 state（不同 user/session），`InMemorySessionService` 全存内存；
- **`Runner`**：核心编排引擎——收用户输入、路由到 Agent、管 LLM 和工具调用、经 SessionService 更新会话、并**吐出代表进度的 Event**。
- 生产环境会有多 user / 多 session / 多 app，所以这三个 id 是 `run` 的不同参数；本课简化成单 user、单 session。

### 5.2 手写一遍事件循环（看清机理）

```python
user_message = "Hello, I'm ABK"
content = types.Content(role='user', parts=[types.Part(text=user_message)])  # 打包成 ADK Content

final_response_text = "Agent did not produce a final response."   # 兜底默认值

async for event in runner.run_async(               # 异步：LLM/工具都是 I/O 密集
        user_id=user_id, session_id=session_id, new_message=content):
    # 每个 event 是 Agent 的一次进度更新（工具调用请求/结果/中间想法/最终响应）
    if event.is_final_response():                  # 关键：标记本轮收尾
        if event.content and event.content.parts:
            final_response_text = event.content.parts[0].text   # 取第一段文本
        elif event.actions and event.actions.escalate:         # 处理上报/错误
            final_response_text = f"Agent escalated: {event.error_message or 'No specific message.'}"
        break                                       # 拿到最终响应就停

print(f"<<< Agent Response: {final_response_text}")
```

三个要点，正好印证 L2 的 "agent = loop + LLM + switch"：

- **`for` 循环 = 事件循环**：一条用户消息进去，Agent 在给出最终响应前可能做一串事情（调工具、再想……），每一步吐一个 event；
- **`is_final_response()` = 收尾旗标**：Agent 表示"我想完了"，才 break；
- **`escalate`（上报/升级）**：子 Agent 表示"当前信息我处理不了"，把事情**上报给父 Agent 或别的合适 Agent**——这正是 L2 多 Agent 委派的底层机制。

> **对比《Knowledge Graphs for RAG》(Neo4j C1)**：C1 里你直接写 Cypher、直接调 driver，是**命令式**地一步步查图。本课把同样的 Neo4j 调用**包成工具塞进 Agent 的事件循环**——"要不要调这个工具、传什么参数、结果好不好"改由 LLM 在循环里决策。同一个 `graphdb.send_query`，在 C1 是你亲手调用，在 C2 是 Agent 自主编排。抽象层级抬高的代价就是这一圈事件循环和非确定性。

## 6. 封装 `AgentCaller`：单 user 单 session 的复用壳

手写事件循环太啰嗦，讲师把它连同 runner/session 的构造封成 `AgentCaller`，全课复用：

```python
class AgentCaller:
    """对 ADK agent 的简单封装（假设单 user 单 session）。"""
    def __init__(self, agent, runner, user_id, session_id):
        self.agent, self.runner = agent, runner
        self.user_id, self.session_id = user_id, session_id

    async def call(self, user_message: str, verbose: bool = False):
        content = types.Content(role='user', parts=[types.Part(text=user_message)])
        final_response_text = "Agent did not produce a final response."
        async for event in self.runner.run_async(
                user_id=self.user_id, session_id=self.session_id, new_message=content):
            if event.is_final_response():
                if event.content and event.content.parts:
                    final_response_text = event.content.parts[0].text
                elif event.actions and event.actions.escalate:
                    final_response_text = f"Agent escalated: {event.error_message or 'No specific message.'}"
                break
        return final_response_text

# 工厂方法：因为初始化要 await 异步调用，用工厂而非构造器
async def make_agent_caller(agent, initial_state: Optional[Dict[str, Any]] = {}):
    app_name = agent.name + "_app"
    user_id = agent.name + "_user"
    session_id = agent.name + "_session_01"
    session_service = InMemorySessionService()
    await session_service.create_session(
        app_name=app_name, user_id=user_id, session_id=session_id,
        state=initial_state)                        # initial_state = Agent 的初始"记忆"
    runner = Runner(agent=agent, app_name=app_name, session_service=session_service)
    return AgentCaller(agent, runner, user_id, session_id)
```

跑一段多轮对话验证：

```python
hello_agent_caller = await make_agent_caller(hello_agent)

async def run_conversation():
    await hello_agent_caller.call("Hello I'm ABK")   # → Hello to you, ABK
    await hello_agent_caller.call("I am excited")

await run_conversation()
```

注意 `make_agent_caller` 的 `initial_state` 参数——它就是 Agent 的**初始 memory**，L5 之后会用它承载"用户目标"等跨 Agent 共享的关键信息。

## 本课总结

| 要点 | 一句话 |
|---|---|
| 模型可插拔 | ADK 经 LiteLLM 接 OpenAI GPT-4o，框架与模型解耦 |
| 工具返回契约 | `neo4j_for_adk` 把结果规约成 `{status: success/error, ...}`，Agent 才好判断 |
| docstring 是规格 | 工具 docstring 传给 LLM 当功能说明；查询参数 `$` 防注入 |
| description vs instruction | 前者给别的 Agent 看（何时委派），后者给自己看（=system prompt） |
| 三件套运行 | `Agent` + `Runner` + `SessionService`，事件循环里 `is_final_response()` 收尾 |
| escalate | 子 Agent 处理不了就上报父 Agent——多 Agent 委派的底层机制 |
| AgentCaller | 把事件循环+构造封装，工厂方法 `make_agent_caller` 全课复用 |

> **记忆点（引出 L4）**：L3 造出了单个能跑、带工具、有 memory 的 Agent，并留了 `initial_state` 这个共享记忆的口子。L4 在此之上组**一队 Agent**——一个 root agent 加两个子 Agent（say_hello 之外再加 say_goodbye），让它们**通过 delegation 协作、并访问一份可共享的 context**，把 L2 蓝图里的"分层委派"第一次真正跑起来。

## 与我的资产映射

- 设计模式：`agent/skills/agent-selection/11-design-patterns.md`（单 Agent = loop+LLM+switch 的最小实现，escalate 是委派的底层原语）
- 检索层：`agent/skills/agent-selection/3-retrieval.md`（把 Neo4j 查询包成工具，是 GraphRAG 里"Agent 自主查图"的基础形态）
- [[project_selection_matrix]]（框架层：Google ADK 的 Agent/Runner/SessionService 编程模型实测，及经 LiteLLM 换模型的可行性）
