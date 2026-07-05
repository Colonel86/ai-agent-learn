# L03-05 · Agent 定义、用例矩阵与上下文工程

> 课程：Design, Develop, and Deploy Multi-Agent Systems with CrewAI（DeepLearning.AI × CrewAI）
> 本三节任务：打下全课概念地基——L3 定义什么是 AI agent（对比传统自动化），L4 用**复杂度×精度矩阵**和 **agency 谱系**回答"该不该用 agent、用多少 agency"，L5 揭开智能的底牌：**LLM 是特征→预测的模型，context engineering 就是特征工程**。

## 1. L3 · 什么是 AI Agent

### 1.1 工作定义

> An AI agent is **a system that can decide what happens next in order to accomplish a goal**.
> （一个能决定"接下来发生什么"、以达成目标的系统。）

所有 agent 的核心都是一个 LLM；课程后续会展示如何往 LLM 上叠加 tools、guardrails、controls，**让 LLM 表现得像一个 agent**。

从 LLM 到 agent 的推演链条（Joe 的三步）：

```
① 生成：让 LLM 写邮件 → 它写；让它更好笑 → 它至少试试        （创造内容）
② 选择：给它 A/B 两版 → 它说"A 更好，因为…"                （cognition：做出合理选择）
③ 掌舵：把"选哪封邮件"换成"业务目标 + 决定采取哪些步骤"
        → 不再是聊天，而是 AI 在控制应用流（application flow）  （这就是 agent）
```

### 1.2 为什么在意：与传统自动化对比（客服 chatbot 用例）

| | 传统自动化 | AI agent |
|---|---|---|
| 结构 | 人工映射所有分支边：A 输入→B 展示帮助文章→C 查登录态→D 查购买权限→…升级路径 | 给出所有可用动作，agent 依据客户输入**决定做什么、按什么顺序** |
| 边越加越多 | 图迅速变"忙"，必须穷举每条连接 | 无需穷举路径 |
| 漏掉一条边 | 直接 break，不工作 | agent 现场选择最合适的下一步 |

```
传统：A ──▶ B          agent：      ┌─ 展示文章（可能先做）
      A ──▶ C ──▶ D          输入 ──┤─ 查登录态（可能后做）
      A ──▶ 升级…                   └─ 升级（必要时）
      （每条边都要画）              （agent 像选邮件一样选路径）
```

由此换来四个传统自动化给不了的性质：

| 性质 | 含义 |
|---|---|
| **Cognition** | agent 在做选择（不是走死分支） |
| **Real-time reacting** | 依据任意运行时输入决定最合适的下一步 |
| **Self-healing** | 查登录态失败？换一个 API、加一步绕过去 |
| **Self-improving** | 跑得越多越知道什么有效，强化该行为 |

Zoom out 后，驱动 agentic 自动化的就两种能力：**create**（写邮件、生成图像…）+ **decide**（用什么 tool、什么数据、怎么从失败恢复）。

而 agent 要可规模化就必须可靠——回到 L1 三支柱（easy to build / trustworthy / manageable）。反例：客服 agent 大多数时候服务不了请求、或给不符合条件的客户退款，公司就不会用它。

> **对比课程 08《Agentic AI》**：08 课把 agentic 程度定义为"LLM 决定控制流的程度"并给出四大设计模式（reflection/tool use/planning/multi-agent）；本课的定义（"decide what happens next"）与之同源，但把落点从**模式分类**移到**工程后果**——决定权交给 LLM 换来 self-healing/real-time reacting，同时引入非确定性，必须用 guardrails/testing 买回可靠性。两课合读：08 告诉你 agency 是什么，本课告诉你 agency 的价格。

## 2. L4 · 用例怎么选：两张决策图

### 2.1 复杂度 × 精度矩阵（use case matrix）

"use case" = 一个你在决定要不要用 agent 解决的问题。两轴打分（注意是谱系不是四格死区）：

```
 精度要求 高 ┤ 快赢难拿              最有价值也最难
            │                       （例：IRS 表格填报——
            │                        表 70 页 + 手册 700 页，
            │                        真实银行合作项目）
 精度要求 低 ┤ 简单                  ★ 推荐起步区
            │                       （例：内容创作——任务很复杂
            │                        但产出结构有回旋余地）
            └────────────────────────────────
              复杂度 低               复杂度 高
```

