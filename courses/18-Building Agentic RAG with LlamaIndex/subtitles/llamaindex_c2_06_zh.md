# 课程总结

恭喜完成《用 LlamaIndex 构建智能体式 RAG》（Building Agentic RAG with LlamaIndex）课程。

## 你学到了什么

沿着一条循序渐进的能力链，我们一起把 RAG 推到了"智能体"层级：

- **路由智能体（Router Agent）**：让 LLM 在多个查询引擎之间做选择。
- **工具调用（Tool Calling）**：让 LLM 不只选工具，还能为工具推断参数（包括元数据过滤器）。
- **智能体推理循环（Agent Reasoning Loop）**：在单文档之上做**多步推理**，维护对话记忆，并提供高层 / 低层两套接口用于调试和人工引导。
- **多文档智能体（Multi-Document Agent）**：利用 `ObjectIndex` 与 `tool_retriever` 在数十乃至上百个工具中做"工具级 RAG"，构建一个可扩展的研究助手。

## 下一步

如果你希望走得更远，可以考虑：

- **构建自定义智能体**：把 LlamaIndex 的 worker / runner 抽象拆开来，按业务定制每一步的行为。
- **把你的实现以社区模板（community template）形式贡献回来**，让更多人受益。
- **接入更高级的文档解析服务**：例如 LlamaParse 这类专门处理复杂 PDF、表格、图表的工具，能显著提升上游数据质量。

讲师 Jerry Liu 留下的话：

> "期待看到你们用 Agentic RAG 构建出的种种成果。"

去构建吧。
