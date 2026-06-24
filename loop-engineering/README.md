# Loop Engineering 学习沙盒

一个**能真的 pass/fail 地循环**的最小闭环，用来摸熟「spec-kit（状态）+ Loop Engineering（执行）」的机制。
对应文章《最近爆火的 Loop Engineering，到底是什么》里的四件套。

## 它是什么

一个零依赖的「笔记检查器」开发任务，4 个函数全是**桩**，配 4 个**真实 pytest 验收测试**（初始全红）。
循环每完成一个任务，对应测试由红变绿，`tasks.md` 勾掉一个。全绿 = 完成。

```
loop-engineering/
├── notelint.py         # 目标代码（函数桩，待补全）
├── test_notelint.py    # 验收测试 = 客观门控（初始全红）
├── gate.sh             # 硬门控：ruff + pytest 收集（代码没坏）
├── loop-state.json     # 记账：attempted / accepted / 接受率
├── .specify/memory/constitution.md   # 原则 + 红线（spec-kit 同构）
└── specs/001-note-lint/
    ├── spec.md         # 做什么 + 验收标准（rubric）
    ├── plan.md         # 技术方案
    └── tasks.md        # ← 任务队列 = 循环的状态文件
```

> 四件套对应：**状态文件**=`specs/001-note-lint/tasks.md` · **门控**=`gate.sh`+验收测试 · **Skill/执行器**=`.claude/commands/spec-iterate.md` · **自动化**=`/loop`。
> 这里的 spec-kit 文件是**手搓的同构最小版**；真实项目用 `specify init . --ai claude` + `/speckit.*` 生成。

## 一次性准备

```bash
# 把门控工具装进仓库 .venv
.venv/bin/python -m pip install pytest ruff       # 或: uv pip install pytest ruff
chmod +x loop-engineering/gate.sh
```

## 怎么看它工作

```bash
# 1) 看初始状态：硬门控绿（代码没坏），但 4 个验收测试全红
bash loop-engineering/gate.sh
.venv/bin/python -m pytest -q loop-engineering          # → 4 failed

# 2) 跑闭环（自定步速；每轮做一个任务：实现→门控→独立验收→勾选+commit）
/loop /spec-iterate loop-engineering/specs/001-note-lint

# 3) 看终态：tasks.md 全 [x]，全部测试绿
.venv/bin/python -m pytest -q loop-engineering          # → 4 passed
```

手动跑一步（不用循环，先把机制看清楚）：直接 `/spec-iterate loop-engineering/specs/001-note-lint` 调一次。

## 两种驱动方式

同一个沙盒（spec/tasks/gate/code）可以用两种方式把循环跑起来：

| 方式 | 是什么 | 适合 |
|---|---|---|
| **A. `/loop /spec-iterate`** | Claude Code 交互式 harness 反复调用单步命令 | 想在 Claude Code 里看着它一步步跑 |
| **B. `loop_runner.py`（Claude Agent SDK）** | 把循环写成一个**真 Python 程序**：队列/门控/停点/记账在 Python，每个任务调两次 `query()`（实现者 + 独立只读验收者） | 想要可部署、可挂 cron、脱离交互式的“真循环”——文章里 Cherny 说的“我写循环” |

**B 跑法**（不要在交互式会话里跑，会真花 token）：
```bash
.venv/bin/python -m pip install claude-agent-sdk
export ANTHROPIC_API_KEY=sk-ant-...
cd loop-engineering && ../.venv/bin/python loop_runner.py
```
`loop_runner.py` 的关键设计 = **确定性外壳 + 两个 agent**：实现者 `bypassPermissions` 自主写代码，验收者**全新上下文 + 只读工具**独立判 `VERDICT: PASS/FAIL`（实现者不准自评）。停点用唯一指标“接受率 < 0.5”。

## 四个条件（什么时候才该上循环）

这个沙盒只满足「有客观门控」一条，是**学机制**用的。真实项目上循环前确认四条都成立：
① 任务每周重复 ② 有自动门控 ③ token 预算扛得住 ④ Agent 有日志和可跑环境。
缺任一条，循环成本 > 收益。摸熟后把这套 `/spec-iterate` 搬到 **Argus**（真 pytest gate）才回本。
