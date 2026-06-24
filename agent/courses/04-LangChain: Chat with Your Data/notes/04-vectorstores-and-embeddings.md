# LangChain: Chat with Your Data — 第04课：向量存储与嵌入（Vectorstores and Embeddings）

> 本文档融合**字幕讲解**与**官方代码示例**，旨在帮助你完整且高质量地学习本节课。

---

## 1. 课程定位

我们已经把文档**切分成了语义连贯的小块（chunks）**。现在到了下一步：把这些 chunks **放入索引**，以便后续可以快速检索，回答关于这批数据的问题。

实现这一目标的两个核心组件是：

- **嵌入（Embeddings）**
- **向量库（Vector Stores）**

> 这部分在《LangChain for LLM Application Development》中曾简略提到，本课会再次深入讲解，并讨论这种"通用方法"在哪些**边缘场景下会失败**（不用担心，后续课程会修复这些问题）。

---

## 2. RAG 整体工作流回顾

完整的"检索增强生成（RAG）"端到端流程：

```
原始文档（Documents）
    ↓
切分（Splits）
    ↓
为每个 split 生成嵌入（Embeddings）
    ↓
存入向量库（Vector Store）
    ↓
==================== 查询时 ====================
用户问题 → 生成 embedding → 与库中向量比较 → 取 Top-K 相似 chunk
    ↓
[Top-K chunks + 问题] → LLM → 答案
```

---

## 3. 核心概念

### 3.1 嵌入（Embeddings）

**定义：** 将一段文本转化为**数值向量**的过程；语义相近的文本得到相似的向量。

**直观示例：**

| 句子 A | 句子 B | 相似度 |
|--------|--------|--------|
| "我喜欢狗" | "我喜欢犬类" | **高**（都关于宠物） |
| "我喜欢狗" | "外面天气很糟" | **低**（无关主题） |

### 3.2 向量库（Vector Store）

**定义：** 一个数据库，专门存储嵌入向量，并支持**快速查找相似向量**。

**用途：**

- 把每个 chunk 的 embedding 存入向量库
- 后续给定问题 → 转成 embedding → 与库中所有向量比对 → 找出 Top-N 相似的 chunk → 喂给 LLM 生成答案

---

## 4. 环境准备

```python
import os
import openai
import sys
sys.path.append('../..')

from dotenv import load_dotenv, find_dotenv
_ = load_dotenv(find_dotenv())
openai.api_key = os.environ['OPENAI_API_KEY']
```

---

## 5. 加载与切分 CS229 讲义

从本节开始，我们将使用同一组文档：**Andrew Ng 的 CS229 讲义**。

### 5.1 加载（故意制造脏数据）

```python
from langchain.document_loaders import PyPDFLoader

loaders = [
    # 故意重复加载第 1 讲，模拟"脏数据"场景
    PyPDFLoader("docs/cs229_lectures/MachineLearning-Lecture01.pdf"),
    PyPDFLoader("docs/cs229_lectures/MachineLearning-Lecture01.pdf"),
    PyPDFLoader("docs/cs229_lectures/MachineLearning-Lecture02.pdf"),
    PyPDFLoader("docs/cs229_lectures/MachineLearning-Lecture03.pdf"),
]

docs = []
for loader in loaders:
    docs.extend(loader.load())
```

> **注意：** 第 1 讲被加载了两次——这是为了在后面演示**"重复内容污染检索"**这一典型失败模式。

### 5.2 切分

```python
from langchain.text_splitter import RecursiveCharacterTextSplitter

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1500,
    chunk_overlap=150
)

splits = text_splitter.split_documents(docs)
len(splits)   # 输出：209
```

→ 我们得到了 **200+ 个 chunks**，准备进入下一步嵌入。

---

## 6. 嵌入（Embeddings）

使用 **OpenAI Embeddings**。

### 6.1 玩具示例：理解嵌入相似度

先用三个简单句子感受一下嵌入的行为：

```python
from langchain.embeddings.openai import OpenAIEmbeddings

embedding = OpenAIEmbeddings()

sentence1 = "i like dogs"
sentence2 = "i like canines"          # 与 sentence1 语义相近
sentence3 = "the weather is ugly outside"  # 与前两者无关

embedding1 = embedding.embed_query(sentence1)
embedding2 = embedding.embed_query(sentence2)
embedding3 = embedding.embed_query(sentence3)
```

