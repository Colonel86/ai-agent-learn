# LangChain: Chat with Your Data — 第05课：检索（Retrieval）

> 本文档融合**字幕讲解**与**官方代码示例**，旨在帮助你完整且高质量地学习本节课。

---

## 1. 课程定位

上一课介绍了基础的**语义搜索（Semantic Search）**，并指出它在某些场景下会失败：

- **重复内容污染** — Top-K 中出现完全相同的 chunk
- **结构化条件被忽略** — "第 3 讲" 这类限定词没起作用

**本课就是要解决这些问题**，深入探讨更高级的检索方法。

> Retrieval 是 RAG 的核心。本课涉及的很多技术都是过去几个月才出现的**前沿方向**——你们正站在最前沿。

---

## 2. 本课会覆盖的高级检索技术

| 方法 | 关键思想 | 解决的问题 |
|------|----------|-----------|
| **MMR（Maximum Marginal Relevance）** | 既要相关，又要多样 | 重复内容污染 |
| **Self-Query Retriever** | LLM 把问题拆为"语义查询 + 元数据过滤" | 结构化条件被忽略 |
| **Contextual Compression** | 用 LLM 从检索片段中**抽取**最相关部分 | 噪声多、冗余多 |
| **传统 NLP 检索（SVM / TF-IDF）** | 不依赖向量库 | 替代方案 / 对比 |

---

## 3. 准备：连接已有的 Chroma 向量库

```python
import os, openai, sys
sys.path.append('../..')
from dotenv import load_dotenv, find_dotenv
_ = load_dotenv(find_dotenv())
openai.api_key = os.environ['OPENAI_API_KEY']

# 安装 lark（self-query 需要）
# !pip install lark

from langchain.vectorstores import Chroma
from langchain.embeddings.openai import OpenAIEmbeddings

persist_directory = 'docs/chroma/'
embedding = OpenAIEmbeddings()

vectordb = Chroma(
    persist_directory=persist_directory,
    embedding_function=embedding
)

print(vectordb._collection.count())   # 209（上一节存的）
```

---

## 4. MMR：解决"多样性"问题

### 4.1 直观示例：白蘑菇问题

> 厨师问：**"告诉我所有白色的、有大型子实体的蘑菇"**

如果只取语义最相似的 Top-2，结果可能是：

- Doc1：描述形态（白色、大子实体）
- Doc2：描述形态（白色、大子实体）

→ **完全错过了"剧毒"这一关键信息**！

### 4.2 MMR 工作原理

```
查询 query
    ↓
1. 先取 fetch_k 个最相关结果（基于语义相似度）
    ↓
2. 在这 fetch_k 个结果中，权衡"相关性"+"多样性"
    ↓
3. 最终返回 k 个文档给用户
```

| 参数 | 含义 |
|------|------|
| **`fetch_k`** | 第一步：基于纯语义召回的候选数量 |
| **`k`** | 第二步：经过多样性筛选后最终返回的数量 |

### 4.3 玩具示例：白蘑菇

```python
texts = [
    """The Amanita phalloides has a large and imposing epigeous (aboveground) fruiting body (basidiocarp).""",
    """A mushroom with a large fruiting body is the Amanita phalloides. Some varieties are all-white.""",
    """A. phalloides, a.k.a Death Cap, is one of the most poisonous of all known mushrooms.""",
]

smalldb = Chroma.from_texts(texts, embedding=embedding)

question = "Tell me about all-white mushrooms with large fruiting bodies"

# 普通相似度搜索：返回 2 个最相似的（前两条形态描述）
smalldb.similarity_search(question, k=2)
# → 错过"剧毒"信息

# MMR 搜索：先 fetch 3 个，再选出 2 个保证多样性
smalldb.max_marginal_relevance_search(question, k=2, fetch_k=3)
# → 包含"Death Cap, 剧毒"那条
```

### 4.4 应用到真实 MATLAB 问题

```python
# 普通相似度搜索：前两个 chunk 完全一样（脏数据导致的重复）
question = "what did they say about matlab?"
docs_ss = vectordb.similarity_search(question, k=3)
docs_ss[0].page_content[:100]
docs_ss[1].page_content[:100]   # 与 [0] 一致

# MMR 搜索：第一个仍是最相似的，但第二个变得不同了
docs_mmr = vectordb.max_marginal_relevance_search(question, k=3)
docs_mmr[0].page_content[:100]
docs_mmr[1].page_content[:100]   # 不同了！更有多样性
```

