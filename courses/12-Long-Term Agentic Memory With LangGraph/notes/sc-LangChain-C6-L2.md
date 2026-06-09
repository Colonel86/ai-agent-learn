# 第 2 课：构建 Baseline 邮件助理（无记忆版）

> 课程：Long-Term Agentic Memory With LangGraph · Lesson 2
> 讲师：Harrison Chase
> 原文件：
> - `subtitles/sc-LangChain-C6-L2.vtt`
> - `code/lesson_2.md`

---

## 一、本课目标

> **构建一个"裸"的邮件助理**——还没有任何长期记忆功能，只是把基础流程跑通。
>
> 后续 4 节课会逐步把 Semantic / Episodic / Procedural 三类记忆塞进来。

---

## 二、🗺 整体架构

```
邮件输入
    ↓
┌──────────────────────────────────────────┐
│  ① Triage Router（分诊）                  │
│  LLM 分类 → ignore / notify / respond    │
└────────┬───────────┬─────────────────────┘
         │           │
   ignore/notify   respond
         │           │
         ↓           ↓
       END    ┌──────────────────────────┐
              │ ② Response Agent          │
              │  (ReAct loop)             │
              │  Tools:                   │
              │   📅 check_calendar       │
              │   ✉ write_email           │
              │   🗓 schedule_meeting     │
              └──────────────────────────┘
                       ↓
                      END
```

两层结构：
- **外层**：State Graph（Triage → Response）
- **内层**：Response Agent 是个**完整的 ReAct Agent**（LLM + Tools 循环）

---

## 三、Step 1：环境与基础数据

### 3.1 环境变量

```python
import os
from dotenv import load_dotenv
_ = load_dotenv()
```

### 3.2 用户画像（Profile）

```python
profile = {
    "name": "John",
    "full_name": "John Doe",
    "user_profile_background": (
        "Senior software engineer leading a team of 5 developers"
    ),
}
```

> 💡 **改成你自己的信息即可**——这是 Agent 替谁处理邮件。

### 3.3 提示指令（Prompt Instructions）

```python
prompt_instructions = {
    "triage_rules": {
        "ignore":  "Marketing newsletters, spam emails, mass company announcements",
        "notify":  "Team member out sick, build system notifications, project status updates",
        "respond": "Direct questions from team members, meeting requests, critical bug reports",
    },
    "agent_instructions": "Use these tools when appropriate to help manage John's tasks efficiently."
}
```

### 🎯 为什么把这些**单独抽出来**？

> 1. **模块化**：方便维护和可视化
> 2. **🔥 为后续记忆做铺垫**：未来这些**会被记忆系统自动迭代生成**——它们必须能独立于其他 prompt 单独更新

### 3.4 示例邮件

```python
email = {
    "from":    "Alice Smith <alice.smith@company.com>",
    "to":      "John Doe <john.doe@company.com>",
    "subject": "Quick question about API documentation",
    "body":    "Hi John, I was reviewing the API documentation ..."
}
```

四个字段：**from / to / subject / body**——这是邮件的标准 schema。

---

## 四、Step 2：构建 Triage Router

### 4.1 选择模型

```python
from langchain.chat_models import init_chat_model

llm = init_chat_model("openai:gpt-4o-mini")
```

> 💡 用 **`gpt-4o-mini`**——分诊任务简单，省钱。Response Agent 才用大模型。

### 4.2 🆕 用 Pydantic 定义结构化输出

```python
from pydantic import BaseModel, Field
from typing_extensions import Literal


class Router(BaseModel):
    """Analyze the unread email and route it according to its content."""

    reasoning: str = Field(
        description="Step-by-step reasoning behind the classification."
    )
    classification: Literal["ignore", "respond", "notify"] = Field(
        description=(
            "The classification of an email: "
            "'ignore' for irrelevant emails, "
            "'notify' for important information that doesn't need a response, "
            "'respond' for emails that need a reply"
        ),
    )
```

