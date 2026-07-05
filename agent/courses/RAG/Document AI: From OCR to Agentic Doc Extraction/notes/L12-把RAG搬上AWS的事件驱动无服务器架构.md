# L12 · 把 RAG 搬上 AWS 的事件驱动无服务器架构（S3 + Lambda + Bedrock + Strands）

> 课程：Document AI: From OCR to Agentic Doc Extraction（DeepLearning.AI × LandingAI，本课与 AWS 合作）
> 本课任务（概念课）：把 L11 那条**全本地**的 RAG 流水线，逐个组件换成 AWS 托管服务，做成"上传文档即自动解析入库"的**事件驱动、无服务器**生产架构，并用 Strands Agents 搭一个带记忆的 agentic RAG。

## 0. 从本地到云：四个组件的替换

L11 的预处理阶段全在本地：本地存 raw 文档 → 本地跑 ADE Parser（吃你自己机器的算力/内存）→ OpenAI 做 embedding → 本地 ChromaDB。本课把它们逐一换成云服务：

```
本地版                          →   AWS 版
本地文件夹存文档                 →   Amazon S3（对象存储）
本地跑 ADE 解析逻辑              →   AWS Lambda（无服务器计算，S3 上传自动触发）
OpenAI embedding                →   Amazon Bedrock（无服务器 embedding）
本地 ChromaDB                   →   Amazon Bedrock Knowledge Base（托管向量库）
LangChain retriever             →   Strands Agents + 检索工具
```

目的一句话：让流水线 **production ready**，能随文档量弹性伸缩。

## 1. 目标架构总览

架构分两类组件：

- **AI 组件**：LandingAI ADE（解析）+ Strands（agentic 框架）
- **AWS 组件**：Amazon S3、AWS Lambda、Amazon Bedrock

Lambda 和 Bedrock 都是 **serverless**。

## 2. Serverless 到底指什么

字幕给了精确定义，两点：

1. **不预置、不管理任何服务器**——AWS 负责基础设施和安全更新；
2. **只在代码真正运行时付费**，空闲不计费——按需自动伸缩（10 个并发用户还是 10000 个都行），没有基础设施要配，能快速原型和上线新功能。

Lambda 的计费粒度细到毫秒：函数只跑了 2ms，就只付这 2ms 的算力。

## 3. 事件驱动架构（Event-Driven Architecture）

"新文档上传就自动跑 ADE"的机制。EDA 是一种**解耦**设计模式，系统之间靠收发 **event**（"某事发生了"的通知）通信。三步：

```
① Event Producer   产生事件的组件。S3 桶——你上传文件时它发出 "file uploaded" 事件
        │
② Event Channel/Broker   路由事件的中间件。Amazon EventBridge——"谁该被通知什么"的通知系统
        │
③ Event Consumer   订阅并响应事件的服务。AWS Lambda——监听 "file uploaded"，一到就自动开跑
```

消息服务的取舍：**EventBridge** 适合需要复杂路由的事件驱动架构；**Amazon SNS**（pub-sub）+ **Amazon SQS**（队列）支持更简单的 pub-sub 与排队模式。

字幕的类比很到位：轮询（polling）是每隔几秒问一次 S3"有新文件了吗？"；事件驱动像 **push notification**——S3 在事件发生的瞬间通知 Lambda，Lambda 立刻响应，**无需手动触发**。

> **架构师视角**：从 L11 到 L12 真正变的不是"换了几个 AWS 品牌名"，而是**控制流反转**。本地版是你写脚本、你调用解析；云版是"文档落地"这个事件自己驱动整条链。解耦的代价是调试链路变长（要看 CloudWatch 日志、要理 IAM 权限），换来的是伸缩性和"上传即处理"的自动化。判据：一次性/低频处理别上 EDA（复杂度不划算），文档持续涌入、要 7×24 无人值守才值得。

## 4. 三大 AWS 组件拆解

**Amazon S3（Simple Storage Service）**：可无限扩容的对象存储，存任意类型/大小文件。当作"无限的数字文件柜"——raw 输入（PDF/图片/文本）存在专门的 bucket，AI 处理结果（摘要、解析产物）再写回组织好的文件夹。**bucket** 是 S3 顶层容器，类比电脑上的主文件夹。

**AWS Lambda + IAM**：无服务器计算，"按需函数/兼职机器人助手"，被事件（S3 上传、API 调用、定时触发）唤醒才运行，按毫秒计费。Lambda 默认**无任何权限**，要访问别的 AWS 服务需要 IAM：

| IAM 概念 | 类比 | 作用 |
|---|---|---|
| **Role**（角色） | ID 徽章 / 职位 | 代表"谁"——Lambda 运行时假扮的身份（服务没有账号密码，靠 assume role 证明身份，拿临时凭证） |
| **Policy**（策略） | 徽章上写的规则清单 | 代表"能做什么"——JSON 文档，如 `s3:GetObject`（读）、`s3:PutObject`（写） |

一句话记牢：**Role 定义它是谁，Policy 规定它能做什么**。建 Lambda 要：建 role → 挂 policy → 把 role 赋给 Lambda。

