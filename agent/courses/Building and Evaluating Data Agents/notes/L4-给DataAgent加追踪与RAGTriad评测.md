# L4 · 给 Data Agent 加追踪与 RAG Triad 评测（OpenTelemetry + TruLens）

> 课程：Building and Evaluating Data Agents（DeepLearning.AI × Snowflake）
> 本课任务：给前三课搭好的多 agent data agent **接上 tracing**，再用 **RAG Triad** 三指标（context relevance / groundedness / answer relevance）判断它有没有真正完成用户目标——并在 dashboard 里把失败模式一眼看穿。

## 0. 从"能跑"到"可评"：本课在全课里的位置

前三课把 data agent 从零搭到能干活：

| 课 | 交付物 |
|---|---|
| L1 | 定义 data agent：LLM 驱动、连数据源、理解自然语言/代码、做 query 分解 + 检索 + 分析 + 可视化，最后给洞察；并引出"何时可信"这条主线 |
| L2 | 用 **LangGraph** 把 data agent 实现成**分层多 agent workflow**：planner 拆 subgoal → executor 逐步执行 → 子 agent（web researcher / chart generator / chart summarizer / synthesizer） |
| L3 | 加 **cortex researcher** 子 agent，接 Snowflake 的结构化 + 非结构化企业数据（Cortex Analyst 做 text-to-SQL、Cortex Search 查会议纪要） |

L3 结尾 agent 已经"功能齐全"，但没人知道它答得**准不准、有没有瞎编、检索到的东西相不相关**。L4 就补这一环：**先能观测（trace），再能评判（eval）**。开场一句话点题——"agent 已就绪，我们来追踪它达成目标的每一步，评估它是否准确回应了 query"。

## 1. RAG Triad：为什么检索式评测能套到 data agent 上

RAG Triad 本是给 RAG 系统设计的，但 data agent 的内核同样是**检索/研究 + 合成**，所以三指标可以直接迁移。三条边分别卡住 data agent 的三个环节：

```
                用户 query
                    │
        ┌───────────▼────────────┐
        │   ① Context Relevance   │  检索到的 context 与子问题相关吗？
        │   （评每个 research 步） │
        └───────────┬────────────┘
                    ▼  retrieved context
        ┌────────────────────────┐
        │   ② Groundedness        │  合成的回答被 context 支撑吗？（防幻觉）
        └───────────┬────────────┘
                    ▼  final answer
        ┌────────────────────────┐
        │   ③ Answer Relevance    │  最终回答切题吗？（对齐原始 query）
        └────────────────────────┘
```

| 指标 | 两个输入 | 判什么 | 在架构里的锚点 |
|---|---|---|---|
| **Context Relevance** | 子 agent 的 sub-query + 该步 retrieved context | 每个 research 步检索得准不准 | cortex/web researcher 的检索输出 |
| **Groundedness** | retrieved context（全部）+ final answer | 回答是否**全部有据**、没编造 | synthesis 步 |
| **Answer Relevance** | 原始 user query + final answer | 端到端是否切题 | 进 agent 的 query vs 交回用户的答复 |

Context Relevance 会对每个 researcher **单独算再取平均**（aggregate mean），因为一次任务可能有多个检索步。

> **架构师视角**：RAG Triad 的三个指标恰好把"检索质量"和"生成质量"**解耦**了。answer relevance 高但 groundedness 低 = 答得漂亮但在编（危险）；groundedness 高但 context relevance 低 = 老实复述了错的检索材料（要修检索）。单看一个"最终对不对"永远分不清病根在检索还是在生成——这就是为什么 data agent 的评测不能只有一个总分。

## 2. Trace：评测数据从哪来

要算这三个指标，得先从 **trace** 里捞出每一步的 query 和 retrieved context。trace 记录 agent 为达成目标走过的每一步。

- 本课 tracing 建在 **OpenTelemetry** 上：语言无关的分布式追踪系统，把 agent 的每一步捕获成 **span**（一个工作单元）。
- span 类型包括 planning / routing / **retrieval** / tool use / generation。
- **重点盯 retrieval 类型的 span**——context relevance 和 groundedness 要的关键数据都在里面。

启用 tracing 只需一个环境变量：

```python
os.environ["TRULENS_OTEL_TRACING"] = "1"   # 打开 TruLens 的 OTel 追踪
```

## 3. 定义三个 feedback function（LLM-as-judge）

三指标都用 **LLM-as-judge**，评判模型是 **GPT-4o**，经由 TruLens 的 OpenAI provider 调用。核心两个类：

