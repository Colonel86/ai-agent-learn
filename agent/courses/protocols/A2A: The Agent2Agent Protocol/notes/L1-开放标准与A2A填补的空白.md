# L1 · 开放标准与 A2A 填补的空白（HTTP 类比 / 治理 / vs MCP）

> 课程：A2A: The Agent2Agent Protocol（DeepLearning.AI × Google Cloud × IBM Research）
> 本课三件事：**开放标准为什么重要**、A2A 在演进中的 agent 生态里填了什么空白、它解锁哪些使用场景。纯概念课，无代码。

## 1. 空白在哪：框架繁荣，互不兼容

AI 应用正从基础对话 chatbot 快速演进为**agentic 系统**：会推理（reasoning）、规划（planning）、执行工具（executing tools）、管理多步工作流。复杂 agentic 系统依赖**多 agent 协作**达成共同目标——课程举例：trip planning agent，机票、酒店、活动各由不同 agent 负责，还要互相协调出最优行程。

问题：构建 agent 的框架非常多——LangGraph、Microsoft Agent Framework、Google ADK、CrewAI、BeeAI……**各自工作方式略有不同，开箱互不兼容**。所以需要一个共享协议，让 agent **无论用什么模型、什么框架**都能通信协作，多 agent 系统才能跨团队、跨组织地搭建。

## 2. 历史类比：A2A 是 agent 界的 HTTP

1989 年 Tim Berners-Lee 在 CERN 提出万维网，并开发了 HTTP。在 HTTP 之前，FTP、Telnet、Gopher 等多个协议各管一摊；HTTP 后来居上，靠的是**简单 + 开放治理（openly governed）**，由此点燃了 Web 的爆发式增长。

```
1990s Web                          2025+ Agents
─────────────                      ─────────────
FTP / Telnet / Gopher   各管一摊    各框架私有的 agent 通信方式
        │                                  │
        ▼  简单 + 开放治理                  ▼  同一逻辑
      HTTP  ──────────────────────►      A2A
   （任何浏览器 ↔ 任何服务器）      （任何模型/语言/框架的 agent 互通）
```

A2A 的定位就是 **"HTTP for agents"**：让来自任何模型、语言、框架的 agent 用标准化的结构与方法通信。

## 3. 治理与现状（开放标准的"开放"落在哪）

| 事实 | 内容 |
|---|---|
| 发布 | Google 于 **2025 年 4 月**推出 A2A |
| 捐赠 | **2025 年 6 月**捐给 Linux Foundation → 开源、社区治理 |
| 合并 | IBM 的 **Agent Communication Protocol（ACP）** 已并入 A2A |
| 决策机制 | Technical Steering Committee（TSC），成员来自**八家**关键科技企业（含 Google） |
| 中立性 | Linux Foundation 提供 vendor-neutral 的家——协议按**生态与社区的集体需要**演进，而非单一公司的利益 |
| 版本 | **1.0 即将发布**，与旧版本有重大变化（significant changes）——以 a2a-protocol.org 最新规范为准 |
| 采纳 | 协议的价值取决于采纳度；A2A 已有 **150+ 具名合作伙伴**，最新名单见官方文档 |

> **对比 06-protocols.md 的 ACP 消歧**：字幕里"被并入 A2A 的 ACP"是 **IBM 的 Agent Communication Protocol**（agent ↔ agent 轴，2025-08 停止独立演进）；我的协议页特意警告过还有一个**同名不同物**的 ACP——Zed 的 **Agent Client Protocol**（编辑器 ↔ 编程 agent，≈ LSP，独立且活跃）。速记：**一个已死（并入 A2A）、一个还活（Zed），且分属不同轴**。听课时凡出现 "ACP" 一律先问是哪个。

## 4. A2A 能做什么（能力清单）

- agent 之间**动态发现**（dynamically discover each other）；
- 通过标准化的 **task** 协作；
- **共享内容**（share content）；
- 处理**长时运行**与**流式**（long-running & streaming）过程；
- 以上全部具备**企业级安全**。

两条设计原则值得单独记：

1. **每个 agent 都是 opaque（不透明）的**——遵循协议**永远不需要**暴露实现细节；
2. A2A 聚焦的是 **agent 之间的桥梁**，包括**跨组织**的桥梁。

