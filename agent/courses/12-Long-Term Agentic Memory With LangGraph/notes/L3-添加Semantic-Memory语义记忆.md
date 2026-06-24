# 第 3 课：给邮件助理加 Semantic Memory（语义记忆）

> 课程：Long-Term Agentic Memory With LangGraph · Lesson 3
> 讲师：Harrison Chase
> 原文件：
> - `subtitles/sc-LangChain-C6-L3.vtt`
> - `code/lesson_3.md`

---

## 一、本课目标

> **在上一课的 Baseline Email Agent 基础上，给 Response Agent 增加两个工具——让它能读写"语义记忆"（Semantic Memory）。**

### 🎯 三个新能力

1. **🧠 学习用户事实**：自动抽取用户的偏好、人物关系等
2. **💾 存进长期记忆库**：跨对话持久化
3. **🔍 检索这些事实**：在需要时主动搜索

### Hot Path 模式

> Agent 在响应用户的**同一轮里**直接读写记忆——不是异步后台。

---

## 二、🆕 引入两位新成员

### 2.1 LangGraph Store（长期记忆存储）

```python
from langgraph.store.memory import InMemoryStore

store = InMemoryStore(
    index={"embed": "openai:text-embedding-3-small"}
)
```

| 关键参数 | 作用 |
|---------|------|
| **`index={"embed": ...}`** | 指定**嵌入模型**——记忆会被向量化以支持语义检索 |
| 用 `text-embedding-3-small` | OpenAI 的轻量嵌入模型 |

> 💡 **InMemoryStore** 是开发演示用的内存版。生产环境可以换 Postgres / Redis 等持久化后端。

### 2.2 LangMem（LangChain 出品的记忆工具库）

```python
from langmem import create_manage_memory_tool, create_search_memory_tool
```

> **LangMem** = LangChain 团队为本课程发布的**记忆管理工具包**——封装了"读写记忆"的常见模式，开箱即用。

---

## 三、🔧 创建记忆工具

```python
manage_memory_tool = create_manage_memory_tool(
    namespace=(
        "email_assistant",
        "{langgraph_user_id}",       # 🔑 模板变量
        "collection"
    )
)
search_memory_tool = create_search_memory_tool(
    namespace=(
        "email_assistant",
        "{langgraph_user_id}",
        "collection"
    )
)
```

### 🎯 关键概念：Namespace（命名空间）

> **三层 namespace 结构**给记忆做"隔离 / 分组"：

```
("email_assistant", "{user_id}", "collection")
        │              │             │
        │              │             └─ 集合名（可分多个集合）
        │              └─ 用户 ID（不同用户记忆完全隔离）
        └─ 应用名
```

### 🆕 `{langgraph_user_id}` 是模板变量

> 运行时通过 **`config`** 注入：
>
> ```python
> config = {"configurable": {"langgraph_user_id": "lance"}}
> response = agent.invoke({...}, config=config)
> ```
>
> 这样**多用户场景**下，每个人的记忆完全独立——不会串味。

---

## 四、🔍 看看 LangMem 工具长什么样

### 4.1 `manage_memory_tool`（写记忆）

```python
print(manage_memory_tool.name)
# 'manage_memory'

print(manage_memory_tool.args)
# {
#   "content": "...",     # 要存的内容
#   "action":  "create" | "update" | "delete",
#   "id":      "..."      # 不传会自动生成
# }
```

### 4.2 `search_memory_tool`（读记忆）

```python
print(search_memory_tool.args)
# {
#   "query":  "...",      # 搜索词
#   "limit":  10,
#   "offset": 0,
#   "filter": {...}       # 可选过滤
# }
```

> 🎯 **每个 memory 都有一个 ID**——支持 CRUD 全套操作（增 / 删 / 改 / 查）。

---

## 五、把工具挂到 Response Agent 上

### 5.1 更新 System Prompt

新增了两条 Tool 说明：

