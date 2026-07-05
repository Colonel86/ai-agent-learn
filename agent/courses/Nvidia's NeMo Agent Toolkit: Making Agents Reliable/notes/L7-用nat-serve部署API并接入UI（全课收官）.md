# L7 · 用 nat serve 部署 API 并接入 UI（全课收官）

> 课程：Nvidia's NeMo Agent Toolkit: Making Agents Reliable（DeepLearning.AI × Nvidia）
> 本课任务：把 climate_analyzer 工作流以 HTTP / WebSocket API 的形式**服务化**，跑起 NeMo Agent Toolkit UI 接到这个 API 上，在一个 polished、production-ready 的界面里和 agent 对话。（含 L8 结语与全课收官。）

## 0. 前课衔接与本课目标

盘点已有：agent 建好了（L3）、和 calculator agent 组合了（L5）、接了 observability（L4）、跑过 evals（L6）。本课把最后一块补上——**放一个 UI 在它前面，让它真正能在现实世界被使用**。三件事：把 agent 服务成 API、接上第一课见过的 UI、看看 agent 场景下 **API-first 架构**长什么样。

## 1. nat serve：一条命令得到生产级 API 服务器

`nat serve` 在前面课程已出现过，本课正式作为主角：

```bash
nat serve --config_file configs/serve_config.yml   # 对着 config 起 API 服务
```

它托管的是一个 **FastAPI server**，开箱自带：

| 能力 | 说明 |
|---|---|
| WebSocket 支持 | 双向长连接，配合流式输出 |
| OpenAPI docs | API 文档自动生成 |
| Health checks | 健康检查端点，接入编排/负载均衡的前提 |

Notebook 里因为要在 Jupyter 后台跑，包了一堆 subprocess 辅助代码——讲师特意提醒**别被那些代码带偏，本质就是对 config 跑一次 `nat serve`**。

> **对比 9-serving-deployment.md**：这是"框架自带 serving"路线的典型样本——对标自己手写 FastAPI wrapper（样板代码全自己背：流式、schema、健康检查）或 LangServe/托管平台（绑定框架或供应商）。NAT 的立足点是**服务面从 config 推导**：workflow 定义即 API 定义，换 agent 不换服务代码。判据不变：需要精细控制路由/鉴权/多租户时自己写服务层，要的是"标准 agent API 快速上线"时框架自带 serving 性价比最高。

## 2. NeMo Agent Toolkit UI：刻意分离的开源前端

UI 是一个**独立的开源仓库**——刻意与工具包分离，理由很务实：**你很可能有自己的 UI，官方不想造成交叉依赖**。使用方式就是标准 npm 项目：

```bash
# 拉下 UI 仓库、装依赖之后
npm run dev        # 本地起在 3000 端口
```

Notebook 同样以 subprocess 方式启动，并用一段 helper script 计算正确的访问 URL（本地是 `localhost:3000`，但 Jupyter 托管环境不同，URL 会不同）。

## 3. 实战对话：从"背训练数据"到"查真实数据"

打开 UI，用建议问题开场：**"What was Mexico's average temperature 1990 to 2000 versus global?"**

关键对照：第一个 notebook（L2）里看过同一个 UI，当时 agent **只能靠 LLM 训练数据里恰好有什么来回答**；现在的 climate agent 有能拉取真实世界数据的工具，还有 calculator 可以对数据做计算。结果：agent 成功运行、给出正确答案。

UI 还能展开 **intermediate steps**：看到 chain of thought、agent 调 `calculate_statistics` 等工具时**传入的数据和返回的数据**——这相当于**在实时聊天环境里评估 agent**。可以继续追问 follow-up（"2000 年墨西哥具体平均气温？"），在更接近真人使用的场景里对着数据聊。

再上难度：**"给法国做一份完整气候分析，含趋势和可视化"**——agent 完成复杂分析并生成可视化图表、落到仓库里。

## 4. UI 的传输特性与 API-first 的含义

UI 功能不止聊天框：

- **实时流式**：边生成边看 agent"思考"，而不是憋一口气返回全部结果；
- **三种通道**：HTTP streaming / WebSockets / 标准 HTTP 任选；
- **UI 只是示例**：**任何前端都能连你的 API**——这就是 API-first 的意义，UI 可换、可自研、可多端。

> **架构师视角**：观察这套交付顺序——先 API（契约）后 UI（消费方），且官方把 UI 拆成独立仓库。这是把"agent 产品"解耦成**能力面（workflow）、服务面（nat serve）、体验面（任意前端）**三层：能力面用 config 演化，服务面提供 WebSocket/OpenAPI/健康检查等标准件，体验面随业务自由更换。反例是把 agent 逻辑写进某个 Web 框架的 handler 里——那样评测（L6）和复用（L5）都会被 UI 绑死。

