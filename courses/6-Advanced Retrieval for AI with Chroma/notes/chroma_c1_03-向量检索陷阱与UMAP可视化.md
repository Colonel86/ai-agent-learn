# 第 3 课：简单向量检索的陷阱（Pitfalls）—— UMAP 可视化

> 课程：Advanced Retrieval for AI with Chroma · Lesson 2
> 讲师：Anton Troynikov
> 原文件：
> - `subtitles/chroma_c1_03.vtt`（视频字幕）
> - `code/L3-student.md`（Jupyter Notebook 代码）

---

## 一、本课目标

> **用几何可视化揭示简单向量检索的失败模式：为什么"相似"不等于"相关"？**

核心工具：**UMAP**（把高维 embedding 投影到 2D 可视化）

---

## 二、核心概念：Relevancy vs Distraction（相关 vs 干扰）

### 2.1 两个关键术语

| 术语 | 定义 |
|------|------|
| **Relevancy**（相关性） | 检索结果**真正能回答 query 的内容** |
| **Distractor**（干扰项） | 语义相似但**不回答 query** 的结果 |

### 2.2 为什么 Distractor 危险？

> **Distractor 进入 RAG 上下文后 → LLM 会被带偏 → 输出次优答案**

更糟的是：

- ⚠️ **用户角度**：答案奇怪但说不清哪里错
- ⚠️ **开发者角度**：bug 极难诊断和调试

### 2.3 根本原因

> **Embedding 模型在 embed 时，完全不知道你此刻要解决什么 task/query。**
>
> 我们在**用一个通用表征**去完成一个**特定任务**——这是所有问题的根源。

---

## 三、UMAP：高维 Embedding 的可视化利器

### 3.1 什么是 UMAP？

> **UMAP**（Uniform Manifold Approximation and Projection）
> 开源的**降维可视化**库，能把 384 维 embedding 投影到 2D。

### 3.2 对比其他降维方法

| 方法 | 目标 |
|------|------|
| **PCA** | 找主方向做投影 |
| **t-SNE** | 保留局部邻域 |
| **UMAP** ⭐ | **尽量保留点之间的距离关系**（更适合看 embedding 结构） |

### 3.3 使用前的准备

```python
from helper_utils import load_chroma, word_wrap
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

embedding_function = SentenceTransformerEmbeddingFunction()
chroma_collection = load_chroma(
    filename='microsoft_annual_report_2022.pdf',
    collection_name='microsoft_annual_report_2022',
    embedding_function=embedding_function
)
chroma_collection.count()    # 349
```

---

## 四、三步用 UMAP 可视化 Embedding

### Step 1. 拟合 UMAP Transform

```python
import umap
import numpy as np
from tqdm import tqdm

embeddings = chroma_collection.get(include=['embeddings'])['embeddings']
umap_transform = umap.UMAP(random_state=0, transform_seed=0).fit(embeddings)
```

> 🔒 **固定随机种子** → 每次可重现相同的投影结果。

### Step 2. 定义投影函数（逐点投影，非批量）

```python
def project_embeddings(embeddings, umap_transform):
    umap_embeddings = np.empty((len(embeddings), 2))
    for i, embedding in enumerate(tqdm(embeddings)):
        umap_embeddings[i] = umap_transform.transform([embedding])
    return umap_embeddings
```

> ⚠️ **关键细节**：UMAP 的投影**对输入敏感**——逐点投影才能保证**一致性和可复现性**。批量处理会有细微差异。

### Step 3. 投影 + 画散点图

```python
projected_dataset_embeddings = project_embeddings(embeddings, umap_transform)
```

```python
import matplotlib.pyplot as plt

plt.figure()
plt.scatter(projected_dataset_embeddings[:, 0],
            projected_dataset_embeddings[:, 1], s=10)
plt.gca().set_aspect('equal', 'datalim')
plt.title('Projected Embeddings')
plt.axis('off')
```

观察：同主题的点会聚集在一起——**嵌入空间保留了语义结构**。

> 💡 但注意：2D 投影无法完全还原高维结构，**仅用于建立直觉**。

---

## 五、可视化 Query 与检索结果

### 5.1 可视化函数模板

```python
query_embedding = embedding_function([query])[0]
retrieved_embeddings = results['embeddings'][0]

projected_query_embedding = project_embeddings([query_embedding], umap_transform)
projected_retrieved_embeddings = project_embeddings(retrieved_embeddings, umap_transform)

plt.figure()
plt.scatter(projected_dataset_embeddings[:, 0],
            projected_dataset_embeddings[:, 1], s=10, color='gray')
plt.scatter(projected_query_embedding[:, 0],
            projected_query_embedding[:, 1], s=150, marker='X', color='r')   # 🔴 Query
plt.scatter(projected_retrieved_embeddings[:, 0],
            projected_retrieved_embeddings[:, 1],
            s=100, facecolors='none', edgecolors='g')                        # 🟢 检索结果
plt.gca().set_aspect('equal', 'datalim')
plt.title(f'{query}')
plt.axis('off')
```

### 5.2 图例

| 标记 | 含义 |
|------|------|
| 🔘 灰色点（small） | 整个数据集的 embedding |
| ❌ 红色 X | Query 的 embedding |
| ⭕ 绿色空心圆 | 被检索出来的 Top-K 文档 |

---

## 六、🔬 四个 Query 实验（核心内容）

