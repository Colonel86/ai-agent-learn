# 动作范式选型(最上游分叉:动作怎么"表示")

> **用途**:在选编排框架、选工具、搭沙箱**之前**,先定 Agent 的动作原语用哪一档——function/tool calling、CodeAct、还是 computer/browser-use。
> **适用**:Spec-Kit `/plan` 的第一步(先于 `2-framework/01-decision-tree.md`);或由 `stack-selector` skill 路由进来。
> **最后核对:2026-06**。⚠️ 具体工具/产品名(Operator、computer use 等)变化快,本包给**选型轴**,产品名按当下**现查**,不固化快照。
> **层定位**:这是「**0 号·动作范式**」——最上游分叉。它**不是**和模型层/框架层并列的"又一层",而是先于它们的**前置分叉**:选哪档动作原语,会反向决定下游的编排框架、沙箱(→ `roadmap/agent-selection/7-safety-guardrails.md`)、工具路由与观测形态。在五层心智里它属 **L1 action 范式谱**(见 `/Users/ming/Documents/ai-agent-learn/agent/interview/1.md` «L1 底层契约·Action 范式谱»),矩阵里把它前置为 0,是因为它**预先约束**了 1–7 层的可选集。

---

## 一、何时需要这层选型(以及为什么最先做)

- 新建任何 Agent 时**第一个**该问的问题:"这个 Agent 的一个动作,长什么样?"——别默认只有 JSON 工具调用。
- 目标系统**没有 API**、只能操作界面(遗留系统、第三方网站、桌面软件)。
- 工具数量爆炸 / 一个任务要在多工具间**组合 + 写控制流**(循环、条件、中间变量),离散工具调用 round-trip 太多。
- 任务需要**多模态观察**(看截图、图表、视觉布局)才能决策。

> 👉 **核心原则:动作范式是一阶架构轴,选错会让下游全部跟着错。** 它决定你能用哪些框架、要不要沙箱、trace 长什么样——所以**先于框架决策树**回答(`2-framework/01-decision-tree.md` 的"系统形状 Q0"之前的前置问)。

---

## 二、方案一览表(三档动作原语)

| 方案 | 原理 / 特点 | 取舍(代价) | 适合场景 |
|---|---|---|---|
| **① function / tool calling** ⭐(默认) | 模型吐结构化 `args` 调离散工具;**可校验、可审计、可重放** | 工具多 / 要组合控制流时 **round-trip 多**;约 10–20 工具后选择错误率上升 | 目标系统**有 API**;动作可枚举成离散几步;要强审计/合规 |
| **② CodeAct / code-as-action** | 模型**直接写并执行代码**当作一个动作,在代码里组合多工具、跑循环/条件/中间计算 | **必须沙箱**(执行任意代码);调试/审计比离散调用难;失败更难定位 | 工具多 / 需组合编排 / 有控制流;`smolagents` 默认走这档,Manus 以它为核心(**现查**框架默认) |
| **③ computer-use / browser-use** | **截图 + 点击/键入**操作 GUI;兜底无 API 的系统,并提供**多模态观察** | **慢、脆**(UI 一变就崩)、**blast radius 最大**;需虚拟桌面 + 强护栏 | 目标**无 API**只剩界面;或必须"看得见"的视觉观察(代表实现:Anthropic computer use、OpenAI Operator,**现查**) |

> 三档是**可叠加**的:主循环用 function-calling,某个无 API 的子任务降级到 browser-use 当"一个工具",并不矛盾。先用最轻的,真到了再局部升级。

---

## 三、选型轴(判据:三问)

| 轴 | 问什么 | 偏向 |
|---|---|---|
| **有无 API** | 目标系统/动作面有没有可编程接口(REST/SDK/DB/MCP server)? | 有 → ①/②;**完全没有** → ③ |
| **要否组合控制流** | 一个任务里要不要在多工具间组合、写循环/条件/中间变量? | 否(离散可枚举)→ ①;是(要编排数据流)→ 评估 ② |
| **要否多模态观察** | 决策是否依赖读截图/图表/视觉布局? | 否 → ①/②;是 → ③(即便有 API,也可能要 GUI 提供"看得见"的观察面) |

> 这三轴**相互独立**,按顺序问:先"有没有 API"(否决式,无 API 直接逼向 ③),再"要不要组合控制流"(在有 API 内部决定 ① vs ②),最后"要不要视觉观察"(正交,可把 ③ 拉回来当观察手段)。

---

## 四、快速决策树

```
Q0. 目标系统 / 动作面有没有可编程 API(REST/SDK/DB/MCP server)?
│
├─ 有 API
│    └─ Q1. 一个任务要不要在多工具间组合 + 写控制流(循环/条件/中间变量)?
│          ├─ 否(几步离散、可枚举)        → ⭐ function/tool calling(默认,别上沙箱)
│          └─ 是(工具多 / 要编排数据流)   → 评估 CodeAct(省 round-trip),代价 = 必须沙箱
│
└─ 无 API,只能操作 GUI(遗留系统 / 第三方网站 / 桌面软件)
     └─ Q2. 真的没有任何替代入口吗(官方 API / RPA / 逆向接口)?
           ├─ 有替代  → 回到 function-calling,别碰 GUI(慢/脆/危险)
           └─ 只剩 GUI → computer-use / browser-use(虚拟桌面 + 强护栏,blast radius 大)

正交叠加:决策要不要"看得见"(读截图/图表/视觉布局)?
     └─ 需要 → 即便有 API,也可叠加 browser/computer-use 提供多模态观察面
```