## 5. 项目收尾

清理后台进程，然后是这条主线的完整清单——我们造的 climate analyzer：

1. 连接**真实世界数据源**；
2. 组合**多个 agent**：一个 LangGraph 写的，一个纯 Python 函数写的；
3. 用**生产 API** 服务它；
4. 对它跑了**评测**、接入了**可观测性**；
5. 在 API 前放了 **UI**，证明可以直接和 agent 对话。

## 6. 本课总结

| 要点 | 一句话 |
|---|---|
| nat serve | 一条命令起 FastAPI server：WebSocket + OpenAPI docs + health checks |
| UI 独立仓库 | 官方 UI 与工具包解耦，标准 npm 项目（`npm run dev`，3000 端口） |
| 实战对照 | 同一个 UI，L2 时靠训练数据瞎答，现在靠工具查真实数据并计算 |
| intermediate steps | UI 里可见 chain of thought 与工具调用的入参/出参，即"live 评估" |
| 传输方式 | HTTP streaming / WebSockets / 标准 HTTP；任何前端可接 |
| API-first | workflow 即 API，UI 只是可替换的消费方之一 |

## 全课收官

### L8 结语要点

恭喜完课——你已经拥有用 NAT **创建、观测、评测、部署**智能 agent 工作流的完整基础：把 Python 函数变成可复用工具；构建会推理"该用哪个工具"的 agent；分析真实世界数据；用 tracing 和 evaluations 让 agent 行为可见；编排多个 agent、评测 agentic 性能；把工作流部署为带 API 和精致界面的生产级应用。带着这些技能，你可以**系统性地 debug、度量、改进 agent**，扩展工作流，组合工具与 agent 去解决新问题。

### L1–L7 全课回顾

| 课 | 一句话 |
|---|---|
| L1 | 课程总览：原型到生产的落差，NAT 补 observability / eval / deploy 三块，且兼容 LangChain / LlamaIndex / CrewAI / 纯 Python 已有 agent |
| L2 | NAT workflow 入门：YAML config 是核心，CLI 跑最小 workflow 并 `nat serve` 成 REST API |
| L3 | ReAct agent + 自定义工具：Python 函数注册为 NAT tool（Pydantic 输入 schema + 描述），打包分析 NOAA 气候数据 |
| L4 | 可观测性：几行 config 接 Phoenix，看统一观测流、用 trace 找性能瓶颈、改 config 前后对比 |
| L5 | 多 agent 组合：现成 LangGraph calculator agent 封装为 NAT tool，硬编码 LLM provider 提升进 config |
| L6 | 评测：config 顶层 `eval` 节 + `nat eval` + Ragas AnswerAccuracy，抓住并修复"自信的错答案" |
| L7 | 部署：`nat serve` 生产 API + 独立 UI，API-first 收官 |

> **架构师的裁决**：NAT 在可观测/评测/部署工具链里的位置，是**"生产化外壳"而非又一个 agent 框架**——它不替你写 agent 逻辑（LangGraph/CrewAI/纯 Python 照旧），而是给任何框架的 agent 统一套上 config-driven 的 observability + eval + serving。**选 NAT 当**：团队多框架混用需要统一编排与观测出口、想要"改 config 不改代码"的实验与回归工作流、或者需要 serving 环节（WebSocket/OpenAPI/健康检查）一并解决、且认同 NVIDIA 生态。**选替代当**：深度单栈 LangChain 且要托管平台与团队协作→ LangSmith；只缺 tracing + 代码式实验、要开源自托管→ Phoenix/Arize（注意 NAT 的 trace 本身就外发给 Phoenix——二者常是互补而非竞争）；组织已有 ML 平台、要 model registry 与 LLM tracing 同一屋檐→ MLflow。核心判据两条：① 你缺的是"观测/评测单点"还是"观测+评测+部署一体化"——缺单点别引入整个工具包；② 你的 agent 栈是单框架还是多框架——单框架用其原生生态摩擦更小，多框架才是 NAT 统一层价值最大的地方。

## 与我的资产映射

- 部署/服务层选型：`agent/skills/agent-selection/9-serving-deployment.md`（"框架自带 serving vs 手写服务层"新增 NAT 样本）
- 可观测/评测层：`agent/skills/agent-selection/5-observability-eval.md`（NAT→Phoenix 的互补关系；裁决块可直接回填）
- 课程 21（Evaluating AI Agents）：Phoenix 侧的代码式评测对照
- 面试素材：API-first 三层解耦（能力面/服务面/体验面）+ 工具链裁决，适配「可观测与评测体系」类追问
- [[project_selection_matrix]]
