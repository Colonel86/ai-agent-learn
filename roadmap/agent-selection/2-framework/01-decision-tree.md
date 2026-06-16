# 01 · 决策树:1 分钟快速排除

> 目的:用最少的问题把候选从"全市场"收敛到 **2-3 个**。决策树负责**排除**,不负责给最终答案——最终答案交给评分卡(`02`)。
> 用法:从 Q0 开始,顺着回答往下走。每个叶子给出"候选集",再去 `03` 画像里深挖。

---

## 前置:先分清"协议层"和"框架层"

很多人把 **MCP** 和 LangGraph 放一起比,这是错的——它们不是同一层:

| 层 | 是什么 | 例子 | 选型关系 |
|---|---|---|---|
| **协议层** | Agent 如何接入工具/上下文的标准 | **MCP**、ACP、A2A | 与框架**正交**,可叠加 |
| **框架/SDK 层** | Agent 的编排、状态、循环 | LangGraph、crewAI、LlamaIndex、裸 SDK | 决策树选的是这一层 |

> 👉 **MCP 几乎总是"加分项而非替代项"**:无论选哪个框架,只要要对接外部工具/数据源,都可以让它们以 MCP server 形式暴露。所以决策树不在 MCP 和框架之间二选一。

---

## 主决策树

```
Q0. 这个系统的"形状"本质是什么?
│
├─ A. 只要把 LLM 输出变成可靠的结构化数据(抽取/分类/改写),工具很少或没有
│      → 【裸 SDK + 类型层】  Anthropic/OpenAI SDK + Pydantic AI / Instructor
│      → 不要上重框架。理由:没有编排需求,框架只是负担。
│
├─ B. 核心是"问知识库/文档",检索质量是成败关键(RAG-first)
│      │
│      ├─ 主要是检索+生成,流程相对固定
│      │     → 【LlamaIndex】(数据连接器最全) 或 【Haystack】(管线工程化最强)
│      │
│      └─ 检索要"自主决策"(agent 决定查不查、查哪个索引、要不要 web fallback)
│            → 【LlamaIndex(Agentic RAG)】 或 【Haystack(ConditionalRouter)】
│            → 若同时要复杂状态控制,转 Q1 用 LangGraph + 检索工具
│
├─ C. 多个"角色/专家"协作完成一件事(规划者+执行者+评审者…)
│      │
│      ├─ 角色边界清晰、偏"团队分工"心智 → 【crewAI】(角色/任务抽象最直观)
│      ├─ 偏"对话式协作/可编程编排"      → 【AutoGen / AG2】
│      └─ 要对每个 agent 的状态与转移精细控制 → 【LangGraph(多 agent 图)】
│
├─ D. 单 agent,但流程复杂:有分支、循环、反思、Human-in-the-Loop、需要可恢复
│      → 转 Q1
│
└─ E. 绑定单一模型厂商,想要"官方最短路径"起步
       ├─ 全程 OpenAI → 【OpenAI Agents SDK】
       ├─ 全程 Anthropic → 【Anthropic SDK + 自建循环】(或 Claude Agent SDK)
       └─ 全程 Google/Gemini → 【Google ADK】
```

---

## Q1. 复杂单 agent / 状态控制分支

```
Q1. 你需要下面哪些"运行时能力"?(勾得越多越偏 LangGraph)
│
├─ [ ] 显式状态(state)跨步骤累积、可读可改
├─ [ ] 条件分支 / 循环 / 自反思(reflection)
├─ [ ] 持久化(checkpointer):可中断、可恢复、多会话
├─ [ ] Human-in-the-Loop:中途暂停等人审批
├─ [ ] 时间旅行(time-travel)/ 回放调试
│
├─ 勾选 ≥2  → 【LangGraph】 ✅(状态机式编排,这正是它的甜区)
├─ 勾选 =1 且只是"加个循环"  → 【Haystack(max_loops)】 或 【裸 SDK 手写循环】
└─ 勾选 =0  → 回到主树,你可能不需要状态图,选更轻的
```

---

## Q2. 横切约束(每个候选都要过一遍)

无论上面落到哪,以下约束可能**直接否决**某个候选:

| 约束 | 触发的取舍 |
|---|---|
| **团队不熟 / 要快速出 MVP** | 偏成熟生态(LangChain/LlamaIndex 文档多)或官方 SDK;避开小众框架 |
| **强可观测性要求(tracing 必须)** | 优先原生支持 LangSmith / Phoenix / Langfuse 的(LangGraph、LlamaIndex 友好) |
| **Eval 必须接现有框架** | 选 eval 友好的(见 `03` 各画像的 Eval 行) |
| **极致控制 / 怕黑盒 / token 敏感** | 偏裸 SDK 或轻框架(Pydantic AI),避开重抽象 |
| **怕 Vendor lock-in** | 避开绑死单一厂商的官方 SDK;选框架抽象层(可换底层模型) |
| **生产 serving / 部署** | 看是否有官方部署方案(LangGraph Platform、Haystack REST) |
| **合规 / 数据出域** | 影响模型与托管选择,通常与框架正交但要在 plan 里单列 |

---

## 决策树速记卡

| 你的场景一句话 | 首选候选 |
|---|---|
| 「我就要个可靠 JSON」 | 裸 SDK + Pydantic AI / Instructor |
| 「问我的文档/知识库」 | LlamaIndex / Haystack |
| 「让 AI 自己决定查不查资料」 | Agentic RAG(LlamaIndex)/ Haystack 路由 |
| 「几个角色分工干活」 | crewAI / AutoGen |
| 「流程要分支+循环+能暂停恢复」 | LangGraph |
| 「就用 OpenAI/Gemini 官方最短路」 | OpenAI Agents SDK / Google ADK |
| 「要接一堆外部工具(任何框架下)」 | 叠加 MCP |

> ✅ 决策树给的是**候选集**。两个及以上候选时,务必进 `02-scorecard.md` 做加权量化,别凭手感拍板。
