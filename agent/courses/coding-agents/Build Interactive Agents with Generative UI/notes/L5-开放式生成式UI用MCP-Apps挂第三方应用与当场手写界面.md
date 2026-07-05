# L5 · 开放式生成式 UI：用 MCP Apps 挂第三方应用 + 让 Agent 当场手写界面

> 课程：Build Interactive Agents with Generative UI（DeepLearning.AI × CopilotKit）
> 本课任务：走到生成式 UI 光谱**最远的一端**——先用 **MCP Apps** 把 Agent 接到 Excalidraw 这类第三方现成应用（和 ChatGPT/Claude 应用商店同一套协议），再打开 `openGenerativeUI` 让 Agent **当场生成任意 HTML/CSS/JS 界面**。核心张力：极致灵活 ⇄ 极难可控。

## 0. 承上：从「约束」到「拆掉约束」

前几课都在**约束** Agent 能展示什么——L3 用专用组件（受控）、L4 用积木目录（声明式）。L5 反过来，**移除这些约束**，分两条路：

```
生成式 UI 光谱
受控(L3) ──── 声明式(L4) ──────────── 开放式(L5) ─────────────────►
 专用组件      积木目录            ① MCP Apps：交给第三方现成应用
 最可控        有护栏的灵活         ② Open-Ended：Agent 当场手写全新界面
                                    最灵活、最不可控
```

## 1. 路线一：MCP Apps —— 借第三方应用的壳

不为每个新能力自建 UI，而是**把全栈 Agent 接到已经存在、自带 UI 与品牌的第三方应用**。开发者只需接线（wire up），Agent 自己决定何时调用、怎么交互。

**为什么值得**：MCP Apps 是 ChatGPT 与 Claude 应用商店支持的标准——意味着**用户在那些环境里用的同一批应用（Figma、HubSpot、Excalidraw……）可以原样搬进你自己的 Agent 应用**。

### 1.1 三段式架构

| 部件 | 职责 |
|---|---|
| **MCP Server** | MCP Apps 是对 MCP 协议的**扩展**：同一台服务原本就供你熟悉的 MCP tools，现在**还能供 UI resources**，可组装成 iframe 网页表示 |
| **Host 前端** | UI resources 被嵌进**双层 iframe**（隔离 + 安全） |
| **MCP App View** | iframe 里跑的那个 app，与宿主应用**隔离**，仅通过 **JSON-RPC** 与 host 前端通信 |

### 1.2 一个容易混淆的点：Apps 与 Tools 已解耦

字幕特意澄清：MCP Apps 由 MCP server 供，但**和该 server 返回的 MCP tools 完全独立**。

- 前身是老标准 **MCP UI**——它允许**任何 MCP tool** 在任意交互里可选地返回 UI resources；
- 演进为 **MCP Apps** 后，**把 UI resources 与 MCP tools 彻底解耦**：同一台 server 供两者，但**它们互不交互**。

另一设计要点是**渐进增强（progressive enhancement）**：host 支持 MCP Apps → 渲染富 UI；不支持 → 退化成普通 MCP tool 的文本输出，依然可用。

### 1.3 代码：一行 URL 接入 Excalidraw

CopilotKit 开箱托管，你只需把 server URL 交给 `CopilotRuntime`：

```ts
const runtime = new CopilotRuntime({
  agents: { default: appAgent },
  mcpApps: {
    servers: [
      { type: "http",
        url: "https://mcp.excalidraw.com",   // ← 只需一个 MCP server URL
        serverId: "example_mcp_server" },     //   没有单独给 app 的 URL
    ],
  },
});
```

CopilotRuntime **自动访问这些 server、判断是否供了 MCP apps**，并给 Agent 增补 app 发现能力。演示：`Show me a simple network diagram of three routers, two laptops and a server using excalidraw` → 一张真的 Excalidraw 图嵌进聊天。再追问「加标签、标题、更连贯」→ 有改善但**仍不完美**——这已经预演了开放式的取舍。

> **MCP Apps 的定位（何时不用）**：它是「一个设计成住在另一个 app 里的 app」，**天然带间接层开销（indirection overhead）**。字幕明确：**你通常不该把自己 app 的核心功能实现成 MCP app**。它高度优化于一个特定用例——把应用商店里的第三方应用搬进你的 Agent，附带「外部完全自定义品牌 + 与第三方服务交互」的好处，代价就是那层间接。

## 2. 路线二：Open-Ended Generative UI —— Agent 当场手写界面

光谱最远端：Agent **当场写全新应用**（HTML/CSS/JS），通常嵌进 AI 聊天里。给 Agent **完全的创作自由**。

