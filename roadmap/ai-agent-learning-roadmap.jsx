import { useState } from "react";

const PHASES = [
  {
    id: 1,
    title: "基石构建",
    subtitle: "Foundation",
    duration: "第 1-4 周",
    color: "#E8590C",
    accent: "#FFF4E6",
    icon: "🧱",
    goals: "掌握 LLM 核心原理、Prompt Engineering 和基础开发框架",
    modules: [
      {
        name: "LLM 原理与 Prompt 工程",
        hours: "~12h",
        items: [
          "Transformer 架构核心概念（Attention、Tokenization）",
          "Prompt Engineering 系统化方法论（CoT / Few-shot / ReAct）",
          "温度、Top-P 等参数对输出的影响",
          "OpenAI / Anthropic / 开源模型 API 对比实践",
        ],
        project: "🔨 实战：构建一个多模型切换的智能问答 CLI 工具",
      },
      {
        name: "Python 异步编程与工程化",
        hours: "~8h",
        items: [
          "asyncio / aiohttp 异步编程模式",
          "Pydantic 数据验证与类型安全",
          "Poetry / UV 项目管理与依赖管理",
          "日志、配置管理、错误处理最佳实践",
        ],
        project: "🔨 实战：搭建一个结构良好的 AI 项目脚手架模板",
      },
    ],
    resources: [
      { type: "课程", name: "DeepLearning.AI - ChatGPT Prompt Engineering" },
      { type: "文档", name: "Anthropic Prompt Engineering Guide" },
      { type: "书籍", name: "《Build a Large Language Model from Scratch》" },
    ],
  },
  {
    id: 2,
    title: "Agent 核心能力",
    subtitle: "Core Agent Skills",
    duration: "第 5-10 周",
    color: "#1971C2",
    accent: "#E7F5FF",
    icon: "🤖",
    goals: "深入理解 Agent 架构，掌握 LangChain / LlamaIndex 核心框架",
    modules: [
      {
        name: "Agent 架构模式深入",
        hours: "~15h",
        items: [
          "ReAct / Plan-and-Execute / Reflection 模式",
          "Function Calling 与 Tool Use 机制",
          "Agent 记忆系统（短期 / 长期 / 工作记忆）",
          "Agent 决策循环与状态管理",
        ],
        project: "🔨 实战：构建一个能搜索网页、读写文件、执行代码的个人助手 Agent",
      },
      {
        name: "LangChain / LangGraph 实战",
        hours: "~15h",
        items: [
          "LangChain Expression Language (LCEL) 编排",
          "LangGraph 状态图与条件路由",
          "自定义 Tool / Retriever / Memory 开发",
          "LangSmith 可观测性与调试",
        ],
        project: "🔨 实战：用 LangGraph 构建一个多步骤任务执行 Agent（如自动化调研报告生成）",
      },
    ],
    resources: [
      { type: "课程", name: "DeepLearning.AI - AI Agents in LangGraph" },
      { type: "官方", name: "LangChain / LangGraph 官方文档" },
      { type: "论文", name: "ReAct / Reflexion / LATS 论文精读" },
    ],
  },
  {
    id: 3,
    title: "RAG 与知识系统",
    subtitle: "Knowledge Engineering",
    duration: "第 11-16 周",
    color: "#2F9E44",
    accent: "#EBFBEE",
    icon: "📚",
    goals: "构建生产级 RAG 系统，掌握向量数据库与检索优化",
    modules: [
      {
        name: "RAG 架构与高级检索",
        hours: "~15h",
        items: [
          "文档解析：PDF / HTML / 表格 / 图片的结构化提取",
          "Chunking 策略：语义分块、递归分块、上下文感知分块",
          "Embedding 模型选型与微调（BGE / Cohere / OpenAI）",
          "向量数据库实战（Milvus / Qdrant / Weaviate）",
        ],
        project: "🔨 实战：为一个真实的技术文档库构建语义搜索系统",
      },
      {
        name: "高级 RAG 模式",
        hours: "~12h",
        items: [
          "Multi-Query / HyDE / Step-back 查询改写",
          "混合检索（向量 + BM25 + 知识图谱）",
          "Re-ranking 与 Contextual Compression",
          "RAG 评估体系（Ragas / DeepEval 框架）",
        ],
        project: "🔨 实战：企业级知识库问答系统（含权限控制与引用溯源）",
      },
    ],
    resources: [
      { type: "课程", name: "DeepLearning.AI - Building & Evaluating Advanced RAG" },
      { type: "博客", name: "LlamaIndex RAG 高级教程系列" },
      { type: "项目", name: "参考 Verba / RAGFlow 开源项目" },
    ],
  },
  {
    id: 4,
    title: "多 Agent 与编排",
    subtitle: "Multi-Agent Orchestration",
    duration: "第 17-20 周",
    color: "#9C36B5",
    accent: "#F8F0FC",
    icon: "🎭",
    goals: "掌握多 Agent 协作模式、MCP 协议与企业级编排方案",
    modules: [
      {
        name: "多 Agent 协作模式",
        hours: "~12h",
        items: [
          "Supervisor / Hierarchical / Debate 协作模式",
          "CrewAI / AutoGen 框架对比实战",
          "Agent 间通信协议与任务分解策略",
          "冲突解决、共识机制与质量把关",
        ],
        project: "🔨 实战：构建一个 3-Agent 协作的内容生产流水线（研究→写作→审核）",
      },
      {
        name: "MCP 协议与工具集成",
        hours: "~10h",
        items: [
          "MCP（Model Context Protocol）协议深度解读",
          "自定义 MCP Server 开发（TypeScript / Python）",
          "Agent 与外部系统集成（数据库 / API / SaaS）",
          "工具编排、权限控制与安全沙箱",
        ],
        project: "🔨 实战：开发一套 MCP Server 生态（GitHub + 数据库 + 日历）",
      },
    ],
    resources: [
      { type: "官方", name: "Anthropic MCP 官方文档与 SDK" },
      { type: "框架", name: "CrewAI / AutoGen / LangGraph Multi-Agent 文档" },
      { type: "案例", name: "研读 ChatDev / MetaGPT 源码" },
    ],
  },
  {
    id: 5,
    title: "架构师进阶",
    subtitle: "Architect Level-Up",
    duration: "第 21-24 周",
    color: "#E03131",
    accent: "#FFF5F5",
    icon: "🏛️",
    goals: "具备企业级 Agent 系统设计能力，成为技术架构决策者",
    modules: [
      {
        name: "企业级 Agent 架构设计",
        hours: "~12h",
        items: [
          "Agent 系统的可靠性设计（重试 / 回退 / 熔断）",
          "成本控制：Token 预算管理、模型路由、缓存策略",
          "安全架构：Prompt 注入防护、输出过滤、审计日志",
          "可观测性：Tracing / Metrics / Evaluation Pipeline",
        ],
        project: "🔨 实战：为团队设计一个完整的 Agent Platform 架构方案",
      },
      {
        name: "综合项目：端到端 Agent 平台",
        hours: "~20h",
        items: [
          "设计多租户 Agent 运行平台架构",
          "实现 Agent 工作流编排引擎（可视化 DAG）",
          "集成 RAG 知识库 + 多工具 + 多 Agent",
          "部署、监控、评估全链路打通",
        ],
        project:
          "🔨 毕业项目：构建一个完整的企业 AI Agent 平台（含管理后台、Agent 编排、知识库、监控大盘）",
      },
    ],
    resources: [
      { type: "架构", name: "研读 Dify / Coze / FastGPT 架构设计" },
      { type: "书籍", name: "《Designing Data-Intensive Applications》" },
      { type: "社区", name: "参与 LangChain / LlamaIndex 开源贡献" },
    ],
  },
];

