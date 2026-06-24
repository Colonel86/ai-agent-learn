# LangChain: Chat with Your Data — 第06课：基于检索的问答（Question Answering）

> 本文档融合**字幕讲解**与**官方代码示例**，旨在帮助你完整且高质量地学习本节课。

---

## 1. 课程定位

我们已经完成了：

- **加载 → 切分 → 向量化存储 → 检索**

现在到了关键一步：**把检索到的文档 + 用户问题一起喂给 LLM，得到答案**。

> 本课会介绍多种实现方式，并比较它们的优劣。

---

## 2. 整体流程

```
用户问题
    ↓
检索相关文档（splits）
    ↓
[System Prompt + 检索文档 + 用户问题] → 语言模型 → 答案
```

### 2.1 默认方式：Stuff（直接塞入）

把所有 chunks 塞进同一个上下文窗口，**只调用一次** LLM。

- ✅ **简单、便宜、效果通常很好**
- ❌ 文档太多时，**装不下**上下文窗口

### 2.2 应对长上下文的三种方案

| 方法 | 一句话理解 |
|------|------------|
| **Map-Reduce** | 每个 chunk 单独问一次 LLM，再汇总成最终答案 |
| **Refine** | 顺序处理：每次基于前一个答案 + 新 chunk **迭代精化** |
| **Map-Rerank** | 每个 chunk 单独问 LLM 并打分，选**得分最高**的作为答案 |

---

## 3. 准备：连接已有 Chroma 向量库

```python
import os, openai, sys
sys.path.append('../..')
from dotenv import load_dotenv, find_dotenv
_ = load_dotenv(find_dotenv())
openai.api_key = os.environ['OPENAI_API_KEY']

# 根据日期选择 LLM 版本（gpt-3.5-turbo-0301 在 2023-09-02 后弃用）
import datetime
current_date = datetime.datetime.now().date()
if current_date < datetime.date(2023, 9, 2):
    llm_name = "gpt-3.5-turbo-0301"
else:
    llm_name = "gpt-3.5-turbo"
print(llm_name)

from langchain.vectorstores import Chroma
from langchain.embeddings.openai import OpenAIEmbeddings

persist_directory = 'docs/chroma/'
embedding = OpenAIEmbeddings()
vectordb = Chroma(persist_directory=persist_directory, embedding_function=embedding)

print(vectordb._collection.count())   # 209
```

### 3.1 快速 sanity check

```python
question = "What are major topics for this class?"
docs = vectordb.similarity_search(question, k=3)
len(docs)   # 3
```

### 3.2 初始化 LLM

```python
from langchain.chat_models import ChatOpenAI

# temperature=0：希望事实性答案，低随机性、高保真
llm = ChatOpenAI(model_name=llm_name, temperature=0)
```

---

## 4. RetrievalQA Chain（基础用法）

### 4.1 一行创建 + 调用

```python
from langchain.chains import RetrievalQA

qa_chain = RetrievalQA.from_chain_type(
    llm,
    retriever=vectordb.as_retriever()
)

result = qa_chain({"query": question})
result["result"]
```

**输出（节选）：**

> "The major topic for this class is machine learning. Additionally, the class may cover statistics and algebra as refreshers in the discussion sections. Later in the quarter, the discussion sections will also cover extensions for the material taught in the main lectures."

> 这里使用了**默认的 Stuff** 方法。

---

## 5. 自定义 Prompt

### 5.1 PromptTemplate 是什么？

它把**指令 + context + question** 组装成传给 LLM 的最终 prompt。

### 5.2 完整代码

```python
from langchain.prompts import PromptTemplate

# 自定义 prompt 模板
template = """Use the following pieces of context to answer the question at the end. \
If you don't know the answer, just say that you don't know, don't try to make up an answer. \
Use three sentences maximum. Keep the answer as concise as possible. \
Always say "thanks for asking!" at the end of the answer.
{context}
Question: {question}
Helpful Answer:"""

QA_CHAIN_PROMPT = PromptTemplate.from_template(template)

# 创建带自定义 prompt 的 chain
qa_chain = RetrievalQA.from_chain_type(
    llm,
    retriever=vectordb.as_retriever(),
    return_source_documents=True,            # ← 同时返回检索到的源文档
    chain_type_kwargs={"prompt": QA_CHAIN_PROMPT}
)
```

### 5.3 测试

```python
question = "Is probability a class topic?"
result = qa_chain({"query": question})

result["result"]
# 输出：
# "Yes, probability is assumed to be a prerequisite for the class. The instructor
#  assumes familiarity with basic probability and statistics, and we'll go over some
#  of the prerequisites in the discussion sections as a refresher course.
#  Thanks for asking!"   ← 注意末尾按指令加上了 "thanks for asking!"
```