### 6.2 用点积比较相似度

> **小提示：** 不熟悉点积也没关系——只需记住：**值越大，越相似**。

```python
import numpy as np

np.dot(embedding1, embedding2)   # ≈ 0.96   ← 高相似（都关于狗）
np.dot(embedding1, embedding3)   # ≈ 0.77   ← 低相似（狗 vs 天气）
np.dot(embedding2, embedding3)   # ≈ 0.76   ← 低相似
```

**结论：** Embedding 成功捕捉了语义——前两句相似度显著高于第 1/3 与 2/3 句。

> **建议练习：** 暂停一下，自己造几个句子，跑一下点积，观察相似度。

---

## 7. 向量库：Chroma

### 7.1 为什么选 Chroma

LangChain 集成了 **30+ 种向量库**。本课选 **Chroma**，原因：

- **轻量级、内存型**，开箱即用
- 适合教学和小型实验

> 其他向量库（如托管/云存储型方案）适合**持久化大规模数据**的生产场景。

### 7.2 安装

```bash
pip install chromadb
```

### 7.3 创建持久化向量库

```python
from langchain.vectorstores import Chroma

persist_directory = 'docs/chroma/'

# 清理旧的数据库目录，避免污染本次实验
!rm -rf ./docs/chroma

vectordb = Chroma.from_documents(
    documents=splits,
    embedding=embedding,
    persist_directory=persist_directory   # ← Chroma 专属参数：指定磁盘持久化目录
)

print(vectordb._collection.count())   # 输出：209，与 splits 数量一致
```

### 7.4 持久化保存（供后续课程使用）

```python
vectordb.persist()
```

---

## 8. 相似度搜索（Similarity Search）

### 8.1 基础用法

```python
question = "is there an email i can ask for help"

docs = vectordb.similarity_search(question, k=3)   # k 指定返回的文档数

len(docs)   # 3
print(docs[0].page_content)
# 输出包含: cs229-qa@cs.stanford.edu
# 这是 CS229 的 TA 邮箱，用于回答课程问题
```

→ 完美命中！基于 embedding 的语义搜索找到了"求助邮箱"的相关内容。

---

## 9. 失败模式（Failure Modes）

> 单纯的相似度检索能解决约 **80%** 的需求，但仍存在两个典型失败模式。下一节会修复它们。

### 9.1 失败模式 1：重复内容污染

```python
question = "what did they say about matlab?"
docs = vectordb.similarity_search(question, k=5)

docs[0]   # 内容 X
docs[1]   # 内容 X（与 docs[0] 完全一致！）
```

**原因：** 我们故意把 `MachineLearning-Lecture01.pdf` 加载了两次，导致**完全重复的 chunk** 同时被检索出来。

**问题：**

- 同样的信息出现在两个不同的 chunk 中
- 这两个重复内容都会传给 LLM
- 第二份重复内容**毫无价值**——本来可以放一个不同视角的 chunk

> **关键洞察：** 语义搜索只关心"相似性"，**不强制结果的多样性（diversity）**。下一节会介绍如何**同时**保证"相关性 + 多样性"。

### 9.2 失败模式 2：结构化条件被忽略

```python
question = "what did they say about regression in the third lecture?"
docs = vectordb.similarity_search(question, k=5)

for doc in docs:
    print(doc.metadata)
```

**期望：** 所有结果都来自第 3 讲。

**实际：**

- 部分来自第 3 讲 ✓
- 部分来自第 2 讲 ✗
- 部分来自第 1 讲 ✗

```python
print(docs[4].page_content)   # 来自第 1 讲，但确实提到了 regression
```

**原因分析：**

- "**第 3 讲**" 是一个**结构化筛选条件**（应该作为元数据过滤）
- 但 embedding 是把**整个句子**做语义编码，主要捕捉到了 "regression" 这个主题
- 因此检索到的内容确实和 regression 相关，但并未限制在第 3 讲

> **关键洞察：** 结构化信息（如 "第 N 讲"、"某个时间段"、"某位作者"）**无法被纯语义嵌入完美捕捉**，需要额外的 metadata filtering。下一节会介绍 **Self-Query Retriever** 等方案。

