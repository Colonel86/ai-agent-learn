# AI Agent 架构师 · 专项路线图

> **定位**：与《AI-Agent-学习路线图-完整版.md》**互补并行**，专门填补「高级工程师 → 架构师」的能力差距
> **周期**：与主 Roadmap 24 周同步推进，每周**额外** 2-4 小时
> **更新时间**：2026-05-10

---

## 🧭 设计理念

主 Roadmap 是**纵向**的（按技术栈分阶段：Prompt → Agent → RAG → Multi-Agent → 架构）。
本 Roadmap 是**横向**的（按架构师视角拆解四条横切线 + 一组专属交付物）。

> **架构师 ≠ 高级工程师 + 1 年经验**。
> 架构师 = 高级工程师 + **横切思维** + **决策产出物** + **跨域判断力**。

---

## 🧵 四条横切线（贯穿全部 24 周）

每个项目（Project 1~10）完成时，必须回答这四条线的问题。把这份 Checklist 钉在每个项目的 README 顶部。

### 线 ①：Eval（评测）

| 问题 | 必答内容 |
| --- | --- |
| 这个 Agent / RAG 怎么算"对"？ | 写出 3 条以上可量化指标 |
| 离线测试集是什么？ | 至少 50 条 golden dataset |
| 回归怎么跑？ | pytest + dataset，commit 触发 |
| 在线怎么观测质量？ | LLM-as-Judge 或人工抽样 |

