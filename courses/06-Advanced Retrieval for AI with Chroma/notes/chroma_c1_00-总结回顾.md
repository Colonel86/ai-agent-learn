# Advanced Retrieval for AI with Chroma —— 总结回顾

> 课程：**Advanced Retrieval for AI with Chroma**（DeepLearning.AI 短课）
> 讲师：Anton Troynikov（Chroma 联合创始人）
> 用途：一页式快速回顾。逐课详记见各 `chroma_c1_0*` 笔记。

---

## 一句话主线

> **简单向量检索的致命缺陷是「相似 ≠ 相关」——通用 embedding 在编码时根本不知道你要问什么。三类改进分别在「检索前/中/后」三个位置补救：改 Query 文本、改 Query 向量、重排结果。**

全课用同一个案例贯穿：对**微软 2022 年报 PDF** 做问答。

---

## 问题的根源（L1–L3）

- **RAG 现状**：embed query → 向量最近邻 → 取 Top-K 喂 LLM。看似简单好用。
- **核心缺陷**：「相似」不等于「包含答案」。失败模式有三种：
  | 陷阱 | 表现 |
  |---|---|
  | **Distractor 污染** | 相似话题但不含答案（如问 revenue 却召回 cost） |
  | **边缘 Query** | Query 落在点云稀疏处 → 结果四面八方、杂乱 |
  | **无关 Query** | 数据集根本没这内容，**仍强行返回 Top-K**，全是噪声 |
- **根本原因**（全课最重要一句）：**Embedding 模型在编码时对你的查询任务一无所知——它是通用表征，不是任务定制表征。**
- **诊断工具 UMAP**：把 384 维 embedding 投影到 2D，肉眼看 query（🔴）、召回文档（🟢）、整个数据集（灰）的几何关系。Distractor 一眼可见。
  - 几何直觉：Query 在稠密区 → 邻居紧凑相关；在稀疏边缘 → 结果分散。
  - ⚠️ Distractor 最坑的不是错，而是**用户说不清哪错、开发者难以调试**。

---

## RAG 基础流程（L2 要点）

读 PDF（**过滤空页**）→ **两级切分** → embed → 装 Chroma → 检索 → 拼 prompt 调 LLM。

- **两级切分是最易踩的坑**：
  1. **Character 级**（`RecursiveCharacterTextSplitter`，按 `\n\n→\n→". "→" "` 优先级递归）—— **定语义边界**。
  2. **Token 级**（`SentenceTransformersTokenTextSplitter`，`tokens_per_chunk=256`）—— **在边界内补刀**，适配 embedding 模型 256 token 的上下文窗口。
  - 关键：第二级是对**每个 Character chunk 单独再切**（嵌套，非并列），绝不回原文重切，否则语义边界全废。超窗的块极少（例中 347→349 只多 2 块）。
  - ⚠️ 超窗会被模型**静默截断**，不报错但语义丢失——新手最常见错误。
- **同一个 embedding function 索引和查询都要用**，否则向量不在同一空间。
- **RAG 的灵魂是一行 system prompt**：`"Answer the user's question using only this information."` —— 把 LLM 从「知识库」变成「信息处理器」。

---

## 三大改进技术（全课精华）

| 维度 | 🅰 Query Expansion | 🅱 Cross-Encoder Re-rank | 🅲 Embedding Adapter |
|---|---|---|---|
| **介入位置** | 检索**之前** | 检索**之后** | 检索**之间**（embedding 级） |
| **改什么** | Query 文本 | 结果排序 | Query 向量 |
| **要训练吗** | ❌ 纯 prompt | ❌ 用预训练模型 | ✅ 但极轻（一个线性层） |
| **要用户数据吗** | ❌ | ❌ | ✅（或 LLM 合成） |
| **难度** | ⭐ | ⭐⭐ | ⭐⭐⭐ |

### 🅰 Query Expansion（L4）—— 让 Query「更像答案」
两种做法：
- **生成假设答案（HyDE 思路）**：让 LLM **故意幻觉**一个「年报里可能长这样」的答案，拼到 query 后再检索。原理：答案文本的向量比问题文本的向量更容易匹配到「长得像答案」的文档。几何上 = **把 Query 这个点搬到更好的位置**。
- **Multiple Queries**：让 LLM 生成 5 个**换角度（不是换句式）**的相关问题，并行检索后**去重**。几何上 = **把 Query 克隆成多个点**覆盖更大语义区域。
- 副作用：Multi-Query 召回量暴增（6×10=60），鱼龙混杂 → 引出下一课。
- 心法：**一旦把 LLM 塞进检索管道，prompt 工程就成了你的新工作负载。**

