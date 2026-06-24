# 部署 / Serving 形态选型(同步 / 流式 / 异步后台 + 持久执行)

> **用途**:为 Agent 选**跑在什么基础设施形态上**——决定运行时基础设施,而非框架内部(`2-framework/`)、也不是前端事件如何渲染(`10-agent-ux.md`)。
> **适用**:Spec-Kit `/speckit.plan`;或由 `stack-selector` skill 路由进来。
> **触发时机**:demo → 产品的形态转变期;请求超时 / 任务变长 / 要 HITL 暂停 / 要可恢复 / 并发压力上来时。
> **最后核对:2026-06**。结论分级:形态分流 ✅稳定 / 具体托管产品名与限额 ⚠️快照(定型前现查官网)。
> **层定位**:对应 `agent/interview/1.md` 的 **L5 部署 / 安全运行时 · 运行形态**——栈顶运行时层,把跑通的 agent 安全放进生产。

---

## 🚦 一、何时需要这层选型

- 单请求开始超时、或用户盯着空白屏等太久。
- 任务从"秒级一问一答"变成"分钟到小时的长链"(coding agent、后台研究、批处理)。
- 要 HITL 中途暂停等人批准,或要崩溃/重启/隔天回来还能接上(可恢复)。
- 并发 / 峰值上来,要伸缩、限流、降级。

> 👉 **核心分流轴 = 交互时长**(`1.md` L5「运行形态第一道分流」):秒级 → 同步;边生成边看 → 流式;分钟到小时 / 要可恢复 / 要 HITL 暂停 → 异步后台 + 持久执行(durable execution)。这是 demo → 产品最主要的一次形态转变。

---

## 🧭 二、三种运行形态(先按交互时长分流)

| 形态 | 交互时长 | 一句话 | 对前端的体感 |
|---|---|---|---|
| **同步请求-响应** ⭐ | 秒级 | 一个 HTTP 请求阻塞到出完整结果 | 转圈 → 一次性出结果 |
| **流式(SSE)** | 几秒~几十秒 | 同一请求内 server→client 持续推 token/事件 | 打字机、边生成边看 |
| **异步后台 + 持久执行** | 分钟~小时 | enqueue 立即返 job_id,任务后台跑、状态落盘可恢复 | 可关页面,事后看进度 / 收通知 |

> 三者是**可叠加的层**,不是互斥单选:异步后台通常 =(任务队列 **或** durable execution)+ 完成通知(webhook/push)+(可选)前端轮询 / SSE 拉进度。

---

## 🧰 三、候选形态对比表

| 方案 | 原理 / 特点 | 取舍 | 适合场景 |
|---|---|---|---|
| **同步 web 服务**(REST,请求-响应)⭐ | 一个请求阻塞到完整结果 | 最简单、零额外基建;但占连接、有超时上限、无进度、无法恢复 | 秒级、单步/短链、结果一次性返回 |
| **SSE 流式** | 同一连接 server→client 持续推 token/事件;断了客户端可重连 | 体感延迟低、能显示进度;仍是单连接、后端要常驻、断流要自己接回 | 几秒~几十秒、要打字机 / 边生成边看 |
| **任务队列**(Celery / RQ+Redis / SQS 等,⚠️现查) | 接口 enqueue 立即返 job_id,worker 后台跑,轮询 / 回调取结果 | 解耦、worker 可横向扩、可重试;但队列本身**不记"执行到哪一步"**,崩了整任务重跑 | 分钟级批处理、不要求步级可恢复 |
| **Durable execution**(Temporal / Restate / Inngest / LangGraph Platform 等,⚠️现查) | 工作流每步落 checkpoint,崩溃/重启/暂停后从断点恢复;内建重试、定时、signal | 真正可恢复 + 可暂停(HITL)+ 可观测;代价是基建/心智重(要按"可重放"写、副作用要**幂等**) | 小时级长任务、HITL 暂停、coding/research agent |
| **Serverless**(Lambda / Cloud Run / Functions,⚠️现查) | 按请求拉起、自动伸缩、按用量计费 | 零运维、抗突发;但有执行时长上限、冷启动、长连接/流式支持受限、不宜常驻有状态 | 突发流量的无状态短任务;长任务需配队列 / durable |
| **Webhook 回调** | 任务完成后服务端反向 POST 通知客户端/第三方 | 不占连接、适合超长任务的"完成通知";要求调用方有可达端点 + 签名校验 + 重试 | 后台任务完成通知、系统间集成 |

