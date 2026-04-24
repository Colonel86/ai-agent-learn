# AI Agent 高级开发工程师 · 学习路线图

> **目标**：从中级开发者成长为 AI Agent 高级开发工程师 + 架构师  
> **周期**：6 个月（24 周）· 每天 1-2 小时  
> **更新时间**：2026 年 4 月

---

## 每周节奏建议


| 时间    | 任务               |
| ----- | ---------------- |
| 周一~周三 | 📖 理论学习 + 文档阅读   |
| 周四~周五 | 💻 动手编码 + 项目实战   |
| 周六    | ✍️ 复盘总结 + 写技术博客  |
| 周日    | 🌐 开源项目阅读 / 社区交流 |


---

## Phase 1 · 基石构建（第 1-4 周）

> 🎯 **目标**：掌握 LLM 核心原理、Prompt Engineering 和基础开发框架

### 📚 系统化课程


| 资源                                                                                                                                                  | 类型                                                                                                                                                                        | 说明                                                   |
| --------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------- |
| [DeepLearning.AI — ChatGPT Prompt Engineering for Developers](https://www.deeplearning.ai/short-courses/chatgpt-prompt-engineering-for-developers/) | 免费                                                                                                                                                                        | Andrew Ng 与 OpenAI 合作的经典入门课，1.5h 快速掌握 Prompt 工程核心方法论 |
| [DeepLearning.AI — Building Systems with the ChatGPT API](https://www.deeplearning.ai/short-courses/building-systems-with-chatgpt/)                 | 免费                                                                                                                                                                        | 学习如何用 LLM API 构建完整系统，包括 Chain of Thought、分类路由等模式     |
| [Anthropic Prompt Engineering 互动教程](https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering)                                        | 免费                                                                                                                                                                        | Anthropic 官方提供的 Prompt 工程最佳实践，涵盖 Claude 模型使用技巧       |
| [DataCamp — Associate AI Engineer for Developers Track](https://www.datacamp.com/tracks/associate-ai-engineer-for-developers)                       | 付费[https://app.datacamp.com/learn/career-tracks/associate-ai-engineer-for-developers](https://app.datacamp.com/learn/career-tracks/associate-ai-engineer-for-developers) | 结构化职业路径课程，从开发者到 AI 工程师，包含交互式编码环境和技能评估                |


### 📖 必读书籍 & 文章


| 资源                                                                                                                                          | 类型                                                                                                                                                              | 说明                                                       |
| ------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------- |
| [《Build a Large Language Model (From Scratch)》— Sebastian Raschka](https://www.manning.com/books/build-a-large-language-model-from-scratch) | 书籍[https://github.com/skindhu/Build-A-Large-Language-Model-CN/tree/main/cn-Book](https://github.com/skindhu/Build-A-Large-Language-Model-CN/tree/main/cn-Book) | 从零实现一个 LLM，深入理解 Transformer、Tokenization、Attention 等核心原理 |
| [Lilian Weng — LLM Powered Autonomous Agents](https://lilianweng.github.io/posts/2023-06-23-agent/)                                         | 经典博客                                                                                                                                                            | OpenAI 研究员的博客，Agent 领域最经典的综述文章，必读                        |
| [The Illustrated Transformer — Jay Alammar](https://jalammar.github.io/illustrated-transformer/)                                            | 免费                                                                                                                                                              | 用可视化方式讲解 Transformer 架构，直觉式理解 Attention 机制               |


### 🛠️ 实践工具 & 文档


| 资源                                                    | 类型  | 说明                                                               |
| ----------------------------------------------------- | --- | ---------------------------------------------------------------- |
| [OpenAI API 官方文档](https://platform.openai.com/docs)   | 必读  | 掌握 Chat Completions API、Function Calling、Structured Output 等核心接口 |
| [Anthropic Claude API 文档](https://docs.anthropic.com) | 必读  | 学习 Claude 的 Tool Use、System Prompt、Vision 等特性                    |
| [Pydantic 官方文档](https://docs.pydantic.dev)            | 工具  | AI 应用开发必备的数据验证库，LangChain 等框架的核心依赖                               |
| [UV 包管理器](https://github.com/astral-sh/uv)            | 工具  | 2026 年最流行的 Python 包管理器，替代 pip/poetry，CrewAI 等框架推荐使用              |


### 🔨 阶段实战项目

- **项目 1：多模型智能问答 CLI**（入门）
  - 支持 GPT-4 / Claude / 开源模型切换的命令行问答工具
  - 练习 API 调用、流式输出、错误处理
- **项目 2：Prompt 模板管理系统**（进阶）
  - 构建一个 Prompt 版本管理 + A/B 测试框架
  - 学习 Pydantic 验证和异步编程

---

## Phase 2 · Agent 核心能力（第 5-10 周）

> 🎯 **目标**：深入理解 Agent 架构，掌握 LangChain / LangGraph 核心框架

### 📚 系统化课程


| 资源                                                                                                              | 类型           | 说明                                                                     |
| --------------------------------------------------------------------------------------------------------------- | ------------ | ---------------------------------------------------------------------- |
| [DeepLearning.AI — AI Agents in LangGraph](https://www.deeplearning.ai/short-courses/ai-agents-in-langgraph/)   | 免费           | LangChain 团队亲授，学习用 LangGraph 构建有状态的 Agent 循环流程                         |
| [DeepLearning.AI — Agentic AI 设计模式系列](https://www.deeplearning.ai/short-courses/)                               | 免费           | Andrew Ng 的 Agentic AI 四大设计模式：Reflection、Tool Use、Planning、Multi-Agent |
| [Udemy — AI Engineer Agentic Track: Complete Agent & MCP Course](https://www.udemy.com/topic/ai-agents/)        | 付费 · 8.3万+学员 | 覆盖 OpenAI Agents SDK、CrewAI、LangGraph、AutoGen、MCP 五大框架，含 8 个实战项目       |
| [Coursera — AI Agent Developer Specialization (Vanderbilt)](https://www.coursera.org/specializations/ai-agents) | 可免费旁听        | Vanderbilt 大学专项课程，涵盖 Agent 架构、Tool Use、Memory、多 Agent 系统               |
| [Hugging Face — AI Agents Course](https://huggingface.co/learn/agents-course)                                   | 免费           | Hugging Face 社区开源课程，侧重开源模型 + Agent 开发                                  |


### 📖 核心论文 & 博客


| 资源                                                                                                | 类型   | 说明                                                    |
| ------------------------------------------------------------------------------------------------- | ---- | ----------------------------------------------------- |
| [ReAct: Synergizing Reasoning and Acting in Language Models](https://arxiv.org/abs/2210.03629)    | 必读论文 | Agent 领域最重要的论文之一，定义了"推理+行动"的核心范式                      |
| [Reflexion: Language Agents with Verbal Reinforcement Learning](https://arxiv.org/abs/2303.11366) | 必读论文 | 自我反思机制，Agent 从错误中学习的关键模式                              |
| [Tree of Thoughts: Deliberate Problem Solving with LLMs](https://arxiv.org/abs/2305.10601)        | 推荐论文 | 树形搜索推理，理解 Agent 如何做复杂决策                               |
| [LangGraph 官方文档 — Concepts & Tutorials](https://langchain-ai.github.io/langgraph/)                | 必读   | StateGraph、条件路由、Checkpointing、Human-in-the-loop 等核心概念 |


### 🛠️ 框架 & 工具


| 资源                                                    | 类型   | 说明                                                   |
| ----------------------------------------------------- | ---- | ---------------------------------------------------- |
| [LangChain + LangGraph](https://docs.langchain.com)   | 核心框架 | 2026 年 Agent 开发事实标准。LangChain 管基础组件，LangGraph 管有状态编排 |
| [LangSmith](https://smith.langchain.com)              | 调试工具 | Agent 可观测性平台，Trace 每一步决策、Token 用量、延迟分析               |
| [OpenAI Agents SDK](https://platform.openai.com/docs) | 框架   | OpenAI 官方 Agent 框架，支持 handoff、guardrails、tracing     |


### 🔨 阶段实战项目

- **项目 3：个人助手 Agent**（核心）
  - 用 LangGraph 构建能搜索网页、读写文件、执行代码的个人助手
  - 练习 Tool Use 和状态管理
- **项目 4：自动化调研报告 Agent**（进阶）
  - 多步骤执行 Agent：接收主题 → 搜索资料 → 整理大纲 → 撰写报告
  - 使用条件路由和自我纠正

---

## Phase 3 · RAG 与知识系统（第 11-16 周）

> 🎯 **目标**：构建生产级 RAG 系统，掌握向量数据库与检索优化

### 📚 系统化课程


| 资源                                                                                                                                  | 类型  | 说明                                      |
| ----------------------------------------------------------------------------------------------------------------------------------- | --- | --------------------------------------- |
| [DeepLearning.AI — Building & Evaluating Advanced RAG](https://www.deeplearning.ai/short-courses/building-evaluating-advanced-rag/) | 免费  | LlamaIndex 团队合作课程，覆盖句子窗口检索、自动合并检索、评估指标  |
| [DeepLearning.AI — LangChain Chat with Your Data](https://www.deeplearning.ai/short-courses/langchain-chat-with-your-data/)         | 免费  | 学习文档加载、分块、嵌入、检索和对话式 RAG 的完整链路           |
| [Coursera — IBM RAG and Agentic AI Professional Certificate](https://www.coursera.org/professional-certificates/ibm-rag-agentic-ai) | 付费  | IBM 的 RAG + Agentic AI 专业认证，包含向量数据库、评估等 |


### 📖 深度阅读


| 资源                                                                                                                                                               | 类型   | 说明                                                                       |
| ---------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---- | ------------------------------------------------------------------------ |
| [Building Agentic RAG Systems with LangGraph (2026 Guide)](https://rahulkolekar.com/building-agentic-rag-systems-with-langgraph/)                                | 教程   | 从 Naive RAG 到 Agentic RAG，含 Router → Retriever → Grader → Generator 完整实现 |
| [Next-Generation Agentic RAG with LangGraph (2026 Edition)](https://medium.com/@vinodkrane/next-generation-agentic-rag-with-langgraph-2026-edition-d1c4c068d2b8) | 深度文章 | 覆盖混合记忆、上下文融合、Graph-of-Thought 推理等前沿模式                                    |
| [LangChain 官方 — Agentic RAG Tutorial](https://docs.langchain.com/oss/python/langgraph/agentic-rag)                                                               | 官方教程 | 官方手把手教程：检索工具、文档评分、查询重写、状态图编排                                             |
| [LangChain 官方 — Adaptive RAG Tutorial](https://langchain-ai.github.io/langgraph/tutorials/rag/langgraph_adaptive_rag/)                                           | 官方教程 | 自适应 RAG：查询分析 + 自我纠正 RAG 的统一实现                                            |
| [Build a RAG System from Scratch (2026) — Nerd Level Tech](https://nerdleveltech.com/guides/rag-hands-on-tutorial)                                               | 动手教程 | Docker 环境可复现，含 Chunking、嵌入、混合检索、Re-ranking、RAGAS 评估                      |


### 🛠️ 技术栈选型


| 技术                                                  | 类型   | 说明                                                              |
| --------------------------------------------------- | ---- | --------------------------------------------------------------- |
| 向量数据库：Milvus / Qdrant / Weaviate / ChromaDB         | 存储层  | 生产级选 Milvus 或 Qdrant；原型验证用 ChromaDB。重点理解 HNSW 索引和混合检索           |
| Embedding 模型：OpenAI text-embedding-3 / BGE / Cohere | 嵌入层  | 对比不同模型的维度、性能和成本。中文场景优先考虑 BGE 系列                                 |
| [RAGAS / DeepEval](https://docs.ragas.io)           | 评估   | RAG 系统必备评估工具，衡量 Faithfulness、Answer Relevancy、Context Precision |
| [LlamaIndex](https://docs.llamaindex.ai)            | 检索框架 | 专注于检索管道的框架，与 LangChain 互补。适合构建复杂的文档解析和索引流水线                     |


### 🔨 阶段实战项目

- **项目 5：技术文档语义搜索引擎**（核心）
  - 为真实文档库构建 RAG 系统：文档解析 → 智能分块 → 混合检索 → Re-ranking → 答案生成
- **项目 6：企业知识库问答系统**（综合）
  - 支持权限控制、引用溯源、对话历史、自适应检索的生产级知识库 Agent

---

## Phase 4 · 多 Agent 与 MCP 编排（第 17-20 周）

> 🎯 **目标**：掌握多 Agent 协作模式、MCP 协议与企业级编排方案

### 📚 系统化课程 & 教程


| 资源                                                                                                                                        | 类型      | 说明                                                                       |
| ----------------------------------------------------------------------------------------------------------------------------------------- | ------- | ------------------------------------------------------------------------ |
| [Anthropic — Introduction to MCP（官方课程）](https://anthropic.skilljar.com/introduction-to-model-context-protocol)                            | 官方 · 免费 | Anthropic 官方 MCP 课程，覆盖 Tools / Resources / Prompts 三大基础原语和 Python SDK 实战 |
| [Anthropic — MCP Advanced Topics（官方课程）](https://anthropic.skilljar.com/model-context-protocol-advanced-topics)                            | 官方 · 免费 | 进阶内容：Transport 机制、Sampling、通知系统、文件权限、生产部署策略                              |
| [DataCamp — CrewAI vs LangGraph vs AutoGen 对比教程](https://www.datacamp.com/tutorial/crewai-vs-langgraph-vs-autogen)                        | 免费教程    | 三大多 Agent 框架的全面对比，含代码示例和架构分析                                             |
| [DigitalOcean — CrewAI Crash Course](https://www.digitalocean.com/community/tutorials/crewai-crash-course-role-based-agent-orchestration) | 免费教程    | 从零到生产级多 Agent 工作流，包含工具集成、监控和最佳实践                                         |


### 📖 核心文档 & 深度阅读


| 资源                                                                                            | 类型  | 说明                                                                       |
| --------------------------------------------------------------------------------------------- | --- | ------------------------------------------------------------------------ |
| [MCP 官方文档](https://modelcontextprotocol.io)                                                   | 必读  | MCP 协议规范、快速入门、SDK 文档。2025 年底已捐赠给 Linux Foundation                        |
| [MCP GitHub 生态](https://github.com/modelcontextprotocol)                                      | 源码  | Python / TypeScript / C# / Java / Ruby / PHP SDK，MCP Inspector 调试工具      |
| [CrewAI 官方文档](https://docs.crewai.com)                                                        | 必读  | 角色定义、任务编排、工具集成、训练和追踪等核心功能                                                |
| [AutoGen / Microsoft Agent Framework 文档](https://microsoft.github.io/autogen/)                | 参考  | 对话式多 Agent 框架，已与 Semantic Kernel 合并为 Microsoft Agent Framework           |
| [Multi-Agent Frameworks 2026 深度对比](https://gurusup.com/blog/best-multi-agent-frameworks-2026) | 综述  | LangGraph / CrewAI / AutoGen / OpenAI SDK / Google ADK / Claude SDK 全面对比 |


### 🛠️ 框架选型指南


| 框架              | 适用场景         | 特点                                           |
| --------------- | ------------ | -------------------------------------------- |
| **LangGraph**   | 复杂状态流 + 条件路由 | 最高灵活性，内置 Checkpointing 和时间旅行调试。适合需要精细控制的生产系统 |
| **CrewAI**      | 快速原型 + 角色协作  | 20 行代码启动，角色化 DSL 直觉。适合任务明确的多 Agent 协作        |
| **AutoGen/AG2** | 对话式协作 + 人机交互 | GroupChat 模式，Agent 间辩论和精炼。适合质量敏感的离线任务        |


### 🔌 Agent 通信协议栈（MCP / A2A / AG-UI）

> 这几类协议**不是竞争关系，而是分层互补**——类比 TCP / HTTP / HTML。
> 真实系统里一个 agent 经常同时用到好几个：**MCP 接工具、A2A 跟别的 agent 协作、AG-UI 给前端**。
> 架构师的关键能力就是搞清楚每一层要用什么、怎么组合。

#### 📐 四层协议全景

| 层次                        | 代表协议                     | 解决的问题                          |
| ------------------------- | ------------------------ | ------------------------------ |
| **Agent ↔ 工具 / 上下文**       | **MCP**                  | agent 如何接入外部数据、API、文件、能力        |
| **Agent ↔ Agent**          | **A2A**（Agent2Agent）     | 跨框架 / 跨厂商 / 跨组织的 agent 互通       |
| **Agent ↔ 用户 UI**          | **AG-UI**                | agent 后端到前端的流式、有状态、人在回路通信       |
| **工具内嵌 UI**（特殊层）           | **MCP Apps / MCP-UI**    | 工具调用直接返回可交互富 UI（图表、地图、表单）       |

#### 🎯 AG-UI：Agent 和前端的"接口标准"

**解决的问题**：把 agent 后端输出（流式 token、工具调用、状态变化、人在回路审批）标准化地送到前端，传统 REST / GraphQL 搞不定这类场景。

**核心做法**：
- **基于事件的流式协议**，定义了约 16 种标准事件类型（run start、text delta、tool call、state patch、reasoning trace、human approval…）
- **底层传输不限**：SSE / WebSocket / Webhook 都可以
- **专门处理**：流式文本、运行生命周期、工具调用、共享状态同步、推理轨迹、人在回路审批

**典型场景**：
- LangGraph / CrewAI / AutoGen 后端 + React / Vue 前端，需要状态双向同步
- 需要在 UI 上展示 agent "思考过程" 并允许用户中途干预
- 跨框架可移植（换后端框架不用重写前端）

#### 📡 同类 / 相关协议对比（2026 年现状）

**① Agent ↔ User UI 层**（AG-UI 同类）

| 协议 / SDK            | 主推方                  | 机制                                          | 定位                           |
| ------------------- | -------------------- | ------------------------------------------- | ---------------------------- |
| **AG-UI**           | CopilotKit 等社区推动     | 事件流协议，框架中立                                  | agent ↔ 前端应用的"通用总线"          |
| **MCP Apps / MCP-UI** | Anthropic + OpenAI   | 工具调用返回 UI 资源（`ui://` URI + 沙箱 iframe）      | 工具结果带富 UI。2026-01-26 起 **MCP Apps** 成为官方规范，MCP-UI 的 `UIResourceRenderer` 已标记弃用，推荐用实现 MCP Apps 的 **AppRenderer** |
| **A2UI**            | Google               | 声明式生成式 UI，从预定义 widget 集合生成；跨 Web / 移动 / 桌面 | 宿主应用原生渲染，不是发 HTML 而是发 UI 描述   |
| **OpenAI Apps SDK** | OpenAI               | ChatGPT 宿主内的 App 模式                         | 局限于 OpenAI 生态                |
| **Vercel AI SDK**   | Vercel               | 纯 SSE + React hooks                         | 简单场景最省事，但不是标准协议              |

**② Agent ↔ Agent 层**

| 协议     | 主推方   | 机制                                         | 定位                                |
| ------ | ----- | ------------------------------------------ | --------------------------------- |
| **A2A** | Google | HTTP + JSON-RPC 2.0（v0.3 起可选 gRPC），每个 agent 发布 **Agent Card** 声明能力 | 强调 **"不透明性"**：agent 只暴露能做什么，不暴露怎么做。适合跨组织 / 跨厂商协作 |

**③ 最朴素的方案：REST API**

把 agent 当普通 HTTP endpoint 用（前端轮询或一次性拿结果）。**短任务可以**，长任务 / 流式 / 人在回路场景越来越吃力。

#### 🧭 选型决策树

| 你的需求                             | 推荐方案                      |
| -------------------------------- | ------------------------- |
| 给前端做流式对话，追求简单                    | **Vercel AI SDK** 或自己写 SSE |
| 复杂 agent 交互（状态同步、generative UI、human-in-the-loop）+ 跨框架可移植 | **AG-UI** ⭐                |
| 工具本身要返回交互式界面（在 Claude / ChatGPT 宿主里跑） | **MCP Apps**              |
| 多 agent 跨组织 / 跨厂商协作               | **A2A**                   |
| 单组织内多 agent 协作                    | LangGraph / CrewAI 的内部编排（不需要标准协议） |

#### 📖 学习资源

| 资源                                                          | 类型  | 说明                              |
| ----------------------------------------------------------- | --- | ------------------------------- |
| [AG-UI 官方文档](https://docs.ag-ui.com)                        | 必读  | 协议规范、16 种事件类型、参考实现              |
| [AG-UI GitHub](https://github.com/ag-ui-protocol/ag-ui)     | 源码  | 协议源码 + 多语言 SDK（Python / TS）     |
| [CopilotKit 官方文档](https://docs.copilotkit.ai)               | 配套  | AG-UI 背后主推者，提供开箱即用的 React 组件     |
| [A2A 官方站](https://a2a-protocol.org)                         | 必读  | Google 主导的 A2A 协议规范和 Agent Card 机制 |
| [MCP Apps 规范（Model Context Protocol 扩展）](https://modelcontextprotocol.io) | 必读  | 2026-01-26 正式合入 MCP 规范的 UI 扩展   |
| [MCP-UI 项目](https://github.com/idosal/mcp-ui)               | 参考  | MCP Apps 的前身实现，可看历史演进            |


### 🔨 阶段实战项目

- **项目 7：3-Agent 内容生产流水线**（核心）
  - 研究 Agent → 写作 Agent → 审核 Agent 协作流水线，用 CrewAI 实现
- **项目 8：MCP Server 生态开发**（核心）
  - 开发 3 个 MCP Server（GitHub API + PostgreSQL + Google Calendar），用 MCP Inspector 调试
- **项目 9：混合编排系统**（挑战）
  - 用 LangGraph 做总编排，CrewAI 做子任务执行，Agent 通过 MCP 调用外部工具
- **项目 10：AG-UI 前端集成 Demo**（加分）
  - 把项目 3 / 4 的 LangGraph agent 通过 AG-UI 协议暴露给 React 前端
  - 实现流式输出、工具调用可视化、人在回路审批按钮、状态双向同步
  - 体会 "协议分层" 在真实系统里的价值

---

## Phase 5 · 架构师进阶（第 21-24 周）

> 🎯 **目标**：具备企业级 Agent 系统设计能力，成为技术架构决策者

### 📚 架构设计学习


| 资源                                                                                                                           | 类型   | 说明                                      |
| ---------------------------------------------------------------------------------------------------------------------------- | ---- | --------------------------------------- |
| 《Designing Data-Intensive Applications》— Martin Kleppmann                                                                    | 经典书籍 | 分布式系统圣经，理解可靠性、可扩展性、可维护性。Agent 平台架构的理论基础 |
| 《LLM Engineer's Handbook》                                                                                                    | 推荐书籍 | LLM 工程实战手册，覆盖从训练到部署的全链路工程实践             |
| [Johns Hopkins — Agentic AI Certificate Program](https://online.lifelonglearning.jhu.edu/jhu-certificate-program-agentic-ai) | 认证项目 | 16 周在线认证，覆盖推理模型、多 Agent 系统、强化学习等高级主题    |


### 📖 开源项目源码研读（必做）


| 项目                                               | 学习重点                                 |
| ------------------------------------------------ | ------------------------------------ |
| [Dify](https://github.com/langgenius/dify)       | 工作流编排引擎、RAG Pipeline、多模型管理、多租户架构设计   |
| [RAGFlow](https://github.com/infiniflow/ragflow) | 深度文档理解、智能分块、GraphRAG 实现，生产级 RAG 系统设计 |
| [ChatDev](https://github.com/OpenBMB/ChatDev)    | 模拟软件公司的多 Agent 协作，角色分工和通信协议设计        |
| [MetaGPT](https://github.com/geekan/MetaGPT)     | 标准化 SOP 驱动的多 Agent 协作，工程化 Agent 系统设计 |


### 🏛️ 架构师核心能力专项


| 能力项       | 关键内容                                                     |
| --------- | -------------------------------------------------------- |
| 🏗️ 可靠性设计 | 重试策略、回退机制、熔断器模式、幂等性设计                                    |
| 💰 成本工程   | Token 预算管理、模型路由（大小模型混用）、语义缓存、Prompt 压缩                   |
| 🛡️ 安全架构  | Prompt 注入防护、输出过滤（Guardrails）、数据隔离、审计日志                   |
| 🔭 可观测性   | LangSmith Tracing、自定义 Metrics、Evaluation Pipeline、A/B 测试 |
| ⚖️ 技术选型   | 框架对比、Trade-off 分析、技术债管理                                  |
| 📢 沟通领导   | 架构评审、技术布道、团队赋能                                           |


### 🔨 毕业项目（约 40-60 小时）

**🎓 企业 AI Agent 平台**

构建一个完整的企业级 AI Agent 平台，包含：

- 多租户 Agent 运行平台架构
- 可视化工作流编排引擎（DAG）
- RAG 知识库 + 多工具 + 多 Agent 集成
- MCP Server 生态接入
- 监控大盘 + 评估系统
- 部署、监控、评估全链路打通

> 完成后开源到 GitHub 并写系列技术博客

---

## 🌐 持续跟进的社区 & 信息源

- **Twitter/X 关注**：@AndrewYNg @LangChainAI @llaboratory @CrewAIInc
- **Reddit**：r/AI_Agents、r/LangChain、r/LocalLLaMA
- **Discord**：LangChain、LlamaIndex、CrewAI 官方社区
- **Newsletter**：The Batch (DeepLearning.AI)、AI Engineering Weekly
- **GitHub**：关注 LangGraph / CrewAI / Dify 的 Release Notes

---

## 💼 求职 & 个人品牌建设

- **GitHub**：保持绿点，所有实战项目开源并写好 README
- **技术博客**：每两周一篇，记录学习和项目心得（推荐 Medium / 掘金）
- **开源贡献**：给 LangChain / CrewAI / Dify 提 PR，从文档和测试开始
- **技术分享**：在公司内部或社区做 Agent 开发相关的 Tech Talk

---

## 💡 关键建议

1. **项目 > 课程**：每个阶段的实战项目比看视频更重要，做完就推到 GitHub
2. **读源码 > 看教程**：多读 Dify / LangGraph / CrewAI 源码，比任何教程都有效
3. **坚持写博客**：既是复盘也是个人品牌建设，面试时的最好证明
4. **保持节奏**：每天 1-2 小时，关键是不断不停，6 个月后你会惊讶于自己的进步

