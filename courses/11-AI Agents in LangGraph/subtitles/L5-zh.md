构建长时运行的智能体时，持久化和流式输出是两个关键能力。

---

**持久化（Persistence）**

通过 **Checkpointer** 实现——在每个节点之间自动保存状态快照。

```python
from langgraph.checkpoint.sqlite import SqliteSaver

memory = SqliteSaver.from_conn_string(":memory:")  # 内存数据库，也可接 Redis/Postgres
abot = Agent(model, [tool], system=prompt, checkpointer=memory)
```

只需在 `graph.compile(checkpointer=checkpointer)` 时传入即可，其余代码无需修改。

**Thread ID** 用于区分不同对话：

```python
thread = {"configurable": {"thread_id": "1"}}
```

演示效果：
- Thread 1：问"SF 天气" → 问"LA 呢？" → 问"哪个更暖？" → 正确回答（有上下文记忆）
- Thread 2：直接问"哪个更暖？" → 模型困惑，不知道在比较什么（无历史记录）

同一 thread ID = 同一对话历史；不同 thread ID = 全新对话。这对生产环境中的多用户并发至关重要。

---

**流式输出（Streaming）**

**消息级流式**：用 `graph.stream()` 替代 `graph.invoke()`，每次节点产生更新时立即返回，可以实时看到中间过程：

```python
for event in abot.graph.stream(messages, thread):
    print(event)
# 输出顺序：AI消息（决定调用工具）→ Tool消息（搜索结果）→ AI消息（最终回答）
```

**Token 级流式**：用异步的 `astream_events()` 方法，监听 `on_chat_model_stream` 事件，逐 token 实时打印（函数调用阶段无内容可流，只有最终回答阶段才会流式输出）：

```python
async for event in abot.graph.astream_events(messages, thread, version="v1"):
    if event["event"] == "on_chat_model_stream":
        print(event["data"]["chunk"].content, end="|")
```

需要将 SqliteSaver 替换为 AsyncSqliteSaver 以支持异步。

---

**总结**

持久化 + 流式输出是生产级智能体的标配：前者让智能体能在多对话间保持记忆，后者让用户实时看到智能体的执行过程。

持久化还为下一节的**人工介入（Human-in-the-Loop）**奠定基础——暂停执行、等待人工审核、再继续都依赖 Checkpointer。我们下节课见。