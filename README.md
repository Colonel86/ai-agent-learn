# AI Agent 学习之路

> 目标：从中级开发者成长为 AI Agent 高级开发工程师 + 架构师  
> 周期：6 个月（24 周）· 每天 1-2 小时

## 目录结构

```
ai-agent-learn/
├── roadmap/                          # 学习路线图
│   ├── AI-Agent-学习路线图-完整版.md  # 完整 24 周学习计划
│   └── *.jsx                         # 路线图可视化组件
├── notes/                            # 学习笔记
│   └── cowork-learning-strategy.md  # Cowork 辅助学习方案
├── projects/                         # 实战项目代码
├── skills/                           # 自定义 Skill
│   └── study-session/                # 学习会话助手 Skill
└── AI-Agent-学习追踪表.xlsx           # 学习进度追踪表
```

## 学习路线

| 阶段 | 周数 | 主题 |
|------|------|------|
| Phase 1 | 1-4 | 基石构建：LLM 原理 + Prompt Engineering + API |
| Phase 2 | 5-10 | Agent 核心：LangChain + LangGraph |
| Phase 3 | 11-16 | RAG 与知识系统 |
| Phase 4 | 17-20 | 多 Agent + MCP 编排 |
| Phase 5 | 21-24 | 架构师进阶 + 毕业项目 |

## 实战项目

1. 多模型智能问答 CLI
2. Prompt 模板管理系统
3. 个人助手 Agent（LangGraph）
4. 自动化调研报告 Agent
5. 技术文档语义搜索引擎
6. 企业知识库问答系统
7. 3-Agent 内容生产流水线
8. MCP Server 生态开发
9. 企业 AI Agent 平台（毕业项目）

## 技术栈

- **LLM API**: OpenAI, Anthropic Claude
- **Agent 框架**: LangChain, LangGraph, CrewAI, AutoGen
- **RAG**: LlamaIndex, Qdrant, ChromaDB, RAGAS
- **协议**: MCP (Model Context Protocol)
- **工具**: LangSmith, Pydantic, UV

## 开始日期

2026 年 4 月

---

> GitHub: [@Colonel86](https://github.com/Colonel86)


- "你们线上 token 成本多少？做了什么优化，降了多少？"
- "trace 落库后你真的用它排查过什么问题？讲一个。"
- "eval 集怎么建的？多少 case？发现过什么 regression？"

主干（不变，甚至更重要了）：把 Argus 推到生产。 妙处在于它的每一步都直接命中这份 JD：

- 给它加 MCP server → JD 加分项①，字面命中
- 给它建 eval framework（用 DeepEval/Promptfoo）→ JD 加分项②，字面命中
- 接 trace 落库 + 成本追踪 → JD 职责 3
- 加 retry/fallback/预算硬限 → JD 职责 4