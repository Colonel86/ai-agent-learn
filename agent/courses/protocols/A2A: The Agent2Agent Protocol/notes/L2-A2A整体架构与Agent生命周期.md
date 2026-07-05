# L2 · A2A 整体架构与 Agent 生命周期（Agent Card / Message / Task / 四种执行模式）

> 课程：A2A: The Agent2Agent Protocol（DeepLearning.AI × Google Cloud × IBM Research）
> 本课沿"**Agent A 需要 Agent B 做一件事**"这条主线，走完 A2A 的核心构建块：发现（Agent Card）→ 通信（传输绑定）→ 生命周期（Message / Task / Artifact + 四种执行模式）。细节以官方规范文档为准。

## 1. A2A 在技术栈里做什么

A2A 把 agent 工作流的复杂性**抽象成一门通用语言**：标准化的数据结构 + 对外通信方法。它复用标准 Web 技术在独立系统之间通信：

| Web 技术 | 在 A2A 中的角色 |
|---|---|
| HTTP | 底层传输 |
| JSON-RPC / gRPC / HTTP+JSON（REST 风格） | 三种协议绑定（protocol bindings） |
| Server-Sent Events（SSE） | 流式推送 |

结论：**任何框架**建好的 agent，包一层就成为 A2A agent，即可与任何其他 A2A agent 协作。

## 2. 角色设定：client agent 与 remote agent

| 角色 | 定义 |
|---|---|
| **Client agent**（Agent A） | 向 remote agent 发起请求的一方；**通常是直接与最终用户交互的 agent** |
| **Remote agent**（Agent B） | 被请求方，实际干活的 agent |

```
用户 ──► Agent A (client) ──①发现──► agent-card.json
                │                        │
                └────②按 card 的 URI/绑定/鉴权 发请求────► Agent B (remote)
                ◄────③Message（快）或 Task（慢）──────────┘
```

## 3. 发现：Agent Card

Agent A 怎么找到 Agent B、并知道它能干什么？——每个 A2A agent **必须发布一张 Agent Card**：一个 JSON 文件，通常托管在 agent server 的 well-known URL：

```
https://<agent-host>/.well-known/agent-card.json
```

（本课程假设 agent 的 URL 已知；agent discovery 与 registry 见课程补充材料。）

Agent Card 是 agent 的**数字名片**——类比 web 爬虫的 `robots.txt`、REST API 的 Swagger/OpenAPI 定义，但**专为 agentic 能力定制**。Agent B 的 card 告诉 Agent A 开启对话所需的一切：

| Card 字段（按字幕） | 内容 |
|---|---|
| name | agent 叫什么 |
| 能力描述 | 它能做什么 |
| protocol version | 用的哪个协议版本 |
| URI + protocol bindings | 去哪、用哪种绑定说话 |
| media types | 支持哪些媒体类型 |
| capabilities | streaming、push notification、custom extensions 等特殊能力 |
| authentication | 如何鉴权 |

> **对比 06-protocols.md / 课程 10-MCP**：MCP 的能力发现是连接后调 `list_tools` 拿**工具清单**（进程级、拿到的是函数 schema）；A2A 的发现是抓一个**静态 well-known JSON**（Web 级、拿到的是"名片 + 合同"，含鉴权与传输元数据）。前者假设你已经决定连它，后者支持**先浏览再决定**——这正是选型矩阵里 A2A "运行时发现对端"回本条件的技术底座。而两者都逃不掉注册表问题：矩阵对 MCP 的建议（小团队先维护一张清单，别先上发现服务）对 A2A registry 同样适用。

## 4. 通信：三种协议绑定 + 四种执行模式

Agent B 的 card 声明了该用什么 URI、什么绑定；Agent A 照着发请求即可。协议支持 **JSON-RPC、gRPC、HTTP+JSON（REST 风格接口）** 三种绑定。

其上是**四种执行模式**——这是本课的主骨架：

| 模式 | 一句话 | 适用 |
|---|---|---|
| Synchronous | 等一个立即回复 | 简单、能快速完成的请求 |
| Asynchronous | 不阻塞，拿 task ID 轮询 | 复杂、耗时的请求 |
| Streaming | 连接保持打开，对端持续推送 | 要看实时进度 / 边生成边看 |
| Push notifications | 留一个回调 URL，事件发生时对方主动推 | 不知道对端**何时甚至是否**会回复 |

## 5. 同步起步：Message 与 Part

Agent A 用 **`message/send`** 方法发出一个包在 SendMessageRequest 里的 **Message 对象**：

- **Message = 对话中的一轮**（one turn），比如 Agent A 问一个问题；
- Message 有 **Role**（`user` / `agent`），并包含若干 **Parts**；
- **Part = 实际内容**：纯文本、文件、多模态数据、或结构化 JSON。