const WEEKLY_PLAN = {
  title: "每周节奏建议（1-2h/天）",
  days: [
    { day: "周一~周三", task: "理论学习 + 文档阅读", icon: "📖" },
    { day: "周四~周五", task: "动手编码 + 项目实战", icon: "💻" },
    { day: "周六", task: "复盘总结 + 写技术博客", icon: "✍️" },
    { day: "周日", task: "开源项目阅读 / 社区交流", icon: "🌐" },
  ],
};

const ARCHITECT_SKILLS = [
  { name: "系统设计", desc: "高可用、可扩展、容错性", icon: "🏗️" },
  { name: "技术选型", desc: "框架对比、Trade-off 分析", icon: "⚖️" },
  { name: "成本意识", desc: "Token 经济学、资源优化", icon: "💰" },
  { name: "安全思维", desc: "注入防护、数据隔离", icon: "🛡️" },
  { name: "沟通领导", desc: "架构评审、技术布道", icon: "📢" },
  { name: "全局视野", desc: "行业趋势、生态整合", icon: "🔭" },
];

export default function LearningRoadmap() {
  const [activePhase, setActivePhase] = useState(0);
  const [expandedModule, setExpandedModule] = useState(null);

  const phase = PHASES[activePhase];

  return (
    <div
      style={{
        fontFamily: "'Noto Sans SC', 'Noto Sans JP', system-ui, sans-serif",
        background: "#0F1117",
        color: "#E4E4E7",
        minHeight: "100vh",
        padding: "0",
      }}
    >
      {/* Header */}
      <div
        style={{
          background: "linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%)",
          padding: "32px 24px 24px",
          borderBottom: "1px solid rgba(255,255,255,0.06)",
        }}
      >
        <div style={{ maxWidth: 800, margin: "0 auto" }}>
          <div
            style={{
              fontSize: 11,
              letterSpacing: 3,
              textTransform: "uppercase",
              color: "#818CF8",
              marginBottom: 8,
              fontWeight: 600,
            }}
          >
            AI Agent 高级开发工程师 · 学习路线图
          </div>
          <h1
            style={{
              fontSize: 28,
              fontWeight: 800,
              margin: 0,
              background: "linear-gradient(135deg, #C7D2FE, #818CF8, #6366F1)",
              WebkitBackgroundClip: "text",
              WebkitTextFillColor: "transparent",
              lineHeight: 1.3,
            }}
          >
            从中级开发者到 Agent 架构师
          </h1>
          <p style={{ color: "#9CA3AF", fontSize: 14, margin: "8px 0 0", lineHeight: 1.6 }}>
            6 个月 · 每天 1-2 小时 · 5 个阶段 · 理论 + 实战项目驱动
          </p>
        </div>
      </div>

      <div style={{ maxWidth: 800, margin: "0 auto", padding: "20px 16px 40px" }}>
        {/* Phase Navigator */}
        <div
          style={{
            display: "flex",
            gap: 6,
            overflowX: "auto",
            padding: "4px 0 16px",
            WebkitOverflowScrolling: "touch",
          }}
        >
          {PHASES.map((p, i) => (
            <button
              key={p.id}
              onClick={() => {
                setActivePhase(i);
                setExpandedModule(null);
              }}
              style={{
                flex: "none",
                padding: "10px 14px",
                borderRadius: 10,
                border: activePhase === i ? `2px solid ${p.color}` : "2px solid transparent",
                background: activePhase === i ? `${p.color}18` : "#1C1C24",
                color: activePhase === i ? p.color : "#9CA3AF",
                cursor: "pointer",
                fontSize: 13,
                fontWeight: activePhase === i ? 700 : 500,
                whiteSpace: "nowrap",
                transition: "all 0.2s",
              }}
            >
              <span style={{ marginRight: 4 }}>{p.icon}</span>
              P{p.id}
              <span style={{ display: "block", fontSize: 10, opacity: 0.7, marginTop: 2 }}>
                {p.duration}
              </span>
            </button>
          ))}
        </div>

        {/* Active Phase Detail */}
        <div
          style={{
            background: "#1C1C24",
            borderRadius: 16,
            border: `1px solid ${phase.color}30`,
            overflow: "hidden",
            marginBottom: 20,
          }}
        >
          {/* Phase Header */}
          <div
            style={{
              padding: "20px 24px",
              borderBottom: `1px solid ${phase.color}20`,
              background: `linear-gradient(135deg, ${phase.color}10, transparent)`,
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 8 }}>
              <span style={{ fontSize: 28 }}>{phase.icon}</span>
              <div>
                <div style={{ fontSize: 10, color: phase.color, fontWeight: 600, letterSpacing: 1.5 }}>
                  PHASE {phase.id} · {phase.duration.toUpperCase()}
                </div>
                <h2 style={{ fontSize: 22, fontWeight: 800, margin: "2px 0 0", color: "#F4F4F5" }}>
                  {phase.title}
                  <span style={{ fontSize: 14, fontWeight: 400, color: "#71717A", marginLeft: 8 }}>
                    {phase.subtitle}
                  </span>
                </h2>
              </div>
            </div>
            <p style={{ fontSize: 14, color: "#A1A1AA", margin: 0, lineHeight: 1.6 }}>
              🎯 {phase.goals}
            </p>
          </div>

          {/* Modules */}
          <div style={{ padding: "16px 20px" }}>
            {phase.modules.map((mod, mi) => {
              const isExpanded = expandedModule === mi;
              return (
                <div
                  key={mi}
                  style={{
                    background: isExpanded ? "#25252F" : "#22222B",
                    borderRadius: 12,
                    marginBottom: mi < phase.modules.length - 1 ? 10 : 0,
                    border: isExpanded ? `1px solid ${phase.color}40` : "1px solid #2E2E38",
                    overflow: "hidden",
                    transition: "all 0.2s",
                  }}
                >
                  <button
                    onClick={() => setExpandedModule(isExpanded ? null : mi)}
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
                      fontWeight: 600,
                      textAlign: "left",
                    }}
                  >
                    <span>
                      <span style={{ color: phase.color, marginRight: 8 }}>▸</span>
                      {mod.name}
                    </span>
                    <span
                      style={{
                        fontSize: 11,
                        color: "#71717A",
                        background: "#2E2E38",
                        padding: "3px 10px",
                        borderRadius: 20,
                      }}
                    >
                      {mod.hours}
                    </span>
                  </button>

                  {isExpanded && (
                    <div style={{ padding: "0 16px 16px" }}>
                      {/* Learning Items */}
                      <div style={{ marginBottom: 14 }}>
                        {mod.items.map((item, ii) => (
                          <div
                            key={ii}
                            style={{
                              display: "flex",
                              alignItems: "flex-start",
                              gap: 10,
                              padding: "6px 0",
                              fontSize: 13,
                              color: "#D4D4D8",
                              lineHeight: 1.5,
                            }}
                          >
                            <span
                              style={{
                                width: 6,
                                height: 6,
                                borderRadius: "50%",
                                background: phase.color,
                                marginTop: 6,
                                flexShrink: 0,
                              }}
                            />
                            {item}
                          </div>
                        ))}
                      </div>
                      {/* Project */}
                      <div
                        style={{
                          background: `${phase.color}12`,
                          border: `1px solid ${phase.color}25`,
                          borderRadius: 8,
                          padding: "10px 14px",
                          fontSize: 13,
                          color: phase.color,
                          fontWeight: 600,
                          lineHeight: 1.5,
                        }}
                      >
                        {mod.project}
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {/* Resources */}
          <div
            style={{
              padding: "14px 20px 18px",
              borderTop: "1px solid #2E2E38",
            }}
          >
            <div style={{ fontSize: 12, fontWeight: 600, color: "#71717A", marginBottom: 8 }}>
              📎 推荐资源
            </div>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
              {phase.resources.map((r, ri) => (
                <span
                  key={ri}
                  style={{
                    fontSize: 12,
                    padding: "5px 10px",
                    borderRadius: 6,
                    background: "#25252F",
                    color: "#A1A1AA",
                    border: "1px solid #2E2E38",
                  }}
                >
                  <span style={{ color: phase.color, fontWeight: 600, marginRight: 4 }}>
                    {r.type}
                  </span>
                  {r.name}
                </span>
              ))}
            </div>
          </div>
        </div>

        {/* Architect Skills */}
        <div
          style={{
            background: "#1C1C24",
            borderRadius: 16,
            padding: "20px",
            marginBottom: 20,
            border: "1px solid #2E2E38",
          }}
        >
          <h3 style={{ fontSize: 16, fontWeight: 700, margin: "0 0 14px", color: "#F4F4F5" }}>
            🏛️ 架构师核心能力模型
          </h3>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))",
              gap: 10,
            }}
          >
            {ARCHITECT_SKILLS.map((s, i) => (
              <div
                key={i}
                style={{
                  background: "#25252F",
                  borderRadius: 10,
                  padding: "12px 14px",
                  border: "1px solid #2E2E38",
                }}
              >
                <div style={{ fontSize: 20, marginBottom: 4 }}>{s.icon}</div>
                <div style={{ fontSize: 14, fontWeight: 700, color: "#E4E4E7" }}>{s.name}</div>
                <div style={{ fontSize: 12, color: "#71717A", marginTop: 2 }}>{s.desc}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Weekly Rhythm */}
        <div
          style={{
            background: "#1C1C24",
            borderRadius: 16,
            padding: "20px",
            border: "1px solid #2E2E38",
          }}
        >
          <h3 style={{ fontSize: 16, fontWeight: 700, margin: "0 0 14px", color: "#F4F4F5" }}>
            📅 {WEEKLY_PLAN.title}
          </h3>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(160px, 1fr))", gap: 10 }}>
            {WEEKLY_PLAN.days.map((d, i) => (
              <div
                key={i}
                style={{
                  background: "#25252F",
                  borderRadius: 10,
                  padding: "12px 14px",
                  border: "1px solid #2E2E38",
                }}
              >
                <div style={{ fontSize: 18, marginBottom: 4 }}>{d.icon}</div>
                <div style={{ fontSize: 13, fontWeight: 700, color: "#C7D2FE" }}>{d.day}</div>
                <div style={{ fontSize: 12, color: "#A1A1AA", marginTop: 2, lineHeight: 1.4 }}>
                  {d.task}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Footer Tips */}
        <div
          style={{
            marginTop: 20,
            padding: "16px 20px",
            background: "linear-gradient(135deg, #1e1b4b20, #312e8120)",
            border: "1px solid #4338CA30",
            borderRadius: 12,
            fontSize: 13,
            color: "#A5B4FC",
            lineHeight: 1.7,
          }}
        >
          <strong style={{ color: "#C7D2FE" }}>💡 关键建议：</strong>
          每个阶段的实战项目都要认真做并开源到 GitHub，这是你最好的能力证明。
          学习过程中坚持写技术博客，既是复盘也是个人品牌建设。
          多读优秀开源项目源码（Dify / LangGraph / CrewAI），比看教程更有效。
        </div>
      </div>
    </div>
  );
}
