# 05 · 接入 Spec-Kit 工作流

> 目的:把本选型包嵌进 Spec-Kit 的 `speckit.specify → speckit.clarify → speckit.plan → speckit.tasks → speckit.analyze → speckit.implement` 流程,让"选框架"成为 plan 阶段的一个标准、可追溯的步骤。

---

## 一、各阶段在哪里用

| Spec-Kit 阶段 | 用本包做什么 | 产出 |
|---|---|---|
| `/speckit.constitution` | 把"选型原则"写进项目宪法(见下方片段) | 宪法里的选型条款 |
| `/speckit.specify` | 在 spec 里明确**数据特征 + 业务形态 + 约束** | 选型输入三要素 |
| `/speckit.clarify` | 用决策树(`01`)的关键问题反向澄清需求 | 补齐缺失约束 |
| `/speckit.plan` | 跑完整 3 步选型,记录评分与结论 | 选型小结(转 ADR) |
| `/speckit.tasks` | 把"框架接入/PoC 验证"列为前置任务 | 含验证任务的清单 |
| `/speckit.analyze` | **只读质量门**:核对 spec/plan/tasks 是否符合 constitution——含本文新增的「宪法选型条款」(见第二节) | 一致性/覆盖核对报告 |
| `/speckit.checklist` | 生成本 feature 的质量检查清单(可含选型验收项) | 自定义质量清单 |
| `/speckit.implement` | 按选定栈实现;偏离时回到 `02` 复核 | 实现 + 复核记录 |

---

## 二、写进 Constitution 的选型条款(片段)

把下面这段放进项目 `constitution.md`,让每次 plan 都遵守:

```markdown
## 技术选型原则(Agent Stack)

1. 选型必须经过 `roadmap/agent-selection/2-framework/` 的 3 步流程(决策树→评分卡→场景验证),
   不得凭手感直接拍板。
2. 任何框架选型必须有 ≥1 个备选(备选可以是"裸 SDK 起步")。
3. 从能解决问题的最轻方案起步;引入重框架需在 plan 里说明"复杂度为何已到"。
4. 选型结论须记录:首选 / 备选 / 理由(为什么>怎么做) / 已知代价 / 复核触发条件。
5. 重大选型落定后用 `skills/adr-writer` 沉淀为 ADR。
6. 工具/数据接入优先走 MCP,与编排框架解耦。
```

---

## 三、`/speckit.plan` 阶段可复制的 Prompt 块

在 plan 阶段直接粘贴(把尖括号替换成实际内容):

```
请用 roadmap/agent-selection/2-framework/ 这套选型包,为本 feature 选 Agent 框架/SDK。

输入:
- 业务一句话:<…>
- 数据特征:<规模/结构/更新频率/语言/多模态…>
- 关键约束:<成本上限 / 延迟要求 / 团队熟悉度 / 合规红线 / 是否绑定厂商>

请执行:
1. 用 01-decision-tree 收敛到 2-3 个候选,说明排除了什么、为什么。
2. 用 02-scorecard 选一套权重(或自定义),给候选逐维打分并加权,给出排序。
3. 用 04-scenario-playbook 找最接近的场景卡做交叉验证,确认没有更成熟的方案被漏掉。
4. 输出:首选 + 备选 + 选择理由(为什么>怎么做)+ 已知代价 + 复核触发条件。
5. 若是重大决策,提示我是否用 adr-writer 沉淀为 ADR。

保持简洁;若评分表较长,直接写进 plan 文件而不是全部打印在对话里。
```

> 也可以不粘 prompt,直接调 skill:`使用 framework-selector 帮我选型`(见 `skills/framework-selector/`)。

---

## 四、选型小结落地位置

| 范围 | 建议路径 |
|---|---|
| 单个 feature 的选型 | 写进该 feature 的 `plan.md`「技术选型」小节 |
| 跨 feature / 项目级选型 | 用 adr-writer 沉淀为 ADR(保存路径由 adr-writer 按决策范围决定) |
| 通用经验沉淀(新框架画像) | 回填到 `03-framework-profiles.md` |

---

## 五、和工具选型的分工提醒

一个 plan 里常**同时**有两层选型,别混:

- **编排框架/SDK 选型** → 本包(`roadmap/agent-selection/2-framework/`)
- **工具/API 检索方案选型(100+ 工具规模)** → `roadmap/agent-selection/4-tools.md`

两者独立决策,但都进同一份 plan 的「技术选型」小节。
