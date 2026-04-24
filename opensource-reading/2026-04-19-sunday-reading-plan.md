# 开源项目阅读日 · 2026-04-19（周日）

> **当前阶段**：Phase 1 · 基石构建（第 3 周末）
> **学习上下文**：Prompt Engineering 课程已完成 ep01-ep09；Building Systems 课程进行至 ep06
> **时长建议**：2 小时，单一项目深度阅读 > 多项目泛读

---

## 今日首选：OpenAI Python SDK（openai-python）

**仓库**：https://github.com/openai/openai-python

### 为什么是它

你目前正在密集使用 Chat Completions API、Structured Output、Function Calling 这些接口。先读官方 SDK 的源码，能把"API 使用者"升级成"API 设计理解者"。这是 Phase 2 进入 LangChain/LangGraph 之前最划算的一步——因为几乎所有 Agent 框架底层都在包装它。

### 推荐阅读顺序（约 1.5 小时）

第一轮：骨架理解（30 分钟）
- `src/openai/_client.py` — 同步/异步客户端的双实现，看 `OpenAI` 和 `AsyncOpenAI` 如何共享配置
- `src/openai/_base_client.py` — 所有 HTTP 请求的中枢，重点看 `_request`、`_retry_request`、`_process_response` 三个方法
- `src/openai/_exceptions.py` — 异常分层（APIError → APIConnectionError / APIStatusError → RateLimitError 等）

第二轮：核心资源（40 分钟）
- `src/openai/resources/chat/completions/completions.py` — Chat Completions 的请求构造与流式处理
- `src/openai/lib/streaming/chat/_completions.py` — `stream()` 辅助函数，看它如何封装 SSE 解析并暴露事件式接口
- `src/openai/lib/_parsing/_completions.py` — Structured Output 背后的 Pydantic schema 转换逻辑

第三轮：设计模式提炼（20 分钟）
- `src/openai/_utils/` — 看他们如何实现 `required_args`、`deepcopy_minimal`、`maybe_transform` 这些通用工具
- `src/openai/pagination.py` — `SyncCursorPage` / `AsyncCursorPage` 的分页抽象

### 重点关注的设计决策

- **同步/异步镜像**：`_client.py` 中两套客户端共用一套资源定义，通过 `_base_client.py` 的泛型模板把 transport 抽离出来。这是 Python SDK 处理 sync/async 双支持的标准解法
- **`NOT_GIVEN` 哨兵值**：为什么不用 `None`？因为 `None` 对某些 API 字段本身是有语义的（例如"清空"）。思考你以后写 SDK / 包装器时怎么区分"没传"和"传了 null"
- **Pydantic + TypedDict 双轨**：响应体用 Pydantic model（运行时校验 + IDE 补全），请求参数用 `TypedDict`（零开销、纯类型提示）
- **流式解析的事件化包装**：裸 SSE 难用，`stream()` 把它转成 `ChatCompletionStreamEvent`，把"字节流"抽象成"语义事件"
- **重试策略**：看 `_retry_request` 如何处理 `Retry-After` header、指数退避、以及哪些错误会重试、哪些不会

---

## 备选项目（进度超前或已看完可切换）

### 备选 A：Anthropic Python SDK（对比阅读）

**仓库**：https://github.com/anthropics/anthropic-sdk-python

**阅读方式**：和 openai-python 并排看 `_base_client.py`、`resources/messages.py`、流式接口。Anthropic 的 tool use 设计和 OpenAI 的 function calling 在 SDK 层的差异很能启发你思考"协议设计"。

### 备选 B：Pydantic v2 AI 相关模块

**仓库**：https://github.com/pydantic/pydantic

**重点**：`pydantic/main.py` 的 `BaseModel.model_json_schema()` —— OpenAI 的 Structured Output 背后依赖它。理解 Pydantic 如何把 Python 类型转成 JSON Schema，你就明白 LangChain 里 `with_structured_output()` 是怎么变魔术的。

### 备选 C：LangChain `langchain-core`（Phase 2 预热）

**仓库**：https://github.com/langchain-ai/langchain（子目录 `libs/core/langchain_core/`）

**今日仅建议 30 分钟快速浏览**，作为 Phase 2 的前瞻：
- `langchain_core/runnables/base.py` — 核心抽象 `Runnable`，LCEL 的根基
- `langchain_core/messages/` — 消息类型分层（HumanMessage / AIMessage / ToolMessage）

不建议今天深入，因为没铺垫上下文会很吃力。Phase 2 第 5 周正式读。

---

## 阅读方法（建议）

1. **Top-down 而非 line-by-line**：先用 `tree -L 3` 看目录结构，再读 `__init__.py` 了解公开 API，最后沿公开 API 往下挖
2. **带问题读**：开始前写下 3 个你想搞懂的问题，例如"流式输出在哪里解析？"、"重试如何配置？"。读完回来回答
3. **画图**：对 `_base_client.py` 这种中枢类，花 10 分钟画一张请求生命周期流程图（客户端 → 构造请求 → 发送 → 重试 → 解析 → 返回）
4. **复现一个小实验**：看完后写 20 行代码，用标准 `httpx` 复刻一个最小版本的 `_retry_request`。能写出来才算真懂

---

## 今日笔记模板

建议在 `/Users/ming/Documents/ai-agent-learn/opensource-reading/` 下新建笔记文件 `2026-04-19-openai-python-sdk.md`，结构如下：

```
# openai-python 源码阅读笔记

## 项目定位
（30 字内总结这个项目解决什么问题）

## 关键抽象
- Client / Resource / Model 三层是怎么分的？
- sync 和 async 怎么共享代码？

## 三个最优雅的设计
1. ...
2. ...
3. ...

## 一个我没看懂的地方
（写下来，下周问 Claude 或查文档）

## 可以借鉴到我项目里的
- 项目 1（多模型问答 CLI）：...
- 项目 2（Prompt 模板管理）：...

## 我的小实验
（链接到自己写的最小复刻代码）
```

---

## 本周回顾 Tips

周日除了读源码，也建议花 20 分钟：
- 回顾本周 `courses/building-systems/notes/` 里新增的 ep02-ep06 笔记
- 检查 `courses/prompt-engineering/code/` 下的练习代码，能否跑通
- 在 `AI-Agent-学习追踪表.xlsx` 里把本周进度标记为已完成

下周（第 4 周）是 Phase 1 最后一周，建议预留时间启动**项目 1：多模型智能问答 CLI**，把今天读源码学到的"sync/async 双客户端"、"流式事件"这些模式用上。
