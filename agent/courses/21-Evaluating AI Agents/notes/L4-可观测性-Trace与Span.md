# L4：可观测性、Trace 与 Span

智能体能跑通只是开始。要做评估，先要能**看见**它每一步在做什么——这就是**可观测性（Observability）**要解决的问题。

## 什么是可观测性

可观测性是一个通用的软件工程概念：**对应用的每一层都有完整可见度**。落到 LLM 应用里，通常意味着追踪：

- Prompt 与响应
- Token 使用量
- LLM 调用前后发生的其他调用与逻辑

## Trace 与 Span

可观测性的基本积木：

- **Trace（轨迹）**：应用一次端到端的运行——从一个输入开始，到产出输出结束。一次 `run_agent` 调用就是一个 Trace。
- **Span（跨度）**：Trace 内部的一个具体步骤——一次 LLM 调用、一次工具调用、一段代码逻辑、一次数据库查询等。

> 一个 Trace 由多个 Span 构成，Span 之间通常呈**树状嵌套**——某个 Span 可以是另一个 Span 的子节点，整体形成层级。

在 Phoenix UI 中，颜色通常约定为：

- **橙色**：LLM Span
- **黄色**：Tool Span
- **蓝色**：Chain Span（普通逻辑步骤）
- 还有 Agent 类型作为最外层

## OpenTelemetry（OTEL）：行业标准

Trace 和 Span 的概念来自 **OpenTelemetry（OTEL）**——一个被广泛使用的应用可观测性标准，远远不只用于 LLM/AI。它定义了：

- 在应用中捕获 Trace/Span 的方式（这一过程称为**埋点 / Instrumentation**）
- **Collector** 与 **Processor**：接收并处理 Trace/Span 的组件
- 将数据投递到可视化与分析平台

## Arize Phoenix：本课程用的可观测平台

**Arize Phoenix** 在课程中担任两个角色：

1. 作为 OTEL Collector，接收你应用发来的 Trace/Span
2. 提供一个 UI，让你可视化 Trace，并在其上跑评估

## 埋点（Instrumentation）：自动 vs 手动

**埋点**是指在代码中**标记**哪些函数或代码块要被记录为 Span，以及在 Span 上附加哪些属性。

- **手动埋点**：用 `with` 语句创建 Span，或用装饰器（Decorator）包裹方法
- **自动埋点（Auto-Instrumentation）**：Phoenix 等工具针对热门库（**OpenAI、LlamaIndex、LangChain** 等）提供开箱即用的自动埋点，省去大量样板代码

> 在 Arize 的 OpenInference 库里，`OpenAIInstrumentor` 就是一个针对 OpenAI SDK 的自动埋点器。

## 可观测性为什么重要

1. **简化调试**——开发期看可视化 Trace 比翻日志和 print 容易得多
2. **生产监控的数据底座**——所有请求、所有输入都被记录，构成持续运行的明细数据库
3. **驱动评估（Evals）**——后续课程会从 Phoenix 导出 Span，在大规模数据上跑评估
4. **驯服 LLM 的不确定性**——LLM 本质上不可预测，唯一可控的办法就是**先看清楚、再评估、再改进**

下一课进入 Notebook 实战：把这些埋点技巧应用到你已经构建的智能体上，并启动你的第一个 Phoenix 实例收集 Trace。
