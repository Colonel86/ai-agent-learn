# 第 5 课：Cross-Encoder Re-ranking —— 给检索结果精细打分

> 课程：Advanced Retrieval for AI with Chroma · Lesson 4
> 讲师：Anton Troynikov
> 原文件：
> - `subtitles/chroma_c1_05.vtt`（视频字幕）
> - `code/L5-student.md`（Jupyter Notebook 代码）

---

## 一、本课目标

> **在向量检索拿回 Top-K 之后，用 Cross-Encoder 重新打分排序，把"真正相关"的结果顶到前面。**

解决上一课 Multi-Query 技术带来的**"召回过多、鱼龙混杂"**问题。

---

## 二、Re-ranking 的核心思想

### 2.1 两阶段检索架构

```
┌──────────────────────────────────────────────┐
│  Stage 1: 向量检索（快，但粗）               │
│  Embedding-based Retrieval → Top-K 文档      │
└────────────────┬─────────────────────────────┘
                 ↓
┌──────────────────────────────────────────────┐
│  Stage 2: Re-ranking（慢，但精）            │
│  Cross-Encoder 对 (Query, Doc) 打分         │
│  → 按分数重排 → 选 Top-N                    │
└──────────────────────────────────────────────┘
```

### 2.2 为什么要两阶段？

| 阶段 | 特点 | 能处理的规模 |
|------|------|-------------|
| **Bi-Encoder 向量检索** | 快（向量距离） | 百万～亿级文档 |
| **Cross-Encoder 重排** | 慢（每对都跑一遍模型） | 几十～几百个候选 |

**策略**：先用 Bi-Encoder **粗筛**成 10-100 个候选，再用 Cross-Encoder **精排**。

---

## 三、🔑 Bi-Encoder vs Cross-Encoder 原理对比

### 3.1 Bi-Encoder（之前用的 Sentence Transformer）

```
Query  ──► [Encoder] ──► query_vector
Doc    ──► [Encoder] ──► doc_vector
                          ↓
            cosine_similarity(query_vec, doc_vec)
```

**特点**：
- Query 和 Doc **独立编码**
- 可以**预先计算**所有 Doc 的向量，离线缓存
- 查询时只 embed 一次 query，再做向量最近邻
- ✅ **快**，但**不够精**

### 3.2 Cross-Encoder（本课的新工具）

```
[Query, Doc]  ──► [BERT Cross-Encoder] ──► 单个分数（相关度）
```

**特点**：
- Query 和 Doc **一起送进模型**，输出一个标量分数
- 模型能**在内部 attend**到 Query 和 Doc 的交互关系
- ❌ 无法预计算（每来一个 Query 要重新跑所有 Doc）
- ✅ **精度显著更高**

### 3.3 直观类比

> **Bi-Encoder**：分别看两张照片，判断"长得像不像"
> **Cross-Encoder**：把两张照片**贴在一起看**，判断"这一对是不是同一个人"

---

## 四、应用场景一：挖掘"长尾结果"

### 4.1 问题

- 平时 Top-5 检索
- 第 6～第 10 位可能藏着**真正相关**的文档，但被向量距离"埋没"

### 4.2 解决方案

- 扩大到 **Top-10** 召回
- 用 Cross-Encoder 重排
- 取新排序的 Top-5 送给 LLM

### 4.3 代码实现

```python
from helper_utils import load_chroma, word_wrap, project_embeddings
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
import numpy as np

embedding_function = SentenceTransformerEmbeddingFunction()
chroma_collection = load_chroma(
    filename='microsoft_annual_report_2022.pdf',
    collection_name='microsoft_annual_report_2022',
    embedding_function=embedding_function
)
```

#### Step 1. 扩大召回到 10 个

```python
query = "What has been the investment in research and development?"
results = chroma_collection.query(
    query_texts=query, n_results=10,
    include=['documents', 'embeddings']
)
retrieved_documents = results['documents'][0]
```

#### Step 2. 加载 Cross-Encoder 模型

```python
from sentence_transformers import CrossEncoder

cross_encoder = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
```

> 🪶 **模型信息**：
> - `ms-marco-MiniLM-L-6-v2` 是基于 **MS MARCO** 数据集训练的经典 Re-ranker
> - **非常轻量**，纯本地运行（无需 API）
> - 专为 Query-Document 相关性打分设计

#### Step 3. 给每对 (Query, Doc) 打分

```python
pairs = [[query, doc] for doc in retrieved_documents]
scores = cross_encoder.predict(pairs)

print("Scores:")
for score in scores:
    print(score)
```

#### Step 4. 按分数重排

```python
print("New Ordering:")
for o in np.argsort(scores)[::-1]:      # argsort 降序
    print(o + 1)                         # +1 是为了 1-indexed 打印
```

### 🎯 观察到的现象

| 原排名 | 新排名（Re-rank 后） |
|--------|----------------------|
| 1 | 2 |
| **2** | **1** ← 第 2 名被顶到第 1 |
| 4 | 低 |
| 5 | 低 |
| **6, 7** | **进入 Top-5** ← 长尾被挖出来了 |

> ✅ **结论**：长尾里的第 6、7 个结果实际相关度**比第 4、5 个更高**。

