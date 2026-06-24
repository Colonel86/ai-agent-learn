import { useState } from "react";

const PHASES = [
  {
    id: 1,
    title: "Phase 1 · 基石构建",
    duration: "第 1-4 周",
    color: "#E8590C",
    sections: [
      {
        title: "📚 系统化课程",
        items: [
          {
            name: "DeepLearning.AI — ChatGPT Prompt Engineering for Developers",
            url: "https://www.deeplearning.ai/short-courses/chatgpt-prompt-engineering-for-developers/",
            tag: "免费",
            desc: "Andrew Ng 与 OpenAI 合作的经典入门课，1.5 小时快速掌握 Prompt 工程核心方法论",
          },
          {
            name: "DeepLearning.AI — Building Systems with the ChatGPT API",
            url: "https://www.deeplearning.ai/short-courses/building-systems-with-chatgpt/",
            tag: "免费",
            desc: "学习如何用 LLM API 构建完整系统，包括 Chain of Thought、分类路由等模式",
          },
          {
            name: "Anthropic Prompt Engineering 互动教程",
            url: "https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering",
            tag: "免费",
            desc: "Anthropic 官方提供的 Prompt 工程最佳实践，涵盖 Claude 模型的使用技巧",
          },
          {
            name: "DataCamp — Associate AI Engineer for Developers Track",
            url: "https://www.datacamp.com/tracks/associate-ai-engineer-for-developers",
            tag: "付费",
            desc: "结构化职业路径课程，从开发者到 AI 工程师，包含交互式编码环境和技能评估",
          },
        ],
      },
      {
        title: "📖 必读书籍 & 文章",
        items: [
          {
            name: "《Build a Large Language Model (From Scratch)》— Sebastian Raschka",
            url: "https://www.manning.com/books/build-a-large-language-model-from-scratch",
            tag: "书籍",
            desc: "从零实现一个 LLM，深入理解 Transformer、Tokenization、Attention 等核心原理",
          },
          {
            name: "Lilian Weng 博客 — LLM Powered Autonomous Agents",
            url: "https://lilianweng.github.io/posts/2023-06-23-agent/",
            tag: "经典",
            desc: "OpenAI 研究员的博客，Agent 领域最经典的综述文章，必读",
          },
          {
            name: "The Illustrated Transformer — Jay Alammar",
            url: "https://jalammar.github.io/illustrated-transformer/",
            tag: "免费",
            desc: "用可视化方式讲解 Transformer 架构，直觉式理解 Attention 机制",
          },
        ],
      },
      {
        title: "🛠️ 实践工具 & 文档",
        items: [
          {
            name: "OpenAI API 官方文档",
            url: "https://platform.openai.com/docs",
            tag: "必读",
            desc: "掌握 Chat Completions API、Function Calling、Structured Output 等核心接口",
          },
          {
            name: "Anthropic Claude API 文档",
            url: "https://docs.anthropic.com",
            tag: "必读",
            desc: "学习 Claude 的 Tool Use、System Prompt、Vision 等特性",
          },
          {
            name: "Pydantic 官方文档",
            url: "https://docs.pydantic.dev",
            tag: "工具",
            desc: "AI 应用开发必备的数据验证库，LangChain 等框架的核心依赖",
          },
          {
            name: "UV 包管理器",
            url: "https://github.com/astral-sh/uv",
            tag: "工具",
            desc: "2026 年最流行的 Python 包管理器，替代 pip/poetry，CrewAI 等框架推荐使用",
          },
        ],
      },
      {
        title: "🔨 阶段实战项目",
        items: [
          {
            name: "项目 1：多模型智能问答 CLI",
            tag: "入门",
            desc: "支持 GPT-4 / Claude / 开源模型切换的命令行问答工具，练习 API 调用、流式输出、错误处理",
          },
          {
            name: "项目 2：Prompt 模板管理系统",
            tag: "进阶",
            desc: "构建一个 Prompt 版本管理 + A/B 测试框架，学习 Pydantic 验证和异步编程",
          },
        ],
      },
    ],
  },
  {
    id: 2,
    title: "Phase 2 · Agent 核心能力",
    duration: "第 5-10 周",
    color: "#1971C2",
    sections: [
      {
        title: "📚 系统化课程",
        items: [
          {
            name: "DeepLearning.AI — AI Agents in LangGraph",
            url: "https://www.deeplearning.ai/short-courses/ai-agents-in-langgraph/",
            tag: "免费",
            desc: "LangChain 团队亲授，学习用 LangGraph 构建有状态的 Agent 循环流程",
          },
          {
            name: "DeepLearning.AI — Agentic AI 设计模式系列",
            url: "https://www.deeplearning.ai/short-courses/",
            tag: "免费",
            desc: "Andrew Ng 的 Agentic AI 四大设计模式：Reflection、Tool Use、Planning、Multi-Agent",
          },
          {
            name: "Udemy — AI Engineer Agentic Track: Complete Agent & MCP Course",
            url: "https://www.udemy.com/topic/ai-agents/",
            tag: "付费 · 8.3万+学员",
            desc: "覆盖 OpenAI Agents SDK、CrewAI、LangGraph、AutoGen、MCP 五大框架，含 8 个实战项目",
          },
          {
            name: "Coursera — AI Agent Developer Specialization (Vanderbilt)",
            url: "https://www.coursera.org/specializations/ai-agents",
            tag: "可免费旁听",
            desc: "Vanderbilt 大学专项课程，涵盖 Agent 架构、Tool Use、Memory、多 Agent 系统",
          },
          {
            name: "Hugging Face — AI Agents Course",
            url: "https://huggingface.co/learn/agents-course",
            tag: "免费",
            desc: "Hugging Face 社区开源课程，侧重开源模型 + Agent 开发",
          },
        ],
      },
      {
        title: "📖 核心论文 & 博客",
        items: [
          {
            name: "ReAct: Synergizing Reasoning and Acting in Language Models",
            url: "https://arxiv.org/abs/2210.03629",
            tag: "必读论文",
            desc: "Agent 领域最重要的论文之一，定义了"推理+行动"的核心范式",
          },
          {
            name: "Reflexion: Language Agents with Verbal Reinforcement Learning",
            url: "https://arxiv.org/abs/2303.11366",
            tag: "必读论文",
            desc: "自我反思机制，Agent 从错误中学习的关键模式",
          },
          {
            name: "Tree of Thoughts: Deliberate Problem Solving with LLMs",
            url: "https://arxiv.org/abs/2305.10601",
            tag: "推荐论文",
            desc: "树形搜索推理，理解 Agent 如何做复杂决策",
          },
          {
            name: "LangGraph 官方文档 — Concepts & Tutorials",
            url: "https://langchain-ai.github.io/langgraph/",
            tag: "必读",
            desc: "StateGraph、条件路由、Checkpointing、Human-in-the-loop 等核心概念",
          },
        ],
      },
      {
        title: "🛠️ 框架 & 工具",
        items: [
          {
            name: "LangChain + LangGraph",
            url: "https://docs.langchain.com",
            tag: "核心框架",
            desc: "2026 年 Agent 开发事实标准。LangChain 管基础组件，LangGraph 管有状态编排",
          },
          {
            name: "LangSmith",
            url: "https://smith.langchain.com",
            tag: "调试工具",
            desc: "Agent 的可观测性平台，Trace 每一步决策、Token 用量、延迟分析",
          },
          {
            name: "OpenAI Agents SDK",
            url: "https://platform.openai.com/docs",
            tag: "框架",
            desc: "OpenAI 官方 Agent 框架，支持 handoff、guardrails、tracing",
          },
        ],
      },
      {
        title: "🔨 阶段实战项目",
        items: [
          {
            name: "项目 3：个人助手 Agent",
            tag: "核心",
            desc: "用 LangGraph 构建能搜索网页、读写文件、执行代码的个人助手，练习 Tool Use 和状态管理",
          },
          {
            name: "项目 4：自动化调研报告 Agent",
            tag: "进阶",
            desc: "多步骤执行 Agent：接收主题 → 搜索资料 → 整理大纲 → 撰写报告，使用条件路由和自我纠正",
          },
        ],
      },
    ],
  },
  {
    id: 3,
    title: "Phase 3 · RAG 与知识系统",
    duration: "第 11-16 周",
    color: "#2F9E44",
    sections: [
      {
        title: "📚 系统化课程",
        items: [
          {
            name: "DeepLearning.AI — Building & Evaluating Advanced RAG",
            url: "https://www.deeplearning.ai/short-courses/building-evaluating-advanced-rag/",
            tag: "免费",
            desc: "LlamaIndex 团队合作课程，覆盖句子窗口检索、自动合并检索、评估指标",
          },
          {
            name: "DeepLearning.AI — LangChain Chat with Your Data",
            url: "https://www.deeplearning.ai/short-courses/langchain-chat-with-your-data/",
            tag: "免费",
            desc: "学习文档加载、分块、嵌入、检索和对话式 RAG 的完整链路",
          },
          {
            name: "Coursera — IBM RAG and Agentic AI Professional Certificate",
            url: "https://www.coursera.org/professional-certificates/ibm-rag-agentic-ai",
            tag: "付费",
            desc: "IBM 的 RAG + Agentic AI 专业认证，包含向量数据库、评估等内容",
          },
        ],
      },
      {
        title: "📖 深度阅读",
        items: [
          {
            name: "Building Agentic RAG Systems with LangGraph (2026 Guide)",
            url: "https://rahulkolekar.com/building-agentic-rag-systems-with-langgraph/",
            tag: "教程",
            desc: "从 Naive RAG 到 Agentic RAG，含 Router → Retriever → Grader → Generator 完整实现",
          },
          {
            name: "Next-Generation Agentic RAG with LangGraph (2026 Edition)",
            url: "https://medium.com/@vinodkrane/next-generation-agentic-rag-with-langgraph-2026-edition-d1c4c068d2b8",
            tag: "深度文章",
            desc: "覆盖混合记忆、上下文融合、Graph-of-Thought 推理等前沿模式",
          },
          {
            name: "LangChain 官方 — Agentic RAG Tutorial",
            url: "https://docs.langchain.com/oss/python/langgraph/agentic-rag",
            tag: "官方教程",
            desc: "官方手把手教程：检索工具、文档评分、查询重写、状态图编排",
          },
          {
            name: "LangChain 官方 — Adaptive RAG Tutorial",
            url: "https://langchain-ai.github.io/langgraph/tutorials/rag/langgraph_adaptive_rag/",
            tag: "官方教程",
            desc: "自适应 RAG：查询分析 + 自我纠正 RAG 的统一实现",
          },
          {
            name: "Nerd Level Tech — Build a RAG System from Scratch (2026)",
            url: "https://nerdleveltech.com/guides/rag-hands-on-tutorial",
            tag: "动手教程",
            desc: "Docker 环境可复现，含 Chunking、嵌入、混合检索、Re-ranking、RAGAS 评估",
          },
        ],
      },
      {
        title: "🛠️ 技术栈选型",
        items: [
          {
            name: "向量数据库：Milvus / Qdrant / Weaviate / ChromaDB",
            tag: "存储层",
            desc: "生产级选 Milvus 或 Qdrant；原型验证用 ChromaDB。重点理解 HNSW 索引和混合检索",
          },
          {
            name: "Embedding 模型：OpenAI text-embedding-3 / BGE / Cohere",
            tag: "嵌入层",
            desc: "对比不同模型的维度、性能和成本。中文场景优先考虑 BGE 系列",
          },
          {
            name: "评估框架：RAGAS / DeepEval",
            url: "https://docs.ragas.io",
            tag: "评估",
            desc: "RAG 系统必备评估工具，衡量 Faithfulness、Answer Relevancy、Context Precision",
          },
          {
            name: "LlamaIndex",
            url: "https://docs.llamaindex.ai",
            tag: "检索框架",
            desc: "专注于检索管道的框架，与 LangChain 互补。适合构建复杂的文档解析和索引流水线",
          },
        ],
      },
      {
        title: "🔨 阶段实战项目",
        items: [
          {
            name: "项目 5：技术文档语义搜索引擎",
            tag: "核心",
            desc: "为真实文档库构建 RAG 系统：文档解析 → 智能分块 → 混合检索 → Re-ranking → 答案生成",
          },
          {
            name: "项目 6：企业知识库问答系统",
            tag: "综合",
            desc: "支持权限控制、引用溯源、对话历史、自适应检索的生产级知识库 Agent",
          },
        ],
      },
    ],
  },
  {
    id: 4,
    title: "Phase 4 · 多 Agent 与 MCP 编排",
    duration: "第 17-20 周",
    color: "#9C36B5",
    sections: [
      {
        title: "📚 系统化课程 & 教程",
        items: [
          {
            name: "Anthropic — Introduction to MCP (官方课程)",
            url: "https://anthropic.skilljar.com/introduction-to-model-context-protocol",
            tag: "官方 · 免费",
            desc: "Anthropic 官方 MCP 课程，覆盖 Tools / Resources / Prompts 三大基础原语和 Python SDK 实战",
          },
          {
            name: "Anthropic — MCP Advanced Topics (官方课程)",
            url: "https://anthropic.skilljar.com/model-context-protocol-advanced-topics",
            tag: "官方 · 免费",
            desc: "进阶内容：Transport 机制、Sampling、通知系统、文件权限、生产部署策略",
          },
          {
            name: "DataCamp — CrewAI vs LangGraph vs AutoGen 对比教程",
            url: "https://www.datacamp.com/tutorial/crewai-vs-langgraph-vs-autogen",
            tag: "免费教程",
            desc: "三大多 Agent 框架的全面对比，含代码示例和架构分析",
          },
          {
            name: "DigitalOcean — CrewAI Crash Course",
            url: "https://www.digitalocean.com/community/tutorials/crewai-crash-course-role-based-agent-orchestration",
            tag: "免费教程",
            desc: "从零到生产级多 Agent 工作流，包含工具集成、监控和最佳实践",
          },
          {
            name: "ZTM Academy — Build AI Agents with CrewAI",
            url: "https://zerotomastery.io",
            tag: "付费",
            desc: "Bootcamp 风格，专注 CrewAI，最终构建一个完整的 AI 面试教练",
          },
        ],
      },
      {
        title: "📖 核心文档 & 深度阅读",
        items: [
          {
            name: "MCP 官方文档",
            url: "https://modelcontextprotocol.io",
            tag: "必读",
            desc: "MCP 协议规范、快速入门、SDK 文档。2025 年底已捐赠给 Linux Foundation",
          },
          {
            name: "MCP GitHub 生态",
            url: "https://github.com/modelcontextprotocol",
            tag: "源码",
            desc: "Python / TypeScript / C# / Java / Ruby / PHP SDK，MCP Inspector 调试工具",
          },
          {
            name: "CrewAI 官方文档",
            url: "https://docs.crewai.com",
            tag: "必读",
            desc: "角色定义、任务编排、工具集成、训练和追踪等核心功能",
          },
          {
            name: "AutoGen (AG2 / Microsoft Agent Framework) 文档",
            url: "https://microsoft.github.io/autogen/",
            tag: "参考",
            desc: "对话式多 Agent 框架，已与 Semantic Kernel 合并为 Microsoft Agent Framework",
          },
          {
            name: "Multi-Agent Frameworks 2026 深度对比",
            url: "https://gurusup.com/blog/best-multi-agent-frameworks-2026",
            tag: "综述",
            desc: "LangGraph / CrewAI / AutoGen / OpenAI SDK / Google ADK / Claude SDK 全面对比",
          },
        ],
      },
      {
        title: "🛠️ 框架选型指南",
        items: [
          {
            name: "LangGraph — 复杂状态流 + 条件路由场景首选",
            tag: "图编排",
            desc: "最高灵活性，内置 Checkpointing 和时间旅行调试。适合需要精细控制的生产系统",
          },
          {
            name: "CrewAI — 快速原型 + 角色协作场景首选",
            tag: "角色编排",
            desc: "20 行代码启动，角色化 DSL 直觉。适合任务明确的多 Agent 协作",
          },
          {
            name: "AutoGen/AG2 — 对话式协作 + 人机交互场景",
            tag: "对话编排",
            desc: "GroupChat 模式，Agent 间辩论和精炼。适合质量敏感的离线任务",
          },
        ],
      },
      {
        title: "🔨 阶段实战项目",
        items: [
          {
            name: "项目 7：3-Agent 内容生产流水线",
            tag: "核心",
            desc: "研究 Agent → 写作 Agent → 审核 Agent 协作流水线，用 CrewAI 实现",
          },
          {
            name: "项目 8：MCP Server 生态开发",
            tag: "核心",
            desc: "开发 3 个 MCP Server（GitHub API + PostgreSQL + Google Calendar），用 MCP Inspector 调试",
          },
          {
            name: "项目 9：混合编排系统",
            tag: "挑战",
            desc: "用 LangGraph 做总编排，CrewAI 做子任务执行，Agent 通过 MCP 调用外部工具",
          },
        ],
      },
    ],
  },
  {
    id: 5,
    title: "Phase 5 · 架构师进阶",
    duration: "第 21-24 周",
    color: "#E03131",
    sections: [
      {
        title: "📚 架构设计学习",
        items: [
          {
            name: "《Designing Data-Intensive Applications》— Martin Kleppmann",
            tag: "经典书籍",
            desc: "分布式系统圣经，理解可靠性、可扩展性、可维护性的核心原则。Agent 平台架构的理论基础",
          },
          {
            name: "《LLM Engineer's Handbook》",
            tag: "推荐书籍",
            desc: "LLM 工程实战手册，覆盖从训练到部署的全链路工程实践",
          },
          {
            name: "Johns Hopkins — Agentic AI Certificate Program",
            url: "https://online.lifelonglearning.jhu.edu/jhu-certificate-program-agentic-ai",
            tag: "认证项目",
            desc: "16 周在线认证，覆盖推理模型、多 Agent 系统、强化学习等高级主题",
          },
        ],
      },
      {
        title: "📖 开源项目源码研读",
        items: [
          {
            name: "Dify — 开源 LLM 应用开发平台",
            url: "https://github.com/langgenius/dify",
            tag: "必读源码",
            desc: "学习工作流编排引擎、RAG Pipeline、多模型管理、多租户架构的设计",
          },
          {
            name: "RAGFlow — 企业级 RAG 引擎",
            url: "https://github.com/infiniflow/ragflow",
            tag: "推荐源码",
            desc: "深度文档理解、智能分块、GraphRAG 实现，学习生产级 RAG 系统设计",
          },
          {
            name: "ChatDev — 多 Agent 软件开发模拟",
            url: "https://github.com/OpenBMB/ChatDev",
            tag: "参考源码",
            desc: "模拟软件公司的多 Agent 协作开发，学习角色分工和通信协议设计",
          },
          {
            name: "MetaGPT — 多 Agent 框架",
            url: "https://github.com/geekan/MetaGPT",
            tag: "参考源码",
            desc: "标准化 SOP 驱动的多 Agent 协作，学习工程化的 Agent 系统设计",
          },
        ],
      },
      {
        title: "🏛️ 架构师核心能力专项",
        items: [
          {
            name: "可靠性设计",
            tag: "能力项",
            desc: "重试策略、回退机制、熔断器模式、幂等性设计。参考：AWS Well-Architected Framework",
          },
          {
            name: "成本工程",
            tag: "能力项",
            desc: "Token 预算管理、模型路由（大小模型混用）、语义缓存、Prompt 压缩",
          },
          {
            name: "安全架构",
            tag: "能力项",
            desc: "Prompt 注入防护、输出过滤（Guardrails）、数据隔离、审计日志、合规性",
          },
          {
            name: "可观测性",
            tag: "能力项",
            desc: "LangSmith Tracing、自定义 Metrics、Evaluation Pipeline、A/B 测试框架",
          },
        ],
      },
      {
        title: "🔨 毕业项目",
        items: [
          {
            name: "🎓 企业 AI Agent 平台（综合项目）",
            tag: "约 40-60 小时",
            desc: "多租户 Agent 运行平台：含可视化工作流编排、RAG 知识库、多 Agent 协作、MCP 工具集成、监控大盘、评估系统。完成后开源到 GitHub 并写系列技术博客",
          },
        ],
      },
    ],
  },
];

