# L3 · 用 Letta 构建 MemGPT Agent：Agent State 全解

## 1. Letta 的架构特点：Agent 即服务

Letta 与多数 agent 框架的根本差异：**它是一个 server**。你连接运行中的 Letta 服务（`localhost:8283` / Letta Cloud / Desktop），通过 API 创建和交互 agent。

```python
from letta_client import Letta
client = Letta(base_url="http://localhost:8283")
```

**一切 agent state 自动存进服务端数据库**——不需要自己做 checkpoint/重载，state 永远在。

> **架构师视角**：这是"**stateful agent as a service**"路线。对比：LangGraph 是库（persistence 靠你配 checkpointer），12a 是自建（手写 MemoryManager + Oracle）。Letta 把持久化做成默认且不可见——代价是**必须部署/依赖一个服务**。选型时问一句：团队要的是"库的灵活"还是"服务的省心"？这直接进 [[project_selection_matrix]] 记忆层的对比表。

## 2. 设计 Agent 的四个旋钮（knobs）

课程明确给了 agent 设计的调参面板，本质都在控制"每步什么进 context"：

1. **Prompt**：system prompt + persona（定义行为）
2. **Tools**：agent 能调什么
3. **记忆管理方式**：怎么组织/管理记忆（L4 自定义）
4. **记忆内容**：core / archival 里实际存了什么

## 3. 创建 agent 与消息交互

```python
agent_state = client.agents.create(
    name="simple_agent",
    memory_blocks=[
        {"label": "human", "value": "My name is Charles", "limit": 10000},  # 可覆盖字符上限
        {"label": "persona", "value": "You are a helpful assistant and you always use emojis"},
    ],
    model="openai/gpt-4o-mini-2024-07-18",
    embedding="openai/text-embedding-3-small",
)
response = client.agents.messages.create(agent_id=agent_state.id,
    messages=[{"role": "user", "content": "hows it going????"}])
```

响应是一个**消息类型列表**（这套类型系统贯穿全课）：
- `reasoning_message` —— agent 内心独白（L2 的 inner thoughts）
- `assistant_message` —— 给用户的回复
- `tool_call_message` / `tool_return_message` —— 工具调用与返回
- `user_message`

还带 usage：`completion_tokens / prompt_tokens / step_count`。**step_count = agent 走了几步**——简单回复是 1，带工具链的任务会更高。

## 4. Agent State 的四大件（逐一可查）

| 组件 | 查看方式 | 说明 |
|---|---|---|
| System prompt | `agent_state.system` | 很长；含大量记忆管理指令。**能改但慎改** |
| Tools | `agent_state.tools` | 默认带 6 件套（见下） |
| Core memory | `agent_state.memory` | blocks 列表，每块有唯一 ID |
| 消息史/档案 | `client.agents.messages.list()` / `passages.list()` | 走 client 查 |

**默认工具 6 件套**（对照 L2 概念）：
- `archival_memory_insert` / `archival_memory_search` —— 档案记忆读写
- `conversation_search` —— 搜 recall memory（消息史）
- `core_memory_append` / `core_memory_replace` —— 编辑窗口内记忆块
- `send_message` —— **回复用户本身也是工具**（agent 显式选择"我要沟通"）

## 5. Core memory 自编辑实战（heartbeat 现形）

告诉 agent"my name actually Sarah"（此前 human 块写的是 Charles）：

1. reasoning：用户名字更新为 Sarah
2. `core_memory_replace(label="human", old="Charles", new="Sarah")` + **`request_heartbeat=True`**
3. （心跳唤醒第二步）reasoning → `send_message("Nice to meet you Sarah...")`

`step_count == 2`——心跳让 agent 一条消息内做两件事。事后 `client.agents.blocks.retrieve(...)` 可验证块值真的变了。

> 这就是 L1 手写版的框架化：L1 里"非工具即退出"的循环约定，在 Letta 里变成**每个工具都带 `request_heartbeat` 参数**，LLM 显式控制续不续。

## 6. Archival memory 双向写入

- **Agent 写**：发消息"把 'Bob loves cats' 存进 archival" → agent 调 `archival_memory_insert`
- **开发者写**：`client.agents.passages.create(agent_id=..., text="Bob's loves boston terriers")`（直接插库，返回含 embedding）

检索："What animals do I like? Search archival." → agent 调 `archival_memory_search(query="animals")`——**query 是 agent 自己决定的**，还能翻页。两条记忆（agent 存的 + 开发者存的）都被召回。

> **记忆点**：passages（passage = archival 的一行）是开发者和 agent 共用的数据面。生产里这意味着**离线批量灌数据（开发者面）与在线自主积累（agent 面）天然融合在同一存储**——12a 里灌 arXiv 数据集 + agent 工具写回，其实是同一个模式的手工版。
