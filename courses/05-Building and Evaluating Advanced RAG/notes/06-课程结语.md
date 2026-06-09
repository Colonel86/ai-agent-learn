# Building and Evaluating Advanced RAG — 第 06 课：课程结语（中文整理）

> 来源：`subtitles/llamaindex-truera_c1_06_en.vtt`（本节无配套代码）
> 讲师：Jerry Liu（LlamaIndex）、Anupam Datta（TruEra）

---

## 一、恭喜你完成本课程

这门课希望你带走的一件事：**掌握构建、评估并迭代 RAG 应用的一整套方法论**，让你的应用更接近"生产可用"。

不论你的背景是：

- **数据科学 / 机器学习**，还是
- **传统软件开发**，

你都需要掌握这些**核心开发原则**，才能成为一名能够构建**健壮 LLM 软件系统**的 AI 工程师。

---

## 二、行业主旋律：**降低 LLM 幻觉**

讲师的判断：在 LLM 领域持续演进的过程中，**降低幻觉（Hallucination）** 会始终是每一位开发者的**头号优先级**。

值得期待的方向：

- **Base Model** 变得更强；
- **大规模评估**变得**更便宜、更易用**，人人都能搭起自己的评估流水线。

> 本课程里的 **RAG Triad + TruLens** 正是这场"评估普及化"的一个缩影。

---

## 三、下一步：把 RAG 做得更好

### 1) 深挖三条主线

讲师建议继续深入理解三个互相交织的层面：

| 层面 | 关键问题 |
|------|----------|
| **Data Pipeline（数据管线）** | 文档加载、清洗、切分、元数据怎么组织 |
| **Retrieval Strategy（检索策略）** | 向量检索 / 关键词检索 / 混合检索 / 重排…… |
| **LLM Prompts（提示词设计）** | 怎么把 context 喂给 LLM、怎么让它"按证据说话" |

### 2) 本课介绍的两种技术只是冰山一角

除了 **Sentence Window Retrieval** 和 **Auto-merging Retrieval** 之外，还可以继续研究：

- **Chunk size 调参**：不同文档类型的最佳切分策略差别很大；
- **Hybrid Search（混合检索）**：向量检索 + BM25 / 关键词检索的组合；
- **LLM-based Reasoning**：Chain of Thought、ReAct 等让模型"显式推理"的技术；
- 更多高级检索方法（HyDE、多查询改写、父文档检索、知识图谱增强等）。

---

## 四、下一步：把评估做得更深

**RAG Triad（Context Relevance / Groundedness / Answer Relevance）** 是一个很棒的**起点**，但评估的世界远比这三项更宽。Anupam 推荐继续深挖以下方向：

- **Model Confidence（置信度）** & **Calibration（校准）**：模型声称的置信度到底靠不靠谱
- **Uncertainty（不确定性估计）**：能否量化"我不知道"
- **Explainability（可解释性）**：决策过程是否可审计
- **Privacy（隐私）**：输出是否泄露敏感信息
- **Fairness（公平性）**：在不同群体上的行为一致性
- **Toxicity（有害性）**：良性 & 对抗场景下的有害输出检测

**关键词**：不仅要在"善意输入"下表现好，**在对抗输入（adversarial settings）下也要稳健**。

---

## 五、讲师寄语

> "We look forward to seeing what you build next."
> —— 期待看到你接下来构建的东西。

---

## 六、课程整体回顾（全套 6 课串起来）

| 课次 | 主题 | 你能带走什么 |
|------|------|---------------|
| **L1** | 课程介绍 | RAG 三要素 & 评估三元组的意义 |
| **L2** | Advanced RAG Pipeline 总览 | Basic / Sentence Window / Auto-merging 三条 Pipeline 端到端跑通 |
| **L3** | RAG Triad 深入 | Feedback Function 抽象 + 三指标代码级定义 + Dashboard drill-down |
| **L4** | Sentence Window Retrieval 深入 | 内部组件（NodeParser / MetadataReplacement / Reranker）+ window_size 调参实验 |
| **L5** | Auto-merging Retrieval 深入 | 层级节点树 + 只 embed 叶子的索引设计 + 两层 vs 三层实验 |
| **L6** | 结语 | 幻觉是首要问题；继续深挖数据/检索/Prompt；评估不止三元组 |

---

## 七、延伸学习建议（结合整门课的落地路径）

1. **先搭 baseline + Triad**：任何新项目先做一个最朴素的 RAG，挂上 TruLens 三指标，建立参照系。
2. **定位短板**：如果 **Context Relevance 低** → 优化检索；如果 **Groundedness 低** → 检查 prompt 是否强调"只基于 context"、context 是否过大；如果 **Answer Relevance 低** → 检查 prompt 或模型本身。
3. **按 app_id 做实验追踪**：每次改动（window_size、chunk_sizes、top_k、re-ranker、prompt 模板…）都换个 app_id，Dashboard 并排看对比。
4. **超越三元组**：等核心指标跑稳之后，再引入 Honest / Harmless / Helpful 等更细的评估，以及本课提到的置信度 / 公平性 / 有害性检测。