- `Feedback`：把一个评判函数（如 `groundedness_measure_with_cot_reasons`）包成 evaluator；
- `Selector`：从 trace 里**精准挑出**某类 span 的某个属性（如 retrieval span 的 retrieved context / query text）喂给评判函数。

```python
from trulens.providers.openai import OpenAI
provider = OpenAI(model_engine="gpt-4o")           # 判官模型

# ① Groundedness：source=所有检索到的 context（RETRIEVAL span 的 RETRIEVED_CONTEXTS，收成 list）
#                  statement=on_output()=agent 最终答案
f_groundedness = (
    Feedback(provider.groundedness_measure_with_cot_reasons, name="Groundedness")
    .on({"source": Selector(
            span_type=SpanAttributes.SpanType.RETRIEVAL,
            span_attribute=SpanAttributes.RETRIEVAL.RETRIEVED_CONTEXTS,
            collect_list=True)})
    .on_output()
)

# ② Answer Relevance：on_input()=用户 query，on_output()=最终答案（最简单，不用 Selector）
f_answer_relevance = (
    Feedback(provider.relevance_with_cot_reasons, name="Answer Relevance")
    .on_input().on_output()
)

# ③ Context Relevance：question=子 agent 的 QUERY_TEXT，context=每个 chunk（collect_list=False 逐块评）
f_context_relevance = (
    Feedback(provider.context_relevance_with_cot_reasons, name="Context Relevance")
    .on({"question": Selector(span_type=RETRIEVAL, span_attribute=QUERY_TEXT)})
    .on({"context":  Selector(span_type=RETRIEVAL, span_attribute=RETRIEVED_CONTEXTS,
                              collect_list=False)})
    .aggregate(np.mean)                            # 多个 research 步取平均
)
```

三个函数都用 `..._with_cot_reasons` 变体：judge 不仅给 **0~1 分数**，还给 **chain-of-thought 解释**——这在 dashboard 里就是"为什么扣分"的可读依据。

> **对比 5-observability-eval.md 的三支柱**：我的观测选型里把可观测性拆成 traces / metrics / evals。本课是这套抽象的一次干净落地——**OTel span = trace 支柱**（原始步骤），**RAG Triad = eval 支柱**（质量判定），**leaderboard 聚合 = metrics 支柱**（版本级趋势）。关键工程点：eval 不是旁路脚本，而是**从同一份 trace 派生**（Selector 挑 span），所以每个分数都能下钻回具体那一步。

## 4. 埋点：让 trace 里"看得见"检索步

TruLens 的 `TruGraph` 会**自动**追踪整张 LangGraph（每个 node 的输入输出、node 名、规划→执行→工具调用全链路）。但自动追踪只知道"有个 node 跑了"，不知道"这是个 retrieval 步、它的 query 是啥、检索回了啥"。所以要**手动加自定义 instrumentation**——用 `@instrument` 装饰器给 research node 打标签、抽字段：

```python
from trulens.core.otel.instrument import instrument

@instrument(
    span_type=SpanAttributes.SpanType.RETRIEVAL,   # ① 标注：这步是 retrieval
    attributes=lambda ret, exception, *args, **kwargs: {
        # ② query text ← 函数第一个入参 state 里的 agent_query
        SpanAttributes.RETRIEVAL.QUERY_TEXT: args[0].get("agent_query"),
        # ③ retrieved context ← 函数返回值里最后一条 message 的 content
        SpanAttributes.RETRIEVAL.RETRIEVED_CONTEXTS: [ret.update["messages"][-1].content],
    },
)
def cortex_agents_research_node(state: State) -> Command[Literal["executor"]]:
    query = state.get("agent_query", state.get("user_query", ""))
    agent_response = cortex_agent.invoke({"messages": query})
    new_message = HumanMessage(content=agent_response['messages'][-1].content,
                               name="cortex_researcher")
    return Command(update={"messages": [new_message]}, goto="executor")
```

- `ret` = 函数返回值，`args` = 入参（`args[0]` 就是 `state`）；
- **web research node 完全同款处理**：同样标 `RETRIEVAL`、同样抽 `QUERY_TEXT` + `RETRIEVED_CONTEXTS`。

没有这层手动加工，"哪步是检索""进来的 query""出去的 context"会**埋在复杂数据结构深处**，评测无从下手。这就是自动 tracing 之外，data agent 特有的"检索埋点"价值。

## 5. 落库、注册、跑

```python
# ① 建 TruSession，用 SQLite 存 trace + eval（都是 OTel 事件）
connector = DefaultDBConnector(database_url="sqlite:///default.sqlite")
session = TruSession(connector=connector)
session.reset_database()                    # 清掉上轮旧数据

# ② 重建图（节点不变，但 research node 换成带 instrumentation 的版本）
graph = workflow.compile()

# ③ 用 TruGraph 注册 agent：绑定版本号 + 要跑的评测
tru_recorder = TruGraph(
    graph,
    app_name="Sales Data Agent",
    app_version="L4: Base",                 # 版本号→后面对比不同迭代的关键
    feedbacks=[f_answer_relevance, f_context_relevance, f_groundedness],
)
```