---

## 五、应用场景二：配合 Query Expansion 筛选

### 5.1 问题

上一课的 Multi-Query 扩展会：
- 把原 Query 改写成 5 个变体
- 并行检索 → 召回 **6 × 10 = 60** 个结果（去重后可能 30~40 个）
- 全塞给 LLM？→ **上下文爆炸 + 注意力分散**

### 5.2 解决方案

用 Cross-Encoder **以"原始 Query"为基准**，给所有候选重新打分，只保留真正相关的 Top-N。

### 5.3 代码实现

#### Step 1. 生成扩展 Query（上一课的产物）

```python
original_query = "What were the most important factors that contributed to increases in revenue?"
generated_queries = [
    "What were the major drivers of revenue growth?",
    "Were there any new product launches that contributed to the increase in revenue?",
    "Did any changes in pricing or promotions impact the revenue growth?",
    "What were the key market trends that facilitated the increase in revenue?",
    "Did any acquisitions or partnerships contribute to the revenue growth?"
]
```

#### Step 2. 并行检索 + 去重

```python
queries = [original_query] + generated_queries
results = chroma_collection.query(
    query_texts=queries, n_results=10,
    include=['documents', 'embeddings']
)
retrieved_documents = results['documents']

# 去重
unique_documents = set()
for documents in retrieved_documents:
    for document in documents:
        unique_documents.add(document)

unique_documents = list(unique_documents)
```

#### Step 3. 🔑 关键：配对时用**原始 Query**

```python
pairs = []
for doc in unique_documents:
    pairs.append([original_query, doc])    # ⚠️ 注意用 original_query

scores = cross_encoder.predict(pairs)
```

> ⚠️ **核心技巧**：虽然文档是用**多个变体 Query 召回**的，但打分**必须用原始 Query**——因为用户真正想问的是那个原始问题。

#### Step 4. 重排 + 取 Top-N

```python
print("Scores:")
for score in scores:
    print(score)

print("New Ordering:")
for o in np.argsort(scores)[::-1]:
    print(o)
```

---

## 六、💎 本课核心洞察

### 6.1 Cross-Encoder 为什么更精准？

> **Cross-Encoder 在内部对 (Query, Doc) 的 token 之间做全量 attention**——能捕捉到 Bi-Encoder 无法捕捉的细粒度交互。
>
> 举例：Bi-Encoder 可能把 "increase in revenue" 和 "decrease in revenue" 判为高度相似（都是 revenue 话题），但 Cross-Encoder 能分辨出它们的**对立关系**。

### 6.2 两阶段检索的经典设计模式

```
Retrieve (Recall-oriented, fast)
    │
    ▼
Re-rank (Precision-oriented, slow)
    │
    ▼
LLM Generation
```

这是**生产级 RAG 系统的标准架构**。

### 6.3 Cross-Encoder 可以强调 Query 的不同维度

> Anton 的原话：
>
> **"Cross-Encoder 可以强调 Query 的不同部分，而 Embedding 模型做不到。"**

这意味着同样的检索结果，**不同的原始 Query 会带来不同的重排顺序**——这正是我们想要的"任务相关性"。

### 6.4 这个模型有多轻量？

> **完全本地运行**，无需 GPU，无需 API——是 **MiniLM-L-6**（6 层 Transformer，几十 MB）。
>
> 这是它能被广泛部署到生产的关键原因。

---

## 七、📝 速查表

### 7.1 完整代码模板

```python
from sentence_transformers import CrossEncoder
import numpy as np

# 1. 加载 Cross-Encoder
cross_encoder = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')

# 2. Stage-1 粗召回（扩大 n_results）
results = chroma_collection.query(
    query_texts=[original_query],
    n_results=10,
)
candidate_docs = results['documents'][0]

# 3. Stage-2 Cross-Encoder 打分
pairs = [[original_query, doc] for doc in candidate_docs]
scores = cross_encoder.predict(pairs)

# 4. 按分数降序排序
ranked_indices = np.argsort(scores)[::-1]
top_docs = [candidate_docs[i] for i in ranked_indices[:5]]   # 取 Top-5

# 5. top_docs 送给 LLM
```

### 7.2 两种应用场景对比

| 场景 | 输入 | 输出 |
|------|------|------|
| **长尾挖掘** | 单 Query 召回 Top-10 | Re-rank 后 Top-5 |
| **Multi-Query 筛选** | N 个扩展 Query 召回的合集（30-40 个） | Re-rank 后 Top-5（按原始 Query 打分）|

### 7.3 常用 Cross-Encoder 模型

| 模型 | 特点 |
|------|------|
| `cross-encoder/ms-marco-MiniLM-L-6-v2` | 本课使用，轻量，平衡性能与精度 |
| `cross-encoder/ms-marco-MiniLM-L-12-v2` | 精度更高，稍慢 |
| `cross-encoder/ms-marco-electra-base` | ELECTRA 架构，精度更高 |

---

## 🎯 下一课预告

> **Lesson 5 · Embedding Adapters**
>
> 另一种改进思路：**直接修改 Query embedding 本身**——基于用户反馈训练一个"适配器"，让 embedding 空间更贴合任务需求。