```python
agent_system_prompt_memory = """
< Role >
You are {full_name}'s executive assistant ...
</ Role >

< Tools >
1. write_email(to, subject, content)
2. schedule_meeting(attendees, subject, duration_minutes, preferred_day)
3. check_calendar_availability(day)
4. manage_memory - Store any relevant information about contacts, actions,
                   discussion, etc. in memory for future reference            🆕
5. search_memory - Search for any relevant information that may have been
                   stored in memory                                          🆕
</ Tools >

< Instructions >
{instructions}
</ Instructions >
"""
```

### 5.2 重建 Response Agent

```python
tools = [
    write_email,
    schedule_meeting,
    check_calendar_availability,
    manage_memory_tool,            # 🆕
    search_memory_tool,            # 🆕
]

response_agent = create_react_agent(
    "anthropic:claude-3-5-sonnet-latest",
    tools=tools,
    prompt=create_prompt,
    store=store,                    # 🔑 关键：把 store 传给 agent
)
```

> 🎯 **`store=store`** 必须传——这样 LangMem 工具才能找到底层存储。

---

## 六、🧪 直接测试 Response Agent

### 6.1 第 1 次：教它一个事实

```python
config = {"configurable": {"langgraph_user_id": "lance"}}

response = response_agent.invoke(
    {"messages": [{"role": "user", "content": "Jim is my friend"}]},
    config=config,
)
```

**Agent 自主行为**：
1. 看到"Jim is my friend"
2. **主动**调用 `manage_memory` 工具
3. 内容：`"Jim is John Doe's friend"`
4. 默认 `action="create"`，自动生成 ID

### 6.2 第 2 次：让它回忆

```python
response = response_agent.invoke(
    {"messages": [{"role": "user", "content": "who is jim?"}]},
    config=config,                  # 🔑 同一个 user_id
)
```

**Agent 自主行为**：
1. 看到"who is jim?"
2. **主动**调用 `search_memory(query="jim")`
3. 命中之前存的记忆
4. 回复：`"Based on my memory search, Jim is John Doe's friend."`

> ✨ **关键**：Agent 自己决定何时读、何时写——你不需要硬编码这些逻辑。

---

## 七、🔬 直接探查 Store

### 7.1 列出所有 namespace

```python
store.list_namespaces()
# [('email_assistant', 'lance', 'collection')]
```

### 7.2 列出某 namespace 下的所有记忆

```python
store.search(('email_assistant', 'lance', 'collection'))
# [Item(key="...", value={"content": "Jim is John Doe's friend"}, score=None)]
```

### 7.3 带 query 的语义搜索

```python
store.search(('email_assistant', 'lance', 'collection'), query="jim")
# [Item(..., score=0.5xxx)]   ← cosine similarity 分数
```

> 🎯 **score 是余弦相似度**，由初始化时传入的 embedding model 计算。

---

## 八、把记忆塞回完整邮件 Agent

### 8.1 改造点

相比 L2，只有两处变化：

```python
# ① 把 agent 重命名为 response_agent（语义更清晰）
email_agent = email_agent.add_node("response_agent", response_agent)

# ② compile 时传入 store
email_agent = email_agent.compile(store=store)    # 🔑 这一行是新加的
```

### 8.2 端到端流程图（不变）

```
邮件 → triage_router
         ↓
       respond
         ↓
   response_agent（带 5 个工具）
         ↓
   read/write memory + 调其他工具 + 写邮件
```

---

## 九、🎬 完整业务测试

### 9.1 测试 1：第一封新邮件

```python
email_input = {
    "author":  "Alice Smith <alice.smith@company.com>",
    "to":      "John Doe <john.doe@company.com>",
    "subject": "Quick question about API documentation",
    "email_thread": "Hi John, I was reviewing the API documentation ...",
}

response = email_agent.invoke({"email_input": email_input}, config=config)
```

**Agent 行为轨迹**：

```
📧 Classification: RESPOND
   ↓
🤖 AI: 调用 write_email     ← 给 Alice 写回复
   ↓
✅ Tool: Email sent
   ↓
🤖 AI: 调用 manage_memory   ← 自动记下"Alice 问了 API 文档的事"
   ↓
✅ Tool: Memory created
   ↓
🤖 Final AI: "I've responded to Alice and created a memory entry."
```

### 9.2 🌟 测试 2：跟进邮件（验证记忆生效）

