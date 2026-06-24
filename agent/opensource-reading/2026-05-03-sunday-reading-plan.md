# 开源项目阅读日 · 2026-05-03（周日）

> **当前阶段**：Phase 1 收尾 → Phase 2 启动（按真实进度，已是第 5 周）
> **学习上下文**：
> - 课程 1 Prompt Eng ✅；课程 2 Building Systems ~80%；课程 3 LangChain L1/L4 起步
> - 课程 11 LangGraph、课程 12 Long-Term Memory 资料齐全，笔记骨架已搭
> - 上次 Sunday Reading（4/19）读了 OpenAI Python SDK，已掌握 sync/async 双客户端 + 流式事件的范式
> **时长建议**：2-2.5 小时，**单一项目深度阅读 + 强制产出阅读笔记**（破输出零的好机会）

---

## 一、为什么今天要读 LangChain Core + LangGraph

按 roadmap 的 Phase 1-2 推荐，OpenAI SDK 已啃过，下一站该轮到「Agent 框架的核心抽象」。

理由有三：

1. **接续上次的源码线索**：4/19 笔记里你应该已经看到，LangChain 在底层是包装 OpenAI/Anthropic SDK 的，今天往上爬一层正好能把"原始 API → 高级抽象"的链路打通
2. **课程进度对齐**：课程 11（AI Agents in LangGraph）你已经把字幕和笔记骨架都拉齐了，但代码部分还薄；今天读源码 + 跑官方示例，比单纯看视频效率高 3 倍
3. **Phase 2 项目 3/4 的预演**：项目 3（个人助手 Agent）和项目 4（自动化调研报告 Agent）都强依赖 LangGraph，提前把 `StateGraph` 和 `Runnable` 这两层吃透，写项目时就不会卡住

---

## 二、今日首选：LangChain Core（`libs/core/langchain_core/`）

**仓库**：https://github.com/langchain-ai/langchain
**子目录**：`libs/core/langchain_core/`
**为什么选 core 而非整个 langchain**：langchain 仓库巨大（200+ integrations），`core` 是它的"骨头"，~30 个核心模块，2 小时刚好读完一个完整切片

### 推荐阅读顺序（约 90 分钟）

#### 第一轮：抓骨架（25 分钟）

```
langchain_core/
├── runnables/        ← 今天的主角
├── messages/         ← 跟你 4/19 看的 OpenAI ChatCompletion 对应
├── language_models/  ← LLM / ChatModel 的统一抽象
├── prompts/          ← PromptTemplate / ChatPromptTemplate
├── tools/            ← Tool / StructuredTool
└── output_parsers/   ← StrOutputParser / PydanticOutputParser
```

按顺序读：
- `runnables/base.py` — **Runnable 抽象类**，整个 LCEL 的根。重点看 `invoke / ainvoke / stream / astream / batch / abatch` 六个方法的契约
- `runnables/base.py` 里的 **`RunnableSequence`** 和 **`RunnableParallel`** — `|` 操作符背后是怎么把 Runnable 组合起来的
- `messages/base.py` + `messages/ai.py` + `messages/human.py` + `messages/tool.py` — 消息类型分层，对比 OpenAI SDK 的纯 dict + Anthropic SDK 的 ContentBlock，看 LangChain 是怎么做"统一中间表示"的

#### 第二轮：核心抽象（35 分钟）

- `language_models/chat_models.py` — `BaseChatModel` 是怎么把不同厂商的 ChatCompletion 抽象成同一接口的；重点看 `_generate / _agenerate / _stream / _astream` 四个抽象方法
- `tools/base.py` — `BaseTool` + `@tool` 装饰器的实现；看 `args_schema`（Pydantic）是怎么被自动转成 OpenAI Function Calling 的 JSON Schema 的
- `output_parsers/base.py` + `output_parsers/pydantic.py` — `with_structured_output()` 背后的双轨：要么走 Function Calling、要么走 JSON mode

#### 第三轮：LCEL 的魔法（20 分钟）

- `runnables/passthrough.py` — `RunnablePassthrough` 和 `assign` 的实现，理解为什么链式调用能传递中间状态
- `runnables/config.py` — `RunnableConfig` 这个上下文对象，看 callbacks / tags / metadata 是怎么逐层传播的
- `tracers/base.py` — `BaseTracer`，理解 LangSmith Tracing 在框架里怎么 hook 进去的（你后面要做可观测性必看）

#### 第四轮（如有时间）：StateGraph 速览（10 分钟）