> ⚠️ 上表的**具体产品名 / 执行时长上限 / 定价**变动快,本页给**形态选型**,选定厂商前现查官网,不在此固化。形态分类(同步 / 流式 / 队列 / durable / serverless / webhook)本身是稳定心智。

---

## 📐 四、判据 / 选型轴

| 轴 | 问什么 | 倒向 |
|---|---|---|
| **延迟预算 / 交互时长** | 用户要等多久、能不能关页面 | 秒级→同步;几十秒盯着→流式;分钟+ / 可离开→后台 |
| **可恢复性** | 崩溃/重启/隔天回来要不要接得上 | 要 → durable execution + **持久** checkpointer;不要 → 队列 / 同步 |
| **有状态?** | 要不要跨请求保留执行进度 | 有状态 → 需持久后端(复用 `6-memory.md` 的 checkpointer);无状态 → serverless 友好 |
| **HITL 暂停** | 要不要中途等人批准 / 输入 | 要 → durable(`interrupt`+`Command(resume)`),依赖持久 checkpointer(见 `1.md` HITL 段) |
| **并发 / 伸缩** | 峰值 QPS、长任务占用 | 高并发短任务 → serverless / 无状态横扩;长任务 → 队列限流 + worker 池(成本见 `8-cost-economics.md`) |
| **进度可见性** | 用户要不要看到"在干什么" | 要 → 流式 / 进度回传(呈现交 `10-agent-ux.md`) |

> 先给整个 agent **定延迟预算 / SLO**,再据此倒推形态(`1.md`:把延迟从事后指标变成事前设计约束)。

---

## 🎒 五、后台 agent 的一等公民(长运行才需要)

后台长任务区别于同步请求,有三件**必须从一开始就设计**的能力(`1.md` L5):

- **进度回传**:job 状态 + 当前步 / 中间产物。轮询 `GET /status` 或 SSE 重连拉一次 `STATE_SNAPSHOT` 对齐;**呈现细节移交 `10-agent-ux.md`**。
- **用户发起的中断 / 取消**:区别于 HITL 那种"等输入的暂停"——这是"我不要了,停"。需要独立的 cancel 信号通道(durable 的 signal / 队列的 revoke / 协作标志位);worker 要在 **checkpoint 边界**检查取消标志,优雅停止 + 释放资源 + 落终态。
- **完成通知**:任务可能跑很久、用户早关页面 → webhook / push / 邮件。**别假设用户一直连着**;同时给半挂起的 thread 设 TTL,超时自动收尾(对应 HITL"人永远不回来"的坑)。

---

## 🌱 六、最轻起步 → 升级阶梯(每步只升一层)

> **默认同步**。别一上来就 Temporal 全家桶——大多数 agent 起步用同步 / 流式足够;durable execution 的心智成本(可重放、幂等、signal)只在"真的长 + 真的要恢复"时才回本。

```
Q1 一次交互多久出结果?
├─ 秒级、结果一次性          → 同步请求-响应(默认,先不加任何基建)
├─ 几秒~几十秒、要边生成边看  → 同步 + SSE 流式(仍在同一服务里)
└─ 分钟~小时 / 能关页面 ↓
Q2 崩溃/重启/隔天回来要接得上吗?(可恢复性)
├─ 不要(失败整体重跑可接受)  → 任务队列(Celery/SQS/Redis)+ 轮询 / webhook
└─ 要 / 或要 HITL 中途暂停    → durable execution(Temporal / LangGraph Platform)
                              + 持久 checkpointer(复用 6-memory.md:InMemory → Postgres)
Q3 流量突发、且任务无状态短?  → 叠 serverless(Lambda / Cloud Run);长任务别硬塞 serverless
Q4 任务长、用户不盯着?        → 完成通知用 webhook / push,别让前端干等
```

