# SDD Skill 套件(Spec-Kit 驱动 Agent 项目研发)

> **用途**:四个 skill 组成一条「**驱动 / 选 / 记**」的工作链,配合共享知识包 [`../agent-selection/`](../agent-selection/),用 Spec-Kit 把一个 Agent 项目从 idea 驱动到上线。
> **流程总纲(唯一地图)**:[`../agent-selection/spec-kit-workflow.md`](../agent-selection/spec-kit-workflow.md)——阶段×资产映射、宪法条款块、rubric 方法论、上循环条件都在那里。
> **最后核对:2026-07**。

---

## 一、四个 skill 的分工

| skill | 角色 | 管什么 | 不管什么(转交给谁) |
|---|---|---|---|
| [`sdd-architect/`](sdd-architect/) | **驱动** | 定位项目所处阶段(constitution/specify/plan/tasks/implement),给下一步入口,按段推进 | 任何一层的具体选型(→ stack-selector) |
| [`stack-selector/`](stack-selector/) | **选(跨层)** | plan 阶段的分层选型总路由:识别要选哪几层→逐包跑决策流→汇总选型小结 | 编排框架层(→ framework-selector);全流程驱动(→ sdd-architect) |
| [`framework-selector/`](framework-selector/) | **选(框架层专项)** | 编排框架/SDK 三步选型(决策树→评分卡→场景验证) | 其他层(→ stack-selector);工具路由(→ `4-tools.md`) |
| [`adr-writer/`](adr-writer/) | **记** | 把"为什么选 X 不选 Y"沉淀成 ADR(强制备选/负面后果/复核触发条件/自评分) | 怎么选(→ 两个 selector) |

在生命周期上的位置:

```
idea → constitution → specify/clarify → plan → tasks/analyze → implement → 上线 → 复盘
└───────────────── sdd-architect(全程驱动)─────────────────┘
                                          ↑
                                  stack-selector ──转交──→ framework-selector
        adr-writer(重大决策随时沉淀,横切)
                                                      /spec-iterate(执行循环,命令非 skill)
```

## 二、与周边资产的关系

- **知识包** [`../agent-selection/`](../agent-selection/):12 个分层决策包 + 总览 README(空间地图)+ 全流程总纲(时间轴)。skill 是薄路由,知识全在包里——**改结论改包,不改 skill**。
- **执行闭环**:`.claude/commands/spec-iterate.md`(单步执行器)+ `loop-engineering/`(四件套机制沙盒)。
- **项目落地**:`projects/README.md`(真实项目放仓库根 `projects/<name>/`,`specify init` 初始化)。

## 三、怎么用

四个 skill 已通过 `.claude/skills/` symlink 注册(⚠️ `.gitignore` 忽略 `.claude/`,换机器需重建,见下),新会话中按 description 触发词自动加载;也可直接点名:

- 「帮我启动一个新项目 / Argus 下一步做什么」→ **sdd-architect**
- 「帮我做整体架构选型」→ **stack-selector**
- 「LangGraph 还是 crewAI?」→ **framework-selector**
- 「把这个决策写成 ADR」→ **adr-writer**

注册重建(新机器 / 重新 clone 后执行一次):

```bash
mkdir -p .claude/skills
for s in sdd-architect stack-selector framework-selector adr-writer; do
  ln -s ../../agent/skills/sdd/$s .claude/skills/$s
done
```

## 四、维护约定

- skill 保持**薄路由**:只写工作流与转交规则,选型结论/对比表一律放 `agent-selection/` 决策包。
- 新增流程环节时先问:能进总纲的一个小节吗?能,就别新建 skill(反过度工程——工具链的缺口应由真项目暴露,不由推演补全)。
- 各 skill 的「相关资产」清单互相交叉引用,改动任一 skill 的职责边界时同步核对其余三个。