**学习资源**（按优先级）：
- [Anthropic — Building Evals](https://docs.anthropic.com/en/docs/test-and-evaluate/develop-tests) — 官方方法论，必读
- [OpenAI — Evals Cookbook](https://cookbook.openai.com/examples/evaluation/getting_started_with_openai_evals)
- [Hamel Husain — Your AI Product Needs Evals](https://hamel.dev/blog/posts/evals/) — 业界最经典实战文
- 工具栈：**Phoenix (Arize) + Langfuse + Braintrust**（对比试用，选一个深用）
- RAG 专属：RAGAS / DeepEval / TruLens

### 线 ②：Cost（成本工程）

| 问题 | 必答内容 |
| --- | --- |
| 单次请求成本？ | Token in/out × 单价 |
| 月度成本预估？ | DAU × 平均请求数 × 单价 |
| 优化策略？ | Cache / 模型路由 / Prompt 压缩 |
| 成本天花板告警？ | 接入预算监控 |

**学习资源**：
- [Anthropic — Prompt Caching](https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching) — 必须实战
- [OpenAI — Prompt Caching](https://platform.openai.com/docs/guides/prompt-caching)
- 模型路由：**RouteLLM** / **Martian** / 自建分类器
- 语义缓存：**GPTCache** / Redis + Embedding
- Prompt 压缩：**LLMLingua**（微软）

### 线 ③：Security（安全）

| 问题 | 必答内容 |
| --- | --- |
| Prompt Injection 防御？ | 输入校验 + 输出 Guard |
| 工具权限边界？ | 最小权限原则、审计日志 |
| PII / 敏感数据？ | 检测 + 脱敏 + 不出域 |
| Jailbreak 测试？ | 至少跑过一轮红队测试 |

**学习资源**：
- [OWASP Top 10 for LLM Applications 2025](https://genai.owasp.org/resource/owasp-top-10-for-llm-applications-2025/) — 必读，架构评审必答（2025 新增"Vector and Embedding Weaknesses"等条目）
- [Anthropic — Safety Best Practices](https://docs.anthropic.com/en/docs/test-and-evaluate/strengthen-guardrails)
- Guardrails 框架对比：**NeMo Guardrails** / **Llama Guard 4**（Meta 2025-04 发布，多模态 12B）/ **Guardrails AI**
- Prompt Injection 攻防：**Lakera Gandalf**（在线靶场）/ **Rebuff** / **PromptBench**
- PII：**Microsoft Presidio**

### 线 ④：Observability（可观测性）

| 问题 | 必答内容 |
| --- | --- |
| Trace 是否完整？ | 每个工具调用、每次模型调用都有 span |
| 关键 Metrics？ | TTFT / 工具成功率 / 用户满意度 |
| 用户反馈回流？ | 👍👎 → dataset → 下一轮 eval |
| 异常告警？ | 错误率、延迟、成本突增 |

**学习资源**：
- [OpenTelemetry GenAI Semantic Conventions](https://opentelemetry.io/docs/specs/semconv/gen-ai/) — 仍处于 Development（experimental）状态，但已是社区共识方向，建议追踪
- 工具栈广度对比（实际选一个深用）：
  - **LangSmith**（与 LangChain 深绑）
  - **Langfuse**（开源，自托管友好）
  - **Phoenix (Arize)**（开源，eval 强）
  - **Helicone**（无侵入代理）
  - **Datadog LLM Observability**（企业级）

---

## 🧩 补充能力线（架构师常被问到、但主 Roadmap / 横切线未覆盖）

按需穿插到 24 周中，不强制专门排期，但毕业前每条都要有答案。

| 主题 | 关键问题 | 切入点 |
| --- | --- | --- |
| **合规 / 数据治理** | 数据驻留？训练数据合规？日志留存？SOC2 / GDPR / 等保？ | [GDPR 官方](https://gdpr.eu/) + [SOC2 概览](https://www.aicpa-cima.com/topic/audit-assurance/audit-and-assurance-greater-than-soc-2)；先搞清"用户数据是否进训练" |
| **向量数据库选型** | pgvector / Milvus / Qdrant / Weaviate 怎么选？ | 维度（千万级以下首选 pgvector；亿级以上 Milvus / Qdrant），读写比、混合检索（BM25 + vector）支持 |
| **容量规划 / 限流降级** | QPS 上限？Token 预算？多 provider 多活？ | Token bucket 算法 + provider failover；项目 6 / 7 中加并发上限 |
| **数据飞轮闭环** | 用户反馈如何回流到 eval / prompt / fine-tune？ | 👍👎 → dataset 增量 → 周级回归 → 月级 prompt/模型迭代；这条是 Eval + Observability 横切线的合流 |
| **可观测性对接现有栈** | LLM Trace 如何接入 Prometheus + Grafana + 现有 PagerDuty？ | OTel Collector 桥接；指标语义映射到 RED / USE 模型 |
| **分层架构选型(决策资产)** | 模型 / 编排框架 / 检索 / 工具 / 可观测·Eval / 记忆,每层据数据·业务怎么选? | 总览 [`roadmap/agent-selection/README.md`](agent-selection/README.md);交互式用 `stack-selector` skill;上面"向量数据库选型"一行即检索栈层的一部分,详见 [`3-retrieval.md`](agent-selection/3-retrieval.md) |

---

## 🏗️ Phase 0 · 工程基础速通（第 0 周 · 前置 / 并行）

> **若你已掌握，直接跳过；若没有，主 Roadmap 后期会处处卡住。**

| 主题 | 自检题 | 资源 |
| --- | --- | --- |
| Python 异步 | 能解释 `async/await`、`asyncio.gather`、`Semaphore`、超时取消 | [Real Python — asyncio](https://realpython.com/async-io-python/) |
| FastAPI | 能写出 SSE 流式接口 + 依赖注入 + 后台任务 | [FastAPI 官方教程](https://fastapi.tiangolo.com/) |
| 类型 & 测试 | mypy / pyright + pytest + pytest-asyncio | [Pyright 文档](https://microsoft.github.io/pyright/) |
| Docker | 能写多阶段 Dockerfile + docker-compose | Docker 官方 Get Started |
| PostgreSQL + pgvector | 知道索引、事务、向量检索 | [pgvector README](https://github.com/pgvector/pgvector) |
| Redis | Streams / Pub-Sub / Cache / 分布式锁 | Redis 官方 |
| CI/CD | GitHub Actions：lint + test + build | GitHub Actions 官方 |

**产出**：搭一个 FastAPI + PostgreSQL + Redis + Docker Compose 的脚手架仓库，后续所有项目复用。

---

## 📈 Phase 1~4 增量补充

主 Roadmap 已经很完整，这里只列**架构师视角必须补的**。

### Phase 1 增量（第 1-4 周）

- 把 **Eval 横切线** 应用到项目 1、2：每个项目交付时附带至少 20 条测试集 + 自动化跑分脚本
- 阅读：[Lilian Weng — Extrinsic Hallucinations in LLMs](https://lilianweng.github.io/posts/2024-07-07-hallucination/)（理解模型可靠性边界）

### Phase 2 增量（第 5-10 周）

- **Long-running Workflow 编排**（主 Roadmap 完全没有，但生产 Agent 必备）：
  - [Temporal](https://temporal.io) — Agent 长任务、人在回路、重试编排的事实标准
  - [Inngest](https://www.inngest.com) — Serverless 风格替代
  - [Restate](https://restate.dev) — 新兴轻量方案
  - **必做**：把项目 4（自动化调研报告 Agent）改造为 Temporal Workflow，体会"Agent 是一种特殊的工作流"
- 阅读：[Anthropic — Building Effective Agents](https://www.anthropic.com/research/building-effective-agents) — 架构师必读，定义了 Agent vs Workflow 的边界

### Phase 3 增量（第 11-16 周）

- 把 **Cost 横切线** 应用到 RAG：
  - 实测 OpenAI / Cohere / BGE Embedding 的成本×召回率曲线
  - 用 Prompt Cache 把项目 5 的成本砍 30%+，写成博客
- 阅读：[Anthropic — Contextual Retrieval](https://www.anthropic.com/news/contextual-retrieval)

### Phase 4 增量（第 17-20 周）

- 把 **Security 横切线** 单独拉出做一个**安全专项周**：
  - 跑通 OWASP LLM Top 10 的每一项，写 demo 复现
  - 给项目 7（多 Agent 流水线）加 Guardrails，做红队测试
  - 产出：《Agent 安全 Checklist》开源博客
- A2A / AG-UI 已在主 Roadmap，**架构师重点**：自己实现一个最小 A2A Agent Card 注册中心（理解协议本质）

---

## 🏛️ Phase 5 重写 · 架构师专项（第 21-24 周）

> **主 Roadmap 的 Phase 5 偏"提及"，本节给出可执行的产出物清单。**

### 第 21 周：决策与判断力

**学习目标**：会做"是否该用 Agent"的判断。

| 主题 | 学习方式 |
| --- | --- |
| Fine-tuning 判断 | 不动手训，但读完：[OpenAI Fine-tuning Guide](https://platform.openai.com/docs/guides/fine-tuning) + LoRA / QLoRA / DPO 概念 |
| 自托管 vs API | 跑通 vLLM / SGLang / Ollama，跑一次 Llama 3.x 70B，记录单 token 成本 |
| Workflow vs Agent vs Rules | 读 Anthropic《Building Effective Agents》+ Hamel Husain 系列博客，写一篇自己的判断框架 |

**产出**：写一篇博客《我们什么时候不该用 Agent》。

### 第 22 周：可靠性 & 成本工程深挖

| 主题 | 实战 |
| --- | --- |
| 重试 / 熔断 / 幂等 | 用 `tenacity` + `circuitbreaker` 改造项目 6 |
| 模型路由 | 实现一个简单的 RouteLLM：低难度 → Haiku，高难度 → Opus |
| 语义缓存 | 给项目 6 接 GPTCache，实测命中率 |
| 预算护栏 | Token 预算超限自动降级 |

**产出**：《企业 Agent 可靠性 Checklist》— 至少 30 条。

### 第 23 周：架构师交付物训练

这一周**不学新东西**，专门练写作产出。

| 产出 | 模板 / 参考 |
| --- | --- |
| **ADR × 3**（Architecture Decision Record） | [Michael Nygard ADR 模板](https://github.com/joelparkerhenderson/architecture-decision-record) |
| **系统设计文档 × 1**（基于毕业项目） | 仿 [Google Design Doc Template](https://www.industrialempathy.com/posts/design-docs-at-google/) |
| **架构图 × 3** | C4 Model（Context / Container / Component） |
| **故障复盘读书笔记 × 5** | 阅读对象见下表 |

**故障复盘必读清单**：
- [Anthropic Status](https://status.anthropic.com) / [OpenAI Status](https://status.openai.com/incidents) — 关注大型事故的 incident 详情页（非 status 首页）
- Replit AI Agent 删库事件（2025-07）：参考 [The Register 报道](https://www.theregister.com/2025/07/21/replit_saastr_vibe_coding_incident/) 与 [AI Incident Database #1152](https://incidentdatabase.ai/cite/1152/)（Replit 官方未发布正式 postmortem，但公开信息足以复盘）
- 收藏 [Awesome Postmortems](https://github.com/danluu/post-mortems)，每周读 1 篇（覆盖更广的传统系统故障）

### 第 24 周：毕业项目 + 技术布道

主 Roadmap 已有毕业项目（企业 AI Agent 平台），架构师视角**额外要求**：

- ✅ 平台带 **完整四条横切线**：Eval Pipeline + Cost Dashboard + Security Guard + OTel Trace
- ✅ 至少 **3 份 ADR** 解释关键技术选型
- ✅ 一份 **完整系统设计文档**（30+ 页 / Markdown）
- ✅ 一次 **公开技术分享**（公司内部 Tech Talk / Meetup / B 站）
- ✅ 至少 **1 个开源 PR** 提到 LangGraph / Dify / Phoenix 任一仓库

---

## 📦 多模态 & Voice Agent（选修，但 2026 强烈建议）

主 Roadmap 完全没有，但 2025-2026 语音 / 多模态 Agent 已进入生产级落地阶段（OpenAI Realtime、Anthropic 流式工具调用、Pipecat / LiveKit 生态成熟）。

| 主题 | 资源 |
| --- | --- |
| Realtime API | [OpenAI Realtime](https://platform.openai.com/docs/guides/realtime) / Anthropic 流式工具调用 |
| Voice 框架 | [Pipecat](https://github.com/pipecat-ai/pipecat) / [LiveKit Agents](https://docs.livekit.io/agents/) |
| Vision Agent | Claude Vision / GPT-4o Vision |
| Computer Use Agent | [Anthropic Computer Use](https://docs.anthropic.com/en/docs/build-with-claude/computer-use) / [OpenAI Operator (CUA)](https://openai.com/index/introducing-operator/) — 注意是两家不同产品，benchmark 与适用场景不同 |

**建议**：抽 1-2 周做一个 Voice Agent demo，作为差异化作品。

---

## 🎖️ 架构师能力自检表（毕业前自测）

打钩自评，要求 **≥ 80% 通过**：

### 技术深度
- [ ] 能在白板上画出生产级 Agent 系统的完整数据流（含 Trace / Eval / Guard / Cache）
- [ ] 能解释 Prompt Cache 在不同模型下的命中规则与失效条件
- [ ] 能对比 Temporal vs LangGraph Checkpointing，说出何时用哪个
- [ ] 能现场写一个最小 OWASP LLM Top 10 复现 demo
- [ ] 知道 vLLM / SGLang / TensorRT-LLM 的差异

### 横切判断
- [ ] 给定业务场景，30 分钟内画出系统架构图 + 列出关键 Trade-off
- [ ] 能估算 100 万 DAU Agent 系统的月成本量级（误差 < 30%）
- [ ] 能说出"这个场景不该用 Agent"的至少 3 个理由
- [ ] 看到一个 PR 能立刻指出潜在的 Prompt Injection 风险

### 产出物
- [ ] 个人博客 ≥ 12 篇技术深度文章
- [ ] GitHub ≥ 3 个完整项目，每个带 Eval / Cost / Trace
- [ ] ≥ 3 份 ADR + ≥ 1 份系统设计文档
- [ ] ≥ 1 次公开技术分享
- [ ] ≥ 1 个被合并的开源 PR

### 跨域沟通
- [ ] 能给非技术 PM 讲清楚 Agent 的能力边界
- [ ] 能给后端工程师讲清楚为什么 Agent 系统设计与微服务不同
- [ ] 能给 Security 团队讲清楚 LLM 应用的攻击面

---

## 🔗 与主 Roadmap 的对应关系

| 主 Roadmap 阶段 | 本路线图对应内容 |
| --- | --- |
| Phase 1（第 1-4 周） | + 横切线 ① Eval 启动 + Phase 0 工程基础 |
| Phase 2（第 5-10 周） | + Workflow 编排（Temporal）+ Anthropic Effective Agents |
| Phase 3（第 11-16 周） | + 横切线 ② Cost 实战 |
| Phase 4（第 17-20 周） | + 安全专项周 + A2A 自实现 |
| Phase 5（第 21-24 周） | **本路线图全面替换**：决策训练 / 可靠性 / 交付物 / 布道 |

---

## 💡 给自己的话

> **架构师不是技能堆砌，而是判断力的复利。**
>
> 主 Roadmap 让你"什么都会"，本 Roadmap 让你"知道在什么场景下选什么、为什么、代价是什么"。
>
> 完成主 Roadmap 你能拿到 Senior 工程师 offer；
> 完成两个 Roadmap，你能在架构评审会上**拍板**。
