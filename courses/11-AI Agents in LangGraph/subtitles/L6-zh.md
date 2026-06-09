本节介绍 LangGraph 中三种人工介入（Human-in-the-Loop）模式。

---

**模式一：中断执行，等待审批**

在 `graph.compile()` 时添加 `interrupt_before=["action"]`，智能体在执行工具调用前自动暂停：

```python
self.graph = graph.compile(
    checkpointer=checkpointer,
    interrupt_before=["action"]
)
```

暂停后可以检查当前状态：
```python
state = abot.graph.get_state(thread)
# state.next 显示 ("action",)，即下一步将执行工具节点
```

确认无误后，传入 `None` 继续执行：
```python
for event in abot.graph.stream(None, thread):
    print(event)
```

也可以在循环中加入用户确认交互，让人类决定是否继续。

---

**模式二：修改当前状态**

智能体误解了"LA"为洛杉矶，实际上想问路易斯安那州。可以直接修改状态中的工具调用参数：

```python
current_values = abot.graph.get_state(thread)
# 找到最后一条 AI 消息中的 tool_calls，修改查询参数
current_values.values["messages"][-1].tool_calls[0]["args"]["query"] = "current weather in Louisiana"
# 更新状态
abot.graph.update_state(thread, {"messages": current_values.values["messages"]})
# 继续执行
for event in abot.graph.stream(None, thread):
    print(event)
```

---

**模式三：时间旅行（Time Travel）**

每次状态变更都被 Checkpointer 保存为快照，可以通过 `get_state_history()` 获取所有历史状态：

```python
states = list(abot.graph.get_state_history(thread))
# states[-1] 是最早的状态
to_replay = states[-1]  # 找到想回溯的状态
```

**直接从历史状态继续执行**：
```python
for event in abot.graph.stream(None, to_replay.config):
    print(event)
```

**从历史状态修改后分支执行**：
```python
# 修改历史状态中的工具参数
abot.graph.update_state(to_replay.config, {"messages": modified_messages})
# 从新的分支状态继续
for event in abot.graph.stream(None, branch_state.config):
    print(event)
```

**注入模拟工具结果**（跳过真实工具调用）：
```python
# 假装工具返回了 54°C
fake_tool_message = ToolMessage(
    tool_call_id=tool_call_id,
    name="tavily_search",
    content="54 degrees Celsius"
)
# 以 action 节点的身份注入，跳过真实工具调用
abot.graph.update_state(config, {"messages": [fake_tool_message]}, as_node="action")
```

---

**三种模式总结**

- **中断审批**：在关键节点暂停，由人类决定是否继续
- **状态修改**：纠正智能体的判断或工具参数
- **时间旅行**：回溯到历史状态，重新执行或从分支点探索不同路径

这些能力都依赖上一节介绍的持久化（Checkpointer）机制。

下一节将构建本课程的压轴项目——一个由多个 LLM 调用组成、状态更复杂的智能体。我们下节课见。