结论：**最有价值的问题在高复杂度侧，最快的胜利在低精度侧**——所以推荐从"高复杂度 + 低精度"象限起步：复杂任务正是 agent 所长（价值大），而允许产出有创造性弹性（容易过验收）。有的公司这样起步、有的那样，没有对错，后续模块会讲策略。日常要持续问自己：**哪些用例的投入产出比最高？**

### 2.2 Agency 谱系：LLM 调用 → 单 agent → crew

不管什么用例，都要在 agency 谱系上选一个位置：

```
低 agency ◀──────────────────────────────────────▶ 高 agency
单次 LLM 调用          一个 agent           一个 crew（多个专职 agent 协作）
（LLM 只是工具）                            （每一步做什么都由 agent 决定）
```

CrewAI 为此提供**两个主抽象**：

| 抽象 | 优化目标 | 适用 |
|---|---|---|
| **Crews** | agency 最大化：agents + memories + tools + tasks 自主协作 | meeting prep 这类开放调研任务 |
| **Flows** | control 最大化：极薄的低层框架，**你决定什么按什么顺序发生** | 需要编排"普通 Python 函数 → 单次 LLM 调用 → 整个 crew"的混合系统 |

### 2.3 Flow 示范用例：员工福利对话助手

```
员工发消息（对话入口，像普通 chatbot）
   │
   ▼
处理消息 ← 无需 agency：一次 LLM 调用判断
   │        "上下文够不够直接回答？"
   ├── 够 ──▶ 直接回复，回到对话（体感 = 普通聊天）
   │
   └── 需进一步分析 ──▶ 启用整个 crew：
             查数据库/内部系统 → 校验 → 分析 → 产出答案 → 回到对话
```

要点：**在且仅在需要的地方 opt-in agency**（本例只在"分析"一步用 crew）。系统一旦变复杂，就长成这种结构化混排的样子——**LLMs + agents + crews 的 mix**。

> **架构师视角**：这两张图合起来就是一个完整的选型算法——先用矩阵判断"值不值得做、验收多严"，再用 agency 谱系判断"给多少决定权"。这正是 11-design-patterns.md 里"先 workflow 后 agent、按需升级 agency"原则的 CrewAI 版本，也与 Anthropic《Building effective agents》"能用 workflow 就别用 agent"的立场一致。Flows 把"编排是确定性的、节点内部才有 agency"做成了一等公民——面试讲编排分层时可直接引用这个 benefits-chatbot 图。

## 3. L5 · 什么让 agent 智能：LLM 原理 + Context Engineering

### 3.1 先看传统 AI：特征 → 预测

降雨预测模型：特征 =（location, season, temperature）→ 预测下不下雨。

| location | season | temperature | 预测 |
|---|---|---|---|
| Mumbai | 夏 | 90°F | 不下雨 |
| Taipei | 冬 | 65°F | 下雨 |
| Tokyo（没见过） | 夏 | 85°F | 模型泛化给出预测 |

**训练** = 让模型见足够多的样例，学到特征与结果的相关性，从而对没见过的组合也能预测。

### 3.2 迁移到 LLM：你打的每个字都是特征

Joe 自认这是简化类比，但极有用：LLM 也是一个常规 AI 模型，只是**特征 = 你到目前为止输入的所有词**。

```
prompt（= 特征）──────────────▶ answer（= 预测）

"give me a stock report on Tesla"
   ↓ 改特征（≈ 改 season/temperature）
"As an exceptional FINRA approved advisor,
 give me a stock report on Tesla"        → 预测被剧烈改变，答案不同
```

所以：**你对答案的控制力比你以为的大得多**——这就是 prompting 的本质。而系统的智能来自**海量特征输入 + 特征间复杂关联**的下一步预测能力；把特征喂好的能力，就是构建智能 agent 的能力。

### 3.3 强类型软件 vs 非确定性 agentic 系统

| | 传统软件 | Agentic 系统 |
|---|---|---|
| 输入 | 强类型，明确知道进来什么 | 未知（菜谱 or 博士论文，都可能） |
| 变换 | 明确定义 | 模型是黑盒 |
| 输出 | 明确知道出去什么 | 未知 |
| 测试 | 2 + 2 恒等于 4 | 不能这样测 |

