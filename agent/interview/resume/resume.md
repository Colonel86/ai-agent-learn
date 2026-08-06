# 耿明 · AI Agent 架构师/技术经理

- 哈尔滨商业大学 · 电子信息工程 · 本科 · 13716068721 · ives.geng@gmail.com

## 个人优势

- **3 年 AI Agent 开发经验（2023 至今），2 个生产级产品上线**：
  - **xBubble**（https://dappos.com）— 基于 LangGraph 的 Web3 AI 操作系统，多 Agent 编排 + 双层记忆，日均 0.2 万次查询
  - **Mentis**（https://gmentis.ai/chat）— 对话式智能助理
- **架构主导，而非框架使用者**：两段 Agent 经历均为核心架构设计者——链图主导智能层 Multi-Agent Framework 编排与 Memory 子系统架构；宜信主导 V2 架构重构（双模式路由 / Skill 配置驱动），核心代码 ↓70%、新增能力零核心改动，重构决策全程由评估数据驱动。
- **覆盖 Agent 全栈五层**：底层契约（结构化输出 / 工具）→ 编排（状态机 / 协议）→ 上下文（RAG / 记忆）→ 多 Agent 协作 → 生产化（评测 / 安全护栏 / 部署）；标准化 build → eval → deploy 闭环，沉淀为被 6 名工程师采用的内部框架。
- **10+ 年工程功底，复合背景**：4 年区块链（Go / Solidity / Rust，DeFi / 智能合约审计），链上数据语义直接转化为 Agent 领域信号识别；此前 5 年 iOS（汽车之家架构师）、3 年 C（银行交易 / POS 嵌入式），多次从 0 到 1 组建团队。

## 技能

- **AI Agent 编排与框架**：LangGraph、LangChain、CrewAI、Agentic 设计模式（Reflection / Planning / Multi-Agent 协作）、StateGraph、conditional routing、Human-in-the-Loop、persistence（checkpointing）、multi-step reasoning
- **工具层与协议**：Model Context Protocol (MCP)、Tool Use / Function Calling、A2A、Agent Skills、Pydantic type-safe schema
- **上下文工程（RAG / 检索）**：RAG、vector retrieval、reranking、query expansion、Agentic RAG、Knowledge Graph RAG、embedding、vector store（pgvector / Chroma）、cross-encoder、语义缓存与 prompt 压缩
- **Agent 记忆（Memory）**：Long-Term Memory（semantic / episodic / procedural）、记忆框架实战（Letta / Mem0 / Zep·Graphiti / Hindsight / LangMem）、记忆生命周期（写入 / 消解 / 检索 / 遗忘）
- **评测与可观测（LLMOps）**：LangSmith、Phoenix、RAGAS、DeepEval、LLM-as-a-Judge、轨迹评估（trajectory / convergence）、评估驱动开发（EDD）、评测数据集版本化与实验对比、OpenTelemetry / OpenInference 埋点、分布式 tracing、离线评测、CI 评测门禁（规则评估 + 模型评分）、CI/CD 中的 Agent 自动化测试（GitLab CI / Jenkins、MR 自动评审）、微调与数据迭代（LoRA / SFT / Memory Tuning）、Spec-Driven Development (Spec Kit)
- **LLM 网关与自托管基础设施**：LiteLLM 统一网关（多模型 OpenAI 兼容接入、API key 管理、限流、预算控制与成本核算、fallback / 负载均衡）、Grafana LGTM 全链路可观测栈（OpenTelemetry Collector、Prometheus、Loki / Promtail、Tempo、Blackbox 可用性探测、Grafana 统一面板）、Caddy 反向代理（自动 HTTPS）+ Keycloak IAM（SSO / OIDC / OAuth2）、基于 trace 的 LLM 调用 token 成本归因与 P99 延迟分析
- **Agent 安全与护栏**：Guardrails AI（validators / hub）、LLM 红队测试（Giskard / prompt injection / jailbreak 评测）、运行时 guardrails 与输出过滤、Agent 权限与治理
- **编程语言**：Python、Go、Solidity、Rust、TypeScript、JavaScript、Move、C、Objective-C
- **区块链**：DeFi、NFT、GameFi、DAO、智能合约审计（Slither / Mythril / Echidna）、跨链协议、去中心化交易所、ERC20 / ERC721

