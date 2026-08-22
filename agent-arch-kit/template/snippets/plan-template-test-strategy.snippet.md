<!--
  agent-arch-kit · plan 模板测试策略钩子
  合并方式：把下面整段插入 .specify/templates/plan-template.md 的
  「技术选型（Selection Check）」之后、「Constitution Check」之前，
  然后运行 /speckit.constitution 重新同步。
  知识来源：.claude/skills/eval-strategy/（按需加载）；对应门禁：constitution §3 G6。
-->

## 测试策略（Test Strategy）

> 依据 eval-strategy 测试金字塔逐层规划本 feature 的评估。填写规则：
> **判分器与门禁类型必须引用 `eval-strategy/<节名>` 的依据；不适用的层填 N/A + 一句理由。**
> 提醒：能用规则绝不上模型；LLM-Judge 未校准的分数不得作为门禁依据。

| 层 | 本 feature 测什么 | 判分器 | 跑在哪 | 门禁（硬/软/无） |
| --- | --- | --- | --- | --- |
| L1 单元级 | | | | |
| L2 组件级 | | | | |
| L3 轨迹级 | | | | |
| L4 端到端 | | | | |
| L5 对抗级 | | | | |
| L6 生产级 | | | | |

### Golden set 增量

- 本 feature 需新增的 golden 用例：<能力分组 × easy/hard 数量；或"复用现有集，无新增 + 理由">
- 坏 case 回流路径是否已通：<线上 trace → 标注 → 入集 的具体机制；T0 可 N/A>
- 前视偏差检查（时序/金融场景必填）：<用例是否含决策时点后信息；不适用则 N/A>

### G6 对齐检查（constitution §3）

- [ ] L4 有带期望输出的回归用例，且已进 CI（T1+ 必须；无则本 feature 不得合入）
- [ ] 变更类 feature 已规划变更前后实验对比（EDD），报告将附在 MR
- [ ] 所用 LLM-Judge 已校准（对照人工一致率 ≥90%）或本 feature 未使用模型判分
- [ ] judge prompt / 判分规则已纳入版本管理（G7）

### 测试留债登记

> 本 feature 明确不做的层/用例（显式留痕，constitution §1 显式取舍原则）：

| 留债项 | 理由 | 偿还触发条件 |
| --- | --- | --- |
| | | |