### 🎯 两个字段的设计

| 字段 | 作用 |
|------|------|
| **reasoning** | LLM 的思考链——为什么这么分类 |
| **classification** | 三选一的最终决定（`Literal` 强约束） |

### 4.3 绑定结构化输出

```python
llm_router = llm.with_structured_output(Router)
```

> ⚡ **`.with_structured_output(Router)`** 让 LLM **必然返回符合 Router schema 的对象**——这是上一门课（Pydantic for LLM Workflows）讲的"直接传模型给 API"的应用。

### 4.4 Prompt Template 与变量插值

```python
from prompts import triage_system_prompt, triage_user_prompt
```

`triage_system_prompt` 包含几个区块：
- **Role**：AI 的角色定位
- **User Background**：用户画像
- **Instructions**：三类分类规则
- **Rules**（带 `{}` 占位符）：实际的 triage 规则
- **Few-shot Examples**：留给后续 Episodic 记忆插入

### 4.5 格式化 Prompt 并调用

```python
system_prompt = triage_system_prompt.format(
    full_name=profile["full_name"],
    name=profile["name"],
    examples=None,                              # 🎯 暂时为空，后续填 episodic
    user_profile_background=profile["user_profile_background"],
    triage_no=prompt_instructions["triage_rules"]["ignore"],
    triage_notify=prompt_instructions["triage_rules"]["notify"],
    triage_email=prompt_instructions["triage_rules"]["respond"],
)

user_prompt = triage_user_prompt.format(
    author=email["from"],
    to=email["to"],
    subject=email["subject"],
    email_thread=email["body"],
)

result = llm_router.invoke([
    {"role": "system", "content": system_prompt},
    {"role": "user",   "content": user_prompt},
])

print(result)
# Router(reasoning="...", classification="respond")
```

---

## 五、Step 3：构建 Response Agent

### 5.1 三个工具（都是 mock）

```python
from langchain_core.tools import tool


@tool
def write_email(to: str, subject: str, content: str) -> str:
    """Write and send an email."""
    return f"Email sent to {to} with subject '{subject}'"


@tool
def schedule_meeting(
    attendees: list[str],
    subject: str,
    duration_minutes: int,
    preferred_day: str
) -> str:
    """Schedule a calendar meeting."""
    return f"Meeting '{subject}' scheduled for {preferred_day} with {len(attendees)} attendees"


@tool
def check_calendar_availability(day: str) -> str:
    """Check calendar availability for a given day."""
    return f"Available times on {day}: 9:00 AM, 2:00 PM, 4:00 PM"
```

> 💡 **生产环境**：把 mock 函数换成 Gmail / Outlook / Google Calendar API 即可。

### 5.2 🆕 动态 Prompt 函数

```python
from prompts import agent_system_prompt


def create_prompt(state):
    return [
        {
            "role": "system",
            "content": agent_system_prompt.format(
                instructions=prompt_instructions["agent_instructions"],
                **profile        # 🔑 用户画像直接展开到 prompt
            )
        }
    ] + state['messages']
```

### 🎯 为什么 prompt 是个**函数**而不是字符串？

> Agent 每轮思考时都要重新拼接 prompt——
> - 系统消息（含动态变量）
> - **历史对话**（来自 state）
>
> 函数式 prompt **可以根据 state 动态生成**。

### 5.3 用 `create_react_agent` 一键构建

```python
from langgraph.prebuilt import create_react_agent

tools = [write_email, schedule_meeting, check_calendar_availability]

agent = create_react_agent(
    "openai:gpt-4o",
    tools=tools,
    prompt=create_prompt,
)
```

> ✨ **`create_react_agent`** 是 LangGraph 提供的**开箱即用 ReAct Agent**——LLM ↔ Tools 自动循环。

### 5.4 单测

```python
response = agent.invoke({
    "messages": [{
        "role": "user",
        "content": "what is my availability for tuesday?"
    }]
})

response["messages"][-1].pretty_print()
# "You have the following available time slots on Tuesday:
#  9 a.m., 2 p.m., and 4 p.m."
```

