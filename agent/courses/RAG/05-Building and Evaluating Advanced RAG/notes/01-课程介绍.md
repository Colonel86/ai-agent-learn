# Building and Evaluating Advanced RAG — 第 01 课：课程介绍（中文整理）

> 来源：`llamaindex-truera_c1_01_en.vtt` 原始字幕翻译整理
> 讲师：Andrew Ng（DeepLearning.AI）、Jerry Liu（LlamaIndex 联合创始人 & CEO）、Anupam Datta（TruEra 联合创始人 & 首席科学家）

---

## 一、为什么需要"高级 RAG"

**检索增强生成（Retrieval Augmented Generation，RAG）** 已经成为让 LLM 回答"用户自有数据"相关问题的关键方法。

但要真正把一个**高质量的 RAG 系统**做到生产可用，代价并不低，需要同时解决三件事：

1. **高效的检索技术** —— 为 LLM 提供高度相关的上下文；
2. **合理的上下文组织** —— 让 LLM 基于这些上下文生成答案；
3. **有效的评估框架** —— 帮助你在**初期开发**和**上线后的维护**两个阶段都能高效迭代、持续改进。

本课程正是围绕这三点展开。

---

## 二、课程涵盖的两种高级检索方法

本课将重点介绍两种能**显著优于朴素检索**的高级方法：

### 1. Sentence Window Retrieval（句子窗口检索）

不仅检索与问题最相关的那**一句话**，而是把该句子**前后若干句**（即一个"窗口"）一起作为上下文返回给 LLM，从而提供更连贯的语境。

### 2. Auto-merging Retrieval（自动合并检索）

将文档组织成**树状结构**：
- 每个父节点的文本被划分到它的多个**子节点**中；
- 当若干**子节点**被识别为与用户问题相关时，系统会自动把它们**合并**为整个**父节点**的文本，作为上下文一次性提供给 LLM。

> 听起来步骤不少，后续课程会结合代码详细演示。
> 核心要点：这两种方法都能**动态地检索到更连贯的文本块**，优于简单切分+向量相似度的做法。

---

## 三、评估 RAG 的"三元组"指标（RAG Triad）

为了评估基于 RAG 的 LLM 应用，课程引入一组对应 RAG **三个主要执行步骤**的评估指标，非常有效：

| 指标 | 英文 | 评估对象 | 作用 |
|------|------|----------|------|
| **上下文相关性** | Context Relevance | 检索到的文本块 vs. 用户问题 | 衡量"检索"环节是否找对了资料；定位/调试检索阶段的问题 |
| **有据性 / 扎实性** | Groundedness | LLM 的回答 vs. 上下文 | 衡量回答是否真的**基于**检索到的上下文（而不是编造） |
| **答案相关性** | Answer Relevance | LLM 的回答 vs. 用户问题 | 衡量最终答案是否切题 |

通过这三个指标，你可以**系统地分析系统的哪一部分运转良好、哪一部分仍需改进**，从而**有针对性地**优化最需要投入精力的那个环节。

> 这与机器学习中的 **Error Analysis（错误分析）** 思路非常相似。
> Andrew 指出：这种系统化方法能让你在构建可靠的问答系统时**效率大大提高**。

---

## 四、课程目标与结构

本课程的目标是帮助你构建**生产就绪（production-ready）的 RAG-based LLM 应用**。而"生产就绪"的关键之一，就是在系统上**以系统化的方式迭代**。

课程后半部分将让你动手实践：

- 使用 **sentence window retrieval** 和 **auto-merging retrieval** 两种检索方法；
- 使用 **context relevance、groundedness、answer relevance** 三种评估指标；
- 学习如何通过**系统化的实验跟踪（experiment tracking）** 建立一个 baseline，并快速在此基础上持续改进；
- 基于 LlamaIndex 与 TruEra 团队协助合作伙伴构建 RAG 应用的实际经验，分享这两种检索方法的**调参建议**。

---

## 五、讲师介绍

- **Jerry Liu** —— LlamaIndex 联合创始人兼 CEO。Andrew 表示长期关注 Jerry 和 LlamaIndex 在社交媒体上分享的 RAG 实践经验，很期待由他来系统地讲授这套方法论。
- **Anupam Datta** —— TruEra 联合创始人兼首席科学家。曾任 CMU 教授，在**可信 AI（Trustworthy AI）**，以及如何**监控、评估和优化 AI 应用效果**的方向上已研究超过十年。

---

## 六、致谢

本课程由多方团队共同打造：

- **LlamaIndex 团队**：Logan Markewich
- **TruEra 团队**：Shayak Sen、Joshua Reini、Barbara Lewis
- **DeepLearning.AI 团队**：Eddie Shyu、Dialla Ezzeddine

---

## 七、下一课预告

下一课将概览整个课程的脉络，你会实际体验两种问答系统：

- 一种使用 **Sentence Window Retrieval**；
- 一种使用 **Auto-merging Retrieval**；

并在 **RAG Triad**（context relevance / groundedness / answer relevance）上**对比它们的表现**。

> "Sounds great. Let's get started." —— Andrew Ng
