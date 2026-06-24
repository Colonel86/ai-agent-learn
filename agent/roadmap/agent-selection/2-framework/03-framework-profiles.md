# 03 · 框架画像:逐个深挖

> 目的:决策树/评分卡指向某个候选后,来这里看它的**甜区、反模式、隐藏成本、成熟度**。
> 结论分级:✅ 稳定经验 / ⚠️ 当下快照(易变) / ❓ 待验证。
> **最后核对:2026-06**(Agent 框架迭代快,超过 6 个月请复核版本与 API)。
> 课程回溯:括号内是本仓库对应学习笔记。

---

## 画像速览表

| 框架/SDK | 一句话定位 | 心智模型 | 甜区 | 别用它来 |
|---|---|---|---|---|
| 裸 SDK(Anthropic/OpenAI) | 最大控制的底座 | 你自己写循环 | 简单工具调用、结构化输出、强控制 | 复杂多 agent 编排(轮子太多) |
| Pydantic AI | 类型优先的轻 agent | 函数+类型契约 | Python 结构化输出、轻量 agent | 重状态机/多 agent 协作 |
| LangChain | LLM 应用组件大全 | 链(Chain) | 快速拼装、组件最多 | 复杂有状态 agent(用 LangGraph) |
| LangGraph | 状态机式编排 | State+Nodes+Edges | 复杂流程、循环、HITL、可恢复 | "就要个 JSON"(杀鸡用牛刀) |
| LlamaIndex | 数据/RAG 框架 | 索引+查询引擎 | RAG、Agentic RAG、文档密集 | 纯多 agent 对话协作 |
| Haystack | 生产级管线编排 | Pipeline(DAG) | RAG-first、工程化部署 | 极简脚本(管线是负担) |
| crewAI | 多 agent 协作 | 角色+任务 | 角色分工清晰的协作 | 需精细状态控制 |
| Microsoft Agent Framework(MAF) | 微软官方多 agent(AutoGen+SK 合并,2026-04 GA) | 可对话 agent + 工作流 | 多 agent 协作新项目、原生 MCP/A2A | 简单单 agent(过重) |
| AutoGen / AG2 | 多 agent 对话(原版维护模式 / AG2 社区分叉) | 可对话 agent | PoC 式多 agent 验证 | 多 agent 生产新项目(改用 MAF/crewAI) |
| OpenAI Agents SDK | OpenAI 官方 agent 层 | Agent+Handoff+Tool | 全程 OpenAI、官方最短路 | 跨厂商可移植 |
| Google ADK | Google 官方 agent 层 | Agent+Tool | 全程 Gemini/Vertex | 跨厂商可移植 |
| Claude Agent SDK | Anthropic 官方 agent 层 | Agent 循环+工具+子 agent | 全程 Claude、官方最短路、原生 MCP | 跨厂商可移植 |
| MCP(协议,非框架) | 工具/上下文接入标准 | Client-Server | 把工具/数据标准化接入任意框架 | 当编排框架用(它不是) |

---

## 1. 裸 SDK(Anthropic SDK / OpenAI SDK) ✅

- **是什么**:直接调模型 API,自己写工具循环、消息管理、重试。
- **甜区**:工具少、流程简单;对 token/延迟/prompt 要极致控制;不想被框架黑盒挡住。
- **反模式**:多 agent、复杂状态、需要现成连接器时——你会把框架重新发明一遍。
- **隐藏成本**:状态/会话/可观测全靠自己搭;团队多人时缺统一抽象。
- **成熟度**:✅ 最高,API 最稳。
- **架构师笔记**:**起步默认从这里考虑**。很多"需要框架"的直觉,其实裸 SDK + 几十行就够。框架是当复杂度真的来了才引入的。
- 课程:`10-MCP`、各 `claude-api` 参考。

## 2. Pydantic AI ✅

- **是什么**:以 Pydantic 类型为契约的轻量 agent 框架(类型化工具 I/O、结构化输出、依赖注入)。
- **甜区**:Python 项目要"可靠结构化输出 + 少量工具 + 类型安全";想要比裸 SDK 多一点结构,又不想要 LangChain 的重量。
- **反模式**:重状态机、复杂多 agent 编排。
- **隐藏成本**:相对年轻,生态不如 LangChain 广。
- **成熟度**:⚠️ 上升期,社区活跃。
- **架构师笔记**:与 Instructor / OpenAI `responses.parse` / Anthropic tool_use 是同一战场——**"结构化输出"问题的首选层**。
- 课程:`07-Pydantic for LLM Workflows`;skill:`skills/pydantic-ai-agent`。

## 3. LangChain ✅⚠️

- **是什么**:最大的 LLM 应用组件库(模型/检索/记忆/工具/链)。
- **甜区**:快速拼装原型;需要某个现成集成时大概率它有。
- **反模式**:复杂有状态 agent——官方自己都推荐转 **LangGraph**;链抽象在复杂控制流下会变得难调试。
- **隐藏成本**:抽象层多、版本演进快、"魔法"多时调试成本高。
- **成熟度**:✅ 生态最大,但 API 历史包袱重。
- **架构师笔记**:把它当"**组件超市**"用(取 Retriever/Loader/Splitter 等),编排交给 LangGraph 或自己。
- 课程:`03-LangChain`、`04-Chat with Your Data`、`09-Functions Tools and Agents`。