✅ Agent 调用 `check_calendar_availability` 工具，拿到 mock 数据返回。

---

## 六、Step 4：组装完整邮件 Agent（State Graph）

### 6.1 定义 State

```python
from typing_extensions import TypedDict, Annotated
from langgraph.graph import add_messages


class State(TypedDict):
    email_input: dict                            # 用户传入的邮件
    messages: Annotated[list, add_messages]      # Agent 执行中的消息列表
```

### 🆕 `Annotated[list, add_messages]`

> **告诉 LangGraph**：`messages` 字段在多次更新时**采用追加（append）合并策略**，而不是覆盖。

### 6.2 🌟 核心：Triage Router 节点（带 Command）

```python
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command
from typing import Literal


def triage_router(state: State) -> Command[
    Literal["response_agent", "__end__"]
]:
    # 拆解邮件
    author = state['email_input']['author']
    to = state['email_input']['to']
    subject = state['email_input']['subject']
    email_thread = state['email_input']['email_thread']

    # 拼 prompt
    system_prompt = triage_system_prompt.format(
        full_name=profile["full_name"],
        name=profile["name"],
        user_profile_background=profile["user_profile_background"],
        triage_no=prompt_instructions["triage_rules"]["ignore"],
        triage_notify=prompt_instructions["triage_rules"]["notify"],
        triage_email=prompt_instructions["triage_rules"]["respond"],
        examples=None
    )
    user_prompt = triage_user_prompt.format(
        author=author, to=to, subject=subject, email_thread=email_thread
    )

    # 调 LLM 分类
    result = llm_router.invoke([
        {"role": "system", "content": system_prompt},
        {"role": "user",   "content": user_prompt},
    ])

    # 三分支处理
    if result.classification == "respond":
        print("📧 Classification: RESPOND")
        goto = "response_agent"
        update = {
            "messages": [{
                "role": "user",
                "content": f"Respond to the email {state['email_input']}",
            }]
        }
    elif result.classification == "ignore":
        print("🚫 Classification: IGNORE")
        update, goto = None, END
    elif result.classification == "notify":
        print("🔔 Classification: NOTIFY")
        update, goto = None, END
    else:
        raise ValueError(f"Invalid classification: {result.classification}")

    return Command(goto=goto, update=update)
```

### 🌟 关键新概念：`Command`

> **同时返回"下一步去哪"和"如何更新 state"** —— LangGraph 的强大原语。

```python
return Command(
    goto="response_agent",     # 下一个节点
    update={"messages": [...]}  # 同时更新 state
)
```

### 🎯 类型提示：`Command[Literal["response_agent", "__end__"]]`

> 显式声明这个节点**只可能跳到这两个目的地**——LangGraph 用它做静态校验和图可视化。

---

## 七、组装并编译图

```python
email_agent = StateGraph(State)
email_agent = email_agent.add_node(triage_router)
email_agent = email_agent.add_node("response_agent", agent)   # 子图
email_agent = email_agent.add_edge(START, "triage_router")
email_agent = email_agent.compile()
```

### 🆕 子图嵌套

> **`response_agent`** 本身就是一个完整的 ReAct Agent（独立的图）——这里把它**作为节点**塞进外层图里。

### 可视化（Mermaid 图）

```python
display(Image(email_agent.get_graph(xray=True).draw_mermaid_png()))
```

`xray=True` 让图**展开嵌套子图**，能看到 Response Agent 内部的 ReAct 循环结构。

---

## 八、🧪 端到端测试

### 8.1 测试 1：垃圾营销邮件 → 应当 IGNORE

```python
email_input = {
    "author":  "Marketing Team <marketing@amazingdeals.com>",
    "to":      "John Doe <john.doe@company.com>",
    "subject": "🔥 EXCLUSIVE OFFER: Limited Time Discount! 🔥",
    "email_thread": "Don't miss out on this INCREDIBLE opportunity! 80% OFF..."
}
response = email_agent.invoke({"email_input": email_input})
# 🚫 Classification: IGNORE
```