### 6.1 Query 1：`What is the total revenue?`（主题相关）

```python
query = "What is the total revenue?"
results = chroma_collection.query(
    query_texts=query, n_results=5,
    include=['documents', 'embeddings']
)
```

**观察**：
- 5 个结果里有几个确实和 revenue 相关
- 但**也混进了"costs / 支出"相关的内容**——同属"钱"的话题，不是 revenue 本身
- 🎯 **这就是 Distractor 的典型例子**

---

### 6.2 Query 2：`What is the strategy around artificial intelligence (AI)?`（结构聚集）

```python
query = "What is the strategy around artificial intelligence (AI) ?"
```

**观察**：
- 结果大多落在**同一个数据集区域**
- 有些点**几乎和 Query 重合** → 高度相关
- 但也有**只是提到技术/metaverse、不是真正 AI 战略**的干扰项

---

### 6.3 Query 3：`What has been the investment in research and development?`（结果分散）

```python
query = "What has been the investment in research and development?"
```

**观察**：
- 检索结果**散布在数据集各处**
- 只有**一两个**真正是关于 R&D 支出的
- 其他都是泛泛的"investment"话题

### 🎯 几何直觉（Anton 的核心洞察）

> **把数据想象成高维空间里的一团点云：**
>
> - Query 落在**点云稠密处** → 邻居紧密聚集 ✅
> - Query 落在**点云稀疏边缘** → 邻居来自**四面八方**，结果分散 ❌

这就是为什么同一个检索系统对不同 Query **表现差异巨大**。

---

### 6.4 Query 4：`What has Michael Jordan done for us lately?`（完全无关）

```python
query = "What has Michael Jordan done for us lately?"
```

**观察**：
- 整个 PDF **根本没提 Michael Jordan**
- 但系统**仍然返回了 5 个"最近邻"**
- 这 5 个结果**在投影图上完全散乱**
- **100% 都是 Distractor**

### ⚠️ 这是最危险的场景

> **向量检索会"强行"给你返回结果——即使 Query 和数据集毫无关系。**
>
> 如果下游接 RAG，**整个 context window 全是 Distractor** → LLM 胡说八道。

---

## 七、💎 本课核心洞察

### 7.1 向量检索的三大陷阱

| # | 陷阱 | 典型表现 |
|---|------|----------|
| 1 | **Distractor 污染** | 相似话题但不含答案 |
| 2 | **边缘 Query** | 结果散乱、质量差 |
| 3 | **无关 Query** | 仍强行返回结果，全部是噪声 |

### 7.2 根本原因（本课最重要的一句）

> **Embedding Model 在编码时，对你的查询任务一无所知。**
>
> 它是**通用表征**，不是**任务定制表征**。

### 7.3 几何直觉三要点

- 📍 Query 在**稠密区域** → 结果紧凑相关
- 📍 Query 在**稀疏边缘** → 结果分散杂乱
- 📍 Query **超出数据集范围** → 强制返回，全是噪声

### 7.4 Distractor 的真实危害

```
相似 ≠ 相关 → Distractor 入场 → 污染 RAG 上下文 → LLM 输出次优
→ 用户看不出哪错了 → 开发者调试地狱
```

---

## 八、完整代码流程（一页速览）

```python
# --- Setup ---
from helper_utils import load_chroma
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
import umap, numpy as np, matplotlib.pyplot as plt
from tqdm import tqdm

embedding_function = SentenceTransformerEmbeddingFunction()
chroma_collection = load_chroma(
    filename='microsoft_annual_report_2022.pdf',
    collection_name='microsoft_annual_report_2022',
    embedding_function=embedding_function,
)

# --- UMAP 训练 ---
embeddings = chroma_collection.get(include=['embeddings'])['embeddings']
umap_transform = umap.UMAP(random_state=0, transform_seed=0).fit(embeddings)


def project_embeddings(embs, transform):
    out = np.empty((len(embs), 2))
    for i, e in enumerate(tqdm(embs)):
        out[i] = transform.transform([e])
    return out


projected_dataset = project_embeddings(embeddings, umap_transform)


# --- 可视化单次查询 ---
def visualize_query(query):
    results = chroma_collection.query(
        query_texts=query, n_results=5,
        include=['documents', 'embeddings']
    )
    q_emb = embedding_function([query])[0]
    r_embs = results['embeddings'][0]
    p_query = project_embeddings([q_emb], umap_transform)
    p_ret = project_embeddings(r_embs, umap_transform)

    plt.figure()
    plt.scatter(projected_dataset[:, 0], projected_dataset[:, 1],
                s=10, color='gray')
    plt.scatter(p_query[:, 0], p_query[:, 1],
                s=150, marker='X', color='r')
    plt.scatter(p_ret[:, 0], p_ret[:, 1],
                s=100, facecolors='none', edgecolors='g')
    plt.gca().set_aspect('equal', 'datalim')
    plt.title(f'{query}')
    plt.axis('off')


# --- 四个实验 ---
visualize_query("What is the total revenue?")
visualize_query("What is the strategy around artificial intelligence (AI)?")
visualize_query("What has been the investment in research and development?")
visualize_query("What has Michael Jordan done for us lately?")  # 无关
```

---

## 🎯 下一课预告

> **Lesson 3**：**Query Expansion**——用 LLM 改写查询，让 Query "更像答案"，把检索质量推上新台阶。
