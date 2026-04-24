# 第 4 课：Query Expansion —— 用 LLM 重写查询

> 课程：Advanced Retrieval for AI with Chroma · Lesson 3
> 讲师：Anton Troynikov
> 原文件：
> - `subtitles/chroma_c1_04.vtt`（视频字幕）
> - `code/L4-student.md`（Jupyter Notebook 代码）

---

## 一、本课目标

> **用 LLM 增强原始 Query——让它"更像答案"或"覆盖更多角度"——显著改善检索质量。**

核心思想：**信息检索（IR）不是新学科，但有了 LLM 之后，我们多了一把强有力的"查询增强"利器。**

---

## 二、两种 Query Expansion 技术对比

| 技术 | 英文 | 核心思路 | 代码函数 |
|------|------|----------|----------|
| **🅰 生成假设答案** | Expansion with Generated Answers（HyDE 思路） | 让 LLM 先**胡编一个答案**，拼到 Query 后去检索 | `augment_query_generated` |
| **🅱 生成多个相关问题** | Expansion with Multiple Queries | 让 LLM 生成 N 个**相关但角度不同**的问题，并行检索 | `augment_multiple_query` |

---

---

# 🅰 技术一：Expansion with Generated Answers

## 1. 核心原理

```
原始 Query
    ↓ 送给 LLM
LLM 生成"假设答案"（hypothetical answer，允许幻觉！）
    ↓ 拼接
joint_query = original_query + hypothetical_answer
    ↓ embed 并检索
Top-K 文档
```

### 🧠 为什么 work？

