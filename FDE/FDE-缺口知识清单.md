# FDE 能力缺口 · 知识清单

> **用途**：列出从「AI Agent 学习者」走向 **FDE（Forward Deployed Engineer）** 还需要补的知识，作为后续逐周并行计划的输入。
> **创建日期**：2026-06-17
> **配套文档**：
> - 目标与时间线 → [`../FDE-Learning.md`](../FDE-Learning.md)（主目标 Anthropic Applied AI FDE，+ OpenAI 并行）
> - 生产化四条横切线 → [`../roadmap/AI-Agent-架构师专项路线图.md`](../roadmap/AI-Agent-架构师专项路线图.md)
> - 现状诊断 → [`../notes/weekly-reviews/`](../notes/weekly-reviews/)（输入过载、9 个项目 0 进度、无上线代码）

---

## 核心判断

> **你的 AI/LLM 知识层已经很全**（Prompt → RAG → Agent → LangGraph → Memory → Multi-Agent → Eval → Testing 都学过）。
> FDE 的缺口**几乎全在 AI 之外**——在「把知识变成**上线系统** + **客户交付** + **面试**」这三件事上。
> 所以本清单**刻意跳过已掌握的 AI 原理**，只列真正的缺口。

**图例**：🔴 核心缺口（必补） · 🟡 进阶/加分 · 🟢 已懂原理（只需"工程化"复用）
**标签**：`[共同]` 两家都要 · `[A]` Anthropic 特化 · `[P]` Palantir 特化

---

## 模块 1 · 软件工程与生产化 `[共同]` —— 最大缺口
把 notebook / demo 变成"能上线、能被别人用"的系统。

| 知识点 | 级别 |
|---|---|
| 后端服务：REST API 设计、FastAPI、async/并发、分层结构 | 🔴 |
| 数据持久化：PostgreSQL、表设计、索引、migration（Alembic）、SQL 进阶（join/窗口函数） | 🔴 |
| 外部集成：调不稳定/无文档 API、重试退避、限流、超时、幂等 | 🔴 |
| 容器与部署：Docker、一种云（AWS 优先：Lambda/S3/RDS/EC2 基础）、secrets 管理 | 🔴 |
| CI/CD：GitHub Actions（自动测试 + 自动部署） | 🔴 |
| 测试工程：pytest、单元/集成测试、mock LLM、回归 | 🟢 课程 24 有，需落到项目 |
| Git/协作进阶：分支、PR、code review、commit 规范 | 🟡 刚起步 |

## 模块 2 · 数据工程 `[P 重 / A 轻]`

| 知识点 | 级别 |
|---|---|
| SQL 深度 + 查询优化 | 🔴 两家都用 |
| ETL / 数据管道：batch vs streaming、调度（Airflow/Dagster 概念） | 🟡 |
| 脏数据 / 大规模数据处理：pandas / polars、清洗 | 🟡 |
| 数据建模与本体（Ontology） | 🔴 `[P]` |
| Foundry / AIP 平台范式：Pipeline Builder、Workshop、Ontology | 🔴 `[P]` |

> 📘 这两项 `[P]` 的详细学习内容、资源与分阶段计划 → [`Palantir-Foundry-Ontology-学习总纲.md`](./Palantir-Foundry-Ontology-学习总纲.md)（含配套一手资料精读）

## 模块 3 · LLM 应用"生产化" `[共同]` —— 懂原理，缺工程落地
原理已学过（🟢），缺的是把它**做成可靠上线的工程**（这四条正好是架构师路线图的四条横切线）：

| 知识点 | 级别 |
|---|---|
| MCP server 实战：写真实 `@tool`、部署、鉴权 | 🔴 `[A]` JD 直接要求 |
| Agent 可靠性：工具失败恢复、超时、幂等、降级 | 🔴 |
| Eval 工程化（线①）：golden dataset≥50、LLM-as-Judge、回归进 CI | 🔴 |
| 成本工程（线②）：token 计量、prompt caching、模型路由、预算告警 | 🔴 |
| 安全（线③）：OWASP LLM Top10、prompt injection 防御、guardrails、PII、红队 | 🔴 |
| 可观测性（线④）：tracing/span、TTFT/工具成功率、反馈回流 | 🔴 |
| Prompt 版本管理 / A-B | 🟡 |

## 模块 4 · 客户面 / 咨询 / 沟通 `[共同]` —— 最难自学，FDE 的灵魂

| 知识点 | 级别 |
|---|---|
| 需求挖掘：模糊业务问题 → 技术方案 | 🔴 |
| 问题分解：结构化拆解（Palantir 有专门白板轮） | 🔴 P 特别重 |
| 技术写作：设计文档 / RFC、向非技术人讲清方案 | 🔴 |
| 范围管理：敢说"不"、里程碑、预期管理 | 🟡 |
| Post-sales / 交付后持续支持经验 | 🔴 `[A]` JD 字面 |
| Demo / 演示能力 | 🟡 |

## 模块 5 · 面试专项 `[employer-specific]`

| 知识点 | 级别 |
|---|---|
| `[A]` CodeSignal 90 分钟 4 阶段（偏工程实现，非纯算法） | 🔴 |
| `[P]` DSA 白板：图/堆/哈希/树 + Problem Decomposition + 陌生代码库速上手 | 🔴 |
| LLM 系统设计 | 🔴 共同 |
| `[A]` Values round：读 RSP / Core Views / Constitutional AI，备真实道德张力故事，**不预演 STAR** | 🔴 Anthropic 最大 reject 点 |
| `[P]` Mission alignment："why Palantir"、战略思维 | 🔴 |
| 两道硬筛题能答 Yes："shipped in production?" / "post-sales experience?" | 🔴 |

## 模块 6 · 垂直领域 & 可见度 `[A 加分]` —— 是"产出"不是"学"

| 项 | 级别 |
|---|---|
| 金融/加密/量化 vertical（Argus 正好命中） | 🟡 `[A]` plus |
| 端到端上线作品（Argus）、开源、技术博客、简历/LinkedIn | 🔴 博客已逾期 |

---

## 怎么读这份清单

- 真正要"啃新知识"的，集中在 **模块 1（软件工程）** 和 **模块 2（数据工程）**——课程里完全没碰。
- **模块 3** 几乎全是 🟢→🔴 的"原理已会、工程未做"，靠**做项目**补，不靠看课。
- **模块 4 / 5** 靠**练 + 实战**，不靠学。
- `[P]` 和 `[A]` 标签就是雇主分叉：
  - 选 **Palantir** → 多背模块 2 的 Foundry/DSA；
  - 选 **Anthropic** → 主攻模块 3 的 MCP + 模块 5 的 Values round。
  - **共同核心**（模块 1、3、4 大部分）无论选哪家都要补。

---

## 下一步（待办）

- [ ] 选定雇主分叉（Anthropic 为主 / Palantir 为主 / 先做共同内核）
- [ ] 把本清单排成**逐周并行计划**，对齐现有 24 周路线 + Argus
- [ ] 给每个 🔴 配学习资源 + 落地到具体项目