`app_name` + `app_version` 是**版本追踪的钩子**——改一版 agent 换个 version 号，dashboard 就能横向比性能。随后用 `with tru_recorder as recording:` 包住 `graph.invoke(state)`，连发三条 query，每步都被录进库：

1. "top 3 client deals + 画图"（简单，主要走 text-to-SQL）；
2. "找 pending deals + 研究监管变化 + 用会议纪要给新价值主张"（复杂，多 researcher）；
3. "最大 client deal + 会议纪要重点话题 + 找相关新闻"。

## 6. Dashboard：把失败模式看穿

```python
from trulens.dashboard import run_dashboard
_ = run_dashboard(port=8001)                # 打开后点第二个链接（DeepLearning 环境）
```

**Leaderboard**（按 app_version 聚合）第一眼：base 版 **answer relevance 低、groundedness 低**。勾选版本 → Examine Records 逐条下钻，三条 query 各暴露一种典型失败：

| Query | 现象 | 指标读数 | 判官解释（病根） |
|---|---|---|---|
| Q1 top3+图 | 出了图但**没有文字总结** | Answer Relevance = 0 | chart summarizer 没给文字答复→回答完全不切题；context relevance 也低（research 没返回答题所需材料） |
| Q2 pending deals | 答得相关但**不落地** | Answer Relevance 高 / **Groundedness 低** | 很多论断不是 context 支撑的，是 LLM **自己推断**的；根因是部分检索到的 context 本就不相关 |
| Q3 largest deal | 拿不到最大 deal 信息 | — | **访问 Snowflake 出错**，数据没取到 |

在 record 里还能展开 **trace 树**看 agent 实际走的路径：planner → executor → cortex research → **replan** → 第二次 web research → 第二次 cortex search → synthesizer；点任意 node 可看它的输入输出。**评分 + trace 联动**，才能定位"到底哪步、为什么错"。

> **对比课程 21 Evaluating AI Agents（Arize/Phoenix 路线）**：那门课也是 OTel span + LLM judge 的组合，但停在 RAG/答案质量层。本课的独特处在于：① 判官同时输出 CoT 解释，dashboard 里可读可下钻；② 评测**直接绑在 LangGraph 节点上**（TruGraph 自动 + @instrument 手动），不是离线批处理；③ 用 `app_version` 把评测做成**可回归对比的产品指标**。这正是 `06-full-link-trace-and-observability` 面试包要的"trace→eval→版本回归"闭环。

## 本课总结

| 要点 | 一句话 |
|---|---|
| RAG Triad | data agent = 检索+合成，故 context relevance / groundedness / answer relevance 三指标可直接套用 |
| 指标解耦 | 三指标把"检索质量"与"生成质量"分开，能区分"检索错"还是"生成编" |
| Trace = 评测数据源 | OTel span（尤其 retrieval 类型）承载 query 与 retrieved context |
| 埋点 | `@instrument` 手动标 span 类型 + 抽 QUERY_TEXT/RETRIEVED_CONTEXTS，否则数据埋太深 |
| 版本化评测 | TruSession 落 SQLite、TruGraph 按 app_version 注册，dashboard 下钻定位失败模式 |

> **记忆点（引出 L5）**：RAG Triad 回答的是"**目标完成得对不对**"（goal completion），但它看不见 agent 内部**计划得好不好、执行有没有照计划走、走得冤不冤枉**。L5 引入 **GPA（Goal-Plan-Act alignment）** 四把新尺子——plan quality / plan adherence / execution efficiency / logical consistency——从"答案对错"深入到"过程健康度"。

## 与我的资产映射

- 观测·eval 层选型：`agent/skills/agent-selection/5-observability-eval.md`（traces/metrics/evals 三支柱 → 本课是 OTel+TruLens 的完整落地样例；RAG Triad 作为 data/RAG-agent 的默认评测集）
- 设计模式：`agent/skills/agent-selection/11-design-patterns.md`（LLM-as-judge + CoT reasons 作为可解释评测模式）
- 面试包：`06-full-link-trace-and-observability`（span→eval→版本回归闭环）、`09-eval-driven-development`（RAG Triad 作 goal-completion 评测集）
- 对比锚点：课程 21 Evaluating AI Agents（Phoenix/Arize 的 OTel+judge 路线）
- [[project_selection_matrix]]
</content>