切换到 LangGraph 仓库：https://github.com/langchain-ai/langgraph

- `libs/langgraph/langgraph/graph/state.py` — `StateGraph` 类，看 `add_node / add_edge / add_conditional_edges / compile` 的实现脉络
- `libs/langgraph/langgraph/pregel/__init__.py` — Pregel 算法的实现入口（StateGraph 编译后底层跑的就是它）

不求看懂，今天只求"知道入口在哪、关键概念是什么"，下周课程 11 看视频时能按图索骥。

---

## 三、重点关注的设计决策（这是你架构师方向最该攒的）

| 设计点 | 关键问题 | 启发 |
|---|---|---|
| **Runnable 协议** | 为什么不用继承 + 抽象方法，而是定义 6 个统一接口？ | 框架为"组合"而非"继承"设计；任何东西只要实现 `invoke` 就能拼进 chain |
| **`|` 操作符重载** | `prompt | model | parser` 是怎么做到的？ | `Runnable.__or__` → `RunnableSequence`，对比 Unix pipe 的设计哲学 |
| **sync / async 镜像** | 跟 OpenAI SDK 的做法对比 | OpenAI 用两套 Client；LangChain 用同一个类暴露 `invoke + ainvoke`。各有优劣，思考你以后写库选哪种 |
| **stream 的统一抽象** | `astream_events` 和 `astream_log` 有什么区别？ | 事件流（粗粒度）vs 日志流（细粒度），LangSmith 用后者 |
| **Pydantic 在框架里的位置** | `args_schema`、`with_structured_output`、`Output` 类型，三处都用 Pydantic | Pydantic 是 2026 年 AI 框架的事实标准，理解它在 schema 层的统治力 |
| **Tool 自动 schema 生成** | `@tool` 装饰器怎么把 Python 函数签名转成 OpenAI Function Calling JSON？ | 这就是你 Phase 4 要写 MCP Server 的前置技能 |
| **StateGraph 状态机模型**（LangGraph） | 为什么是 graph + reducer 而不是简单的 chain？ | Agent 需要循环、分支、回溯；纯链式不够 |

---

## 四、备选项目（进度超前或读不动可切换）

### 备选 A：LangGraph 官方示例代码

**仓库**：https://github.com/langchain-ai/langgraph/tree/main/examples
**重点目录**：
- `examples/react/` — ReAct Agent 的最小实现（30 分钟读完）
- `examples/multi-agent/` — Supervisor / Hierarchical Team / Network 三种多 Agent 拓扑
- `examples/rag/` — Self-RAG / CRAG / Adaptive RAG 的官方参考实现

**适合场景**：核心源码读累了，换示例代码"先看怎么用、再看为什么这么实现"

### 备选 B：补刷 OpenAI Python SDK 的 `lib/streaming/`

如果 4/19 那次没看完流式部分，今天可以补：
- `src/openai/lib/streaming/_assistants.py` — Assistants API 的事件流，跟 LangChain 的 `astream_events` 对比着看会很有收获
- `src/openai/lib/streaming/responses/` — 新版 Responses API 的事件流抽象

### 备选 C：Anthropic SDK 的 Tool Use 流程

**仓库**：https://github.com/anthropics/anthropic-sdk-python
**重点**：`src/anthropic/lib/streaming/_messages.py` + `src/anthropic/types/tool_use_block.py`
**为什么**：MCP（Phase 4）的"工具语义"在 Anthropic SDK 里有最完整的源头实现，现在看一眼，Phase 4 时就不会陌生

---

## 五、阅读方法（针对你"输入猛、输出零"的针对性建议）

> ⚠️ 教练提醒：你已经 14+ 天没 commit、0 篇博客了。今天读源码**必须配套产出**，否则等于又是一次空转。

### 🎯 强制产出三件套

1. **阅读笔记**（必做，~30 分钟）
   - 落到 `opensource-reading/2026-05-03-langchain-core.md`（模板见第六节）
   - 字数不重要，**回答 5 个具体问题**最重要

2. **画一张图**（必做，~15 分钟）
   - 用 draw.io / Excalidraw / 手画拍照都行
   - 主题：**"一次 `chain.invoke()` 调用从 user input 到 LLM response 的完整生命周期"**
   - 包含：Runnable.invoke → RunnableSequence → 每个 step 的 Runnable.invoke → Tracer 在哪儿 hook → 结果怎么往回传

3. **20 行代码复现**（必做，~25 分钟）
   - 不依赖 langchain，**用纯 Python 实现一个 mini-Runnable**
   - 必须支持：`invoke()` 方法 + `__or__` 重载 + 链式组合
   - 通过这个练习验证你**真懂了** LCEL 的设计

