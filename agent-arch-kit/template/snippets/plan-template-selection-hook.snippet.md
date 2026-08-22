<!--
  agent-arch-kit · plan 模板选型矩阵钩子
  合并方式：把下面整段插入 .specify/templates/plan-template.md 的
  「Constitution Check」小节之前（选型先行，门禁在后），然后运行 /speckit.constitution 重新同步。
  本 snippet 是四资产装配的关键件：它让选型矩阵在 plan 阶段被"强制消费"，
  并把 ADR 升格规则（constitution §2.3）接进流程。
-->

## 技术选型（Selection Check）

> 依据 constitution §2：每个选型决策必须逐层对照选型矩阵；矩阵入口
> `.claude/skills/selection-matrix/`。填写规则：
> **一致 → 引用矩阵条目编号即可；偏离 → 写理由；命中升格条件 → 落 ADR 并引用编号。**
> 本 feature 不涉及的层填 N/A（无须理由）。

| 层 | 矩阵结论（条目引用） | 本 feature 采用 | 一致/偏离 | 偏离理由 / ADR 编号 |
| --- | --- | --- | --- | --- |
| 模型 | | | | |
| 框架/编排 | | | | |
| 检索（RAG） | | | | |
| 工具层/协议 | | | | |
| 观测·评估 | | | | |
| 记忆 | | | | |

### 选型红线自查（constitution §2.1，任一违反 = 计划不通过）

- [ ] R1 数据不出域：敏感数据场景未选用数据出域的 SaaS
- [ ] R2 简单场景未引编排框架（或已回答"框架解决了裸 SDK 的什么问题"）
- [ ] R3 编排选择为 LangGraph，或偏离已按 §2.3 落 ADR
- [ ] R4 无硬编码密钥；凭证走密钥管理 + 短时效 token
- [ ] R5 高危操作有确定性 HITL 闸门
- [ ] R6 埋点走 OTel 标准，未绑定私有独占格式

### ADR 升格检查（constitution §2.3）

对上表每个「偏离」项与新引入依赖，逐条判断 A1–A4：

| 决策 | A1 影响≥2模块/替换>1周 | A2 偏离矩阵默认 | A3 新重大依赖 | A4 团队分歧 | 结论 |
| --- | --- | --- | --- | --- | --- |
| | | | | | 落 ADR-NNN / 记入本节即可 |

> 已落的 ADR 在此列出：ADR-NNN《标题》——一句话结论。

### 回写预埋（constitution §4）

- 本 feature 预计可能产生的矩阵回写点：<层 + 待验证结论；没有则写"暂无">
- 本 feature 依赖的存量 ADR 及其 Revisit Triggers 是否临近触发：<ADR 编号 / 无>