const BONUS = [
  {
    title: "🌐 持续跟进的社区 & 信息源",
    items: [
      "Twitter/X 关注：@AndrewYNg @LangChainAI @llaboratory @CrewAIInc",
      "Reddit: r/AI_Agents、r/LangChain、r/LocalLLaMA",
      "Discord: LangChain、LlamaIndex、CrewAI 官方社区",
      "Newsletter: The Batch (DeepLearning.AI)、AI Engineering Weekly",
      "GitHub: 关注 LangGraph / CrewAI / Dify 的 Release Notes",
    ],
  },
  {
    title: "💼 求职 & 个人品牌建设",
    items: [
      "GitHub：保持绿点，所有实战项目开源并写好 README",
      "技术博客：每两周一篇，记录学习和项目心得（推荐 Medium / 掘金）",
      "开源贡献：给 LangChain / CrewAI / Dify 提 PR，从文档和测试开始",
      "技术分享：在公司内部或社区做 Agent 开发相关的 Tech Talk",
    ],
  },
];

export default function DetailedResources() {
  const [activePhase, setActivePhase] = useState(0);
  const [expandedSections, setExpandedSections] = useState({});

  const toggleSection = (key) => {
    setExpandedSections((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const phase = PHASES[activePhase];

  return (
    <div
      style={{
        fontFamily:
          "'Noto Sans SC', 'Noto Sans JP', -apple-system, BlinkMacSystemFont, system-ui, sans-serif",
        background: "#0B0D11",
        color: "#E4E4E7",
        minHeight: "100vh",
      }}
    >
      {/* Header */}
      <div
        style={{
          background: "linear-gradient(160deg, #0f172a 0%, #1e1b4b 60%, #312e81 100%)",
          padding: "28px 20px 20px",
          borderBottom: "1px solid rgba(99,102,241,0.15)",
        }}
      >
        <div style={{ maxWidth: 840, margin: "0 auto" }}>
          <div
            style={{
              fontSize: 10,
              letterSpacing: 2.5,
              textTransform: "uppercase",
              color: "#A5B4FC",
              fontWeight: 700,
              marginBottom: 6,
            }}
          >
            详细资源清单 · 2026 年 4 月更新
          </div>
          <h1
            style={{
              fontSize: 24,
              fontWeight: 800,
              margin: 0,
              color: "#E0E7FF",
              lineHeight: 1.3,
            }}
          >
            AI Agent 开发工程师 · 全阶段学习资料
          </h1>
          <p style={{ fontSize: 13, color: "#818CF8", margin: "6px 0 0" }}>
            课程 · 论文 · 书籍 · 文档 · 开源项目 · 实战项目 — 全部按阶段整理
          </p>
        </div>
      </div>

      <div style={{ maxWidth: 840, margin: "0 auto", padding: "16px 16px 40px" }}>
        {/* Phase Tabs */}
        <div
          style={{
            display: "flex",
            gap: 4,
            overflowX: "auto",
            padding: "0 0 14px",
            WebkitOverflowScrolling: "touch",
          }}
        >
          {PHASES.map((p, i) => (
            <button
              key={p.id}
              onClick={() => {
                setActivePhase(i);
                setExpandedSections({});
              }}
              style={{
                flex: "none",
                padding: "8px 12px",
                borderRadius: 8,
                border:
                  activePhase === i
                    ? `2px solid ${p.color}`
                    : "2px solid transparent",
                background:
                  activePhase === i ? `${p.color}15` : "#161821",
                color: activePhase === i ? p.color : "#71717A",
                cursor: "pointer",
                fontSize: 12,
                fontWeight: activePhase === i ? 700 : 500,
                whiteSpace: "nowrap",
                transition: "all 0.15s",
              }}
            >
              P{p.id}{" "}
              <span style={{ opacity: 0.7, fontSize: 10 }}>
                {p.duration}
              </span>
            </button>
          ))}
        </div>

        {/* Phase Title */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 10,
            marginBottom: 14,
            padding: "12px 16px",
            background: `${phase.color}0A`,
            borderRadius: 10,
            borderLeft: `3px solid ${phase.color}`,
          }}
        >
          <div>
            <h2
              style={{
                fontSize: 20,
                fontWeight: 800,
                margin: 0,
                color: "#F4F4F5",
              }}
            >
              {phase.title}
            </h2>
            <span
              style={{ fontSize: 12, color: phase.color, fontWeight: 600 }}
            >
              {phase.duration}
            </span>
          </div>
        </div>

        {/* Sections */}
        {phase.sections.map((section, si) => {
          const key = `${activePhase}-${si}`;
          const isOpen = expandedSections[key] !== false;
          return (
            <div
              key={key}
              style={{
                background: "#14161D",
                borderRadius: 12,
                marginBottom: 10,
                border: "1px solid #1E2030",
                overflow: "hidden",
              }}
            >
              <button
                onClick={() => toggleSection(key)}
                style={{
                  width: "100%",
                  padding: "14px 16px",
                  background: "none",
                  border: "none",
                  color: "#E4E4E7",
                  cursor: "pointer",
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  fontSize: 15,
                  fontWeight: 700,
                  textAlign: "left",
                }}
              >
                <span>{section.title}</span>
                <span
                  style={{
                    fontSize: 11,
                    color: "#52525B",
                    transform: isOpen ? "rotate(180deg)" : "rotate(0)",
                    transition: "transform 0.2s",
                  }}
                >
                  ▼
                </span>
              </button>

              {isOpen && (
                <div style={{ padding: "0 14px 14px" }}>
                  {section.items.map((item, ii) => (
                    <div
                      key={ii}
                      style={{
                        background: "#1A1D28",
                        borderRadius: 8,
                        padding: "12px 14px",
                        marginBottom: ii < section.items.length - 1 ? 8 : 0,
                        border: "1px solid #252836",
                      }}
                    >
                      <div
                        style={{
                          display: "flex",
                          alignItems: "flex-start",
                          justifyContent: "space-between",
                          gap: 8,
                          flexWrap: "wrap",
                        }}
                      >
                        <div style={{ flex: 1, minWidth: 200 }}>
                          {item.url ? (
                            <a
                              href={item.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              style={{
                                fontSize: 14,
                                fontWeight: 700,
                                color: "#C7D2FE",
                                textDecoration: "none",
                                lineHeight: 1.4,
                              }}
                              onMouseOver={(e) =>
                                (e.target.style.textDecoration = "underline")
                              }
                              onMouseOut={(e) =>
                                (e.target.style.textDecoration = "none")
                              }
                            >
                              {item.name} ↗
                            </a>
                          ) : (
                            <div
                              style={{
                                fontSize: 14,
                                fontWeight: 700,
                                color: "#D4D4D8",
                                lineHeight: 1.4,
                              }}
                            >
                              {item.name}
                            </div>
                          )}
                        </div>
                        {item.tag && (
                          <span
                            style={{
                              fontSize: 10,
                              fontWeight: 700,
                              padding: "3px 8px",
                              borderRadius: 4,
                              background: `${phase.color}20`,
                              color: phase.color,
                              whiteSpace: "nowrap",
                              flexShrink: 0,
                            }}
                          >
                            {item.tag}
                          </span>
                        )}
                      </div>
                      <p
                        style={{
                          fontSize: 12.5,
                          color: "#9CA3AF",
                          margin: "6px 0 0",
                          lineHeight: 1.6,
                        }}
                      >
                        {item.desc}
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          );
        })}

        {/* Bonus Section - only show after last phase */}
        {activePhase === PHASES.length - 1 && (
          <div style={{ marginTop: 20 }}>
            {BONUS.map((b, bi) => (
              <div
                key={bi}
                style={{
                  background: "#14161D",
                  borderRadius: 12,
                  padding: "16px 18px",
                  marginBottom: 10,
                  border: "1px solid #1E2030",
                }}
              >
                <h3
                  style={{
                    fontSize: 15,
                    fontWeight: 700,
                    margin: "0 0 10px",
                    color: "#E4E4E7",
                  }}
                >
                  {b.title}
                </h3>
                {b.items.map((item, ii) => (
                  <div
                    key={ii}
                    style={{
                      fontSize: 13,
                      color: "#A1A1AA",
                      padding: "4px 0",
                      paddingLeft: 12,
                      borderLeft: "2px solid #312E81",
                      marginBottom: 6,
                      lineHeight: 1.5,
                    }}
                  >
                    {item}
                  </div>
                ))}
              </div>
            ))}
          </div>
        )}

        {/* Navigation hint */}
        <div
          style={{
            marginTop: 16,
            textAlign: "center",
            fontSize: 12,
            color: "#52525B",
          }}
        >
          点击顶部 P1-P5 切换阶段 · 点击各分类标题展开/收起
        </div>
      </div>
    </div>
  );
}
