# L14 · 全课收官 — 从 OCR 到 Agentic 文档抽取

> 课程：Document AI: From OCR to Agentic Doc Extraction（DeepLearning.AI × LandingAI）
> 本课任务（收官篇）：回望整门课的主线，把"为什么要 agentic"讲清，并给出传统 OCR pipeline 与 agentic 文档抽取的取舍判据，以及文档抽取在 RAG/agent 上游的定位。

## 0. 结语：这门课到底教了什么

大量数据锁在 PDF 等文档里（本地、网上、企业云存储）。这门课教你搭文档处理流水线，把复杂文档变成 **LLM-ready 的 markdown 文本**并抽取信息供分析。结语原话浓缩为一条主线：

```
convert images → text（OCR）
        ↓  分析 layout（bounding boxes）
        ↓  逻辑排序 recognizable chunks（reading order）
        ↓  用 VLM 理解上下文中的文字
        ↓  用 ADE（vision-first、agentic 的文档理解方法）处理复杂文档
        ↓  搭 RAG 应用回答非结构化文件的问题
        ↓  把应用搬上云、做成 event-driven
```

一句话：**从"只会抠字的传统 OCR"，一路加能力，到"看得懂版面、排得对顺序、理解得了语境、追溯得回原页、还能上云自动跑"的 agentic 文档抽取。**

## 1. 为什么必须走向 agentic：每一层补的洞

回看主线，每一层都在补前一层的坑——这正是"agentic 文档抽取"相对传统 OCR pipeline 的价值来源：

| 层 | 传统方式的洞 | 本课补法 |
|---|---|---|
| 文字识别 | 纯 OCR 只出字符串，手写/表格/扫描图翻车 | 深度学习 OCR（PaddleOCR 检测+识别） |
| 版面 | 不知道哪块是标题/表格/图 | layout 检测 + bounding boxes |
| 顺序 | 多栏/复杂排版下阅读顺序错乱 | LayoutReader 等排序模型 |
| 语义 | 识别出字≠理解含义 | VLM 在上下文中理解 |
| 整合 | 上面几步各自为战、需人工拼 | ADE 一个 API 端到端 agentic 处理，输出 grounded chunk |
| 下游 | 抽完的数据怎么被问答用 | RAG（检索 + grounded 生成） |
| 规模 | demo 跑本地扛不住量 | 云上 serverless + event-driven |

## 全课收官

### ① 结语要点

- **agentic 不是噱头，是把 OCR/layout/reading-order/VLM 这几件本来要人工串的事，交给一个会自己选工具的系统**——ADE 是 vision-first 的 agentic 文档理解，用户不必自己拼 OCR/layout/VLM。
- **grounding 贯穿始终**：每个 chunk 带 bbox，能追溯回原页——这是从"能抽"到"敢在受监管场景上线"的关键。
- **文档抽取是上游、不是终点**：解析出干净带元数据的 chunk 之后，价值靠 RAG/agent 在下游兑现（问答、跨文档对比、带来源摘要）。
- **从 demo 到生产是独立一课**：本地跑通只是起点，serverless + event-driven 才让它扛得住真实文档洪流。

### ② L1-L14 全课回顾表