**Amazon Bedrock**：全托管，单一 API 访问一堆基础模型（Claude、AWS Nova 等 LLM + embedding 模型），"预训练模型的菜单"，不用自己训练托管。它在架构里驱动三处：

```
Knowledge Base   解析后的文档自动 embedding 并存成向量，提供语义检索
Agent Runtime    提供 agent 推理/回答的基础模型
AgentCore Memory 存 agent 的记忆（对话历史、用户偏好、语义事实）
```

Bedrock 本身也 serverless，自动伸缩、按用量付费。

## 5. Strands Agents 框架

AWS 开源 SDK，专为在 notebook 和生产环境搭 agent 而设计：

- **简化编排**，与 S3/Bedrock 等 AWS 资源无缝集成，无需复杂手写代码；
- **声明式 agent 定义**：指定用哪个 Bedrock 模型、agent 能用哪些工具、记忆怎么运作 → 配置清晰、可维护、易改；
- **企业就绪**：内置 tracing/logging、性能监控、错误处理，支持灵活部署。

> **对比 课程 19「Event-Driven Agentic Document Workflows with LlamaIndex」**：两门课都用**事件驱动**处理文档，但抽象层次不同。课程 19 的事件是**框架内**的（LlamaIndex Workflow 里 `@step` 之间用 Python event 对象串联，属于应用内编排）；本课的事件是**基础设施级**的（S3 → EventBridge → Lambda，跨服务、跨进程）。前者解决"一个文档处理程序内部各步骤怎么解耦"，后者解决"文档从哪来、谁来触发处理、如何弹性扩容"。生产系统往往两层叠用：基础设施 EDA 管"何时启动处理"，框架 EDA 管"处理内部怎么流转"。

## 6. 端到端六步流程

```
① 上传文档   PDF 传到 S3 input/medical 文件夹（lab 用医学研究论文）
             → 上传事件触发 Lambda
② Lambda 解析 跑 ADE Parser，结构化产出写回 S3 output/medical：
             markdown（解析内容）+ JSON（chunk 信息，含 type 与 bbox 用于 visual grounding）
             ——全自动，你只管上传
③ 入库       markdown 从 S3 摄取进 Knowledge Base，Bedrock 逐 chunk 生成 embedding 存进向量库
             （摄取完即可检索；也可再建一个专门做摄取的 Lambda，lab 里从简只做解析这一个）
④ 建检索工具 search_knowledge_base 工具——agent 需要文档信息时调它，查向量库返回最相关内容
⑤ 建记忆     AgentCore Memory（见第 7 节）
⑥ 建 agent 并对话  配 system prompt + 检索工具 + 记忆 + Bedrock LLM → 可与用户交互
```

## 7. AgentCore Memory：三类长期记忆

```
User Preference   存喜好/厌恶/个人上下文（"我喜欢金枪鱼寿司"）
Semantic Memory   存事实、实体、关系
Summary Memory    存对话摘要与要点
```

关键特性：**记忆跨 session 持久化**。字幕的演示——用户先说"我喜欢金枪鱼寿司"，agent 记下；下一个 session 问"今天午饭吃啥"，agent 答"来点寿司？你说过喜欢金枪鱼"。价值在于 agent **记得你**，不是每次孤立答题，而是随时间积累上下文、学习偏好，像个真助手。

## 本课总结

| 要点 | 一句话 |
|---|---|
| 组件替换 | 本地文件/算力/embedding/向量库 → S3 / Lambda / Bedrock / Bedrock KB |
| Serverless | 不管服务器 + 用时才付费 + 自动伸缩，毫秒计费 |
| 事件驱动 | Producer(S3) → Broker(EventBridge) → Consumer(Lambda)，push 而非 poll |
| IAM | Role = 是谁（徽章），Policy = 能做什么（徽章上的规则） |
| Bedrock 三用 | Knowledge Base（检索）+ Agent Runtime（推理）+ AgentCore Memory（记忆） |
| Strands Agents | AWS 开源 SDK，声明式配 模型/工具/记忆，企业就绪 |
| 记忆三类 | User Preference / Semantic / Summary，跨 session 持久 |

> **记忆点（引出 L13）**：本课是"蓝图讲解"——把 S3/Lambda/Bedrock/Strands 每个组件的角色讲透，但没动手。L13 是收官实验：用 `boto3` 从 notebook 里把这套架构**真正建起来**（打包 Lambda、建 IAM role、挂 S3 触发器、摄取进 Knowledge Base、装带 visual grounding 的检索工具、配三类记忆、组装 Strands agent），最后与医学文档 agent 对话验证记忆生效。

## 与我的资产映射

- 部署/服务层：`agent/skills/agent-selection/9-serving-deployment.md`（serverless 与事件驱动作为 agent 上云的部署形态；EventBridge vs SNS/SQS 的路由取舍）
- 记忆层：`agent/skills/agent-selection/6-memory.md`（AgentCore 三类长期记忆——偏好/语义/摘要——是记忆分型的现成落地范例）
- 框架层：`agent/skills/agent-selection/2-framework/`（Strands Agents 作为"云原生 + AWS 深度集成"这一档的候选，与 LangGraph/CrewAI 并列）
- [[project_selection_matrix]]
