# DeepLearning.AI 全量课程目录(含 Agent 开发分类)

> 抓取自 https://www.deeplearning.ai/courses ,共 124 门,抓取日期 2026-07-02。
> 分类口径:严格按「是否 AI Agent 应用开发」判定。✅ 核心=直接构建/编排/生产化 Agent;🔧 支撑=RAG/检索/结构化输出/评测/安全等上下文与质量层;⌨️=用 AI 编码工具提效;— 其他=模型层/ML基础/领域应用/基础设施。
>
> **「是否需要学习」列说明**:按当前目标——面试 **AI Agent 高级开发工程师/架构师**(非全量 FDE、非 ML 研究方向)——给出的默认判断,已核对 `agent/courses/` 现有笔记标已学。判定口径:
> - ✅ 已学 —— `agent/courses/` 已有对应笔记
> - 🎯 需要 —— 未学,且填补当前面试目标的真实缺口(新机制/新协议,不与已学内容重叠)
> - ⏸️ 可选 —— 未学,但与已学内容或选型矩阵重叠,或偏垂类 demo(语音/图片视频/浏览器/数据库等具体行业应用),优先级低,时间充裕再学
> - ❌ 不需要 —— 超出当前目标范围(AI 编码工具提效、纯 ML/模型训练/量化/领域应用等)
>
> 这是默认建议,不是最终结论——你比我更清楚自己的实际缺口,可直接改标记。

## ✅ Agent 核心(35 门)