代码同样一行开关：

```ts
const runtime = new CopilotRuntime({
  agents: { default: appAgent },
  openGenerativeUI: true,        // ← 打开：注入一个「开放式生成 UI」中间件到 AG-UI 栈
  mcpApps: { servers: [ /* Excalidraw ... */ ] },
});
```

底层机制与 A2UI 同构：**通过给后端 Agent 传一个特殊工具来实现**，经 AG-UI middleware 栈传播。演示：`Make it rain tacos!` → 界面**一块块流式构建**出来，得到「下塔可雨」的效果——但**有点怪**。再优化 prompt（用更像塔可的 emoji、让雨更像真雨）→ 好一些。

**取舍（字幕反复强调）**：

| 维度 | 开放式生成 UI 的表现 |
|---|---|
| 速度 | 更慢（当场生成） |
| 确定性 | 更低、更不一致 |
| 出错率 | 更高，「你永远不知道对面会给你什么」 |
| 质量敏感度 | **对模型选择、prompt、agent skills 极度敏感**——优化 prompt/skills 能显著改善 |
| 成熟度 | 仍处**探索阶段**，但随 AI 栈演进会占越来越大角色 |

> **架构师视角**：L3→L4→L5 是一条清晰的「**可控性 ↓、灵活性 ↑、成本/延迟 ↑**」单调曲线。L5 两条路解决的是同一个问题——**长尾请求宽到无法用固定组件库覆盖**——但手段不同：MCP Apps 是「**外包**」（借别人打磨好的成熟应用，把风险转移给第三方），Open-Ended 是「**自产**」（Agent 现写，风险自留、质量吃 prompt/skill）。架构判断：能外包就别自产——whiteboard/设计/规划这类「工具型任务」优先找现成 MCP App；只有当没有现成应用、且界面无需每次可靠时，才动用 Open-Ended，并把它当成**对 prompt engineering 和 skills 投资回报最高**的一段。

> **对比 A2A 客户端的「委派给远端 Agent」**：MCP Apps 与 A2A 是**同一种「把控制权交出去」的架构直觉，只是交给的对象不同**。A2A 客户端把**一个任务**委派给远端 **Agent**（对方自主完成、回传结果）；MCP Apps 把**一段 UI 交互**委派给远端**应用**（对方自带界面与品牌、经 JSON-RPC 回话）。两者都靠标准协议解耦、都让宿主「不必自建全部能力」。区别在粒度与产物：A2A 换回的是**任务结果/数据**，MCP Apps 换回的是**可交互的界面壳**。设计一个复杂 Agent 前端时，这两条「外包线」可以叠加——A2A 拿数据、MCP Apps 借界面。

> **记忆点（引出 L6）**：L3–L5 造的富 UI **都只活在聊天窗口里**。L6 要**冲出聊天窗口**——构建一个 Agent 与前端**共享同一份实时状态（shared state）**的全栈应用（一个「Agentic 待办板」）：Agent 从后端建待办、用户在前端勾选，两侧**自动双向同步**。这正是造 Claude Code / Cursor 式应用（across 法律/会计/营销各垂直）的地基，靠的是两个新原语——**前端工具调用**与**共享状态同步**。

## 本课总结

| 要点 | 一句话 |
|---|---|
| 开放式 = 拆约束 | 不再限于预注册组件/schema，Agent 可挂全应用或当场手写界面 |
| MCP Apps | 对 MCP 的扩展，同一 server 供 tools **也**供 UI resources；三段式（server/host/view），双层 iframe + JSON-RPC |
| Apps ≠ Tools | 从 MCP UI 演进而来，UI resources 已与 tools **彻底解耦**；渐进增强，不支持则退化为文本 |
| 一行接入 | `mcpApps.servers` 给 URL / `openGenerativeUI: true` 开关，底层都靠特殊工具经 AG-UI 传播 |
| 取舍 | 极致灵活但更慢、更不确定、更易错；对 prompt/skill/模型极敏感；仍探索阶段 |

## 与我的资产映射

- 呈现层选型：`agent/skills/agent-selection/10-agent-ux.md`（②生成式 UI 维度最重档——开放式生成 UI 的可控性/成本取舍，何时该退回受控/声明式）
- 工具/协议层：`agent/skills/agent-selection/4-tools.md` + `2-framework/06-protocols.md`（MCP Apps 作为 MCP 协议扩展；与 A2A「委派」直觉的对照）
- 安全：`agent/skills/agent-selection/7-safety-guardrails.md`（第三方应用嵌入的 trust/permissions/iframe 隔离护栏）
- [[project_selection_matrix]]