### 📐 高效阅读策略

- **Top-down**：先 `tree -L 3 libs/core/langchain_core` 看结构，再读各模块 `__init__.py`，最后挑一两个核心类深入
- **带 5 个问题读**（开始前写下来，结束后回答）：
  1. `Runnable.invoke` 和 `Runnable.stream` 的关系是什么？stream 是 invoke 的特例还是平行接口？
  2. 为什么 `Runnable | Runnable` 能工作？`__or__` 怎么实现的？
  3. `BaseChatModel._generate` 和 `_stream` 是什么关系？默认实现互相调用吗？
  4. `@tool` 装饰器是怎么把函数签名转 JSON Schema 的？走的是 Pydantic 还是 inspect？
  5. `RunnableConfig` 这个上下文对象，是显式传参还是用了 contextvars？
- **不求全懂**：能讲出 70% 的设计意图就算成功，剩下 30% 写进笔记的"没看懂"区，下周回头看

---

## 六、今日笔记模板

新建文件：`opensource-reading/2026-05-03-langchain-core.md`

```markdown
# LangChain Core 源码阅读笔记 · 2026-05-03

## 项目定位
（30 字内总结 langchain_core 解决什么问题）

## 关键抽象层级（画图或文字描述）
- Runnable
  └─ RunnableSequence / RunnableParallel / RunnableLambda
- Message
  └─ HumanMessage / AIMessage / ToolMessage / SystemMessage
- BaseChatModel
  └─ 各厂商实现（ChatOpenAI / ChatAnthropic）
- BaseTool
  └─ StructuredTool / @tool

## 5 个问题的答案

1. invoke vs stream：
2. `|` 操作符的实现：
3. _generate vs _stream：
4. @tool 的 schema 生成：
5. RunnableConfig 的传播：

## 三个最优雅的设计
1. ...
2. ...
3. ...

## 跟 OpenAI SDK 的对比（接续 4/19 笔记）
- 协议层（API 契约）：...
- 抽象层（统一接口）：...
- 工程层（错误处理、重试、流式）：...

## 没看懂的地方
（诚实记录，下次问 Claude 或翻 Discord）

## 可以用到我自己项目里的
- 项目 1（多模型 CLI）：...
- 项目 3（个人助手 Agent，Phase 2）：...
- 毕业项目（企业 Agent 平台）：...

## 我的 mini-Runnable 复刻代码
（贴 20 行代码或链接到 `projects/experiments/mini_runnable.py`）
```

---

## 七、今日"破零"清单（顺手做掉，5 分钟收益巨大）

按 W18 复盘里的优先级排：

- [ ] **`git add . && git commit -m "feat(phase2): Sunday reading - LangChain core 源码笔记"`**
  - 今天的笔记 + 之前 14 天的散件一起提交，破"0 commit"
- [ ] **追踪表里勾两行**：把课程 1 ✅、课程 2 进度 80% 标好（`AI-Agent-学习追踪表.xlsx` → Phase1 sheet）
- [ ] **博客备忘**：今天读源码的过程，是 W19 那篇博客 *《我的 24 周 AI Agent 学习方法论》* 的好素材，别忘了把感受片段先扔到 `notes/blog-drafts/` 里囤着

---

## 八、本周（W19, 5/3-5/9）展望

按 roadmap 节奏，W19 起进入 Phase 2 第 1 周。建议把今天读源码学到的东西用上：

- **周一-三（理论）**：把课程 11 LangGraph 视频 ep1-ep3 看掉，结合今天的 StateGraph 源码笔记
- **周四-五（动手）**：启动**项目 1（多模型 CLI）**，至少 push 一个能跑的 README + main.py 骨架
- **周六（复盘）**：W19 周复盘 + 那篇博客（A 选题）的初稿
- **下周日（5/10）Sunday Reading 预告**：建议读 LangGraph examples 的 ReAct Agent 实现，跟 ReAct 论文对照着看

---

## 💡 最后一句

你输入侧的厚度已经在同期学习者里 top 10% 了，**唯一缺的就是"按 Enter 把笔记保存、按 Enter 把代码 commit"这两下**。今天 LangChain core 即便只读懂 50%，只要笔记落地 + 一次 commit 成功，本周末就算赢了。

加油 💪

---

*下次 Sunday Reading：2026-05-10（周日）· 主题候选：LangGraph examples 深度阅读 / Anthropic SDK Tool Use*