### 8.2 测试 2：同事问 API 文档 → 应当 RESPOND

```python
email_input = {
    "author":  "Alice Smith <alice.smith@company.com>",
    "to":      "John Doe <john.doe@company.com>",
    "subject": "Quick question about API documentation",
    "email_thread": "Hi John, I was reviewing the API documentation..."
}
response = email_agent.invoke({"email_input": email_input})
# 📧 Classification: RESPOND
# → Response Agent 接管
# → 调用 write_email 工具
# → 完成回复

for m in response["messages"]:
    m.pretty_print()
```

输出会看到：
1. Human Message：Triage Router 注入的"Respond to the email ..."
2. AI Message：Agent 调用 `write_email` 工具
3. Tool Message：Email sent 确认
4. Final AI Message：总结"I've responded to Alice's email..."

---

## 九、💎 本课核心知识点

### 9.1 双层 Agent 架构

| 层 | 职责 | 实现 |
|----|------|------|
| **外层 State Graph** | 流程编排（分诊 → 响应/结束） | `StateGraph` |
| **内层 ReAct Agent** | 业务执行（调工具、循环思考） | `create_react_agent` |

### 9.2 三个 LangGraph 关键概念

| 概念 | 作用 |
|------|------|
| **`State`** | 整个 Agent 的"状态"，节点间传递 |
| **`Command`** | 节点的返回值——同时控制路由和状态更新 |
| **`Annotated[list, add_messages]`** | 消息列表的"追加"合并策略 |

### 9.3 Pydantic 在分类中的作用

> **`Router` 模型 + `with_structured_output()` = LLM 永远只输出 ignore/respond/notify 三选一**

避免了"LLM 偶尔说点别的话"的尴尬。

### 9.4 模块化的远见

> Profile / triage_rules / agent_instructions **故意拆出来** ——**为下一课的"记忆系统"做准备**：
>
> - **Procedural 记忆**：这些 prompts 自己会被自动迭代
> - **必须能独立更新**

---

## 十、📝 完整代码模板（速查）

```python
# === 1. 配置 ===
profile = {"name": "...", "full_name": "...", "user_profile_background": "..."}
prompt_instructions = {
    "triage_rules": {"ignore": "...", "notify": "...", "respond": "..."},
    "agent_instructions": "...",
}

# === 2. Triage（结构化输出） ===
class Router(BaseModel):
    reasoning: str
    classification: Literal["ignore", "respond", "notify"]

llm_router = llm.with_structured_output(Router)

# === 3. Tools ===
@tool
def write_email(to, subject, content): ...

@tool
def schedule_meeting(attendees, subject, duration_minutes, preferred_day): ...

@tool
def check_calendar_availability(day): ...

# === 4. Response Agent (ReAct) ===
agent = create_react_agent("openai:gpt-4o", tools=tools, prompt=create_prompt)

# === 5. State ===
class State(TypedDict):
    email_input: dict
    messages: Annotated[list, add_messages]

# === 6. Triage Node (with Command) ===
def triage_router(state) -> Command[Literal["response_agent", "__end__"]]:
    result = llm_router.invoke([...])
    if result.classification == "respond":
        return Command(goto="response_agent", update={"messages": [...]})
    return Command(goto=END, update=None)

# === 7. Compile ===
graph = StateGraph(State)
graph.add_node(triage_router)
graph.add_node("response_agent", agent)
graph.add_edge(START, "triage_router")
email_agent = graph.compile()

# === 8. Run ===
response = email_agent.invoke({"email_input": email})
```

---

## 🎯 下一课预告

> **Lesson 3**：把 **Semantic Memory（语义记忆）** 加到 Response Agent 上——
>
> Agent 在 hot path 中**即时读写记忆**，记住用户偏好、人物画像、上下文事实。