| 发布 | 课程 | 合作方 | 简介 | 是否需要学习 |
|---|---|---|---|---|
| 2026-06-17 | [Voice for AI Agents and Applications](https://www.deeplearning.ai/courses/voice-for-ai-agents-and-applications) | Vocal Bridge | 通过三种集成模式为你的 AI Agent 和应用添加语音能力:嵌入式语音、叠加在现有 Agent 上的语音、作为可调用工具的语音。 | ⏸️ 可选 |
| 2026-05-20 | [AI Agents for Image and Video Generation](https://www.deeplearning.ai/courses/ai-agents-for-image-and-video-generation) | Google | 构建能生成图像和视频的 AI Agent,自动评估输出质量,并持续迭代直到结果达到你的质量标准。 | ⏸️ 可选 |
| 2026-05-06 | [Build Interactive Agents with Generative UI](https://www.deeplearning.ai/courses/build-interactive-agents-with-generative-ui) | CopilotKit | 构建超越纯文本的全栈 Agent 应用,按需生成图表、表单、白板等自定义 UI。 | ⏸️ 可选 |
| 2026-03-18 | [Agent Memory: Building Memory-Aware Agents](https://www.deeplearning.ai/courses/agent-memory-building-memory-aware-agents) | Oracle | 构建一套完整的 Agent 记忆系统,让 LLM 能跨会话存储、检索、精炼知识——把无状态 Agent 变成能持续学习和改进的系统。 | ⏸️ 可选(与已学 #12 LangGraph 长期记忆重叠) |
| 2026-02-11 | [A2A: The Agent2Agent Protocol](https://www.deeplearning.ai/courses/a2a-the-agent2agent-protocol) | Google Cloud,IBM Research | 使用 A2A(标准化 Agent 间通信的开放协议)连接来自不同框架和团队的 Agent。 | 🎯 需要 |
| 2026-01-28 | [Agent Skills with Anthropic](https://www.deeplearning.ai/courses/agent-skills-with-anthropic) | Anthropic | 为 Agent 配备按需调用的专家知识,实现可靠的编码、研究和数据分析工作流。 | ✅ 已学 |
| 2026-01-14 | [Document AI: From OCR to Agentic Doc Extraction](https://www.deeplearning.ai/courses/document-ai-from-ocr-to-agentic-doc-extraction) | LandingAI | 构建能解析文档并提取信息的 Agent 系统,基于图表、表格、表单等视觉元素进行信息定位。 | ⏸️ 可选 |
| 2025-12-17 | [Nvidia's NeMo Agent Toolkit: Making Agents Reliable](https://www.deeplearning.ai/courses/nvidia-nat-making-agents-reliable) | Nvidia | 使用 Nvidia NeMo Agent Toolkit 中的可观测性、评测与部署工具,把概念验证级的 Agent demo 转变为生产级系统。 | 🎯 需要 |
| 2025-12-03 | [Building Coding Agents with Tool Execution](https://www.deeplearning.ai/courses/building-coding-agents-with-tool-execution) | E2B | 构建能编写并执行代码来完成任务的 AI Agent,在保护你系统免受不可信代码影响的沙箱云环境中安全运行。 | ⏸️ 可选(已有 code-sandbox 笔记覆盖概念) |
| 2025-11-19 | [Semantic Caching for AI Agents](https://www.deeplearning.ai/courses/semantic-caching-for-ai-agents) | Redis | 通过实现基于语义(而非精确文本)复用响应的语义缓存,为你的 AI Agent 提速并降低成本。 | 🎯 需要 |
| 2025-11-11 | [Design, Develop, and Deploy Multi-Agent Systems  with CrewAI](https://www.deeplearning.ai/courses/design-develop-and-deploy-multi-agent-systems-with-crewai) | CrewAI | 构建能协作、使用工具与记忆、并可靠扩展到生产环境的实用多 Agent 系统。 | ⏸️ 可选(与已学 crewAI 课重叠) |
| 2025-10-22 | [Governing AI Agents](https://www.deeplearning.ai/courses/governing-ai-agents) | Databricks | 将数据治理集成到你的 Agent 工作流中,确保它安全、合规、准确地处理数据。 | 🎯 需要 |
| 2025-09-30 | [Agentic AI](https://www.deeplearning.ai/courses/agentic-ai) | DeepLearning.AI | 由 Andrew Ng 授课,你将构建通过迭代式多步工作流来采取行动的 Agentic AI 系统。 | ✅ 已学 |
| 2025-09-24 | [Building and Evaluating Data Agents](https://www.deeplearning.ai/courses/building-and-evaluating-data-agents) | Snowflake | 构建、评测并改进一个能规划步骤、连接数据源并提供洞见的多 Agent 系统。 | ⏸️ 可选 |
| 2025-09-24 | [Building Live Voice Agents with Google's ADK](https://www.deeplearning.ai/courses/building-live-voice-agents-with-googles-adk) | Google | 使用 Google 的 Agent Development Kit,构建从简单到多 Agent 播客系统的实时语音 AI Agent。 | ⏸️ 可选 |
| 2025-09-17 | [Build AI Apps with MCP Server: Working with Box Files](https://www.deeplearning.ai/courses/build-ai-apps-with-mcp-server-working-with-box-files) | Box | 构建一个使用 Box MCP server 工具来发现 Box 文件并提取文本的 LLM 应用,并将其改造为使用 A2A 通信的多 Agent 系统。 | ⏸️ 可选(与已学 MCP 课重叠) |
| 2025-09-10 | [Knowledge Graphs for AI Agent API Discovery](https://www.deeplearning.ai/courses/knowledge-graphs-for-ai-agent-api-discovery) | SAP | 构建知识图谱,让你的 AI Agent 能按正确顺序发现并调用正确的 API。 | ⏸️ 可选 |
| 2025-08-27 | [Agentic Knowledge Graph Construction](https://www.deeplearning.ai/courses/agentic-knowledge-graph-construction) | Neo4j | 构建一个能规划、设计并构建知识图谱的多 Agent 系统。 | ⏸️ 可选 |
| 2025-06-04 | [DSPy: Build and Optimize Agentic Apps](https://www.deeplearning.ai/courses/dspy-build-optimize-agentic-apps) | Databricks | 使用 DSPy 和 MLflow 构建、调试并优化 AI Agent。 | 🎯 需要 |
| 2025-05-14 | [MCP: Build Rich-Context AI Apps with Anthropic](https://www.deeplearning.ai/courses/mcp-build-rich-context-ai-apps-with-anthropic) | Anthropic | 使用 Model Context Protocol 构建能访问工具、数据和提示词的 AI 应用。 | ✅ 已学 |
| 2025-05-07 | [Building AI Voice Agents for Production](https://www.deeplearning.ai/courses/building-ai-voice-agents-for-production) | LiveKit,RealAvatar | 构建响应迅速、可扩展、拟人化的 AI 语音应用。 | ⏸️ 可选 |
| 2025-04-23 | [Building Code Agents with Hugging Face smolagents](https://www.deeplearning.ai/courses/building-code-agents-with-hugging-face-smolagents) | Hugging Face | 使用 Hugging Face 的 smolagents 构建能编写并执行代码来完成复杂任务的 Agent。 | ⏸️ 可选 |
| 2025-04-16 | [Building AI Browser Agents](https://www.deeplearning.ai/courses/building-ai-browser-agents) | AGI Inc | 构建能浏览并操作网站的 Agent,并学习如何让它们更可靠。 | ⏸️ 可选 |
| 2025-03-14 | [Long-Term Agentic Memory With LangGraph](https://www.deeplearning.ai/courses/long-term-agentic-memory-with-langgraph) | LangChain | 学习使用 LangGraph 构建具备长期记忆的 AI Agent,用 LangMem 管理记忆。 | ✅ 已学 |
| 2025-03-05 | [Event-Driven Agentic Document Workflows](https://www.deeplearning.ai/courses/event-driven-agentic-document-workflows) | LlamaIndex | 构建事件驱动的 Agentic 工作流,使用 RAG 与人机协同反馈来处理文档并填写表单。 | ✅ 已学 |
| 2025-02-19 | [Evaluating AI Agents](https://www.deeplearning.ai/courses/evaluating-ai-agents) | Arize AI | 学习如何使用结构化评估方法系统性地评测、改进并迭代 AI Agent。 | ✅ 已学 |
| 2025-01-22 | [Building toward Computer Use with Anthropic](https://www.deeplearning.ai/courses/building-toward-computer-use-with-anthropic) | Anthropic | 学习一个能使用并在计算机上完成任务的 AI Assistant 是如何构建的。 | 🎯 需要 |
| 2024-11-07 | [LLMs as Operating Systems: Agent Memory](https://www.deeplearning.ai/courses/llms-as-operating-systems-agent-memory) | Letta | 使用能自主管理自身记忆的 MemGPT Agent 构建系统。 | ⏸️ 可选(与已学记忆课重叠) |
| 2024-10-23 | [Practical Multi AI Agents and Advanced Use Cases with crewAI](https://www.deeplearning.ai/courses/practical-multi-ai-agents-and-advanced-use-cases-with-crewai) | crewAI | 构建能协作解决复杂业务任务的 Agent。 | ⏸️ 可选(与已学 crewAI 课重叠) |
| 2024-06-13 | [Building Your Own Database Agent](https://www.deeplearning.ai/courses/building-your-own-database-agent) | Microsoft | 用自然语言与表格数据和 SQL 数据库交互,让数据分析更高效、更易上手。 | ⏸️ 可选 |
| 2024-06-05 | [AI Agents in LangGraph](https://www.deeplearning.ai/courses/ai-agents-in-langgraph) | LangChain,Tavily | 使用 LangChain 的 LangGraph 和 Tavily 的 agentic 搜索构建 agentic AI 工作流。 | ✅ 已学 |
| 2024-05-29 | [AI Agentic Design Patterns with AutoGen](https://www.deeplearning.ai/courses/ai-agentic-design-patterns-with-autogen) | Microsoft,Penn State University | 使用 AutoGen 框架构建具有多样角色和能力的多 Agent 系统,实现复杂 AI 应用。 | 🎯 需要 |
| 2024-05-15 | [Multi AI Agent Systems with crewAI](https://www.deeplearning.ai/courses/multi-ai-agent-systems-with-crewai) | crewAI | 用多 AI Agent 系统自动化业务流程。通过用自然语言设计和提示一个 AI Agent 团队,超越单一 LLM 提示的表现。 | ✅ 已学 |
| 2024-05-08 | [Building Agentic RAG with Llamaindex](https://www.deeplearning.ai/courses/building-agentic-rag-with-llamaindex) | LlamaIndex | 构建能智能浏览并分析你的数据的自主 Agent。学习使用 LlamaIndex 开发 agentic RAG 系统,实现强大的文档问答与摘要功能,并掌握引导 Agent 推理与调试的技能。 | ✅ 已学 |
| 2023-10-25 | [Functions, Tools and Agents with LangChain](https://www.deeplearning.ai/courses/functions-tools-agents-langchain) | LangChain | 了解 LLM API 的最新进展,使用 LangChain 表达式语言(LCEL)编排和定制 chain 与 agent。 | ✅ 已学 |

## 🔧 Agent 支撑(27 门)

| 发布 | 课程 | 合作方 | 简介 | 是否需要学习 |
|---|---|---|---|---|
| 2025-12-10 | [Multi-vector Image Retrieval](https://www.deeplearning.ai/courses/multi-vector-image-retrieval) | Qdrant | 构建用多个向量表示图像的高级检索系统,实现文本查询与视觉内容之间的细粒度匹配,支持精准的多模态搜索。 | ⏸️ 可选 |
| 2025-09-30 | [Retrieval Augmented Generation (RAG)](https://www.deeplearning.ai/courses/retrieval-augmented-generation) | DeepLearning.AI | 掌握构建生产级 RAG 应用所需的基础理解与实践知识,涵盖架构、部署与评测全流程。 | 🎯 需要 |
| 2025-07-30 | [Pydantic for LLM Workflows](https://www.deeplearning.ai/courses/pydantic-for-llm-workflows) | DeepLearning.AI | 使用 Pydantic 构建具有结构化输出与数据校验的可靠 LLM 应用。 | ✅ 已学 |
| 2025-04-02 | [Getting Structured LLM Output](https://www.deeplearning.ai/courses/getting-structured-llm-output) | DotTxt | 学习如何生成结构化输出,为生产级 LLM 软件应用提供支持。 | 🎯 需要 |
| 2024-11-13 | [Safe and reliable AI via guardrails](https://www.deeplearning.ai/courses/safe-and-reliable-ai-via-guardrails) | GuardrailsAI | 借助 guardrails 提供的额外控制,将你的 LLM 应用从概念验证推进到生产环境。 | 🎯 需要 |
| 2024-10-02 | [Retrieval Optimization: Tokenization to Vector Quantization](https://www.deeplearning.ai/courses/retrieval-optimization-from-tokenization-to-vector-quantization) | Qdrant | 为你的 LLM 应用构建更快、更相关的向量搜索。 | ⏸️ 可选 |
| 2024-08-21 | [Building AI Applications With Haystack](https://www.deeplearning.ai/courses/building-ai-applications-with-haystack) | Haystack | 学习一个灵活的框架,用来构建各种复杂的 AI 应用。 | ✅ 已学 |
| 2024-08-14 | [Improving Accuracy of LLM Applications](https://www.deeplearning.ai/courses/improving-accuracy-of-llm-applications) | AMD, formerly Lamini,Meta | 通过评测、提示工程和记忆调优,系统性地提升 LLM 应用的准确率。 | ⏸️ 可选 |
| 2024-07-31 | [Embedding Models: from Architecture to Implementation](https://www.deeplearning.ai/courses/embedding-models-from-architecture-to-implementation) | Vectara | 学习如何构建嵌入模型,以及如何创建有效的语义检索系统。 | ❌ 不需要 |
| 2024-07-10 | [Prompt Compression and Query Optimization](https://www.deeplearning.ai/courses/prompt-compression-and-query-optimization) | MongoDB | 优化你的 RAG 应用的效率、安全性、查询处理速度与成本。 | ⏸️ 可选 |
| 2024-06-20 | [Function-calling and data extraction with LLMs](https://www.deeplearning.ai/courses/function-calling-and-data-extraction-with-llms) | Nexusflow | 学习应用 function calling 来扩展 LLM 和 Agent 应用的能力。 | 🎯 需要 |
| 2024-04-10 | [Preprocessing Unstructured Data for LLM Applications](https://www.deeplearning.ai/courses/preprocessing-unstructured-data-for-llm-applications) | Unstructured | 改进你的 RAG 系统以检索多样化的数据类型。学习从 PDF、PPT、HTML 等各类文档中提取并规范化内容。 | ⏸️ 可选 |
| 2024-04-03 | [Red Teaming LLM Applications](https://www.deeplearning.ai/courses/red-teaming-llm-applications) | Giskard | 学习如何通过红队测试让 LLM 应用更安全。学习识别与评估大语言模型(LLM)应用中的漏洞。 | 🎯 需要 |
| 2024-03-27 | [JavaScript RAG Web Apps with LlamaIndex](https://www.deeplearning.ai/courses/javascript-rag-web-apps-with-llamaindex) | LlamaIndex | 构建一个使用 RAG 能力与你的数据对话的全栈 Web 应用。学习用 JavaScript 构建 RAG 应用,并用智能 Agent 回答查询。 | ❌ 不需要 |
| 2024-03-13 | [Knowledge Graphs for RAG](https://www.deeplearning.ai/courses/knowledge-graphs-rag) | Neo4j | 学习如何构建并使用知识图谱系统来改进你的检索增强生成应用。使用 Neo4j 的查询语言 Cypher 管理和检索数据。 | ⏸️ 可选 |
| 2024-01-31 | [Building Applications with Vector Databases](https://www.deeplearning.ai/courses/building-applications-vector-databases) | Pinecone | 学习构建六个由向量数据库驱动的应用,包括语义搜索、检索增强生成(RAG)和异常检测。 | ⏸️ 可选 |
| 2024-01-24 | [Automated Testing for LLMOps](https://www.deeplearning.ai/courses/automated-testing-llmops) | CircleCI | 学习如何创建自动化 CI 流水线,在每次变更时评测你的 LLM 应用,实现更快、更安全的开发。 | ✅ 已学 |
| 2024-01-03 | [Advanced Retrieval for AI with Chroma](https://www.deeplearning.ai/courses/advanced-retrieval-for-ai) | Chroma | 学习高级检索技术以提升检索结果的相关性。学习识别低质量查询结果,并用 LLM 改进查询。 | ✅ 已学 |
| 2023-11-29 | [Building and Evaluating Advanced RAG](https://www.deeplearning.ai/courses/building-evaluating-advanced-rag) | TruEra,LlamaIndex | 学习 sentence-window、auto-merging 等优于基线的高级 RAG 检索方法,并评测、迭代你的 pipeline 性能。 | ✅ 已学 |
| 2023-11-08 | [Vector Databases: from Embeddings to Applications](https://www.deeplearning.ai/courses/vector-databases-embeddings-applications) | Weaviate | 设计并实现向量数据库的真实应用场景。构建高效实用的应用,包括混合搜索与多语言搜索。 | ❌ 不需要 |
| 2023-09-06 | [Understanding and Applying Text Embeddings](https://www.deeplearning.ai/courses/google-cloud-vertex-ai) | Google Cloud | 学习如何用文本嵌入加速应用开发过程,理解句子与段落层面的语义。 | ❌ 不需要 |
| 2023-08-29 | [How Business Thinkers Can Start Building AI Plugins With Semantic Kernel](https://www.deeplearning.ai/courses/microsoft-semantic-kernel) | Microsoft | 学习微软的开源编排框架 Semantic Kernel,在你的应用中使用记忆、连接器、chain、planner 等 LLM 构建模块。 | ❌ 不需要 |
| 2023-08-16 | [Large Language Models with Semantic Search](https://www.deeplearning.ai/courses/large-language-models-semantic-search) | Cohere | 学习用 LLM 增强搜索并总结结果,使用 Cohere Rerank 与嵌入实现密集检索。 | ❌ 不需要 |
| 2023-07-05 | [LangChain Chat with Your Data](https://www.deeplearning.ai/courses/langchain-chat-with-your-data) | LangChain | 用 LangChain 创建一个能与你的私有数据和文档对话的聊天机器人。向 LangChain 创始人 Harrison Chase 学习。 | ✅ 已学 |
| 2023-05-31 | [LangChain for LLM Application Development](https://www.deeplearning.ai/courses/langchain) | LangChain | 使用强大且可扩展的 LangChain 框架,学习提示词、解析、记忆、chain、问答与 agent。 | ✅ 已学 |
| 2023-05-31 | [Building Systems with the ChatGPT API](https://www.deeplearning.ai/courses/chatgpt-building-system) | OpenAI | 学习拆解复杂任务、自动化工作流、串联 LLM 调用,并从 LLM 中获得更好的输出。评估 LLM 输入输出的安全性与相关性。 | ✅ 已学 |
| 2023-04-27 | [ChatGPT Prompt Engineering for Developers](https://www.deeplearning.ai/courses/chatgpt-prompt-eng) | OpenAI | 学习 ChatGPT 提示工程的基础知识。学习有效提示技巧,以及如何用 LLM 做摘要、推断、转换和扩写。 | ✅ 已学 |

## ⌨️ AI 编码工具(10 门)

| 发布 | 课程 | 合作方 | 简介 | 是否需要学习 |
|---|---|---|---|---|
| 2026-04-15 | [Spec-Driven Development with Coding Agents](https://www.deeplearning.ai/courses/spec-driven-development-with-coding-agents) | JetBrains | 超越"氛围编程":学习编写清晰的规格说明,为你的编码 Agent 提供构建有意图、可维护软件所需的上下文。 | ❌ 不需要 |
| 2026-01-21 | [Gemini CLI: Code & Create with an Open-Source Agent](https://www.deeplearning.ai/courses/gemini-cli-code-and-create-with-an-open-source-agent) | Gemini CLI | 使用 Gemini CLI(Google 的开源 agentic 编码助手,能协调本地工具与云服务)从命令行构建真实世界的应用,自动化编码与创意工作流。 | ❌ 不需要 |
| 2026-01-07 | [Build with Andrew](https://www.deeplearning.ai/courses/build-with-andrew) | DeepLearning.AI | 如果你从未写过代码,这门课就是为你准备的。不到 30 分钟,你就能学会用语言描述一个想法,并让 AI 把它转化成一个应用。 | ❌ 不需要 |
| 2025-11-11 | [Generative AI for Software Development](https://www.deeplearning.ai/courses/generative-ai-for-software-development) | DeepLearning.AI | 学习实用的提示工程与 LLM 结对编程技巧,用来编写、测试和改进你的代码。 | ❌ 不需要 |
| 2025-11-03 | [Jupyter AI: AI Coding in Notebooks](https://www.deeplearning.ai/courses/jupyter-ai-coding-in-notebooks) | Project Jupyter | 学习在 Jupyter notebook 中用 AI 编码。使用 Jupyter AI 生成代码、获取解释并分析数据。 | ❌ 不需要 |
| 2025-08-06 | [Claude Code: A Highly Agentic Coding Assistant](https://www.deeplearning.ai/courses/claude-code-a-highly-agentic-coding-assistant) | Anthropic | 使用 Claude Code 探索、构建并重构代码库。 | ❌ 不需要 |
| 2025-03-26 | [Vibe Coding 101 with Replit](https://www.deeplearning.ai/courses/vibe-coding-101-with-replit) | Replit | 在一个集成的 Web 开发环境中,用 AI 编码 Agent 设计、构建并部署应用。 | ❌ 不需要 |
| 2025-02-26 | [Build Apps with Windsurf's AI Coding Agents](https://www.deeplearning.ai/courses/build-apps-with-windsurfs-ai-coding-agents) | Windsurf | 学习用一个 Agentic AI 驱动的集成开发环境构建、调试并部署应用。 | ❌ 不需要 |
| 2024-12-11 | [Collaborative Writing and Coding with OpenAI Canvas](https://www.deeplearning.ai/courses/collaborative-writing-and-coding-with-openai-canvas) | OpenAI | 学习使用 OpenAI Canvas,与 AI 协作更高效地写作、编码和创作。 | ❌ 不需要 |
| 2023-09-27 | [Pair Programming with a Large Language Model](https://www.deeplearning.ai/courses/pair-programming-llm) | Google | 学习如何提示 LLM 来帮助改进、调试、理解和为你的代码写文档。用 LLM 简化代码并提升生产力。 | ❌ 不需要 |

## — 其他(52 门)

| 发布 | 课程 | 合作方 | 简介 | 是否需要学习 |
|---|---|---|---|---|
| 2026-06-03 | [Fast & Efficient LLM Inference with vLLM](https://www.deeplearning.ai/courses/fast-and-efficient-llm-inference-with-vllm) | Red Hat | 使用 vLLM 优化、部署并测评一个开源 LLM。 | ❌ 不需要 |
| 2026-05-12 | [Transformers in Practice](https://www.deeplearning.ai/courses/transformers-in-practice) | AMD | 不止于使用 LLM,更要真正理解它们。在 Sharon Zhou 讲授的这门课中,你将建立起推理模型行为、调试真实问题、做出更明智的 transformer 模型部署决策的直觉。 | ❌ 不需要 |
| 2026-04-28 | [AI Prompting for Everyone](https://www.deeplearning.ai/courses/ai-prompting-for-everyone) | DeepLearning.AI | 在 Andrew Ng 讲授的这门新课中成为 AI 高级用户。从信息检索到构建应用,你将培养从当今最强大的 AI 模型中获得真实、有用结果的提示技巧。 | ❌ 不需要 |
| 2026-04-22 | [Building Multimodal Data Pipelines](https://www.deeplearning.ai/courses/building-multimodal-data-pipelines) | Snowflake | 学习构建 AI 驱动的 pipeline,把图像、音频、视频转化为 LLM 可用的文本,并在此基础上构建多模态应用。 | ❌ 不需要 |
| 2026-04-08 | [Efficient Inference with SGLang: Text and Image Generation](https://www.deeplearning.ai/courses/efficient-inference-with-sglang-text-and-image-generation) | RadixArk,LMSys | 学习 LLM 推理的底层原理,并实现包括 KV cache 和 RadixAttention 在内的缓存优化技术,让文本和图像生成更快更省钱。 | ❌ 不需要 |
| 2026-03-04 | [Build and Train an LLM with JAX](https://www.deeplearning.ai/courses/build-and-train-an-llm-with-jax) | Google | 使用 JAX(支撑 Google Gemini 的开源库)从零构建并训练一个 2000 万参数的 LLM,学习驱动现代 AI 开发的核心技术。 | ❌ 不需要 |
| 2026-01-01 | [Data Engineering](https://www.deeplearning.ai/courses/data-engineering) | DeepLearning.AI | 培养你作为数据工程师的技能,通过数据的接入、转换、存储与服务来推动组织目标,并在这个高需求领域发展你的职业生涯。 | ❌ 不需要 |
| 2025-12-02 | [TensorFlow Developer Professional Certificate](https://www.deeplearning.ai/courses/tensorflow-developer-professional-certificate) | DeepLearning.AI | 掌握使用 TensorFlow API 所需的知识,以及在这个最热门的深度学习框架之一中的最佳实践与实战经验。 | ❌ 不需要 |
| 2025-11-30 | [Natural Language Processing Specialization](https://www.deeplearning.ai/courses/natural-language-processing) | DeepLearning.AI | 设计能执行问答、情感分析、语言翻译和摘要的 NLP 应用。 | ❌ 不需要 |
| 2025-11-30 | [AI for Medicine](https://www.deeplearning.ai/courses/ai-for-medicine) | DeepLearning.AI | 从随机对照试验数据中估计治疗效果。解读诊断与预后模型。应用 NLP 从非结构化医疗数据中提取信息。 | ❌ 不需要 |
| 2025-11-04 | [Machine Learning in Production](https://www.deeplearning.ai/courses/machine-learning-in-production) | DeepLearning.AI | 设计一个机器学习生产系统:范围界定、数据、建模、部署。原型开发、部署与持续改进。 | ❌ 不需要 |
| 2025-10-28 | [PyTorch for Deep Learning](https://www.deeplearning.ai/courses/pytorch-for-deep-learning-professional-certificate) | DeepLearning.AI | 学习使用 PyTorch 构建、优化和部署深度学习模型的核心原理。 | ❌ 不需要 |
| 2025-10-28 | [Fine-tuning & RL for LLMs: Intro to Post-training](https://www.deeplearning.ai/courses/fine-tuning-and-reinforcement-learning-for-llms-intro-to-post-training) | AMD | 学习应用微调与强化学习技术来塑造模型行为、提升推理能力,让 LLM 更安全可靠。 | ❌ 不需要 |
| 2025-10-27 | [Generative AI with Large Language Models](https://www.deeplearning.ai/courses/generative-ai-with-llms) | AWS | 理解生成式 AI 的生命周期。描述驱动 LLM 的 transformer 架构。应用训练/调优/推理方法。聆听研究者讲述生成式 AI 的挑战与机遇。 | ❌ 不需要 |
| 2025-09-30 | [Mathematics for Machine Learning and Data Science](https://www.deeplearning.ai/courses/mathematics-for-machine-learning-and-data-science) | DeepLearning.AI | 探索机器学习的基础数学工具箱:微积分、线性代数、统计学与概率论。 | ❌ 不需要 |
| 2025-09-30 | [Fast Prototyping of GenAI Apps with Streamlit](https://www.deeplearning.ai/courses/fast-prototyping-of-genai-apps-with-streamlit) | Snowflake | 使用 MVP 工作流、提示工程和 RAG 快速原型化并部署 GenAI 应用。 | ❌ 不需要 |
| 2025-09-30 | [Data Analytics](https://www.deeplearning.ai/courses/data-analytics) | DeepLearning.AI | 使用行业标准工具和 AI 工具打下扎实的数据分析基础,以提取洞见、做出决策并解决真实业务问题。 | ❌ 不需要 |
| 2025-08-13 | [AI for Good](https://www.deeplearning.ai/courses/ai-for-good) | DeepLearning.AI | 学习一套 AI 项目开发框架。为空气质量、风能、生物多样性和灾害管理构建模型。探索公共卫生与气候变化相关案例研究。 | ❌ 不需要 |
| 2025-07-09 | [Post-training of LLMs](https://www.deeplearning.ai/courses/post-training-of-llms) | University of Washington,NexusFlow | 使用 SFT、DPO 和在线强化学习等后训练技术,让 LLM 适配特定任务和行为。 | ❌ 不需要 |
| 2025-06-27 | [Machine Learning Specialization](https://www.deeplearning.ai/courses/machine-learning) | DeepLearning.AI,Stanford Online | 通过直观的可视化方法学习基础 AI 概念,再学习实现算法和数学所需的代码。 | ❌ 不需要 |
| 2025-06-27 | [Deep Learning Specialization](https://www.deeplearning.ai/courses/deep-learning) | DeepLearning.AI | 构建神经网络(CNN、RNN、LSTM、Transformer),并用 Python 和 TensorFlow 将它们应用于语音识别、NLP 等领域。 | ❌ 不需要 |
| 2025-06-27 | [AI for Everyone](https://www.deeplearning.ai/courses/ai-for-everyone) | DeepLearning.AI | 了解 AI 技术以及如何使用它们。审视 AI 的社会影响,学习如何应对这场技术变革。 | ❌ 不需要 |
| 2025-06-18 | [Building with Llama 4](https://www.deeplearning.ai/courses/building-with-llama-4) | Meta | 使用 Llama 4 开源模型、API 和 Llama 工具构建多模态、长上下文的 GenAI 应用。 | ❌ 不需要 |
| 2025-06-11 | [Orchestrating Workflows for GenAI Applications](https://www.deeplearning.ai/courses/orchestrating-workflows-for-genai-applications) | Astronomer | 使用 Apache Airflow 把你的 GenAI 原型转变为自动化 pipeline。 | ❌ 不需要 |
| 2025-05-21 | [Reinforcement Fine-Tuning LLMs With GRPO](https://www.deeplearning.ai/courses/reinforcement-fine-tuning-llms-grpo) | Predibase | 使用强化微调和奖励函数提升 LLM 的推理能力。 | ❌ 不需要 |
| 2025-04-01 | [Generative AI for Everyoneㅤ](https://www.deeplearning.ai/courses/generative-ai-for-everyone) | DeepLearning.AI | 学习如何使用生成式 AI 的能力与局限。了解真实世界案例概览,以及它对商业和社会的影响,制定有效战略。 | ❌ 不需要 |
| 2025-02-12 | [Attention in Transformers: Concepts and Code in PyTorch](https://www.deeplearning.ai/courses/attention-in-transformers-concepts-and-code-in-pytorch) | StatQuest | 理解并用 PyTorch 实现注意力机制——基于 transformer 的 LLM 的关键要素。 | ❌ 不需要 |
| 2025-02-05 | [How Transformer LLMs Work](https://www.deeplearning.ai/courses/how-transformer-llms-work) | Jay Alammar, Maarten Grootendorst | 理解驱动 LLM 的 transformer 架构,以便更有效地使用它们。 | ❌ 不需要 |
| 2025-01-08 | [Build Long-Context AI Apps with Jamba](https://www.deeplearning.ai/courses/build-long-context-ai-apps-with-jamba) | AI21 labs | 构建能处理超长文档的 LLM 应用,使用 Jamba 模型。 | ❌ 不需要 |
| 2024-12-18 | [Reasoning with o1](https://www.deeplearning.ai/courses/reasoning-with-o1) | OpenAI | 学习如何使用并提示 OpenAI 的 o1 模型来完成复杂推理任务。 | ❌ 不需要 |
| 2024-11-20 | [Building an AI-Powered Game](https://www.deeplearning.ai/courses/building-an-ai-powered-game) | Together AI,AI Dungeon | 学习用 LLM 构建应用,从零创建一个有趣的互动游戏。 | ❌ 不需要 |
| 2024-10-09 | [Introducing Multimodal Llama 3.2](https://www.deeplearning.ai/courses/introducing-multimodal-llama-3-2) | Meta | 体验新版 Llama 3.2 模型的多模态特性,构建 AI 应用。 | ❌ 不需要 |
| 2024-08-28 | [Large Multimodal Model Prompting with Gemini](https://www.deeplearning.ai/courses/large-multimodal-model-prompting-with-gemini) | Google Cloud | 学习使用 Google 的 Gemini 模型进行多模态提示的最佳实践。 | ❌ 不需要 |
| 2024-08-07 | [AI Python for Beginners](https://www.deeplearning.ai/courses/ai-python-for-beginners) | DeepLearning.AI | 借助 AI 辅助学习 Python 编程。掌握高效编写、测试、调试代码的技能,创建真实世界的 AI 应用。 | ❌ 不需要 |
| 2024-07-24 | [Intro to Federated Learning](https://www.deeplearning.ai/courses/intro-to-federated-learning) | Flower Labs | 使用联邦学习框架,在分布式数据上构建和微调 LLM,以获得更好的隐私保护。 | ❌ 不需要 |
| 2024-07-24 | [Federated Fine-tuning of LLMs with Private Data](https://www.deeplearning.ai/courses/intro-to-federated-learning-c2) | Flower Labs | 学习如何使用联邦方法安全地用私有数据微调大语言模型(LLM),增强数据隐私、降低数据泄露风险,并通过参数高效微调(PEFT)和差分隐私优化效率。 | ❌ 不需要 |
| 2024-07-17 | [Pretraining LLMs](https://www.deeplearning.ai/courses/pretraining-llms) | Upstage | 学习从零预训练一个大语言模型的关键步骤。 | ❌ 不需要 |
| 2024-06-26 | [Carbon Aware Computing for GenAI developers](https://www.deeplearning.ai/courses/carbon-aware-computing-for-genai-developers) | Google Cloud | 使用更清洁的能源训练你的机器学习模型。 | ❌ 不需要 |
| 2024-05-21 | [Introduction to on-device AI](https://www.deeplearning.ai/courses/introduction-to-on-device-ai) | Qualcomm | 为边缘设备和智能手机部署 AI。学习模型转换、量化,以及如何为不同设备做部署适配。 | ❌ 不需要 |
| 2024-05-06 | [Quantization in Depth](https://www.deeplearning.ai/courses/quantization-in-depth) | Hugging Face | 使用高级量化技术定制模型压缩。尝试线性量化的不同变体,包括对称与非对称模式,以及不同粒度。 | ❌ 不需要 |
| 2024-04-29 | [Prompt Engineering for Vision Models](https://www.deeplearning.ai/courses/prompt-engineering-for-vision-models) | Comet | 学习面向视觉模型的提示工程,使用 Stable Diffusion,以及物体检测、图像修复等高级技巧。 | ❌ 不需要 |
| 2024-04-22 | [Getting Started with Mistral](https://www.deeplearning.ai/courses/getting-started-with-mistral) | Mistral AI | 探索 Mistral 的开源与商业模型,利用 Mistral 的 JSON 模式生成结构化 LLM 响应。使用 Mistral 的 API 调用用户自定义函数以增强 LLM 能力。 | ❌ 不需要 |
| 2024-04-15 | [Quantization Fundamentals with Hugging Face](https://www.deeplearning.ai/courses/quantization-fundamentals) | Hugging Face | 学习如何量化任意开源模型。学习用 Hugging Face Transformers 库和 Quanto 库压缩模型。 | ❌ 不需要 |
| 2024-03-18 | [Efficiently Serving LLMs](https://www.deeplearning.ai/courses/efficiently-serving-llms) | Predibase | 理解 LLM 如何预测下一个 token,以及 KV caching 等技术如何加速文本生成。编写代码为多用户高效地提供 LLM 应用服务。 | ❌ 不需要 |
| 2024-03-06 | [Open Source Models with Hugging Face](https://www.deeplearning.ai/courses/open-source-models-hugging-face) | Hugging Face | 学习如何使用开源模型和 Hugging Face 工具轻松构建 AI 应用。在 Hugging Face Hub 上查找和筛选开源模型。 | ❌ 不需要 |
| 2024-02-28 | [Prompt Engineering with Llama 2&3](https://www.deeplearning.ai/courses/prompt-engineering-with-llama-2) | Meta | 学习提示词工程和选用 Meta Llama 2 & 3 模型的最佳实践。与 Meta Llama 2 Chat、Code Llama 和 Llama Guard 模型交互。 | ❌ 不需要 |
| 2024-01-17 | [LLMOps](https://www.deeplearning.ai/courses/llmops) | Google Cloud | 学习 LLMOps 最佳实践,设计并自动化针对特定任务微调和部署 LLM 的步骤。 | ❌ 不需要 |
| 2023-12-13 | [Reinforcement Learning From Human Feedback](https://www.deeplearning.ai/courses/reinforcement-learning-from-human-feedback) | Google Cloud | 了解使用基于人类反馈的强化学习(RLHF)来调优和评估 LLM 的入门知识,并微调 Llama 2 模型。 | ❌ 不需要 |
| 2023-08-23 | [Finetuning Large Language Models](https://www.deeplearning.ai/courses/finetuning-large-language-models) | AMD, formerly Lamini | 了解何时该用微调、何时该用提示词来处理 LLM。为你的特定领域挑选合适的开源模型、准备数据并训练评估。 | ❌ 不需要 |
| 2023-08-02 | [Evaluating and Debugging Generative AI](https://www.deeplearning.ai/courses/evaluating-debugging-generative-ai) | Weights & Biases | 学习在你的 ML 工作流中用于管理、版本控制、调试和实验的 MLOps 工具。 | ❌ 不需要 |
| 2023-07-27 | [Building Generative AI Applications with Gradio](https://www.deeplearning.ai/courses/huggingface-gradio) | Hugging Face | 快速创建并演示机器学习应用。在 Hugging Face Spaces 上与团队成员和 beta 测试者分享你的应用。 | ❌ 不需要 |
| 2023-05-31 | [How Diffusion Models Work](https://www.deeplearning.ai/courses/diffusion-models) | - | 从零开始学习并构建扩散模型,理解每一步。了解当今使用中的扩散模型,并实现算法来加速采样。 | ❌ 不需要 |
