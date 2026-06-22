# AI Agent 架构选型矩阵(总览)

> **用途**:一张总图,把所有"选型决策资产"按**层**串起来。做 Agent 架构设计时,从这里出发,按需进对应的层级决策包。
> **适用**:Spec-Kit `/plan` 阶段的总入口;或直接调 `stack-selector` skill 由它路由。
> **最后核对:2026-06**。
> **核心理念**:"AI Agent 架构选型"不是一个决策,而是**横跨多层的一组平行决策**。每层独立选、各有备选,最后拼成完整技术栈。

---

## 一、六层选型地图

| 层 | 决策什么 | 决策资产 | 触发时机 | 课程 |
|---|---|---|---|---|
| 🧠 **模型层** | 用哪个 LLM(每个节点) | [`1-model.md`](1-model.md) | 新建任何 LLM 节点 | 02 |
| 🏗️ **编排框架层** | 用哪个框架/SDK 编排 | [`2-framework/`](2-framework/) | 定系统骨架时 | 11,13,25,07,09 |
| 📚 **检索栈层** | 向量库/embedding/chunking/retriever/进阶方法/GraphRAG/RAG框架 | [`3-retrieval.md`](3-retrieval.md) | RAG/知识检索类 | 04,05,06,18 |
| 🔧 **工具层** | 100+ 工具如何路由选对 | [`4-tools.md`](4-tools.md) | 工具规模大时 | 09,10 |
| 🔍 **可观测/Eval 层** | tracing 平台 + eval 方案 | [`5-observability-eval.md`](5-observability-eval.md) | 上生产/要迭代(横切) | 21,24,05 |
| 🧩 **记忆层** | 记忆类型/存储/更新模式 | [`6-memory.md`](6-memory.md) | 要跨会话记忆时 | 12 |

> 协议层(MCP/A2A/ACP)与上面所有层**正交**,作为加分项叠加,不单列选型——详见 `2-framework/03-framework-profiles.md`。

---

## 二、架构分层图

```
┌──────────────────────────────────────────────────────┐
│  🔍 可观测性 / Eval  (横切:贯穿所有层,上生产必备)        │
├──────────────────────────────────────────────────────┤
│  🏗️ 编排框架层   LangGraph / crewAI / Haystack / 裸SDK  │  ← 系统骨架
│     ├─ 📚 检索栈   向量库+embedding+chunk+rerank        │  ← 能力
│     ├─ 🧩 记忆     semantic/episodic/procedural         │  ← 能力
│     └─ 🔧 工具层   function calling + MCP + 工具路由     │  ← 能力
├──────────────────────────────────────────────────────┤
│  🧠 模型层      轻量 / 主力 / 旗舰 / 自托管(按节点分档)   │  ← 底座
└──────────────────────────────────────────────────────┘
       协议层(MCP/A2A/ACP)正交叠加于工具/agent 接入
```

---

## 三、一次完整选型的推荐顺序

不是所有层一起拍,有先后依赖:

```
① 先定形状与骨架
   业务/数据形状 → 编排框架(2-framework/)
   同时给主循环选 模型档位(1-model)
        │
② 再定能力层(按业务需要,可并行)
   RAG-first?      → 检索栈(3-retrieval)
   要跨会话记忆?   → 记忆(6-memory)
   工具很多?       → 工具路由(4-tools)+ MCP
        │
③ 最后定横切层
   上生产/要迭代   → 可观测 + Eval(5-observability-eval)
        │
④ 沉淀
   重大决策 → skills/adr-writer 写 ADR
```

> ⚠️ **每层都要有备选**(哪怕是"先不做/裸 SDK 起步")。**从最轻方案起步,复杂度真的到了再升级**——过早上重栈是 Agent 项目最常见的过度工程。

---

## 四、怎么用

- **快速、交互式**:调 `stack-selector` skill —— 它识别你要选哪几层,逐层跑决策流,最后汇总成一份带备选+理由的选型小结。
- **手动 / 在 plan 里**:按本表进对应层的决策包,每个包都有"接入 Spec-Kit"的可复制 prompt 块。
- **沉淀**:定下后用 `skills/adr-writer` 把"为什么选 X 不选 Y"写成 ADR。

---

## 五、资产清单

| 资产 | 层 | 形态 |
|---|---|---|
| `roadmap/agent-selection/1-model.md` | 模型 | 单文件包 |
| `roadmap/agent-selection/2-framework/` | 编排框架 | 多文件包(决策树/评分卡/画像/场景/集成) |
| `roadmap/agent-selection/3-retrieval.md` | 检索栈 | 单文件包 |
| `roadmap/agent-selection/4-tools.md` | 工具 | 单文件包 |
| `roadmap/agent-selection/5-observability-eval.md` | 可观测/Eval | 单文件包 |
| `roadmap/agent-selection/6-memory.md` | 记忆 | 单文件包 |
| `skills/stack-selector/` | 路由 | skill(总入口) |
| `skills/framework-selector/` | 编排框架 | skill |
| `skills/adr-writer/` | 沉淀 | skill |

> 维护:各包结论为 2026-06 快照,Agent 生态迭代快,建议 6 个月复核;新增层时回填本表。
