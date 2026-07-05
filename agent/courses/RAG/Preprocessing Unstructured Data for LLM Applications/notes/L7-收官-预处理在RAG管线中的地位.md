# L7 · 收官：预处理在 RAG 管线中的地位（全课回顾 + 架构师裁决）

> 课程：Preprocessing Unstructured Data for LLM Applications（DeepLearning.AI × Unstructured）
> 本课任务：结课回顾。串起从"摄取归一化"到"可运行 RAG bot"的整条主线，并给出架构师层面的取舍裁决。

## 0. 结课语（讲师原话要点）

这门课你学到了三件事，最后拼成第四件：

1. **摄取与归一化（ingest & normalize）**——从多样数据源把内容抽出、统一成规范化 element；
2. **用预处理阶段抽出的 metadata 丰富 RAG**——支撑 hybrid search、更有意义的 chunking；
3. **PDF/图片的高级建模技术**——DLD、Vision Transformer、表格结构解开视觉文档里的内容；
4. **把预处理产出变成一个能跑的 RAG bot**。

你现在已经具备为自己的项目/组织构建一个"知情"RAG bot 的能力。

## 1. 一条主线：非结构化数据 → 规范化 element → RAG

整门课其实只讲一件事：**把杂乱的输入收敛成一种统一的数据结构（document element），让下游 RAG 不再关心原始格式。**

```
多源异构输入                统一抽象                下游消费
HTML / Word ──规则解析─┐
PPTX / MD  ──规则解析─┤
                       ├─► document elements ──► metadata 富化 ──► chunk ──► 向量库 ──► 检索 ──► LLM
PDF(文本) ──fast──────┤     (category/text/     (parent_id/       (by_title)
PDF(扫描)/图片─视觉模型┘      metadata.*)         source/page…)
```

三种抽取范式各就各位：**规则解析**（有内建结构）、**fast 直抽**（文本型 PDF）、**视觉模型**（DLD/Vision Transformer，扫描件与表格）。它们的产物长一个样，这就是 Unstructured 的核心价值。

> **架构师视角**：这门课真正教的不是"某个库怎么调"，而是一种**架构姿势——在系统边界处做归一化（normalize at the boundary）**。把"格式多样性"这个复杂度**堵在摄取层**，用统一 element 抽象作为防火墙，让 chunking / 检索 / 生成等下游全部面对同构数据。这和微服务的 anti-corruption layer、编译器的 IR（中间表示）是同一个思想：**复杂度不消失，但要把它关进一个可控的边界层里**，别让它渗透到整条管线。

> **对比 Document AI 文档抽取**：Document AI / Form Recognizer 这类托管抽取把"归一化边界"整个外包给云厂商——省心，但抽象是**它定的**（它的 element 类型、它的 schema、它的定价）。Unstructured 这条路把边界层留在你自己手里：可换模型、可插自定义 element、可控成本，代价是你要自己运维这层。**边界层归谁所有，就是这道选型题的实质。**

## 全课收官

### ① 结语要点

- 全课主线 = **摄取归一化 → metadata 富化 → 视觉建模 → RAG bot**，四步一线；
- 统一的 document element 抽象是贯穿始终的"脊椎"，让异构输入被同构消费；
- 预处理不是 RAG 的"前置杂活"，而是**决定检索质量上限的地基**——摄取阶段丢掉的结构/元数据，后面补不回来；
- 你已能为自己的组织建一个知情、可引用、可按来源过滤的 RAG bot。

### ② 全课回顾表