> **我们故意让 LLM 幻觉出一个答案——然后用它作为查询。**
>
> 因为**答案文本的向量**比**问题文本的向量**更容易在文档库中找到"长得像答案"的内容。
>
> 📄 对应论文：[arxiv.org/abs/2305.03653](https://arxiv.org/abs/2305.03653)

---

## 2. 代码实现

### 2.1 环境准备

```python
from helper_utils import load_chroma, word_wrap, project_embeddings
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

embedding_function = SentenceTransformerEmbeddingFunction()

chroma_collection = load_chroma(
    filename='microsoft_annual_report_2022.pdf',
    collection_name='microsoft_annual_report_2022',
    embedding_function=embedding_function
)
```

```python
import os, openai
from openai import OpenAI
from dotenv import load_dotenv, find_dotenv

_ = load_dotenv(find_dotenv())
openai.api_key = os.environ['OPENAI_API_KEY']
openai_client = OpenAI()
```

```python
import umap

embeddings = chroma_collection.get(include=['embeddings'])['embeddings']
umap_transform = umap.UMAP(random_state=0, transform_seed=0).fit(embeddings)
projected_dataset_embeddings = project_embeddings(embeddings, umap_transform)
```

### 2.2 定义 `augment_query_generated`

```python
def augment_query_generated(query, model="gpt-3.5-turbo"):
    messages = [
        {
            "role": "system",
            "content": (
                "You are a helpful expert financial research assistant. "
                "Provide an example answer to the given question, "
                "that might be found in a document like an annual report. "
            )
        },
        {"role": "user", "content": query}
    ]

    response = openai_client.chat.completions.create(
        model=model,
        messages=messages,
    )
    return response.choices[0].message.content
```

### 🎯 Prompt 精髓

> "**Provide an example answer** ... that might be found in a document like an annual report."
>
> 明确要求 LLM **模仿文档风格**生成假设答案——让 embedding 落在文档的分布里。

### 2.3 使用示例

```python
original_query = "Was there significant turnover in the executive team?"
hypothetical_answer = augment_query_generated(original_query)

joint_query = f"{original_query} {hypothetical_answer}"
print(word_wrap(joint_query))
```

**示例输出**（假设答案）：
> "In the past fiscal year there was no significant turnover in the executive team. The core members of the executive team remained unchanged..."

### 2.4 用 joint_query 检索

```python
results = chroma_collection.query(
    query_texts=joint_query, n_results=5,
    include=['documents', 'embeddings']
)
retrieved_documents = results['documents'][0]

for doc in retrieved_documents:
    print(word_wrap(doc))
    print('')
```

**观察**：返回的文档是关于**领导层、董事、董事会委员会**的——正是我们想要的！

### 2.5 可视化对比（原 Query vs 增强后 Query）

```python
retrieved_embeddings = results['embeddings'][0]
original_query_embedding = embedding_function([original_query])
augmented_query_embedding = embedding_function([joint_query])

projected_original_query = project_embeddings(original_query_embedding, umap_transform)
projected_augmented_query = project_embeddings(augmented_query_embedding, umap_transform)
projected_retrieved = project_embeddings(retrieved_embeddings, umap_transform)

import matplotlib.pyplot as plt
plt.figure()
plt.scatter(projected_dataset_embeddings[:, 0], projected_dataset_embeddings[:, 1],
            s=10, color='gray')
plt.scatter(projected_retrieved[:, 0], projected_retrieved[:, 1],
            s=100, facecolors='none', edgecolors='g')
plt.scatter(projected_original_query[:, 0], projected_original_query[:, 1],
            s=150, marker='X', color='r')              # 🔴 原 Query
plt.scatter(projected_augmented_query[:, 0], projected_augmented_query[:, 1],
            s=150, marker='X', color='orange')         # 🟠 增强后 Query
plt.gca().set_aspect('equal', 'datalim')
plt.title(f'{original_query}')
plt.axis('off')
```

### 🎯 可视化关键观察

| 标记 | 含义 |
|------|------|
| 🔴 红色 X | 原始 Query 在空间中的位置 |
| 🟠 橙色 X | **增强后 Query**（拼接了假设答案）的位置 |
| 🟢 绿色圆 | 检索到的文档 |

> **关键现象**：🟠 橙色 X **移动到了一个新的位置** → 新位置周围聚集了更相关的文档。

---

---

# 🅱 技术二：Expansion with Multiple Queries

## 1. 核心原理

```
原始 Query
    ↓ 送给 LLM
LLM 生成 N 个相关但角度不同的问题
    ↓
把 [原 Query, Q1, Q2, ..., QN] 都送给检索系统
    ↓ 并行检索 → 去重
合并的文档集
    ↓
送给 LLM 完成 RAG
```

### 🧠 为什么 work？

> **单个 Query = 嵌入空间中的一个点。**
>
> 一个点**不可能**覆盖复杂问题的所有信息维度。
>
> **多个相关 Query = 多个点** → 覆盖更大的语义区域 → 捡回更多相关文档。

---

## 2. 代码实现

### 2.1 定义 `augment_multiple_query`

```python
def augment_multiple_query(query, model="gpt-3.5-turbo"):
    messages = [
        {
            "role": "system",
            "content": (
                "You are a helpful expert financial research assistant. "
                "Your users are asking questions about an annual report. "
                "Suggest up to five additional related questions to help them find "
                "the information they need, for the provided question. "
                "Suggest only short questions without compound sentences. "
                "Suggest a variety of questions that cover different aspects of the topic."
                "Make sure they are complete questions, and that they are related to the original question."
                "Output one question per line. Do not number the questions."
            )
        },
        {"role": "user", "content": query}
    ]

    response = openai_client.chat.completions.create(
        model=model, messages=messages,
    )
    content = response.choices[0].message.content
    return content.split("\n")
```

### 🎯 Prompt 精髓（5 大约束）

| 约束 | 作用 |
|------|------|
| "up to 5 related questions" | 数量控制 |
| **"short questions without compound sentences"** | **避免复合句**——每个 Query 聚焦一个点 |
| **"variety of questions that cover different aspects"** | **多样性**——不是换句式，而是**换角度** |
| "complete questions, related to original" | 保证相关 + 完整 |
| "one question per line, no numbering" | **格式友好**，便于 split 解析 |

> 💡 Anton 强调：**让 LLM 介入检索 = Prompt 工程变成你的新工作**。请动手调整这些 prompts。

### 2.2 使用示例

```python
original_query = "What were the most important factors that contributed to increases in revenue?"
augmented_queries = augment_multiple_query(original_query)

for q in augmented_queries:
    print(q)
```

**生成的变体示例**：

1. What were the most important factors that contributed to **decreases** in revenue?
2. What were the **sources** of revenue?
3. How were sales and revenue distributed across the different **product lines**?
4. Were there any changes in **pricing strategy**?
5. Did the company acquire any **new customers**?

> 🔍 注意：这些不是同义改写，而是**相关但不同的问题**——正是 prompt 要求的"covers different aspects"。

### 2.3 并行检索 + 去重

```python
queries = [original_query] + augmented_queries

# Chroma 原生支持并行多 query
results = chroma_collection.query(
    query_texts=queries, n_results=5,
    include=['documents', 'embeddings']
)

retrieved_documents = results['documents']

# 🔑 必做：去重（不同 Query 可能召回相同文档）
unique_documents = set()
for documents in retrieved_documents:
    for document in documents:
        unique_documents.add(document)

# 分 Query 打印每组结果
for i, documents in enumerate(retrieved_documents):
    print(f"Query: {queries[i]}")
    print('Results:')
    for doc in documents:
        print(word_wrap(doc))
        print('')
    print('-' * 100)
```

### 2.4 可视化增强效果

```python
original_query_embedding = embedding_function([original_query])
augmented_query_embeddings = embedding_function(augmented_queries)

project_original_query = project_embeddings(original_query_embedding, umap_transform)
project_augmented_queries = project_embeddings(augmented_query_embeddings, umap_transform)

# 🔑 注意：results['embeddings'] 是嵌套 list（每个 query 一组），要 flatten
result_embeddings = results['embeddings']
result_embeddings = [item for sublist in result_embeddings for item in sublist]
projected_result_embeddings = project_embeddings(result_embeddings, umap_transform)

import matplotlib.pyplot as plt
plt.figure()
plt.scatter(projected_dataset_embeddings[:, 0], projected_dataset_embeddings[:, 1],
            s=10, color='gray')
plt.scatter(project_augmented_queries[:, 0], project_augmented_queries[:, 1],
            s=150, marker='X', color='orange')          # 🟠 增强 Queries（多个）
plt.scatter(projected_result_embeddings[:, 0], projected_result_embeddings[:, 1],
            s=100, facecolors='none', edgecolors='g')   # 🟢 所有召回文档
plt.scatter(project_original_query[:, 0], project_original_query[:, 1],
            s=150, marker='X', color='r')                # 🔴 原 Query

plt.gca().set_aspect('equal', 'datalim')
plt.title(f'{original_query}')
plt.axis('off')
```

### 🎯 可视化关键观察

> **多个 🟠 橙色 X 散布在空间中** → 它们分别"覆盖"不同区域 → **召回了单一 Query 无法触及的相关文档**。

---

---

## 三、两种技术对比总结

| 维度 | 🅰 Generated Answer | 🅱 Multiple Queries |
|------|--------------------|-----------------------|
| **思路** | Query → 拼假设答案 → 检索 | Query → 生成 N 个相关变体 → 并行检索 |
| **嵌入空间移动** | Query **移动到**新位置 | Query **复制成多点**覆盖更大区域 |
| **产出数量** | 仍然 Top-K | N × Top-K（需**去重**） |
| **适合场景** | 单个明确的事实性问题 | 复合问题 / 信息面广的问题 |
| **副作用** | 假设答案可能误导（但能被 embedding 扭回来） | 结果量大，**需要筛选相关度** |

---

## 四、💎 本课核心洞察

### 4.1 嵌入空间的几何直觉

> **Query = 嵌入空间中的一个点**
>
> - 原始 Query → 一个点
> - 假设答案增强 → **移动**这个点到更合适的位置
> - 多 Query 增强 → **克隆**成多个点覆盖更大区域

### 4.2 两种技术的共同哲学

> **LLM 在 RAG 闭环中不只出现在"生成答案"这一步——它可以先介入到"查询改写"环节。**

### 4.3 Prompt Engineering 成为新工作负载

- 一旦把 LLM 塞进检索管道，**prompt 的设计直接决定检索质量**
- 要动手实验：调 prompt / 换模型 / 跑自己的 query

### 4.4 多 Query 技术的遗留问题

> 📌 召回量变大，但**不是所有结果都真的相关**。

这就引出了**下一课的主题**：

---

## 🎯 下一课预告

> **Lesson 4 · Cross-Encoder Re-ranking**
>
> 检索后再用 **Cross-Encoder** 精细打分，**只保留真正相关的结果**——解决本课 Multi-Query 技术引入的"召回过多"问题。

---

## 📚 参考论文

- **Query Expansion by Prompting LLMs**（本课 HyDE 思想）：[arxiv.org/abs/2305.03653](https://arxiv.org/abs/2305.03653)