> **建议练习：** 暂停一下，尝试更多 query；调整 `k` 的大小，观察排名靠后的结果是否变得不那么相关。

---

## 10. 关于参数 `k`

```python
docs = vectordb.similarity_search(question, k=3)
```

- `k` 越大 → 返回的文档越多
- 但**排名靠后的结果相关性会下降**——头部最相关，尾部可能"勉强相关"

实践中需要**平衡覆盖度与相关性**。

---

## 11. 本课小结

### 11.1 核心收获

| 主题 | 要点 |
|------|------|
| **Embedding** | 把文本转为数值向量；语义相似 → 向量相似 |
| **Vector Store** | 存储 embedding，支持快速相似度查询 |
| **RAG 工作流** | Load → Split → Embed → Store → Query → Retrieve → LLM |
| **持久化** | Chroma 通过 `persist_directory` 写入磁盘 |
| **检索接口** | `vectordb.similarity_search(question, k=N)` |

### 11.2 相似度比较

| 方法 | 解释 |
|------|------|
| **点积（Dot Product）** | 越大越相似 |

### 11.3 已知失败模式

| 失败模式 | 表现 | 下节解决方案 |
|----------|------|--------------|
| **重复内容** | Top-K 中出现完全一样的 chunk | MMR（Maximum Marginal Relevance）等多样性算法 |
| **结构化条件被忽略** | 问题中"第 3 讲"等限定词没起作用 | Self-Query Retriever / metadata filtering |

### 11.4 下一步

下一课将学习如何**强化检索**，修复这两类失败模式：

- 同时保证检索结果的**相关性**和**多样性**
- 让结构化条件（如元数据过滤）真正生效

---

## 附录：完整代码速查

```python
# === 1. 准备 ===
import os, openai, sys
sys.path.append('../..')
from dotenv import load_dotenv, find_dotenv
_ = load_dotenv(find_dotenv())
openai.api_key = os.environ['OPENAI_API_KEY']

# === 2. 加载（故意重复 Lecture01） ===
from langchain.document_loaders import PyPDFLoader
loaders = [
    PyPDFLoader("docs/cs229_lectures/MachineLearning-Lecture01.pdf"),
    PyPDFLoader("docs/cs229_lectures/MachineLearning-Lecture01.pdf"),
    PyPDFLoader("docs/cs229_lectures/MachineLearning-Lecture02.pdf"),
    PyPDFLoader("docs/cs229_lectures/MachineLearning-Lecture03.pdf"),
]
docs = []
for loader in loaders:
    docs.extend(loader.load())

# === 3. 切分 ===
from langchain.text_splitter import RecursiveCharacterTextSplitter
splits = RecursiveCharacterTextSplitter(
    chunk_size=1500, chunk_overlap=150
).split_documents(docs)
print(len(splits))   # 209

# === 4. 嵌入：玩具示例 ===
from langchain.embeddings.openai import OpenAIEmbeddings
import numpy as np
embedding = OpenAIEmbeddings()

e1 = embedding.embed_query("i like dogs")
e2 = embedding.embed_query("i like canines")
e3 = embedding.embed_query("the weather is ugly outside")
print(np.dot(e1, e2))   # ≈ 0.96
print(np.dot(e1, e3))   # ≈ 0.77
print(np.dot(e2, e3))   # ≈ 0.76

# === 5. 创建向量库 ===
from langchain.vectorstores import Chroma
persist_directory = 'docs/chroma/'
!rm -rf ./docs/chroma

vectordb = Chroma.from_documents(
    documents=splits,
    embedding=embedding,
    persist_directory=persist_directory
)
print(vectordb._collection.count())   # 209

# === 6. 相似度搜索 ===
docs = vectordb.similarity_search("is there an email i can ask for help", k=3)
print(docs[0].page_content)

# === 7. 持久化 ===
vectordb.persist()

# === 8. 失败模式 1：重复 ===
docs = vectordb.similarity_search("what did they say about matlab?", k=5)
print(docs[0])
print(docs[1])   # 与 docs[0] 完全一样

# === 9. 失败模式 2：结构化条件被忽略 ===
docs = vectordb.similarity_search(
    "what did they say about regression in the third lecture?", k=5
)
for doc in docs:
    print(doc.metadata)   # 出现非第 3 讲的结果
```