> **架构师视角**：opaque 是 A2A 与"框架内多 agent"的本质分界。框架内协作（LangGraph 子图、crewAI crew）默认共享代码与 state，是**白盒协作**；A2A 只暴露 Agent Card 声明的能力合同，是**黑盒协作**——这才可能跨团队、跨组织，因为对方永远不必给你看代码。代价是你也失去了对对端内部的观测与控制，信任要靠合同 + 鉴权而非代码审查（06-protocols.md §八：跨信任域要做对端身份校验与最小授权）。

## 5. A2A vs MCP：互补，不是竞争

关于 A2A 最大的问题就是它与 Anthropic 创建（现同样捐入 Linux Foundation）的 **MCP** 的关系。答案：**互补协议**。

| | MCP | A2A |
|---|---|---|
| 连接对象 | agent ↔ **工具** | agent ↔ **对等 agent** |
| 本质 | 标准化的 **function calling**——替用户执行任务 | 协作、**委派任务**、管理共享工作流 |
| 对端特性 | 单一、通常**确定性**的任务 | **开放式问题求解者**：能处理歧义与多步工作流 |

成熟的 agentic 系统里通常**两个都用**：用 A2A 与其他 agent 协调，用 MCP 操作自己的工具完成分内工作。

**为什么不干脆用 MCP 通信 / 把 agent 当工具（agents as tools）？** 可以做，但会**降低 agent 的能力**：工具为单一、通常确定性的任务设计；agent 是开放式问题求解者，其处理歧义、多步工作流的能力**无法被单一 input/output schema 描述**。延伸阅读：goo.gle/agents-not-tools。

> **对比课程 10-MCP**：MCP 课教的是把工具收编进 `list_tools` 的平面清单——每个工具一个静态 schema，这正好反衬本课论点：schema 装得下工具，装不下 agent。我的 06-protocols.md 把这对关系钉成两层参考架构"**MCP 接工具/数据（L1）+ A2A 接 agent（L4）**"，并给出升级路径：**单 agent + 好工具(MCP) → 进程内多角色（框架原生 handoff）→ 真跨边界才上 A2A**。课程讲"能用 A2A 做什么"，选型矩阵补上"什么时候先别用"。

## 6. A2A 在 agent 技术栈中的位置

A2A 只是可能的 agent stack 中的**一环**：它作用于 **Agent orchestration 层**，与 Foundation models、存储、云基础设施、应用层等组件并列。

```
┌─────────────────────────────┐
│  Application 层              │
├─────────────────────────────┤
│  Agent orchestration 层      │  ← A2A 在这里
├─────────────────────────────┤
│  Foundation models           │
├─────────────────────────────┤
│  存储 / 云基础设施            │
└─────────────────────────────┘
```

## 7. 本课总结

| 要点 | 一句话 |
|---|---|
| 空白 | 框架繁多且互不兼容，缺一门跨模型/跨框架的 agent 共同语言 |
| HTTP 类比 | 简单 + 开放治理让 HTTP 胜出，A2A 沿同一路径做 "HTTP for agents" |
| 治理 | Google 发起（2025-04）→ Linux Foundation（2025-06），IBM ACP 并入，TSC 八家企业共治，150+ 伙伴 |
| 设计原则 | agent opaque（不暴露实现）、聚焦跨组织的 agent 间桥梁 |
| vs MCP | 互补：MCP 接工具（function calling），A2A 接对等 agent（委派协作）；agent 塞不进单一 I/O schema |
| 栈位 | Agent orchestration 层的一环 |

> **记忆点（引出 L2）**：本课回答了"为什么需要 A2A"；L2 回答"A2A 长什么样"——Agent Card 怎么当名片、client/remote agent 怎么握手、Message/Task/Artifact 三件套、以及同步/异步/流式/推送四种执行模式撑起的 agent 生命周期。

## 与我的资产映射

- 协议层单页：`agent/skills/agent-selection/2-framework/06-protocols.md`（A2A 何时回本、ACP 双缩写消歧、协议=新增攻击面——本课的官方叙事 + 矩阵的冷水判据合并食用）
- 框架画像：`agent/skills/agent-selection/2-framework/03-framework-profiles.md`（LangGraph / ADK / CrewAI / BeeAI 等"互不兼容的框架"各自画像）
- 面试包：`agent/interview/jd-senior-agent-engineer/01-agent-run-loop-and-orchestration.md`（agents-as-tools vs 对等协作的取舍是常考题）、`03-mcp-gateway-and-protocol.md`（MCP 侧对照）
- [[project_selection_matrix]]