| Lesson | 主题 | 核心产出 / 概念 |
|---|---|---|
| L1 | 文档处理基础 | OCR + LLM 组成 agentic 工作流；识别手写/表格/扫描图的难点 |
| L2 | Lab · 简单文档处理 agent | pytesseract OCR + 规则 + LangChain ReAct，看三者如何拼合 |
| L3 | OCR 四十年演进 | 从字形规则到深度学习；引出 layout 与 reading order 新挑战 |
| L4 | Lab · 现代 OCR 栈 | PaddleOCR 的 detection + recognition 双模型 |
| L5 | 布局与阅读顺序 | LayoutReader 检测排序 + VLM 做整体理解 |
| L6 | Lab · 智能文档分析 agent | OCR + layout + VLM 工具，按内容类型自动选工具 |
| L7 | 单一 API 的 agentic 抽取 | ADE 登场：不显式做 OCR/layout/VLM 也能解析 + 抽 key-value |
| L8 | Lab · ADE 文档理解 | `landingai_ade` API 做 parse + extract |
| L9 | Lab · ADE 续（贷款场景） | 按 schema 抽取，贴近真实业务的信息抽取 |
| L10 | RAG 应用介绍 | ADE 解析 → chunk 存向量库 → 检索回答 |
| L11 | Lab · ADE for RAG | ChromaDB + hybrid search + LangChain 链；bbox visual grounding |
| L12 | AWS 事件驱动无服务器架构 | S3/Lambda/Bedrock/Strands 蓝图；serverless + EDA + IAM + 记忆 |
| L13 | Lab · AWS 完整流水线（收官实验） | boto3 建 Lambda/触发器/KB 摄取/带 grounding 检索工具/三类记忆/Strands agent |
| L14 | 全课总结 | 主线回望 + agentic vs 传统 pipeline 的取舍 |

### ③ 架构师的裁决

> **架构师的裁决**：
>
> **一、传统 OCR pipeline vs agentic 文档抽取，怎么选。**
> 别把 ADE 当"永远更好"。判据是**文档的结构复杂度 × 可追溯要求 × 规模**：
> - 版式单一、纯文本、只要文字（如打印发票的固定字段）→ 传统 OCR + 规则最省，可控可预测、无 LLM 成本与幻觉；
> - 混合版面（表格 + 图 + 多栏）、需要理解语境、需要"答案能指回原页"→ agentic 抽取（ADE）才划算，它把 OCR/layout/reading-order/VLM 的拼装成本一次性吃掉，并天然产出带 bbox 的 grounded chunk；
> - 量大且持续涌入 → 无论哪种解析,上游都该是 event-driven serverless（L12/L13），否则解析层自己会成为瓶颈。
> 反过来说，为一次性的几页 PDF 上整套 S3+Lambda+Bedrock，是过度工程。
>
> **二、文档抽取在 RAG 上游的定位。**
> 文档抽取**不是终点，是 RAG/agent 链条最上游的地基**。它决定了下游检索质量的上限：切块粒度、chunk_type、bbox 这些元数据，在解析那一步定死——下游 hybrid search 能不能"只搜表格"、答案能不能高亮回原页，全取决于上游给了什么。一句话——**RAG 的天花板在解析层，不在检索层**。把"文档 → 干净带元数据的 chunk"这段做扎实，检索和生成才有发挥空间；反之，垃圾进垃圾出，再好的 embedding 和 LLM 也救不回来。

## 本课总结

| 要点 | 一句话 |
|---|---|
| 主线 | OCR → layout/bbox → reading order → VLM → ADE → RAG → cloud/event-driven |
| agentic 价值 | 把本要人工串的 OCR/layout/VLM 交给会自选工具的系统，端到端出 grounded chunk |
| grounding | 每 chunk 带 bbox，可追溯回原页——受监管场景上线的前提 |
| 定位 | 文档抽取是 RAG/agent 上游地基，决定下游检索质量上限 |
| 选型 | 结构复杂度 × 可追溯要求 × 规模，决定传统 OCR vs agentic 抽取 vs 是否上云 |

## 与我的资产映射

- 检索层：`agent/skills/agent-selection/3-retrieval.md`（"RAG 天花板在解析层"作为检索选型的前置判断——先看上游 chunk 质量再谈检索算法）
- 部署/服务层：`agent/skills/agent-selection/9-serving-deployment.md`（解析层规模化 → event-driven serverless 的判据）
- 可观测·可追溯：`agent/skills/agent-selection/5-observability-eval.md`（visual grounding / bbox 溯源作为答案可审计性的资产）
- 全景：本课可作为"文档智能"整条链的参考实现，喂给 `agent/skills/agent-selection/README.md` 的分层选型
- 面试素材：`agent/interview/jd-senior-agent-engineer/`（"传统 OCR vs agentic 抽取取舍""文档抽取是 RAG 上游"是 RAG 系统设计题的高分论点）
- [[project_selection_matrix]]
