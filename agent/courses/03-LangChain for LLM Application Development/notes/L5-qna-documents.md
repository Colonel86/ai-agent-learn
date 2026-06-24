# Lesson 5: Q&A over Documents（文档问答）

## 核心问题

LLM 的上下文窗口有限（几千 token），无法直接处理大型文档库。  
**解决方案**：Embedding + Vector Store，只取出与问题最相关的片段传给 LLM。

---

## 完整流程图

```
文档库
  ↓ Document Loader（加载）
  ↓ Text Splitter（分块）
  ↓ Embedding Model（向量化）
  ↓ Vector Store（存储）
              ↑
用户提问 → Embedding → 相似度搜索 → 召回相关块
                                        ↓
                              LLM（生成最终答案）
```

---

## 关键组件

### 1. Document Loader

```python
from langchain.document_loaders import CSVLoader

loader = CSVLoader(file_path="products.csv")
docs = loader.load()  # 每行是一个 Document 对象
```

LangChain 支持多种 Loader：CSV、PDF、网页、Notion、Google Drive 等。

### 2. Embeddings

```python
from langchain_openai import OpenAIEmbeddings

embeddings = OpenAIEmbeddings()
embed = embeddings.embed_query("Hi my name is Harrison")
print(len(embed))   # 1536 维向量
print(embed[:5])    # [-0.021..., 0.006..., ...]
```

**语义相似 = 向量接近**：两只宠物的句子 vs 一辆汽车的句子，前两者向量距离更近。

### 3. Vector Store

```python
from langchain.vectorstores import DocArrayInMemorySearch

db = DocArrayInMemorySearch.from_documents(docs, embeddings)

# 相似度搜索
query = "Please suggest a shirt with sunblocking"
similar_docs = db.similarity_search(query)  # 返回最相关的 4 个 Document
```

`DocArrayInMemorySearch`：无需外部数据库，适合快速原型。  
生产环境可替换为 Chroma、Pinecone、Weaviate 等。

---

## 两种使用方式

### 方式一：一行搞定（VectorstoreIndexCreator）

```python
from langchain.indexes import VectorstoreIndexCreator
from langchain.vectorstores import DocArrayInMemorySearch

index = VectorstoreIndexCreator(
    vectorstore_cls=DocArrayInMemorySearch
).from_loaders([loader])

response = index.query("List all shirts with sun protection")
```

适合快速验证，内部自动完成 load → embed → store → retrieve → generate。

### 方式二：分步骤手动控制

```python
# 1. 加载文档
loader = CSVLoader(file_path="products.csv")
docs = loader.load()

# 2. 创建向量库
embeddings = OpenAIEmbeddings()
db = DocArrayInMemorySearch.from_documents(docs, embeddings)

# 3. 创建 Retriever
retriever = db.as_retriever()

# 4. 创建 LLM
llm = ChatOpenAI(temperature=0.0)

# 5. 组装 RetrievalQA Chain
from langchain.chains import RetrievalQA

qa = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",   # 最常用方式
    retriever=retriever,
    verbose=True
)

response = qa.run("List all shirts with sun protection in markdown table")
```

---

## 四种 chain_type（处理多文档的策略）


| 策略             | 原理                | 优点            | 缺点               |
| -------------- | ----------------- | ------------- | ---------------- |
| **stuff**      | 全部文档塞入一个 prompt   | 简单、便宜、上下文完整   | 文档太多时超出 token 限制 |
| **map_reduce** | 每块单独问答 → 汇总       | 可处理任意数量文档；可并行 | 多次 LLM 调用；块间信息孤立 |
| **refine**     | 逐块迭代，累积答案         | 适合需要整合信息的问题   | 串行调用，速度慢         |
| **map_rerank** | 每块生成答案+置信分 → 取最高分 | 适合事实性问答       | 多次调用；需 LLM 自评分   |


**推荐**：默认用 `stuff`，大文档用 `map_reduce`。

---

## 手动拼接 vs Chain

```python
# 手动（等价于 stuff chain 的内部逻辑）
qdocs = "".join([doc.page_content for doc in similar_docs])
response = llm.invoke(f"{qdocs}\n\nQuestion: {query}")

# 等价的 Chain 写法（推荐）
qa = RetrievalQA.from_chain_type(llm=llm, chain_type="stuff", retriever=retriever)
response = qa.run(query)
```

Chain 封装了：检索 → 格式化 → LLM 调用 → 返回，并且内置了调试支持。

---

## 关键要点

1. **Embedding** 把文本变成数值向量，语义相似则向量接近
2. **Vector Store** 存储向量，支持高效相似度查询
3. **Retriever** 是通用接口，可以换不同的后端实现
4. `stuff` 最简单也最常用，大规模场景再考虑 `map_reduce`
5. 检索不准确往往比 LLM 本身更容易造成错误答案