## 4. LangGraph ✅

- **是什么**:基于状态图的 agent 编排(State + Nodes + Edges + Conditional Edges + Checkpointer)。
- **甜区**:复杂单/多 agent;**循环、反思、Human-in-the-Loop、持久化/可恢复、时间旅行**;要强可控性的严肃系统。
- **反模式**:简单任务(线性 RAG、单次结构化输出)——概念开销不划算。
- **隐藏成本**:学习曲线陡(State 合并语义、图思维);需要配套 LangSmith 才发挥可观测优势。
- **成熟度**:✅ 生产采用度高;有 LangGraph Platform 做部署。
- **架构师笔记**:**"可控性(controllability)"是它的核心卖点**。当你需要精确掌控"下一步走哪、状态怎么变、何时停"时,它最强。记忆/HITL/多会话靠 Checkpointer 解锁。
- 课程:`11-AI Agents in LangGraph`、`12-Long-Term Agentic Memory`。

## 5. LlamaIndex ✅

- **是什么**:数据框架,核心是把外部数据变成可检索可推理的索引;含 Agentic RAG 与事件驱动工作流。
- **甜区**:**RAG-first**;数据连接器(LlamaHub)最全;文档/知识库密集型;要让检索"自主化"(agent 决定查不查、查哪个)。
- **反模式**:纯多 agent 对话协作(不是它的重心)。
- **隐藏成本**:抽象多;深度定制检索流程时要懂它的内部分层。
- **成熟度**:✅ RAG 领域第一梯队。
- **架构师笔记**:**"数据/检索"维度它是默认强项**。事件驱动工作流(Workflows)让它也能表达较复杂的 agent 流程。
- 课程:`18-Agentic RAG with LlamaIndex`、`19-Event-Driven Agentic Document Workflows`。

## 6. Haystack ✅

- **是什么**:deepset 出品的可组合管线框架,Component + Pipeline(DAG,可含环)。
- **甜区**:**RAG-first 且要工程化/可部署**;喜欢显式 DAG、强类型组件、清晰拓扑;要把 prompt 当资产管理。
- **反模式**:极简一次性脚本(管线编排是负担)。
- **隐藏成本**:工具调用等前沿能力在 `haystack_experimental`,稳定性需关注。
- **成熟度**:✅ 生产友好,有 REST 部署。
- **架构师笔记**:与 LangChain 比,**更工整、更工程化**;同一套 DAG 抽象覆盖"线性RAG→分支→循环→工具Agent"。状态留在你自己代码里(Pipeline 无状态),比 LangGraph 更"轻"但少了内建 state/HITL。
- 课程:`25-Building AI Applications with Haystack`(见 `00-总结回顾.md`)。

## 7. crewAI ✅⚠️

- **是什么**:多 agent 协作框架,核心抽象是 Role(角色)+ Task(任务)+ Crew(团队)。
- **甜区**:**多个角色分工协作**且边界清晰(规划者/研究者/写作者/评审者),"团队"心智直观、上手快。
- **反模式**:需要对每个 agent 的状态与转移做精细控制(用 LangGraph)。
- **隐藏成本**:高层抽象 → 控制力与可观测性弱于 LangGraph;复杂分支不好表达。
- **成熟度**:⚠️ 活跃但相对年轻,API 演进中。
- **架构师笔记**:**"多 agent 协作"的最快上手选项**。先用它验证协作价值,若需精细控制再下沉到 LangGraph 多 agent 图。
- 课程:`13-Multi AI Agent Systems with crewAI`。

## 8. AutoGen / AG2 / Microsoft Agent Framework(MAF) ⚠️

- **是什么**:微软系多 agent 对话框架,agent 之间通过消息可编程协作。**现状**:微软原版 **AutoGen 已转入维护模式**(仅修 bug/安全);官方继任是 **Microsoft Agent Framework(MAF)1.0**(AutoGen + Semantic Kernel 合并,2026-04 GA,Python+.NET,原生 MCP/A2A);**AG2** 是原作者社区分叉、仍活跃。
- **甜区**:研究式/实验式多 agent;灵活的对话编排;group chat 模式。**MAF** 面向企业级生产(.NET 一等公民、原生协议)。
- **反模式**:用 AutoGen/AG2 起多 agent 生产新项目——**新项目优先 crewAI 或 MAF**,AutoGen/AG2 仅适合 PoC。
- **隐藏成本**:原版生态分裂、版本动荡;迁到 MAF 有 API 重写成本。
- **成熟度**:⚠️ AutoGen 维护模式 / MAF 1.0 新 GA(2026-04,按版本复核)/ AG2 社区活跃。
- **架构师笔记**:多 agent **首推仍是 crewAI**(最快上手);微软栈/.NET 生产选 **MAF**;AutoGen/AG2 留给想法验证。注意"AutoGen 转维护模式"≠"AutoGen 已死"。本仓库未单列课程,选用前建议补做 PoC。

