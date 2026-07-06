# L12 · Day-Two 运维：安全、扩展与分布式追踪（含全课收官）

> 课程：A2A: The Agent2Agent Protocol（DeepLearning.AI × Google Cloud × IBM Research）
> 本课任务：从 notebook 原型走向生产环境必须补齐的三项 **day-two operations**——**Security（鉴权）、Extensibility（协议扩展）、Observability（调试多级 agent 链）**。纯概念课 + 收官篇，含 Conclusion 要点与全课回顾。

## 0. 三个 day-two 命题

前面所有课的 agent 都在本地裸跑、无严格鉴权。真实世界里：你不想让未授权的 agent 查询你的医疗提供者数据库、刷爆你的 LLM 账单；标准 schema 装不下你的业务私货；L10 那种 concierge → research → search 的链路断了不知道断在哪。A2A 对这三题都有内置答案。

## 1. 安全：TLS 强制 + AgentCard 声明鉴权方案

A2A 构建在标准 Web 协议之上，安全也直接复用 Web 安全的成熟件：

| 组件 | 规定 |
|---|---|
| 传输加密 | **TLS/HTTPS 对生产 A2A agent 是强制的**（mandatory），加密传输中的数据 |
| 鉴权声明 | AgentCard（L2）内含 **security schema**，告诉 client 该怎么鉴权 |
| 支持的标准方法 | API keys、OAuth 2.0、OpenID Connect（OIDC） |

鉴权握手流程（Agent A 调 Agent B）：

```mermaid
sequenceDiagram
    participant A as Agent A
    participant Card as AgentCard(B)
    participant IdP as Identity Provider
    participant B as Agent B
    A->>Card: ① 发现（读 security schema：B 要求 token）
    A->>IdP: ② 取 token（向身份提供方获取 token）
    A->>B: ③ 请求 + Authorization: Bearer &lt;token&gt;
    B-->>A: ④ 验明来者身份 → 应答 或 403 Forbidden
```

代码层面**不用手动设 header**：凭证从 credential store 加载，**AuthInterceptor** 自动读取 server 的 AgentCard、找到要求的 scheme（如 `my_auth_scheme`）、注入正确的 header。

> **架构师视角**：A2A 安全设计的全部聪明之处在于**一件新事都没发明**——TLS、OAuth、OIDC、Bearer token 全是 Web 界跑了十几年的老件，A2A 只规定"鉴权要求写进 AgentCard、由协议层自动协商"。这意味着企业现有的 IdP、密钥管理、网关策略可以原样接入 agent 网络。评估任何新协议时，"复用了多少既有标准"比"发明了多少新概念"更能预测它的存活率。

## 2. 扩展：extension 字段，不碰标准字段

A2A 为兼容性定义了严格的 message/task schema——但业务总有标准之外的需求：传计费码、时延要求、实验性 feature flags。规矩是：

1. **不要覆写标准字段**；用几乎所有主要对象（AgentCard、Message、Task）上都有的专用 **extension 字段**，传任意数据字典。例：保险 agent 要向研究 agent 收查询费，就带上自定义扩展 `x-billing-cost`；
2. **协议规定：不认识的 extension 必须忽略而不是崩溃**（must simply ignore）——向后兼容由此保住；
3. **任何人都可以定义、发布、实现 extension**——协议的适应性与专业化多 agent 系统的工程空间都从这来。

## 3. 可观测：OpenTelemetry 式分布式追踪

怎么调试 L10 那种 concierge 调 research、research 可能再调 search 的系统？坏在哪一环？

A2A 是 agent 间的**通信协议**，天然与分布式追踪标准（**OpenTelemetry**）合拍：**trace ID 放进请求 header，随请求在 concierge → research agent → policy agent 之间逐跳传递**，最后用 Jaeger / Zipkin / Google Cloud Trace 这类工具可视化整条请求生命周期——**哪怕链路跨组织、跨网络**。课程用 Arize 平台展示了实例。

> **对比 5-observability-eval.md**：注意分层——L10 BeeAI 的 trajectory middleware 和 L11 的 TrajectoryExtension 是**框架内**观测（单 agent 的 think/tool 循环），本课的 OTel trace 传播是**协议层**观测（跨 agent、跨框架、跨组织的调用链）。5-observability-eval 里 LangSmith/Langfuse/Phoenix 解决前者；一旦系统是多框架 A2A 拼装，**唯一能贯穿全链路的锚点就是随 header 传播的 trace ID**——选观测方案时先问"我的链路跨不跨框架边界"，跨了就必须押 OTel 兼容的方案。

结语：标准 Web 安全 + 灵活扩展 + 分布式追踪，三件合一，A2A 支撑起 resilient、secure、scalable 的分布式 agent 系统。技术内容到此收束——从 A2A 的"为什么"，经架构与代码实现，到企业级进阶考量。