## 工作经历

### 宜信普惠信息咨询（北京）有限公司 · AI Agent 架构师（2025 – 至今）

- 基于 LangGraph 构建生产级 Agent 系统，服务于加密货币量化研究场景；主导多 Agent 编排、StateGraph 路由、Tool 集成与 Memory 子系统等核心模块。
- 运用 state machine、conditional routing、Human-in-the-Loop、persistence（checkpointing）实现可靠的多步推理；设计 Tool Use / Function Calling 流程，结合 Pydantic type-safe schema 与 structured output（JSON Schema enforcement、constrained decoding）保证输出可控；通过 MCP 构建跨框架、可复用的工具层。
- 实现两层 context engineering：RAG（vector retrieval、reranking、query expansion、Agentic RAG、Knowledge Graph RAG）与 Long-Term Memory（semantic / episodic / procedural）；补齐多轮记忆与引导式提问（上下文摘要主动提取注入 + 对话跟进意图识别）。
- 建立组件级 → 轨迹级 → 任务级的分层评估体系：工具选择 / 参数抽取用 LLM-as-a-Judge 评估，Agent 路径用收敛度（convergence）评估，端到端用带期望输出的实验数据集做回归；prompt / 架构变更先跑实验对比再合入（评估驱动开发 EDD）。
- 集成 Claude Agent SDK 实现 GitLab / Jenkins CI/CD 上的 MR 自动评审，覆盖 8 个仓库；通过 Spec-Driven Development（Spec Kit + Claude Code）沉淀可复用的 Agent 开发模式。

**核心项目 · 量化研究 Agent V2 架构重构**

- 背景：V1 采用多 SubAgent 硬编码层级路由，新增能力需改 4+ 文件（含 2 个核心文件），回归风险高。
- 方案：重构为双模式路由（Fast / Deep）+ Data-First 流水线 + Skill 配置驱动系统（均为本人主导设计）；新增能力降为「加 1 个配置文件、零核心改动、零回归风险」，能力数量翻倍（+10 项），在 30+ Skill 复杂调用场景中保持稳定（行情多指标查询、跨周期信号检测、资金费率与持仓变化联动分析、主动买卖与价格背离判断等）。
- 成果：System Prompt Token ↓43.8%、核心代码 ↓70%、典型查询 LLM 调用 ↓50%；歧义消解准确率 72.2% → 100%（Hard 难度 33.3% → 100%）、跨域查询（如「资金费率 + RSI 关联」）0% → 100%；工具调用命中率 80%+ → 99%+（精确化 when_to_use + 解除单工具约束 + SkillRunner 三轮参数自动修正）。
- 质量底座：从 0 建立 246/246 全通过的测试体系，输出语言 / 格式 / 数据一致性均达 100%。

### 北京链图科技有限公司 · 技术经理（2023 – 2025）

- 作为 AI Agent 团队核心贡献者，深度参与智能层 Multi-Agent Framework 编排与 Memory 子系统的架构设计与实现（见下方核心项目）。
- 负责 Dappos 的 VWManager / VWService 合约开发、维护与测试，以及与 GMX、Kiloex、Kyberswap、Perp、Aark、Quickswap、SOFA、Stader 等 20+ 第三方 Dapp 合约的业务逻辑对接，保障数据同步与资产安全。
- 负责 IntentEX 去中心化交易所相关合约开发（链上资产价格获取、跨链协议对接），以及基于 Golang 的 K 线数据服务端接口开发。
- 前期沉淀的 DeFi 协议对接经验与链上数据语义理解，直接转化为 DeFi Subgraph 的策略验证与 Opportunity Subgraph 的领域信号识别——「区块链工程师 + Agent 工程师」的复合背景。