---

## 五、它如何决定下游(选完这层,下面跟着被约束)

| 下游层 | ① function-calling | ② CodeAct | ③ computer/browser-use |
|---|---|---|---|
| **编排框架**(`2-framework/`) | 几乎所有框架原生支持,自由选 | 偏 `smolagents` / 自建 code-executor / Manus 式(**现查**) | `browser-use` 库 / Operator 式 / 自建 GUI agent loop |
| **沙箱·护栏**(`7-safety-guardrails.md`) | 一般不需沙箱(工具各自鉴权 + 审批闸) | **必须沙箱**(隔离任意代码执行) | **必须虚拟桌面隔离 + 强审批**,blast radius 最大 |
| **工具路由**(`4-tools.md`) | 工具多时上 RAG-over-tools 收窄 | 代码即组合,工具爆炸用 `import` 缓解,弱化路由 | 无"工具清单",动作 = UI 操作 |
| **可观测形态**(`5-observability-eval.md`) | trace 每次 tool call(结构化、好审计) | trace 代码块 + stdout / exec 结果(要记录执行 IO) | trace 截图序列 + 点击轨迹(重,需录屏 / 步骤回放) |

> 👉 一句话:**function-calling 让审计与沙箱都省心;每往右一档,沙箱与观测成本陡增**。这正是"默认从左起步"的根因。

---

## 六、最轻起步 & 降级意识(每档都有"先不做")

- **整体默认 = ① function-calling 起步。** 它离散、可校验、可审计,绝大多数有 API 的系统够用——**先不上 CodeAct、先不上 GUI**。
- **②的"先不做":** 遇到"工具太多 / round-trip 多",**先试 RAG-over-tools / 分层工具**(见 `4-tools.md`)和 plan-and-execute 压调用数;这些都不够、确实要在动作里跑控制流时,**才**升 CodeAct——且同时把沙箱(`7-safety-guardrails.md`)一起立起来,二者绑定不可拆。
- **③的"先不做":** 看到"没有 API"先别急着上 GUI——**先找替代入口**(官方/隐藏 API、RPA、合作方接口)。GUI 自动化是**最后兜底**:慢、脆、blast radius 大,只在确实只剩界面、或必须视觉观察时才用,并配虚拟桌面 + 危险动作 HITL 审批。
- **升级是局部的,不是全局的。** 主循环留在 function-calling,只把那个无 API 的子任务包成一个 browser-use 动作即可——别为一个子问题把整个 Agent 换范式。

---

## 七、场景推荐

| 场景 | 推荐档位 |
|---|---|
| 标准业务 Agent(有 API、动作可枚举) | ⭐ function/tool calling |
| 数据/表格批处理、要在动作里跑循环+中间计算 | CodeAct(沙箱执行) |
| 工具数十上百、需自由组合编排 | CodeAct;或 function-calling + RAG-over-tools(先试后者) |
| 操作无 API 的遗留系统 / 第三方网站 | browser/computer-use(强护栏,兜底) |
| 决策依赖读截图 / 视觉布局 | computer/browser-use 提供多模态观察 |
| 编码 / SWE agent | function-calling(文件/shell 工具)+ 受控代码执行;按需 CodeAct |
| 合规/强审计场景 | 尽量 function-calling(离散可审计),慎用 ②③ |

---

## 八、接入 Spec-Kit(可复制 prompt 块)

```
请用 roadmap/agent-selection/0-action-paradigm.md 为本 feature 定**动作范式**(先于框架与工具选型)。
- 目标系统/动作面:有无可编程 API(REST/SDK/DB/MCP)<…>
- 一个任务是否需在多工具间组合 + 控制流(循环/条件/中间变量)<…>
- 是否需要多模态观察(读截图/图表/视觉布局)<…>
- 约束:审计/合规要求 <…> / 能否提供沙箱·虚拟桌面 <…>
请按三轴(有无 API / 要否组合控制流 / 要否多模态观察)给:推荐档位(默认 function-calling 起步)
+ 备选 + 代价 + "先不做/最轻起步"路径,并说明它对下游框架、沙箱(7-safety)、观测形态的影响。
产品名(Operator / computer use / smolagents 默认等)请现查,不要写死过期快照。
```

定下后接力:动作范式 = ① → 进 `roadmap/agent-selection/2-framework/01-decision-tree.md` 选框架;
= ②/③ → 同时进 `roadmap/agent-selection/7-safety-guardrails.md` 立沙箱/护栏。

---

## 九、交叉引用 + 相关资产

- 心智模型(权威源):`/Users/ming/Documents/ai-agent-learn/agent/interview/1.md` «L1 底层契约·Action 范式谱»(本页是其在选型矩阵里的前置分叉化)。
- 下游前置:`roadmap/agent-selection/2-framework/01-decision-tree.md`(框架决策树——本页是它"系统形状 Q0"之前的上游前置问)。
- 绑定层:`roadmap/agent-selection/7-safety-guardrails.md`(选 ②CodeAct/③GUI 必同时立沙箱·护栏)。
- 相邻层:`roadmap/agent-selection/1-model.md`(模型层,正交)、`roadmap/agent-selection/4-tools.md`(工具路由)、`roadmap/agent-selection/5-observability-eval.md`(观测形态随范式变)。
- 总览:`roadmap/agent-selection/README.md`。沉淀:`skills/adr-writer`。

> **最后核对:2026-06**