### 5.4 查看检索到的源文档

```python
result["source_documents"][0]
# 可以看到答案来自哪个 chunk
```

> **建议练习：** 暂停一下，自己改写 prompt 模板，调整不同问题，观察输出风格的变化。

---

## 6. RetrievalQA 的链类型（chain_type）

### 6.1 Stuff（默认）

```python
qa_chain = RetrievalQA.from_chain_type(
    llm,
    retriever=vectordb.as_retriever()
)
# chain_type 默认 = "stuff"
```

| 优点 | 缺点 |
|------|------|
| 只调用 1 次 LLM；简单、便宜、快 | 文档总长超出上下文窗口时无法使用 |

### 6.2 Map-Reduce

```python
qa_chain_mr = RetrievalQA.from_chain_type(
    llm,
    retriever=vectordb.as_retriever(),
    chain_type="map_reduce"
)

result = qa_chain_mr({"query": question})
result["result"]
```

**底层流程：**

```
检索到 N 个文档
    ↓
Map 阶段：分别送入 LLM，得到 N 个独立答案
    ↓
Reduce 阶段：把 N 个答案再交给 LLM 汇总成最终答案
```

| 优点 | 缺点 |
|------|------|
| 可处理任意多文档；可并行化 | LLM 调用次数多（更慢、更贵）；信息**跨文档分散**时效果可能很差 |

> **观察：** 对前面同样的"概率是否是课程主题"问题，map_reduce 的回答**反而更糟**——因为它对每个文档**独立判断**，跨文档信息无法整合。

### 6.3 Refine

```python
qa_chain_mr = RetrievalQA.from_chain_type(
    llm,
    retriever=vectordb.as_retriever(),
    chain_type="refine"
)

result = qa_chain_mr({"query": question})
result["result"]
```

**底层流程（顺序而非并行）：**

```
Doc1 → LLM → Answer1
Answer1 + Doc2 → LLM → Answer2（基于 Doc2 优化 Answer1）
Answer2 + Doc3 → LLM → Answer3
...
最终 AnswerN
```

**Refine 的核心 prompt 结构：**

> "We have provided an existing answer: {previous_answer}.
> We have the opportunity to refine the existing answer (only if needed) with some more context below: {new_doc}.
> Given the new context, refine the original answer to better answer the question."

| 优点 | 缺点 |
|------|------|
| 能**跨文档累积信息**，结果通常优于 Map-Reduce | 不能并行；同样调用多次 LLM |

> **观察：** Refine 的回答比 Map-Reduce 更好，因为它**鼓励信息延续**：例如最终答案是 "The class assumes familiarity with basic probability and statistics, but we'll have review sections to refresh the prerequisites."

### 6.4 用 LangSmith 平台调试链

如果想可视化每次链调用的内部细节（每个 LLM 调用的 input/output、提示模板、token 消耗），可以接入 **LangSmith**：

```python
# import os
# os.environ["LANGCHAIN_TRACING_V2"] = "true"
# os.environ["LANGCHAIN_ENDPOINT"] = "https://api.langchain.plus"
# os.environ["LANGCHAIN_API_KEY"] = "..."   # 你的 API key
```

操作步骤：

