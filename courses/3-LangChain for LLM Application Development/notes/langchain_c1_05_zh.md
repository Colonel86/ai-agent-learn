# LangChain for LLM Application Development — 第05课：基于文档的问答（中文字幕）

---

使用 LLM 构建的最常见、最复杂的应用之一，是能够在文档上进行问答的系统。

给定一段文本（可能来自 PDF、网页或公司内部文档），能否用 LLM 回答关于这些文档内容的问题，帮助用户更深入地理解和获取所需信息？

这非常强大，因为它将语言模型与它们原本未经训练的数据相结合，使其对你的具体用例更灵活、更适应。这也引入了 LangChain 的关键组件：**嵌入模型（Embedding Models）**和**向量存储（Vector Stores）**。

---

## 快速上手

```python
from langchain.chains import RetrievalQA
from langchain.chat_models import ChatOpenAI
from langchain.document_loaders import CSVLoader
from langchain.vectorstores import DocArrayInMemorySearch
from langchain.indexes import VectorStoreIndexCreator

# 加载CSV数据（户外服装产品描述）
loader = CSVLoader(file_path="outdoor_clothing.csv")

# 一行创建向量索引
index = VectorStoreIndexCreator(
    vectorstore_cls=DocArrayInMemorySearch
).from_loaders([loader])

# 查询
query = "请列出所有具有防晒功能的衬衫"
response = index.query(query)
```

返回结果：包含名称和描述的 Markdown 表格，以及语言模型提供的简洁摘要。

---

## 底层原理

### 核心问题

我们希望将语言模型与大量文档结合使用，但**语言模型一次只能处理几千个 token**。如果文档很大，如何让模型回答关于全部内容的问题？

这就是**嵌入（Embeddings）**和**向量存储（Vector Stores）**的用武之地。

---

### 嵌入（Embeddings）

嵌入为文本片段创建**数值表示**，捕捉文本的语义含义。

- 内容相似的文本片段，其向量表示也会相似
- 这让我们可以在向量空间中比较文本片段

**示例：**
- "我的猫咪很可爱" 和 "我喜欢我的小狗" → 向量非常相似（都关于宠物）
- "我的猫咪很可爱" 和 "我昨天买了辆新车" → 向量差异很大

---

### 向量数据库（Vector Database）

向量数据库用于存储上一步创建的向量表示。

**创建流程（索引时）：**

1. 获取大型文档
2. 将其分割成较小的块（Chunks）
3. 为每个块创建嵌入向量
4. 将向量存入向量数据库 → 这就是创建索引的过程

**运行时流程（查询时）：**

1. 接收查询
2. 为查询创建嵌入向量
3. 与向量数据库中所有向量进行比较
4. 选取最相似的 n 个文本块
5. 将这些文本块放入提示词，传入语言模型
6. 获取最终答案

---

## 分步实现

```python
# Step 1: 加载文档
loader = CSVLoader(file_path="outdoor_clothing.csv")
docs = loader.load()

# Step 2: 创建嵌入
from langchain.embeddings import OpenAIEmbeddings
embeddings = OpenAIEmbeddings()

# 查看嵌入示例（包含1000+个数值元素）
embed = embeddings.embed_query("Hi, my name is Harrison.")

# Step 3: 创建向量存储
db = DocArrayInMemorySearch.from_documents(docs, embeddings)

# Step 4: 相似度搜索
query = "请推荐一件有防晒功能的衬衫"
similar_docs = db.similarity_search(query)  # 返回4个最相关文档

# Step 5: 创建检索器和QA链
retriever = db.as_retriever()
llm = ChatOpenAI(temperature=0)

# 手动组合（等价于一行创建）
qdocs = " ".join([doc.page_content for doc in similar_docs])
response = llm.call_as_llm(f"请列出所有具有防晒功能的衬衫，用Markdown表格展示并对每件进行摘要：{qdocs}")

# 或者使用 RetrievalQA Chain
qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=retriever,
    verbose=True
)
qa_chain.run(query)
```

---

## 四种 QA 方法对比

| 方法 | 原理 | 优点 | 缺点 |
|------|------|------|------|
| **Stuff** | 将所有文档块塞入一个提示词，一次调用 | 简单、便宜、效果好 | 文档过多时超出 token 限制 |
| **Map_reduce** | 对每个块分别调用 LLM，再汇总结果 | 可处理任意数量文档；支持并行化 | 调用次数多；各块独立，可能遗漏关联信息 |
| **Refine** | 迭代处理，逐步在前一块答案基础上完善 | 擅长信息汇总、构建渐进式答案 | 不支持并行；调用次数多；耗时较长 |
| **Map_rerank** | 对每个块单独调用并打分，选分数最高的 | 支持并行；较快 | 需要 LLM 判断评分；调用次数多；成本较高 |

最常用的是 **Stuff**（直接填充），其次是 **Map_reduce**。

这些方法也可用于其他场景，例如 Map_reduce 常用于**长文档摘要**（递归地对信息进行摘要）。

---

## 索引定制化

```python
# 使用 VectorStoreIndexCreator 时也可自定义
index = VectorStoreIndexCreator(
    vectorstore_cls=DocArrayInMemorySearch,
    embedding=OpenAIEmbeddings()  # 可替换为其他嵌入模型
).from_loaders([loader])
```

简洁一行 vs 详细五步，功能等价，取决于你需要多少控制粒度。

---

## 本课小结

- **嵌入**：将文本转化为捕捉语义的数值向量
- **向量数据库**：存储嵌入向量，支持相似度检索
- **RetrievalQA Chain**：检索相关文档片段 → 传入 LLM → 生成答案
- **四种 QA 方法**：Stuff（最常用）、Map_reduce、Refine、Map_rerank

下一节将介绍如何**评估**这些链的性能。
