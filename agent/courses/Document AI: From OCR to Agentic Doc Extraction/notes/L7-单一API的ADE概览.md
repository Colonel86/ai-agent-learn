# L7 · 单一 API 的 Agentic Document Extraction（三支柱 + DPT + DocVQA）

> 课程：Document AI: From OCR to Agentic Doc Extraction（DeepLearning.AI × LandingAI）
> 本课任务：从「手搓多组件管线」切换到 LandingAI 的 **ADE**——一个把文档 AI 全部复杂度收进**单一 API** 的产品。本课是纯讲解（Andrea），铺清 ADE 的定位、两大用例、三支柱、DPT 模型家族、DocVQA 基准与上手方式，为 L8/L9 的动手实验做准备。

## 0. 本课定位：从 L6 的「一大坨」到一个 API

L6 结尾的痛点是引子：PaddleOCR + LayoutReader + LayoutDetection + VLM 工具 + LangChain 编排，每一环都要自己训练/调优/监控。ADE 的一句话主张——

> 前几课看到的大部分复杂度，现在被**一个 API** 替代。

课名叫「A single API for agentic document extraction」，很贴切。ADE 把 presentations / images / spreadsheets / PDF 等输入，转成**结构良好的 Markdown + JSON**。用户从学生、个体户到大企业都有。

## 1. 两大用例

| 用例 | 别名 | 需求核心 |
|---|---|---|
| Field Extraction | key-value pair extraction | 从大量用户上传文档抽特定字段，且能**回溯到原文** |
| RAG | 建「懂内容」的知识助手 | 理解含表格/图/流程图的内容，同样能**回溯到原文** |

两个用例都反复强调一件事：**traceability（可回溯/grounding）**——抽出的每个值都要能指回原文档的具体位置。这是 L8/L9/L10 反复出现的主线。

## 2. 三支柱：Vision-First / Data-Centric / Agentic

ADE 不是对既有方案的增量改良，而是 LandingAI 工程师首创的新路子，属于「agentic 时代」的 **Vision-First、Data-Centric** 方法。

```
        ┌─────────────────────────────────────────┐
        │  AGENTS & APPS  ← 用户真正要的           │
        │  Field Extraction / Document Splitting    │
        ├─────────────────────────────────────────┤
        │  Intelligent Agents: Parsing & Routing    │
        │  text / tables / figures 各走各的路径      │
        ├─────────────────────────────────────────┤
        │  Foundation: Document-Native Vision Models │  ← 地基
        │  训练成「像人一样看文档」                  │
        └─────────────────────────────────────────┘
```

- **Vision-First**：把文档当**视觉对象**——意义编码在版面、结构、空间关系里，而非纯文本流。这是 LandingAI 多年视觉积累的落点。
- **Data-Centric**：训练用最高质量的精挑数据；「对的数据和对的模型架构一样重要」。
- **Agentic**：交付会 **plan / decide / act / verify** 的系统，一直迭代到回答达到质量阈值。

注意中间层的「Parsing & Routing」——text/table/figure 分别走独立路径。这和 L6 手工做的「按区域类型分派工具」是同一思想，只是被内建进了 ADE。

> **架构师视角**：这是一道教科书级的 **buy-vs-build** 决策。L6 的自建管线把「模型训练 / 配置 / 定制编码」全暴露给你，可控但税重；ADE 把这些**抽象掉**，代价是绑定供应商 + 按调用付费。判断标准不是「哪个更先进」，而是文档 AI 是否你的**核心差异化**：若只是业务的支撑能力（多数场景），买单一 API 让团队聚焦用例；若解析质量本身就是产品护城河，才值得自建。ADE 的分层图恰好把「地基视觉模型 / 中层 agent / 顶层 app」切开，也暗示了：你真正该投入的是最顶层的 use case，而非底层解析。

## 3. DPT 模型家族

顶层三支柱底下的地基视觉模型，属于不断成长的 **Document Pre-trained Transformer（DPT）** 家族。录制时可选：

| 型号 | 备注 |
|---|---|
| DPT-1 | figure 描述更长更细（L8 的 IKEA 图示例用它） |
| DPT-2 | 默认主力，约每月更新一次（`dpt-2-latest`） |
| DPT-2-mini | 轻量版 |