## 4. 全课收官

### 4.1 Conclusion 字幕要点

- 全课路径：**为什么 A2A 有价值 → 核心原理 → 亲手构建并运行 A2A agent**；
- 定性判断：A2A 标志着生成式 AI 行业的**成熟**——"孤立 bot 的蛮荒西部（wild west）终结，**internet of agents** 开始"；靠严谨、标准化、安全的自主系统协作方法，解锁以前不可能的**复杂多厂商工作流**；
- 资源与治理：示例代码在 **a2a-samples** 仓库，官方代码全部归口 **google-a2a** GitHub organization；协议**社区治理、开放**（community governed and open），欢迎提 PR 改进协议或分享实现。

### 4.2 L1-L12 全课回顾

| 课 | 一句话 |
|---|---|
| L1 | 为什么要开放标准：agent 生态缺"协作层"协议，A2A 补位并解锁跨团队/跨厂商用例 |
| L2 | 架构与生命周期：HTTP/JSON-RPC/gRPC/SSE 之上的标准数据结构（AgentCard/Task/Message），任何框架的 agent 包一层即可互通 |
| L3 | 系统起点：Vertex AI 上裸写保险条款 QA agent（Policy Agent 雏形），无任何协议包装 |
| L4 | A2A Python SDK 把 Policy Agent 包成 **A2A server**——只需关心"收到请求后干什么" |
| L5 | 手写 **A2A client** 与 server 通信，走完发现→请求→响应全流程 |
| L6 | Google **ADK** + Gemini 构建 Research Agent（Google Search），体验框架内置 A2A 集成 |
| L7 | ADK **SequentialAgent** 用 A2A client 串联两个 server，结果逐级传递——顺序工作流 |
| L8 | **LangGraph + MCP** 构建 Provider Agent：MCP 拿数据（doctors.json）、A2A 供协作——双协议同框 |
| L9 | **Microsoft Agent Framework** 的 A2A client 连 LangGraph agent——第四个框架进场，互操作再验证 |
| L10 | **BeeAI RequirementAgent** 把三个异构 agent 编排成多 agent 系统，编排器自己也注册成 A2A server——递归组合收官 |
| L11 | 生产部署难题与 **Agent Stack**：六项 plumbing 清单、四路线取舍、不改逻辑只加接线 |
| L12 | Day-two 运维：TLS+AgentCard 鉴权、extension 字段扩展、OTel 分布式追踪 |

> **架构师的裁决**：什么时候引入 A2A？判据不是"agent 多不多"，而是**边界**。① 所有 agent 由一个团队、一个框架、一个进程域内开发部署——单框架内部编排（ADK SequentialAgent、LangGraph 子图、BeeAI HandoffTool 本地版）就够，塞 A2A 只会白付网络跳、鉴权、版本协商的税；② 一旦出现**组织边界**（别的团队/厂商的 agent）、**框架边界**（LangGraph 要调 ADK）、**信任边界**（需要独立鉴权计费）、**生命周期边界**（各 agent 独立部署升级）中的任何一条，A2A 的标准化成本立刻回本——这正是微服务 vs 单体的判断在 agent 世界的重演。中间态是务实解：先单框架编排起步，把每个 agent 写得"随时可包成 A2A server"（L4 证明这只是薄薄一层），边界出现时再付协议税。

## 5. 本课总结

| 要点 | 一句话 |
|---|---|
| 安全 | 生产强制 TLS；AgentCard security schema 声明鉴权（API key/OAuth2/OIDC），AuthInterceptor 自动注入 Bearer token，不合法 403 |
| 扩展 | 不覆写标准字段，用 extension 字段传自定义数据（如 x-billing-cost）；不认识的扩展必须忽略；人人可定义发布 |
| 可观测 | trace ID 随 header 跨 agent 逐跳传播，OTel 生态（Jaeger/Zipkin/Cloud Trace/Arize）可视化全链路 |
| 收官 | A2A = 行业成熟标志，internet of agents；社区治理，代码归口 google-a2a org |

## 与我的资产映射

- 观测与评估层：`agent/skills/agent-selection/5-observability-eval.md`（补入"框架内 trajectory vs 协议层 OTel trace"两层观测的分界与选型触发器）
- 安全护栏：`agent/skills/agent-selection/7-safety-guardrails.md`（A2A 的鉴权/403 模型是 agent 间信任边界的协议级实现）
- 协议层：`agent/skills/agent-selection/2-framework/06-protocols.md`（extension 机制 + "忽略未知扩展"的兼容性设计，可作协议演化性评估维度）
- 面试包：`agent/interview/jd-senior-agent-engineer/`（"多 agent 系统怎么做安全与追踪""什么时候用 A2A"两道高频题的答案骨架在本篇 4.2 裁决块）
- [[project_selection_matrix]]