---

## 5. 元数据过滤：解决"结构化条件"问题

### 5.1 手动指定 metadata filter

最直接的方式：自己写过滤条件。

```python
question = "what did they say about regression in the third lecture?"

docs = vectordb.similarity_search(
    question,
    k=3,
    filter={"source": "docs/cs229_lectures/MachineLearning-Lecture03.pdf"}
)

for d in docs:
    print(d.metadata)
# 全部来自第 3 讲
```

> **缺陷：** 每次都要**手动**指定过滤条件，无法泛化。

---

## 6. Self-Query Retriever：让 LLM 自动推断过滤器

### 6.1 核心思想

> **挑战：** 我们希望直接从用户的自然语言问题中**自动推断**出 metadata 过滤条件。

**解法：** 用 LLM 把问题拆解为：

1. `query`：纯语义部分（送入向量搜索）
2. `filter`：metadata 过滤条件

例如："**1980 年关于外星人的电影有哪些？**"

| 拆解结果 | 内容 |
|----------|------|
| `query` | "aliens"（语义搜索） |
| `filter` | `year == 1980`（metadata 过滤） |

> 大多数向量库都支持 metadata filter，所以**不需要换库**。

### 6.2 完整代码

```python
from langchain.llms import OpenAI
from langchain.retrievers.self_query.base import SelfQueryRetriever
from langchain.chains.query_constructor.base import AttributeInfo

# 1. 描述每个 metadata 字段（这些信息会传给 LLM，描述要尽量详细）
metadata_field_info = [
    AttributeInfo(
        name="source",
        description=(
            "The lecture the chunk is from, should be one of "
            "`docs/cs229_lectures/MachineLearning-Lecture01.pdf`, "
            "`docs/cs229_lectures/MachineLearning-Lecture02.pdf`, or "
            "`docs/cs229_lectures/MachineLearning-Lecture03.pdf`"
        ),
        type="string",
    ),
    AttributeInfo(
        name="page",
        description="The page from the lecture",
        type="integer",
    ),
]

# 2. 描述向量库中存的内容是什么
document_content_description = "Lecture notes"

# 3. 初始化 LLM 与 Self-Query Retriever
# 注意：text-davinci-003 已于 2024-01-04 弃用，使用替代模型 gpt-3.5-turbo-instruct
llm = OpenAI(model='gpt-3.5-turbo-instruct', temperature=0)

retriever = SelfQueryRetriever.from_llm(
    llm,
    vectordb,
    document_content_description,
    metadata_field_info,
    verbose=True   # ← 打印底层推理细节
)
```

### 6.3 运行结果

```python
question = "what did they say about regression in the third lecture?"
docs = retriever.get_relevant_documents(question)

for d in docs:
    print(d.metadata)
# 全部来自第 3 讲！
```

打开 `verbose=True` 后，能看到底层的拆解：

```
query: "regression"                      ← 语义部分
filter: source == "docs/cs229_lectures/MachineLearning-Lecture03.pdf"   ← 元数据过滤
```

> **第一次执行会有 `predict_and_parse` 弃用警告，可忽略。**

> **Harrison 说这是他最喜欢的 Retriever，建议用更复杂的、嵌套的 metadata 结构来挑战 LLM 的推理能力。**

---

## 7. 上下文压缩（Contextual Compression）

### 7.1 动机

检索到的文档常常**很长**，但只有其中**一两句**真正与问题相关。

- 把整个文档喂给最终的 LLM 调用 → **更贵 + 更差**

> **解法：** 在文档进入最终 LLM 之前，**先用一个 LLM 提取出最相关的片段**，再传给最终 LLM。

```
Vector Store
    ↓ retrieve
原始（长）文档
    ↓ LLMChainExtractor 抽取
压缩后（短）文档
    ↓
最终 LLM 调用
```

> **代价：** 多了若干次 LLM 调用。
> **收益：** 最终回答更聚焦。

### 7.2 完整代码