所有 DPT 都返回高质量解析：**阅读顺序检测、版面检测、文本识别、figure captioning**——即 L5/L6 里那些要靠 LayoutReader + LayoutDetection + VLM 分别做的事，DPT 一次全包。

## 4. 基准：DocVQA 上超人类

ADE 核心的 DPT 在 **DocVQA** 基准上表现如何？

- **超过人类表现**；
- **99.15% 准确率**，超过所有已发布模型。

DocVQA 是真实扫描文档的问答基准，来自 UCSF Industry Documents Library。示例题：「此人的家庭电话号码是多少？」——答案藏在手写区（绿色 bbox 内）。这类「答案在手写/表格/图里」的题正是 OCR 管线的死穴，也是 ADE 的强项。（讲师推荐去看官方博客的交互式 document gallery。）

## 5. 怎么用：Parse / Split / Extract 三件套

ADE 把三个能力**分开**提供，可灵活组合成你的管线：

| API | 作用 | 本课/后续用到 |
|---|---|---|
| **Parse** | 文档 → Markdown + JSON chunks（结构理解） | L8/L9/L10 主力 |
| **Extract** | Markdown + schema → 结构化字段（KV 抽取） | L8/L9 |
| **Split** | 拆巨型 PDF | 提及，实验不用 |

补充能力：**Parse Jobs**（数百到数千页的超大文档，异步）。

开发方式四选一：可视化 playground（拖拽）、REST API、Python 库、TypeScript 库。**本课实验只用 Python 库 + Parse/Extract 两个 API**。课外用需自备 API key（`va.landing.ai` 可领免费 key + 初始额度）。

> **对比课程 19「Event-Driven Agentic Document Workflows with LlamaIndex」**：那门课用 LlamaIndex 的事件驱动 workflow 把「解析→抽取→校验」编排成显式的事件图，编排逻辑与解析质量都在你手里（灵活但要自己搭）。ADE 反过来——把解析/路由/多模态推理**收进 API 内部的 agent**，你只在外层写薄薄的业务编排。选型分野：需要对**编排流程**做深度定制（分支、重试、人审插入）→ LlamaIndex workflow；只需要**高质量解析**且想少写胶水 → ADE 单一 API。两者可叠加：ADE 做解析层，LlamaIndex/LangChain 做上层编排（正是 L9/L10 的做法）。

## 本课总结

| 要点 | 一句话 |
|---|---|
| 单一 API | ADE 把 L6 的整条多组件管线塌缩成 Parse/Extract 调用 |
| 两大用例 | Field Extraction 与 RAG，都强调可回溯 grounding |
| 三支柱 | Vision-First（文档即视觉对象）/ Data-Centric / Agentic（plan-decide-act-verify） |
| 分层架构 | 地基 DPT 视觉模型 → 中层 parsing&routing agent → 顶层 apps |
| DPT 家族 | DPT-1 / DPT-2(-latest, 月更) / DPT-2-mini，一次给全 layout+order+OCR+caption |
| DocVQA | 99.15%，超人类、超所有已发布模型 |
| 三件套 | Parse / Split / Extract 分开提供、灵活组合 |

> **记忆点（引出 L8）**：本课只讲了 ADE「是什么、为什么」。L8（Lab 4）动手把它跑起来——用 Python 库的 `client.parse()` 把一张水电账单变成带 chunk id / bbox / 每格 grounding 的结构化输出，再用 `client.extract()` + JSON schema 抽出 10 个可回溯的 KV 字段，亲眼看到「单次 API 调用 = 理解整份文档」。

## 与我的资产映射

- 成本经济层：`agent/skills/agent-selection/8-cost-economics.md`（buy-vs-build、按调用付费 vs 自建管线的 TCO）
- 检索层：`agent/skills/agent-selection/3-retrieval.md`（文档摄取解析质量是 RAG 上游闸门）
- 模型层：`agent/skills/agent-selection/1-model.md`（DPT 这类 document-native 专用模型 vs 通用 VLM 的取舍）
- 对比课程：`agent/courses/19-Event-Driven Agentic Document Workflows with LlamaIndex`（编排在外 vs 内）
- [[project_selection_matrix]] · [[project_asset_reuse]]