**核心项目 · xBubble（https://dappos.com，已上线）**

- Web3 AI 操作系统：智能层（Multi-Agent Framework + Memory）+ 执行层（Intent Execution Network），用户通过自然语言完成 Web3 研究 / 策略 / 执行全生命周期任务。
- 基于 LangGraph StateGraph 实现 intent 在 search / DeFi / opportunity 三类 sub-agent 间的确定性路由，跨节点有状态编排（messages、plans、artifacts、HITL 中断、errors）；日均服务 0.2 万次查询，任务成功率提升 23%。
- 设计端到端的 Agent 评测与可观测框架（LangSmith / Phoenix / RAGAS / DeepEval）：分布式 tracing、离线评测、运行时 guardrails；回归逃逸 ↓40%，评测周期 2 天 → 4 小时。
- 在 200+ tools、20+ vertical agents 生态上构建统一工具集成层（MCP 风格 connectors），支撑 tool-augmented plan generation，执行前经 strategy-validator 做风险校验。
- 针对高噪声、强时效的 Web3 数据，工程化实现 tool call（embedding + vector store + cross-encoder）与双层记忆（episodic + durable，由 Compound Memory 统一编排）。
- 标准化 build → eval → deploy 闭环，内部 Agent 框架被 6 名工程师采用，新 Agent 上手时间缩短约 50%。

### 北京云中戏信息技术有限公司 · Solidity 智能合约安全审计（2022 – 2023）

- 智能合约审计组长，带领 6 人团队，完成 10 个以上项目审计，代表项目包括 Shorter Finance、Robbin。
- 熟练使用 Slither、Mythril 进行静态分析，使用 Echidna 进行模糊测试；熟悉审计流程及相关规范。
- 组建团队、优化审计流程、开展内部技术培训。

### 神话科技传媒（深圳）有限公司 · 技术经理（2019 – 2022）

- 管理 12 人团队，负责智能合约开发与 Go 服务端开发，团队从 0 到 1 搭建。
- 基于 eth / nuls / iost 三条公链的去中心化交易功能：三链智能合约开发（Solidity、Java、JavaScript）、移动端 SDK 开发（go-mobile）、交易处理与撮合上链的 Golang 服务端开发。
- NFT 交易所、NFT 合成挖矿、ISM 保险、体育赛事等多条产品线。
- 基于动漫 IP 的 GameFi 合约开发：ERC20 / ERC721 代币、NFT 质押挖矿、英雄随机与算力推图玩法，最终演变为 IP 孵化平台。

### 北京磁云科技 · Golang 开发工程师（2018 – 2019）

- M1 API：开发节点 API，包括 key、account、address、asset、transaction、wallet 等相关接口。
- M1 Client：开发所有功能模块的 client 命令功能。
- mgo sdk：将所有 API 抽象成 SDK 提供给应用开发团队，方便对接节点功能。

### 汽车之家 · 架构师（2016 – 2018）

- 完成主 App 找车功能模块开发。
- AB-Testing SDK、日志上报系统、组件化维护。
- ReactNative 优化方案实施；ARKit 调研并输出 Demo；小视频功能开发。
- 主导移动端架构优化。

### 红演圈（北京）网络科技有限公司 · 移动端团队负责人（2012 – 2016）

- 管理 10 人手机端团队，负责 iOS 端架构设计与优化，团队与 App 均从 0 到 1 搭建。
- 组建手机端研发团队、推进项目进度；架构搭建、优化与技术难题攻关。
- 首页、招募频道、邀约、我的相关工作流等模块开发。

### 北京联银通科技有限公司 · C 开发工程师（2009 – 2012）

- 雅酷银行卡 POS 应用程序开发，基于王府井银行卡标准程序进行定制化功能扩展。
- 乐富支付 POS 机应用程序开发，实现终端远程 TMS 软件及参数的下载与更新功能。
- 参与京东自提点 POS 机应用程序开发，配合京东商城完成终端功能设计、测试与验收。
- 参与华夏银行 BEAI 总线项目，协助完成系统集成与接口开发。