```python
email_input = {
    "author":  "Alice Smith <alice.smith@company.com>",
    "to":      "John Doe <john.doe@company.com>",
    "subject": "Follow up",
    "email_thread": "Hi John, Any update on my previous ask?",
}

response = email_agent.invoke({"email_input": email_input}, config=config)
```

**Agent 行为轨迹**：

```
📧 Classification: RESPOND
   ↓
🤖 AI: 调用 search_memory   ← 🌟 主动查"Alice Smith 之前问过什么"
   ↓
✅ Tool 返回: "Follow up needed. Alice Smith inquired about missing API endpoints."
   ↓
🤖 AI: 调用 write_email     ← 写回复时引用了之前的 API 文档话题
   ↓
🤖 Final: "Thanks for following up regarding the API endpoints documentation..."
```

### 🤯 关键观察

> 即使是**完全独立的两次邮件调用**（中间没有任何对话历史传递），Agent 也能通过**长期记忆**串联起来——这就是"长期记忆"和"对话历史"的本质区别。

---

## 十、💎 本课核心知识点

### 10.1 三大新组件

| 组件 | 作用 |
|------|------|
| **`InMemoryStore`** | LangGraph 的长期记忆存储后端 |
| **LangMem 工具集** | `create_manage_memory_tool` + `create_search_memory_tool` |
| **Namespace 模板** | `(app, {user_id}, collection)` 多租户隔离 |

### 10.2 配置注入机制

```
config = {"configurable": {"langgraph_user_id": "..."}}
                    ↓
         运行时填入 namespace 模板
                    ↓
         不同用户的记忆完全隔离
```

### 10.3 Hot Path 的体现

| 步骤 | 时机 |
|------|------|
| 写记忆 | Agent 处理用户请求**当下**就写 |
| 读记忆 | Agent 思考时**实时**搜索 |
| **零延迟更新** | 下一秒再问，立刻能用 |

✅ 优点：**记忆即时生效**
❌ 缺点：Agent 要做更多事，响应可能稍慢

### 10.4 这就是"语义记忆"的真实形态

| 用户/事件 | 抽取的事实 |
|-----------|-----------|
| "Jim is my friend" | `Jim is John Doe's friend` |
| Alice 问 API 文档 | `Follow up needed: Alice Smith inquired about missing API endpoints` |
| 用户提到偏好 | `John prefers morning meetings` |

**事实 = 简短的自然语言陈述句**，由 LLM 自己决定要不要记。

---

## 十一、📝 完整代码模板（速查）

```python
# === 1. Store ===
from langgraph.store.memory import InMemoryStore
store = InMemoryStore(index={"embed": "openai:text-embedding-3-small"})

# === 2. Memory Tools ===
from langmem import create_manage_memory_tool, create_search_memory_tool

manage_memory = create_manage_memory_tool(
    namespace=("email_assistant", "{langgraph_user_id}", "collection")
)
search_memory = create_search_memory_tool(
    namespace=("email_assistant", "{langgraph_user_id}", "collection")
)

# === 3. Agent（注意 store=store） ===
response_agent = create_react_agent(
    "anthropic:claude-3-5-sonnet-latest",
    tools=[write_email, schedule_meeting, check_calendar_availability,
           manage_memory, search_memory],
    prompt=create_prompt,
    store=store,                      # 🔑
)

# === 4. Compile（也要传 store） ===
email_agent = (
    StateGraph(State)
    .add_node(triage_router)
    .add_node("response_agent", response_agent)
    .add_edge(START, "triage_router")
    .compile(store=store)             # 🔑
)

# === 5. Run（用 config 传 user_id） ===
config = {"configurable": {"langgraph_user_id": "lance"}}
response = email_agent.invoke({"email_input": email_input}, config=config)

# === 6. 直接探查 Store（调试用） ===
store.list_namespaces()
store.search(("email_assistant", "lance", "collection"), query="jim")
```

---

## 🎯 下一课预告

> **Lesson 4**：把 **Episodic Memory（情景记忆）** 加到 Triage Router 上——
>
> 用**Few-shot 示例**让 Agent 从"过去类似邮件如何分诊"中学习，而不是只靠固定规则。