如果请求简单、完成得快，Agent B **直接回一个含答案的 Message**——这就是同步模式的全部。

## 6. 异步与生命周期：Task、Status、Artifact

请求复杂或耗时怎么办？不能让 Agent A 干等。Agent B 可以**不回 Message，改回一个 Task 对象**：

- **Task = agent 要做的那件工作**；
- 字段：**ID**、**context ID**（与相关 Message 对应/关联）、**Status**；
- **Status 表示 Task 生命周期的当前状态**：

```
submitted ──► working ──► completed ✔ (终态)
                 │   └──► failed    ✘ (终态)
                 ▼
          input-required        （Agent B 需要最终用户补充信息）
```

异步流程：Agent A 发初始请求 → Agent B 回 **task ID + 当前 status** → Agent A 拿着 task ID **轮询 `tasks/get`** 拿更新 → 最终 `tasks/get` 返回 completed，**任务产出放在 artifacts 字段**。

- **Artifact** 结构与 Message 类似：有 **artifact ID** 和 **Parts**（装实际响应内容）。

注意一个协议要点：**回 Task 还是回 Message 由 Agent B 决定，Agent A 必须两种情况都能处理**。

> **架构师视角**：Message/Task 二选一 + Status 状态机，本质是把"**agent 的活可能很慢、可能中途要人**"这个现实做进了协议第一等公民——对照我面试包 `01-agent-run-loop-and-orchestration` 的 run-loop：input-required 就是协议化的 HITL 暂停点，context ID 就是跨轮会话关联。普通 RPC 假设"调用即返回"，A2A 假设"调用即开工单"。设计自家 agent 网关时照抄这个状态机，比自己发明 pending/running/done 枚举省掉一轮踩坑。

## 7. 流式与推送：两种"别让我轮询"的方案

**Streaming（SSE）**：轮询对简单场景够用，但要**快速更新**就低效了。若 Agent B 的 card 声明支持 streaming，Agent A 改用 **`message/stream`** 方法——连接保持打开，Agent B 边发生边推送：

| 推送内容 | 例子 |
|---|---|
| 初始 Task 对象 | 开工单 |
| Task status update events / Message | "正在处理 X 部分"、"任务已完成" |
| Task artifact update events | 结果较大（如长摘要）时**分块流式**：第一段、第二段…… |

对用户的价值：**看得到实时进度，答案边生成边出现**。

**Push notifications（webhook）**：完全不知道 Agent B 何时/是否回复时用。通过 **`tasks/pushNotificationConfig/set`** 方法设置，**或在发第一条消息时带上配置**：Agent A 提供一个 **callback URL**，Agent B 在**任务状态变化或 artifact 就绪**时主动向该 URL 推送通知。

## 8. 本课边界

本课覆盖了 A2A 的基础方法与数据结构；**observability、security、extensions** 等更复杂的部分留待后面章节。下一步：用 **A2A Python SDK** 在代码里使用协议。

## 9. 本课总结

| 要点 | 一句话 |
|---|---|
| 技术底座 | HTTP + JSON-RPC/gRPC/HTTP+JSON 三绑定 + SSE，标准 Web 技术拼装 |
| 角色 | client agent（发请求、通常面向用户）vs remote agent（干活） |
| 发现 | Agent Card @ `.well-known/agent-card.json`——数字名片：能力/版本/绑定/媒体类型/streaming 等 capabilities/鉴权 |
| 数据三件套 | Message（一轮，Role+Parts）/ Task（工单：ID+context ID+Status）/ Artifact（产出：ID+Parts） |
| 生命周期 | submitted → working →（input-required）→ completed / failed |
| 四种执行模式 | 同步回 Message；异步回 Task+轮询 `tasks/get`；streaming 走 `message/stream`；push 走 callback URL |
| 协议要点 | 回 Message 还是 Task 由 remote 决定，client 两者都要能处理 |

> **记忆点（引出 L3）**：架构图看完了，该造第一块砖。L3 先不碰 A2A——用 **Claude on Vertex AI** 裸建一个回答保险问题的 QA agent，让它先能干活；L4 再把它包进 A2A server、发出自己的第一张 Agent Card。

## 与我的资产映射

- 协议层单页：`agent/skills/agent-selection/2-framework/06-protocols.md`（A2A 条目 = 本课的"发现 + 通信"两件事；跨信任域鉴权在 §八 攻击面清单）
- 框架画像：`agent/skills/agent-selection/2-framework/03-framework-profiles.md`（后续各课的 server/client 宿主框架画像）
- 面试包：`agent/interview/jd-senior-agent-engineer/01-agent-run-loop-and-orchestration.md`（Task 状态机 ↔ run-loop 的暂停/恢复、HITL 闸门；四种执行模式是"长任务 agent 网关怎么设计"的标准答案）
- [[project_selection_matrix]]