```python
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import LLMChainExtractor

# 美化打印工具
def pretty_print_docs(docs):
    print(f"\n{'-' * 100}\n".join([
        f"Document {i+1}:\n\n" + d.page_content
        for i, d in enumerate(docs)
    ]))

# 创建压缩器
llm = OpenAI(temperature=0, model="gpt-3.5-turbo-instruct")
compressor = LLMChainExtractor.from_llm(llm)

# 包装向量库
compression_retriever = ContextualCompressionRetriever(
    base_compressor=compressor,
    base_retriever=vectordb.as_retriever()
)

question = "what did they say about matlab?"
compressed_docs = compression_retriever.get_relevant_documents(question)
pretty_print_docs(compressed_docs)
```

**观察结果：**

- ✅ 文档**显著更短**
- ❌ 但**仍然有重复**（因为底层用的是普通相似度搜索）

→ 这正是 MMR 该上场的地方！

---

## 8. 组合多种技术：Compression + MMR

只需把基础 retriever 的 `search_type` 换成 `"mmr"`：

```python
compression_retriever = ContextualCompressionRetriever(
    base_compressor=compressor,
    base_retriever=vectordb.as_retriever(search_type="mmr")   # ← 关键改动
)

question = "what did they say about matlab?"
compressed_docs = compression_retriever.get_relevant_documents(question)
pretty_print_docs(compressed_docs)
```

→ 现在结果**既精简、又无重复**。

> **关键洞察：** 不同检索技术可以**组合**使用，达到最优效果。

---

## 9. 不依赖向量库的检索方法

> 到此为止，所有的高级检索技术都是建立在向量库之上的。
> 但还有一些**传统 NLP 检索**方法，完全不需要向量库。

LangChain 的 Retriever 抽象支持：

- **TF-IDF Retriever**（传统词频统计）
- **SVM Retriever**（支持向量机）

### 9.1 准备数据

```python
from langchain.retrievers import SVMRetriever, TFIDFRetriever
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

# 加载 PDF
loader = PyPDFLoader("docs/cs229_lectures/MachineLearning-Lecture01.pdf")
pages = loader.load()
all_page_text = [p.page_content for p in pages]
joined_page_text = " ".join(all_page_text)

# 切分
splits = RecursiveCharacterTextSplitter(
    chunk_size=1500, chunk_overlap=150
).split_text(joined_page_text)
```

### 9.2 创建两种 retriever

```python
# SVM 需要 embedding 模型
svm_retriever = SVMRetriever.from_texts(splits, embedding)

# TF-IDF 直接用文本
tfidf_retriever = TFIDFRetriever.from_texts(splits)
```

### 9.3 测试

```python
# SVM
question = "What are major topics for this class?"
docs_svm = svm_retriever.get_relevant_documents(question)
print(docs_svm[0])   # 命中 MATLAB 等内容，效果不错

# TF-IDF
question = "what did they say about matlab?"
docs_tfidf = tfidf_retriever.get_relevant_documents(question)
print(docs_tfidf[0])   # 效果略差于 SVM
```

> **观察：** 不同方法在不同问题上表现各异。建议在多种问题上对比测试。

---

## 10. 本课小结

### 10.1 检索技术全景

| 技术 | 类型 | 解决问题 | 关键 API |
|------|------|----------|----------|
| **Similarity Search** | 基础 | 通用语义检索 | `vectordb.similarity_search(q, k)` |
| **MMR** | 多样性 | 去重 / 多角度覆盖 | `vectordb.max_marginal_relevance_search(q, k, fetch_k)` |
| **手动 metadata 过滤** | 结构化 | 限定来源、时间等 | `similarity_search(q, k, filter={...})` |
| **Self-Query Retriever** | 自动结构化 | LLM 推断过滤条件 | `SelfQueryRetriever.from_llm(...)` |
| **Contextual Compression** | 抽取 | 减少噪声 / 节省 token | `ContextualCompressionRetriever(...)` |
| **SVM / TF-IDF Retriever** | 传统 NLP | 替代/对比 | `SVMRetriever.from_texts(...)` |

### 10.2 重要洞察

- **MMR** 通过 `fetch_k` → `k` 的两步走，在相关性与多样性之间找平衡
- **Self-Query** 通过 LLM 拆解问题为 query + filter，让结构化条件真正生效
- **Compression** 适合"长文档中只有少数相关片段"的场景，但代价是更多 LLM 调用
- **多种技术可组合**：例如 `Compression + MMR` 同时获得"短"和"无重复"