这既是它的美（同一入口什么都能接），也决定了你必须**加多少控制才能拿到可靠输出**——为后续 guardrails/testing 章节埋下伏笔。

> **对比课程 21《Evaluating AI Agents》**：21 课 L1 的出发点一模一样——"agent 评估 ≠ 传统软件测试，因为非确定性"；本课从建造者视角给出同一枚硬币的另一面：既然输入/输出都不可穷举，质量就要靠**喂进去的特征**（context engineering）来前置保障，靠 eval 来后置度量。前者是 steer，后者是 measure，生产系统两者都要。

### 3.4 Context Engineering：五个可控输入

定义：**优化每一次 API 调用喂给模型的全部输入（作为特征），以换取最优输出。** 示范用例——职位描述（job listing）crew，三个 agent：

```
职位角色输入 → Research Analyst（调研其他职位列表、相关技能、竞对要求）
             → Writer（调研结果 + 职位规格 → 写出 job description）
             → Editor（审校，对齐公司 style 与 culture）
```

进入 context engineering 的五类要素：

| # | 要素 | 作用 |
|---|---|---|
| 1 | **System prompts** | 指导 LLM 应如何表现的底层引导 |
| 2 | **Clear instructions** | 说清对 agent 的期望，尤其是 **definition of done** |
| 3 | **Role playing** | 让 agent 扮演 researcher/writer/editor——同 FINRA advisor 的道理：角色词也是特征，直接改变预测质量 |
| 4 | **Memory** | 记住过去做对/做错了什么 |
| 5 | **Tools** | 完成调研、抓网页、写作、审校所需的一切外部能力 |

> **架构师视角**："prompt = 特征，prompting = 特征工程"是我见过对 context engineering 最好的一句话降维——它把玄学调 prompt 变成了经典 ML 直觉（改特征 → 改预测）。推论也很硬：role playing 不是仪式感，而是**低成本高杠杆的特征注入**；memory 和 tools 之所以归入 context engineering，是因为它们最终都以 token 形式进入同一个特征窗口。这一框架可直接用于面试题"什么是 context engineering、和 prompt engineering 什么关系"。

## 4. 本课总结

| 要点 | 一句话 |
|---|---|
| Agent 定义 | 能决定"接下来发生什么"以达成目标的系统；核心是 LLM + tools/guardrails/controls |
| vs 传统自动化 | 不穷举分支边，agent 现场选路径；换来 cognition / real-time reacting / self-healing / self-improving |
| 两种驱动能力 | create（生成）+ decide（选 tool、选数据、失败恢复） |
| 用例矩阵 | 复杂度×精度；最有价值 = 高复杂度，最快赢 = 低精度，起步选"高复杂度+低精度" |
| Agency 谱系 | 单 LLM 调用 → agent → crew；Crews 要 agency、Flows 要 control，按需 opt-in |
| LLM 本质 | 特征→预测模型，prompt 就是特征；改特征 = 改预测 |
| 非确定性 | 输入未知/黑盒/输出未知，与强类型软件的测试逻辑根本不同 |
| Context engineering | system prompts / clear instructions / role playing / memory / tools 五要素 |

> **记忆点（引出 L6 lab）**：概念全齐了——agent 会决定、用例选好了、智能来自喂进去的特征。L6 动手把这套 context engineering 落成代码：**构建你的第一个 agent 做内容创作**，并领教 Joe 的 80/20 法则——功夫下在 tasks 上多过 agents 上。

## 与我的资产映射

- 设计模式层：`agent/skills/agent-selection/11-design-patterns.md`（agency 谱系 ↔ "workflow 优先、按需升级 agent"；flows ↔ 确定性编排 + 节点内 agency）
- 框架层：`agent/skills/agent-selection/2-framework/03-framework-profiles.md`（CrewAI Crews/Flows 双抽象——与 LangGraph 图控制路线的关键差异点）
- 面试包：`agent/interview/jd-senior-agent-engineer/01-agent-run-loop-and-orchestration`（agent 定义、agency vs control、context engineering 五要素都是 run loop 一题的答案骨架）
- [[project_selection_matrix]]