### 🅱 Cross-Encoder Re-ranking（L5）—— 两阶段检索
- **Bi-Encoder（向量检索）**：query、doc 独立编码，可预计算、快，能扛百万级，但**粗**。
- **Cross-Encoder**：把 `[query, doc]` 一起喂模型出一个相关度分数，内部做全量 attention，**精**但无法预计算（只能跑几十~几百个候选）。
- **经典两阶段模式**：Bi-Encoder 粗召回（recall 导向）→ Cross-Encoder 精排（precision 导向）→ LLM。**这是生产级 RAG 的标准架构。**
- 两个用法：① **挖长尾**（召回 Top-10，重排后第 6/7 名可能比第 4/5 名更相关）；② **筛 Multi-Query 的合集**（⚠️ 打分时**必须用原始 Query**，因为那才是用户真正想问的）。
- Cross-Encoder 能分辨 Bi-Encoder 分不清的对立关系（"increase" vs "decrease" in revenue）。
- 模型轻量：`ms-marco-MiniLM-L-6-v2`，本地无 GPU 可跑。

### 🅲 Embedding Adapter（L6）—— 基于反馈学习查询嵌入
- 在 embedding 模型后插一个**可训练的线性变换矩阵**：`adapted_q = A · q`。
- 训练目标：让相关 doc 与 adapted query **同向（cos→+1）**、不相关 doc **反向（cos→-1）**。所以 label 用 **±1** 配 MSE loss。
- 数据来源：理想是真实用户 👍/👎；课程用 LLM 合成（生成 query → 召回 → LLM 判 yes/no，`max_tokens=1` 省钱）。
- 效果：可视化看到原本散布各处的 query 被**整体搬到相关文档密集区**；本质是**在 embedding 空间做拉伸和挤压**——重要维度放大、无关维度压到 0、误导维度反号。
- 思想与 **LoRA** 一脉相承：冻结大模型，叠一个微型任务专属层。训练秒级完成。

---

## 前沿方向（L7）
1. **直接微调 embedding 模型**（数据多时效果上限高于 Adapter）。
2. **微调 LLM 本身**让它会用检索结果（Self-RAG、RA-DIT）——未来 RAG 不再是「LLM+外挂检索」而是**训练时内化检索能力**。
3. **更复杂的 Adapter**（MLP / Transformer 层 / 多任务）。
4. **更强 Re-ranker**（ColBERT、LLM-based、Listwise）。
5. **智能 Chunking**（被低估！语义感知/自适应/层级分块）——**再好的检索算法也救不了糟糕的分块策略。**

---

## 架构师视角的落地路径

课程给的决策链很务实，按问题选药：
1. 先用**朴素 RAG** 做 baseline，**用 UMAP 可视化**检视质量。
2. 识别失败模式，对症下药：
   - Query 太抽象/覆盖不全 → **Query Expansion**
   - Top-K 混入干扰项 → **Cross-Encoder Re-rank**
   - 需要任务定制且有用户反馈 → **Embedding Adapter**
3. 别忽视**分块策略**——投入产出比常被低估。

三个判断要点：
- **「相似 ≠ 相关」是 RAG 一切问题的根**——通用表征做特定任务必然有 gap，三大技术都是在补这个 gap 的不同位置。
- **两阶段检索（召回粗筛 + 重排精排）是生产标配**，不是可选项。
- **改进有先后性价比**：先上零训练的 Query Expansion + Re-rank，数据攒够了再上需要训练的 Adapter / fine-tune。

---

## 后续衔接
- 这门课是**所有 Agentic RAG 系统的基础能力**——与课程 5（Building and Evaluating Advanced RAG）、18（Building Agentic RAG with LlamaIndex）直接衔接。
- 关键论文：HyDE [2212.10496](https://arxiv.org/abs/2212.10496)、Query Expansion with LLMs [2305.03653](https://arxiv.org/abs/2305.03653)、Self-RAG [2310.11511](https://arxiv.org/abs/2310.11511)。