| 课 | 主题 | 核心产出 / 技能 | 关键 API / 函数 |
|---|---|---|---|
| L1 | 课程导览与 RAG 管线 | 认识 data loading→chunking→embedding→vector db→retrieval | —— |
| L2 | LLM 预处理基础 | RAG 是什么、document element、normalization 概念 | partition_* 家族总览 |
| L3（原课 03） | 规范化多种文档类型 | 把 HTML/PPT/Word/PDF 抽成统一 element | `partition_html` / `partition_pptx` … |
| L4（原课 04） | 元数据与 chunking | element/document 级 metadata、hybrid search、按标题分块 | `chunk_by_title`、metadata 字段 |
| **L4本系列** | **PDF/图片视觉预处理** | **DLD（YOLOX）vs Vision Transformer（Donut）；fast/hi_res 旋钮** | `partition_pdf(strategy=…)`、API `hi_res_model_name` |
| **L5本系列** | **表格抽取与结构推断** | **三法对照；`text_as_html`；表格摘要供检索** | `pdf_infer_table_structure=True`、`metadata.text_as_html` |
| **L6本系列** | **拼装 RAG bot** | **异构语料摄取→metadata 清洗→chunk→Chroma→混合检索** | `chunk_by_title`、`Chroma`、`ConversationalRetrievalChain` |
| **L7本系列** | **收官** | **全课主线回顾 + 架构裁决** | —— |

> 注：本系列笔记的 L4–L7 对应课程后半段视频 05–08；表中上半段 L1–L4 为前序内容的位置标注，供全景对照。

### ③ 架构师的裁决

> **架构师的裁决**：
>
> **一、文档预处理在 RAG 管线中的地位——它是地基，不是杂活。** 业界谈 RAG 常把注意力堆在 embedding 模型、向量库、rerank、prompt 上，而把"文档解析"当成一次性脚本。这是本末倒置：**检索质量的上限在摄取阶段就被封顶了**。表格被拍平、页眉污染叙事、扫描件抽不出字、元数据没留下——这些错误发生在预处理，却在检索/生成阶段以"幻觉""答非所问"的形式爆发，且极难归因。所以架构师应把预处理当成**与检索同等重要的一等公民**投入设计与 eval，而不是外包给一段没人维护的 `parse.py`。
>
> **二、Unstructured 库 vs 自建解析——按"格式多样性 × 规模 × 定制度"三轴决策。**
>
> | 场景 | 倾向 |
> |---|---|
> | 格式高度多样（PDF/PPT/Word/HTML/MD 混杂）、要快速拿到统一 element | **用 Unstructured**——它的价值正是归一化，自建等于重造这个抽象 |
> | 格式单一且固定（如只有一种版式的发票）、量极大、对成本/延迟极致敏感 | **自建/托管抽取**——针对性优化能甩开通用库 |
> | 需要通用库没有的 element 类型、私有版面、特殊本体 | **自建 or Vision Transformer+prompt**——通用库的固定 schema 是天花板 |
> | 数据不出域、合规严格 | 看部署形态：Unstructured 开源本地库可控，其托管 API 需评估数据流向 |
>
> 一句话：**Unstructured 帮你"把多样性归一"这件苦活省了 80%；剩下 20% 的极端规模/极端定制场景，才轮到自建出手。** 默认用库、有明确瓶颈再自建，是成本最优的路径——不要一上来就自研解析器，那是典型的过早优化。

## 本课总结

| 要点 | 一句话 |
|---|---|
| 主线 | 摄取归一化 → metadata 富化 → 视觉建模 → RAG bot，四步一线 |
| 统一抽象 | document element 是贯穿全课的脊椎，异构进、同构出 |
| 地位裁决 | 预处理是 RAG 地基，决定检索质量上限，应享一等公民待遇 |
| 库 vs 自建 | 默认用 Unstructured 省归一化苦活，极端规模/定制再自建 |

## 与我的资产映射

- 检索层：`agent/skills/agent-selection/3-retrieval.md`（"检索质量上限由摄取决定"应作为该文的核心原则条目）
- 工具/服务选型：新增"文档预处理：Unstructured vs 托管抽取 vs 自建"选型三轴，沉淀进选型矩阵
- 资产复用：`normalize at the boundary`（边界层归一化）是可跨项目复用的架构模式，值得独立成条
- 面试包：`agent/interview/jd-senior-agent-engineer/`（"RAG 为什么答错——从预处理归因" 是高质量回答素材）
- [[project_selection_matrix]] · [[project_asset_reuse]]