1. 访问 [LangSmith](https://www.langchain.com/langsmith) 注册
2. 在账户设置创建 API Key
3. 设置上述环境变量
4. 重新跑链 → 在 UI 中查看运行详情

**LangSmith UI 中能看到：**

- **Map-Reduce** 包含 4 次独立 LLM 调用 + 1 次 Stuff 汇总调用
- **Refine** 包含 4 次顺序 LLM 调用，每次都把"上一次答案 + 新文档"组合后再次推理
- 每次调用的完整 system message、user message、回复

---

## 7. RetrievalQA 的局限：不记忆历史对话

### 7.1 问题演示

```python
qa_chain = RetrievalQA.from_chain_type(
    llm,
    retriever=vectordb.as_retriever()
)

# 第一次提问
question = "Is probability a class topic?"
result = qa_chain({"query": question})
result["result"]
# → "Yes, probability is assumed as a prerequisite..."

# 追问（指代上一次回答）
question = "why are those prerequesites needed?"
result = qa_chain({"query": question})
result["result"]
# → "The prerequisites for the class are assumed to be basic knowledge of computer
#    science and basic computer skills and principles."
#   ↑ 完全跑偏了！与上一次提到的"概率"毫无关联
```

### 7.2 根本原因

> **`RetrievalQA` 链没有"状态"概念**——它**不记得**上次问过什么、答过什么。

每一次 `qa_chain({"query": ...})` 都是独立的、隔绝的查询。

> **注意：** LLM 输出有随机性，有时回答中**可能**会涉及概率，但这只是它从检索文档中偶然提取的——并非链记住了上下文。**核心问题是：链没有访问过去问答的能力。**

### 7.3 解决方案预告

要让 LLM 能**追问、上下文衔接**，就需要引入 **Memory（记忆）**——这正是下一节的主题。

---

## 8. 本课小结

### 8.1 核心收获

| 主题 | 要点 |
|------|------|
| **基础链** | `RetrievalQA.from_chain_type(llm, retriever)` |
| **自定义 Prompt** | 通过 `chain_type_kwargs={"prompt": ...}` 传入 `PromptTemplate` |
| **查看源文档** | `return_source_documents=True` |
| **链类型** | Stuff（默认）、Map-Reduce、Refine、Map-Rerank |
| **调试工具** | LangSmith 平台 |

### 8.2 chain_type 对照表

| 类型 | LLM 调用次数 | 并行 | 跨文档整合 | 上下文大小 | 推荐场景 |
|------|---------------|------|-----------|-----------|---------|
| **Stuff** | 1 | — | ✅ 自然整合 | ⚠️ 受限 | 文档总量较小（首选） |
| **Map-Reduce** | N+1 | ✅ | ❌ 弱 | ✅ 任意大 | 海量文档 / 简单聚合 |
| **Refine** | N | ❌ | ✅ 强 | ✅ 任意大 | 需要逐步累积信息的复杂问题 |
| **Map-Rerank** | N+1 | ✅ | ❌ | ✅ 任意大 | 答案在某个单一 chunk 中、需要"挑最好"的场景 |

### 8.3 已知缺陷

- **没有对话记忆** → 无法处理追问、指代

### 8.4 下一步

> **下一节：** 引入 **Memory**，构建真正能"对话"的聊天机器人。

---

## 附录：完整代码速查

```python
# === 0. 准备 ===
import os, openai, sys
sys.path.append('../..')
from dotenv import load_dotenv, find_dotenv
_ = load_dotenv(find_dotenv())
openai.api_key = os.environ['OPENAI_API_KEY']

import datetime
llm_name = "gpt-3.5-turbo-0301" if datetime.datetime.now().date() < datetime.date(2023, 9, 2) else "gpt-3.5-turbo"

from langchain.vectorstores import Chroma
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate

vectordb = Chroma(persist_directory='docs/chroma/', embedding_function=OpenAIEmbeddings())
print(vectordb._collection.count())

llm = ChatOpenAI(model_name=llm_name, temperature=0)

# === 1. 基础 RetrievalQA ===
question = "What are major topics for this class?"
qa_chain = RetrievalQA.from_chain_type(llm, retriever=vectordb.as_retriever())
print(qa_chain({"query": question})["result"])

# === 2. 自定义 Prompt ===
template = """Use the following pieces of context to answer the question at the end. If you don't know the answer, just say that you don't know, don't try to make up an answer. Use three sentences maximum. Keep the answer as concise as possible. Always say "thanks for asking!" at the end of the answer.
{context}
Question: {question}
Helpful Answer:"""
QA_CHAIN_PROMPT = PromptTemplate.from_template(template)

qa_chain = RetrievalQA.from_chain_type(
    llm,
    retriever=vectordb.as_retriever(),
    return_source_documents=True,
    chain_type_kwargs={"prompt": QA_CHAIN_PROMPT}
)
result = qa_chain({"query": "Is probability a class topic?"})
print(result["result"])
print(result["source_documents"][0])

# === 3. 三种 chain_type 对比 ===
for ct in ["stuff", "map_reduce", "refine"]:
    chain = RetrievalQA.from_chain_type(
        llm, retriever=vectordb.as_retriever(), chain_type=ct
    )
    print(ct, "→", chain({"query": "Is probability a class topic?"})["result"])

# === 4. 限制：无对话记忆 ===
qa_chain = RetrievalQA.from_chain_type(llm, retriever=vectordb.as_retriever())
qa_chain({"query": "Is probability a class topic?"})
qa_chain({"query": "why are those prerequesites needed?"})   # ← 上下文丢失

# === 5. (可选) LangSmith 追踪 ===
# os.environ["LANGCHAIN_TRACING_V2"] = "true"
# os.environ["LANGCHAIN_ENDPOINT"] = "https://api.langchain.plus"
# os.environ["LANGCHAIN_API_KEY"] = "your-key"
```
