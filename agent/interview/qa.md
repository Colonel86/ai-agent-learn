1. Agent 解决了什么实际问题

AlphaFi 是一个加密市场分析 Agent。痛点是加密数据极度分散——K 线、衍生品、链上、宏观、舆情散在十几个源里，人工整合成本很高。传统方案两头都不行：固定 Dashboard 穷举不了'BTC 和 ETH 值不值得投资'这种开放问题，纯 LLM 又会编造数字，金融场景零容忍。Agent 的核心价值在于：取数计划本身是推理的产物——理解意图、自主决定要哪些数据切面、并行获取、交叉验证、再合成有数据支撑的分析。同时我很清楚 Agent 化的代价：风险从'说错话'变成'用真数据推出错结论'，所以我做了数据信任分级，输出定位为概率加权的情景分析，不给直接交易信号。

2. 使用了哪些模型和工具

模型：OpenAI gpt-4.1 和 deepseek

框架与工具：
- 多模型路由：OpenRouter
- 编排框架：LangGraph
- LLM访问网关：LiteLLM
- 输入输出护栏（LlamaFirewall, GuardrailsAI, Presidio） 
- 记忆层（mem0 pgvector, postgresSQL), 时序知识图谱（Graphiti）
- 观测/eval: 回归评测（promptfoo）, phoenix, deepeval, ragas
- 离线红队: Promptfoo、DeepTeam、Giskard
- ACL 治理: Unity Catalog
- 部署: K8s，测试/生产 configmap 分离 
- 统一网关：caddy（api层）
- 统一认证：keycloak（签发 RS256 JWT）
- 指标库：prometheus（API 请求率/错误率/时延（RED）+ 探活结果）
- 日志：loki（日志库：全容器日志集中存储，Grafana 里可检索），  promtail （日志采集器：从 docker 日志文件刮日志送进 loki），grafana（│ 总看板（/grafana）：探活、RED、LLM spend 分账、日志、三条告警都在这一页看）

3. Agent 如何进行任务规划和工具调用

分三层：

第一层：模式路由（ModeRouter） — 收到问题后先判断走快还是深：11 条 Deep 信号正则（"对比"、"综合分析"、"值得投资"等）→ 6 条 Fast 信号正则（"当前价格"、"市值多少"等）→ 长度启发式 → 都判不了时用 LLM  参数强制指定。

Fast 模式（简单问题）：Probe → Reflect → Synthesize 三步子图——LLM 选工具并执行 → 检查数据是否充分 → 流式合成回答，最多 3 轮 ReAct。

Deep 模式（复杂分析）：六阶段流水线：
1. Frame（问题建模，判定难度；easy 直接降级回 Fast）
2. DataPlan（规划要取哪些数据）
3. Parallel Fetch（并行取数）
4. Reflect + Refill（数据充分性检查，不足则补取，上限 5 次）
5. Outline → Write（先大纲后流式写作）
6. SelfVerify（仅 hard 题做自校验）

工具检索（ToolRetriever）：不把全部工具塞进 prompt，而是把 31 个 Ski个细粒度"能力文档"（如 coinglass-derivatives 一个 Skill 展开为funding_rate_history、funding_rate_exchanges 等 120+ 条），对查询做关键词打分取 top-K 再交给 LLM 选择——既省 token 又提高选中率。

可靠性全落在架构层：循环上限、熔断降级、数据信任分级都是代码约束，不靠提示词让模型'自觉'——提示词一次注入就能绕过。



4. 如何评估和提升任务成功率

通过RAG手段提高skill和工具调用正确率

高质量回答——分离线/在线 + 检测/防护两个维度，这是最能拉开差距的一题：

评估（怎么量化）：
- 离线 eval 集 + LLM-as-a-judge：偏见/毒性/幻觉没有精确字符串可匹配，用另一个 LLM 按 rubric 判 SAFE/UNSAFE。但要点出裁判本身会错判——所以做人工抽检 / 双裁判 / 明确 rubric 校准。
- 红队回归：维护一个攻击库（注入/越狱/PII/竞品），每次改提示词/换模型都自动重跑，成功率一升就拦上线——把安全测试变成回归测试、CI 化。
- 打到副作用：Agent 类系统评估要直接查底层状态（订单是否被改），而不是听模型说了什么——"模型嘴上拒绝、工具却已执行"是最隐蔽的失败。

提升（怎么变好）——用三层护栏架构：

▎ - 检测层（能力）：换更强的 validator/模型提召回；
▎ - 编排层（语义）：on_fail 选 EXCEPTION/FIX/REFRAIN/REASK，平衡严格度和体验；
▎ - 网关层（一致性）：护栏做成独立服务/OpenAI 兼容端点，保证每个应用都绕不过。

固定题集分类别跑基准，保证纵向可比；
核心是 LLM Judge 五维打分——faithfulness、coverage、insight_depth 这些，带 diff 对比，每次改动都能量化变好还是变坏；
再加全套回归测试目录。

离线拦（promptfoo/deepeval/ragas 做 CI 门禁）→ 运行时救（护栏 on_fail 修复、LiteLLM fallback）→ 在线察（phoenix + RED 指标发现生产退化，Loki 取证归因）——评估不是上线前的一次考试，是覆盖全生命周期的持续回路。

5. 项目是否已正式上线

已经上线：
1. https://dappos.com/
2. https://gmentis.ai/