**升级触发器(顶到天花板才升,不提前)**:体感太慢→加 SSE;单请求会超时 / 要并发多个→上队列;要可恢复 / HITL 暂停 / 隔天接得上→上 durable + 持久 checkpointer;流量突发且无状态→serverless;跑太久没人盯→webhook/push。

---

## 🗺️ 七、场景推荐

| 场景 | 推荐形态 |
|---|---|
| 问答 / 分类 API(秒级) | 同步请求-响应 |
| 聊天助理(打字机) | 同步 + SSE 流式 |
| RAG 报告生成(几十秒) | SSE 流式;超时风险大则改后台 + 轮询 |
| Coding / SWE agent(分钟~小时) | 后台 + durable execution + 持久 checkpointer + 进度回传 + 取消通道 |
| 深度研究 agent(长、可关页面) | 任务队列 / durable + webhook/push 完成通知 |
| HITL 审批流(隔天回来批) | durable + 持久 checkpointer(`interrupt`+`resume`,见 `1.md` HITL 段) |
| 突发流量的无状态工具端点 | serverless |
| computer-use / 浏览器自动化长任务 | 后台 + durable + **沙箱**(见 `0-action-paradigm.md` / `7-safety-guardrails.md`) |

---

## 🧩 八、接入 Spec-Kit(可复制 prompt 块)

```
请用 roadmap/agent-selection/9-serving-deployment.md 为本 feature 选部署 / serving 形态。
- 交互时长 / 延迟预算:<秒级? 几十秒盯着? 分钟~小时?>
- 用户能否关页面离开:<能 / 不能>
- 可恢复性:崩溃/重启/隔天回来要接得上吗:<要 / 不要>
- 有无 HITL 中途暂停:<有 / 无>   并发 / 峰值:<…>   是否要进度可见:<…>
请给:运行形态(同步 / SSE流式 / 任务队列 / durable execution / serverless / webhook)
     + 是否需持久 checkpointer(复用 6-memory.md)
     + 后台三件套(进度回传 / 取消 / 完成通知)各是否要,
每项:推荐 + 备选(最轻起步是什么)+ 理由 + 代价。
具体托管产品名 / 限额 / 定价请现查官网,别写死。前端呈现细节移交 10-agent-ux.md。
```

---

## 🔗 九、交叉引用 + 相关资产

- **心智模型**:`agent/interview/1.md` «L5 部署 / 安全运行时 · 运行形态»(交互时长第一道分流)、«HITL 恢复»段(`interrupt`+`Command(resume)` 依赖**持久** checkpointer,`InMemorySaver` 重启即失忆)。
- **相关层**:
  - `6-memory.md` —— checkpointer / Store 是"有状态 / 可恢复"的持久后端(本页"长运行才上持久化"复用它,InMemory → Postgres)。
  - `10-agent-ux.md` —— 流式 / 进度 / HITL 的**前端呈现**(本页只管基础设施形态,不管事件 schema 怎么渲染)。
  - `2-framework/06-protocols.md` —— AG-UI 作为流式 / HITL 的传输标准(SSE 之上的事件协议)。
  - `7-safety-guardrails.md` —— 长任务沙箱、危险动作审批闸、取消的安全边界。
  - `8-cost-economics.md` —— 长任务并发占用与单位经济学(后台 worker 池成本)。
  - `0-action-paradigm.md` —— CodeAct / computer-use 长任务更倾向后台 + 沙箱形态。
- **总览**:`README.md`。沉淀:定下后用 `skills/adr-writer` 写 ADR。

> **最后核对:2026-06**。形态分流(同步 / 流式 / 后台+持久)稳定;Temporal / LangGraph Platform / Celery / SQS / Lambda 等具体产品名、执行时长上限与定价属 ⚠️快照,选型前现查官网。
