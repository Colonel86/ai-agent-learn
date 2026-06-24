# 结语

恭喜你完成了《事件驱动的智能文档工作流（Event-Driven Agentic Document Workflows）》课程。

回顾这一路：

- 你理解了 **RAG、Agent、Workflow** 三个概念，以及它们如何拼出 **ADW**；
- 你掌握了 LlamaIndex 的 **Workflow** 抽象——`@step`、`StartEvent` / `StopEvent`、自定义 `Event`、`Context`、`send_event` / `collect_events`、流式 `write_event_to_stream`；
- 你用 **LlamaParse + VectorStoreIndex + 查询引擎** 把简历变成 Agent 可查询的知识库；
- 你用**扇出 / 扇入**模式为表单中每个字段并发生成问题，并聚合答案；
- 你用 **`InputRequiredEvent` / `HumanResponseEvent`** 把人放进了回路，让 Agent 接受自然语言反馈再迭代；
- 你用 **Whisper + Gradio** 给 Agent 加了"耳朵"，体验了多模态人机协作。

现在，你已经具备了设计**事件驱动智能文档工作流**的能力：能让一个 Agent 自动填写文档，又能根据人类反馈持续改进，输出更准确的结果。

期待看到你用这些工具搭出自己的 Agent 应用。