## 9. OpenAI Agents SDK ⚠️

- **是什么**:OpenAI 官方 agent 编排层(Agents、Handoffs、Tools、Guardrails、Tracing)。
- **甜区**:**全程 OpenAI 生态**;要官方支持的最短路径;内建 tracing。
- **可移植性**:其实 **provider-agnostic**——经 **LiteLLM 支持 100+ 模型**,换底层模型可行。多模型混用**可行,但属 best-effort/二等公民**(非 OpenAI 模型上部分 hosted tools / 结构化能力会打折)。
- **反模式**:把它当"任意厂商都一等公民"的中立编排层——非 OpenAI 路径是次优支持。
- **隐藏成本**:真正的锁定是**软锁**——tracing、Responses API、hosted tools(web/file search、code interpreter 等)都最贴合 OpenAI,迁出时这些要替换。
- **成熟度**:⚠️ 官方背书但年轻。
- **架构师笔记**:模型可换,但 tracing/Responses/hosted tools 的软锁是真实代价,写进 ADR。

## 10. Google ADK(Agent Development Kit) ⚠️

- **是什么**:Google 官方 agent 开发套件,面向 Gemini / Vertex AI。
- **甜区**:全程 Google Cloud / Gemini;企业级 Vertex 集成。
- **反模式**:跨厂商;非 GCP 技术栈。
- **成熟度**:⚠️ 已 GA(2026-04 ADK 1.0、2026-05 Python 2.0);单厂商绑定是取舍点,不是成熟度短板。
- **架构师笔记**:与 OpenAI Agents SDK 对称的"单厂商官方路线",取舍逻辑相同。

## 11. Claude Agent SDK ⚠️

- **是什么**:Anthropic 官方 agent SDK(原 Claude Code SDK,Python/TS),把 Claude Code 的 agent 循环、内建工具、子 agent、MCP 接入开放给自建 agent。
- **甜区**:**全程 Anthropic/Claude 生态**;要官方最短路 + 内建工具循环、文件/Bash/子 agent 编排、原生 MCP;偏编码 / 计算机使用类 agent。
- **反模式**:把它当跨厂商中立编排层(它是 Claude 优先);把非 Claude 模型当一等公民。
- **隐藏成本**:软锁——agent 循环 / 工具 / 上下文管理贴合 Claude;迁出要替换这套约定。
- **成熟度**:⚠️ 官方背书、迭代快(随 Claude Code 版本走),按版本复核。
- **架构师笔记**:与 OpenAI Agents SDK / Google ADK 对称的**"单厂商官方路线"**,取舍逻辑相同——换"省心 + 官方观测",付可移植性代价,写进 ADR。被本决策包 `01`/`04` 推荐用于 Claude 优先栈。

## 12. MCP(Model Context Protocol)— 协议层 ✅

- **是什么**:Anthropic 主推的开放协议,标准化 Agent 如何接入工具、资源、提示(Client-Server)。
- **定位**:**不是框架,是接入标准**,与上面所有框架**正交可叠加**。
- **何时用**:要把外部工具/数据源以可复用、可治理的方式接进来,且希望跨框架/跨 agent 复用同一批工具。
- **架构师笔记**:决策树里**几乎总是"加分项"**——选定框架后,工具层用 MCP 暴露,换框架时工具不用重写。2026 参考架构是两层:**MCP 接工具/数据 + A2A 接 agent**。⚠️ **"ACP" 是两个毫无关系的同名缩写**:① **Agent Communication Protocol**(IBM/BeeAI,agent↔agent)已于 **2025-08 并入 A2A**(归 Linux Foundation/AAIF);② **Agent Client Protocol**(Zed,编辑器/IDE↔编程 agent,≈LSP)独立活跃。协议与各层正交、不单列选型,详见 `/Users/ming/Documents/ai-agent-learn/agent/interview/1.md` «正交横切带 A · 协议»。
- 课程:`10-MCP`、`courses/00-.../L13-跨Agent标准与ACP.md`(注:该 L13 的 "ACP" 指 **Agent Client Protocol**/Zed,非已并入 A2A 的 IBM ACP)。

---

## 反模式总表(选错的典型信号)

| 你做了 | 症状 | 应该 |
|---|---|---|
| 简单结构化输出上了 LangGraph | 为一个 JSON 写一张图 | 退回裸 SDK + Pydantic AI |
| RAG-first 用了纯多 agent 框架 | 检索质量没人管 | 换 LlamaIndex / Haystack |
| 多角色协作用裸 SDK 硬写 | 重复造调度/消息轮子 | 用 crewAI / LangGraph 多 agent |
| 要 HITL/可恢复却选了无状态管线 | 中断就丢上下文 | 用 LangGraph(Checkpointer) |
| 怕 lock-in 却选了单厂商 SDK | 想换模型要重写 | 用框架抽象层 |
| 在 MCP 和 LangGraph 间"二选一" | 概念错位 | 它们不同层,叠加用 |