### 10.3 下一步

我们已经能够检索到**相关、多样、聚焦**的文档片段。

> **下一节：** 把这些检索到的文档真正喂给 LLM，**回答用户问题**。

---

## 附录：完整代码速查

```python
# === 0. 准备 ===
import os, openai, sys
sys.path.append('../..')
from dotenv import load_dotenv, find_dotenv
_ = load_dotenv(find_dotenv())
openai.api_key = os.environ['OPENAI_API_KEY']
# !pip install lark

from langchain.vectorstores import Chroma
from langchain.embeddings.openai import OpenAIEmbeddings
persist_directory = 'docs/chroma/'
embedding = OpenAIEmbeddings()
vectordb = Chroma(persist_directory=persist_directory, embedding_function=embedding)

# === 1. MMR：玩具示例 ===
texts = [
    """The Amanita phalloides has a large and imposing epigeous (aboveground) fruiting body (basidiocarp).""",
    """A mushroom with a large fruiting body is the Amanita phalloides. Some varieties are all-white.""",
    """A. phalloides, a.k.a Death Cap, is one of the most poisonous of all known mushrooms.""",
]
smalldb = Chroma.from_texts(texts, embedding=embedding)
question = "Tell me about all-white mushrooms with large fruiting bodies"
smalldb.similarity_search(question, k=2)
smalldb.max_marginal_relevance_search(question, k=2, fetch_k=3)

# === 2. MMR：MATLAB 真实场景 ===
question = "what did they say about matlab?"
docs_ss  = vectordb.similarity_search(question, k=3)
docs_mmr = vectordb.max_marginal_relevance_search(question, k=3)

# === 3. 手动 metadata 过滤 ===
docs = vectordb.similarity_search(
    "what did they say about regression in the third lecture?",
    k=3,
    filter={"source": "docs/cs229_lectures/MachineLearning-Lecture03.pdf"}
)

# === 4. Self-Query Retriever ===
from langchain.llms import OpenAI
from langchain.retrievers.self_query.base import SelfQueryRetriever
from langchain.chains.query_constructor.base import AttributeInfo

metadata_field_info = [
    AttributeInfo(name="source",
        description="The lecture the chunk is from, should be one of `docs/cs229_lectures/MachineLearning-Lecture01.pdf`, `docs/cs229_lectures/MachineLearning-Lecture02.pdf`, or `docs/cs229_lectures/MachineLearning-Lecture03.pdf`",
        type="string"),
    AttributeInfo(name="page", description="The page from the lecture", type="integer"),
]
document_content_description = "Lecture notes"
llm = OpenAI(model='gpt-3.5-turbo-instruct', temperature=0)
retriever = SelfQueryRetriever.from_llm(
    llm, vectordb, document_content_description, metadata_field_info, verbose=True
)
docs = retriever.get_relevant_documents(
    "what did they say about regression in the third lecture?"
)

# === 5. Contextual Compression ===
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import LLMChainExtractor

def pretty_print_docs(docs):
    print(f"\n{'-' * 100}\n".join([
        f"Document {i+1}:\n\n" + d.page_content for i, d in enumerate(docs)
    ]))

compressor = LLMChainExtractor.from_llm(llm)
compression_retriever = ContextualCompressionRetriever(
    base_compressor=compressor,
    base_retriever=vectordb.as_retriever()
)
compressed_docs = compression_retriever.get_relevant_documents("what did they say about matlab?")
pretty_print_docs(compressed_docs)

# === 6. Compression + MMR 组合 ===
compression_retriever = ContextualCompressionRetriever(
    base_compressor=compressor,
    base_retriever=vectordb.as_retriever(search_type="mmr")
)

# === 7. SVM / TF-IDF ===
from langchain.retrievers import SVMRetriever, TFIDFRetriever
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

pages = PyPDFLoader("docs/cs229_lectures/MachineLearning-Lecture01.pdf").load()
joined = " ".join([p.page_content for p in pages])
splits = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=150).split_text(joined)

svm_retriever = SVMRetriever.from_texts(splits, embedding)
tfidf_retriever = TFIDFRetriever.from_texts(splits)

svm_retriever.get_relevant_documents("What are major topics for this class?")[0]
tfidf_retriever.get_relevant_documents("what did they say about matlab?")[0]
```
