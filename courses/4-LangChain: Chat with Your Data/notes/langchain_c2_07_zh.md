# LangChain: Chat with Your Data — 第07课：聊天（Chat）

> 本文档融合**字幕讲解**与**官方代码示例**，旨在帮助你完整且高质量地学习本节课。

---

## 1. 课程定位

到目前为止我们已经走完了 RAG 的大半流程：

- ✅ 加载文档（Document Loading）
- ✅ 切分文档（Splitting）
- ✅ 向量存储（Vector Store）
- ✅ 高级检索（Retrieval：MMR、Self-Query、Compression）
- ✅ 基于检索的问答（RetrievalQA）

**还缺最后一块拼图：** 让 LLM 能记住对话历史，**支持追问**——这正是本课要补全的。

> **重要：** 之前讲过的所有高级检索技术（Self-Query、Compression 等）**都可以**和本课的对话能力**自由组合**——LangChain 的组件天然模块化。

---

## 2. 核心思想

```
                       chat_history（历史消息）
                              ↓
用户问题 ───────────► [合并历史 → 重写为独立问题] ───► retriever ───► docs
                                          ↓                              ↓
                                      stand-alone question      检索到的相关文档
                                                          ↓
                                           [docs + 原问题] → LLM → 答案
                                                          ↓
                                               把 (问题, 答案) 追加到 chat_history
```

**关键变化：** `ConversationalRetrievalChain` 在 `RetrievalQA` 的基础上多了一步——**用 LLM 把"对话历史 + 新问题"压缩成一个独立的查询**，再去做检索和问答。

---

## 3. 准备工作

```python
import os, openai, sys
sys.path.append('../..')
import panel as pn   # GUI 库
pn.extension()

from dotenv import load_dotenv, find_dotenv
_ = load_dotenv(find_dotenv())
openai.api_key = os.environ['OPENAI_API_KEY']

# LLM 版本选择（gpt-3.5-turbo-0301 在 2023-09-02 后弃用）
import datetime
current_date = datetime.datetime.now().date()
if current_date < datetime.date(2023, 9, 2):
    llm_name = "gpt-3.5-turbo-0301"
else:
    llm_name = "gpt-3.5-turbo"

# (可选) 接入 LangSmith 追踪
# os.environ["LANGCHAIN_TRACING_V2"] = "true"
# os.environ["LANGCHAIN_ENDPOINT"] = "https://api.langchain.plus"
# os.environ["LANGCHAIN_API_KEY"] = "..."
```

> 如果开通了 LangSmith 平台，建议**从一开始就打开追踪**——本课内部流程更复杂，可视化能极大帮助理解。

---

## 4. 复习：先搭建一个 RetrievalQA（基线）

```python
from langchain.vectorstores import Chroma
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA

# 加载已有向量库
persist_directory = 'docs/chroma/'
embedding = OpenAIEmbeddings()
vectordb = Chroma(persist_directory=persist_directory, embedding_function=embedding)

# 验证
question = "What are major topics for this class?"
docs = vectordb.similarity_search(question, k=3)
len(docs)   # 3

# 初始化 LLM
llm = ChatOpenAI(model_name=llm_name, temperature=0)
llm.predict("Hello world!")   # sanity check

# 构建 PromptTemplate
template = """Use the following pieces of context to answer the question at the end. \
If you don't know the answer, just say that you don't know, don't try to make up an answer. \
Use three sentences maximum. Keep the answer as concise as possible. \
Always say "thanks for asking!" at the end of the answer.
{context}
Question: {question}
Helpful Answer:"""

QA_CHAIN_PROMPT = PromptTemplate(
    input_variables=["context", "question"],
    template=template,
)

# 创建 RetrievalQA
qa_chain = RetrievalQA.from_chain_type(
    llm,
    retriever=vectordb.as_retriever(),
    return_source_documents=True,
    chain_type_kwargs={"prompt": QA_CHAIN_PROMPT},
)

result = qa_chain({"query": "Is probability a class topic?"})
result["result"]
```

→ 这就是上一节的基线，**没有记忆**。

---

## 5. 加入 Memory

### 5.1 ConversationBufferMemory

最简单的一种记忆类型：**把所有历史消息存为一个 buffer（列表）**，每次调用时一并传入。

```python
from langchain.memory import ConversationBufferMemory

memory = ConversationBufferMemory(
    memory_key="chat_history",   # 与 prompt 中的输入变量名对齐
    return_messages=True         # 返回消息列表（而非单个字符串）
)
```

| 参数 | 作用 |
|------|------|
| `memory_key="chat_history"` | 让 chain 在拼接 prompt 时知道从哪个键取历史 |
| `return_messages=True` | 历史以**消息列表**形式返回（适合 ChatModel），而不是合并成字符串 |

> **更深入的 Memory 类型** 见第一门课《LangChain for LLM Application Development》第 03 课。

---

## 6. ConversationalRetrievalChain

### 6.1 创建链

```python
from langchain.chains import ConversationalRetrievalChain

retriever = vectordb.as_retriever()

qa = ConversationalRetrievalChain.from_llm(
    llm,
    retriever=retriever,
    memory=memory
)
```

### 6.2 测试：追问也能对得上

```python
# 第一轮提问
question = "Is probability a class topic?"
result = qa({"question": question})
result['answer']
# → "The instructor assumes that students have basic understanding of probability and statistics..."

# 追问
question = "why are those prerequesites needed?"
result = qa({"question": question})
result['answer']
# → 答案围绕"概率和统计为何被列为前置课程"展开，
#   不再像 RetrievalQA 那样跑偏到"计算机科学基础"
```

→ **追问与上一轮上下文完美衔接**！

---

## 7. 底层流程：LangSmith 看链内部发生了什么

`ConversationalRetrievalChain` 的一次调用，内部**有两次独立的 LLM 调用**：

### 7.1 第一次 LLM 调用：重写为独立问题

**Prompt 模板（节选）：**

> "Given the following conversation and a follow up question, rephrase the follow up question to be a stand-alone question."

**输入：**

- 历史：`Q: Is probability a class topic? / A: The instructor assumes...`
- 追问：`why are those prerequesites needed?`

**输出（独立问题）：**

> "What is the reason for requiring basic probability and statistics as prerequisites for the class?"

### 7.2 第二次 LLM 调用：基于检索结果回答

把上一步的**独立问题**送入 retriever → 取回相关文档 → 走 Stuff Documents Chain：

**System Prompt：**

> "Use the following pieces of context to answer the user's question."
> 
> + 检索到的若干文档片段
> + 独立问题

**输出：** 最终答案。

### 7.3 为什么需要这一步重写？

- **原始追问**（"why are those prerequisites needed?"）单独看是**指代不明**的——retriever 不知道 "those prerequisites" 指什么
- **重写后的独立问题**显式包含 "basic probability and statistics" → retriever 能准确召回相关文档

> **关键洞察：** 这一步是 `ConversationalRetrievalChain` 比 `RetrievalQA` 强大的核心原因。

---

## 8. 端到端：构建 ChatBot UI（Panel + Param）

> 接下来把所有组件整合到一个交互式 UI 中。这一段 GUI 代码较多，但**核心逻辑就是 `load_db` 函数**——它本质上是这门课所学的**全流程的浓缩版**。

### 8.1 一个函数走完所有流程

```python
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.text_splitter import CharacterTextSplitter, RecursiveCharacterTextSplitter
from langchain.vectorstores import DocArrayInMemorySearch
from langchain.document_loaders import TextLoader, PyPDFLoader
from langchain.chains import RetrievalQA, ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain.chat_models import ChatOpenAI


def load_db(file, chain_type, k):
    # 1. 加载文档
    loader = PyPDFLoader(file)
    documents = loader.load()

    # 2. 切分
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
    docs = text_splitter.split_documents(documents)

    # 3. 嵌入
    embeddings = OpenAIEmbeddings()

    # 4. 向量库（用内存型 DocArray，便于 demo）
    db = DocArrayInMemorySearch.from_documents(docs, embeddings)

    # 5. 检索器
    retriever = db.as_retriever(search_type="similarity", search_kwargs={"k": k})

    # 6. 对话型 RAG 链
    # 注意：这里**不传入 memory**，由外部 GUI 维护 chat_history
    qa = ConversationalRetrievalChain.from_llm(
        llm=ChatOpenAI(model_name=llm_name, temperature=0),
        chain_type=chain_type,
        retriever=retriever,
        return_source_documents=True,
        return_generated_question=True,   # 返回 LLM 重写后的独立问题
    )
    return qa
```

> **关键设计：** `memory` 没有传给 chain，而是由外部 UI 维护 `chat_history` 列表，每次调用时显式传入。这样更灵活、易管理。

### 8.2 Panel 聊天界面（核心类）

```python
import panel as pn
import param


class cbfs(param.Parameterized):
    chat_history = param.List([])
    answer = param.String("")
    db_query = param.String("")
    db_response = param.List([])

    def __init__(self, **params):
        super(cbfs, self).__init__(**params)
        self.panels = []
        self.loaded_file = "docs/cs229_lectures/MachineLearning-Lecture01.pdf"
        self.qa = load_db(self.loaded_file, "stuff", 4)

    def call_load_db(self, count):
        if count == 0 or file_input.value is None:
            return pn.pane.Markdown(f"Loaded File: {self.loaded_file}")
        else:
            file_input.save("temp.pdf")
            self.loaded_file = file_input.filename
            button_load.button_style = "outline"
            self.qa = load_db("temp.pdf", "stuff", 4)
            button_load.button_style = "solid"
        self.clr_history()
        return pn.pane.Markdown(f"Loaded File: {self.loaded_file}")

    def convchain(self, query):
        if not query:
            return pn.WidgetBox(pn.Row('User:', pn.pane.Markdown("", width=600)), scroll=True)

        # ★ 关键：因为外部管理 memory，所以手动传入 chat_history
        result = self.qa({"question": query, "chat_history": self.chat_history})

        # ★ 关键：把本轮 (question, answer) 追加到 chat_history
        self.chat_history.extend([(query, result["answer"])])

        self.db_query = result["generated_question"]
        self.db_response = result["source_documents"]
        self.answer = result['answer']

        self.panels.extend([
            pn.Row('User:', pn.pane.Markdown(query, width=600)),
            pn.Row('ChatBot:', pn.pane.Markdown(self.answer, width=600,
                                                style={'background-color': '#F6F6F6'}))
        ])
        inp.value = ''
        return pn.WidgetBox(*self.panels, scroll=True)

    @param.depends('db_query', )
    def get_lquest(self):
        if not self.db_query:
            return pn.Column(
                pn.Row(pn.pane.Markdown(f"Last question to DB:", styles={'background-color': '#F6F6F6'})),
                pn.Row(pn.pane.Str("no DB accesses so far"))
            )
        return pn.Column(
            pn.Row(pn.pane.Markdown(f"DB query:", styles={'background-color': '#F6F6F6'})),
            pn.pane.Str(self.db_query)
        )

    @param.depends('db_response', )
    def get_sources(self):
        if not self.db_response:
            return
        rlist = [pn.Row(pn.pane.Markdown(f"Result of DB lookup:", styles={'background-color': '#F6F6F6'}))]
        for doc in self.db_response:
            rlist.append(pn.Row(pn.pane.Str(doc)))
        return pn.WidgetBox(*rlist, width=600, scroll=True)

    @param.depends('convchain', 'clr_history')
    def get_chats(self):
        if not self.chat_history:
            return pn.WidgetBox(pn.Row(pn.pane.Str("No History Yet")), width=600, scroll=True)
        rlist = [pn.Row(pn.pane.Markdown(f"Current Chat History variable", styles={'background-color': '#F6F6F6'}))]
        for exchange in self.chat_history:
            rlist.append(pn.Row(pn.pane.Str(exchange)))
        return pn.WidgetBox(*rlist, width=600, scroll=True)

    def clr_history(self, count=0):
        self.chat_history = []
        return
```

### 8.3 组装 Dashboard

```python
cb = cbfs()

file_input = pn.widgets.FileInput(accept='.pdf')
button_load = pn.widgets.Button(name="Load DB", button_type='primary')
button_clearhistory = pn.widgets.Button(name="Clear History", button_type='warning')
button_clearhistory.on_click(cb.clr_history)
inp = pn.widgets.TextInput(placeholder='Enter text here…')

bound_button_load = pn.bind(cb.call_load_db, button_load.param.clicks)
conversation = pn.bind(cb.convchain, inp)

jpg_pane = pn.pane.Image('./img/convchain.jpg')

tab1 = pn.Column(
    pn.Row(inp),
    pn.layout.Divider(),
    pn.panel(conversation, loading_indicator=True, height=300),
    pn.layout.Divider(),
)
tab2 = pn.Column(
    pn.panel(cb.get_lquest),
    pn.layout.Divider(),
    pn.panel(cb.get_sources),
)
tab3 = pn.Column(
    pn.panel(cb.get_chats),
    pn.layout.Divider(),
)
tab4 = pn.Column(
    pn.Row(file_input, button_load, bound_button_load),
    pn.Row(button_clearhistory,
           pn.pane.Markdown("Clears chat history. Can use to start a new topic")),
    pn.layout.Divider(),
    pn.Row(jpg_pane.clone(width=400))
)

dashboard = pn.Column(
    pn.Row(pn.pane.Markdown('# ChatWithYourData_Bot')),
    pn.Tabs(
        ('Conversation', tab1),
        ('Database', tab2),
        ('Chat History', tab3),
        ('Configure', tab4)
    )
)
dashboard
```

### 8.4 UI 标签页功能

| 标签页 | 内容 |
|--------|------|
| **Conversation** | 输入问题、查看对话流 |
| **Database** | 查看上一次发往向量库的"独立问题"+ 检索到的源文档 |
| **Chat History** | 查看当前 `chat_history` 列表内容 |
| **Configure** | 上传新 PDF 重建数据库；清空历史 |

### 8.5 实测演示

```
用户：Who are the TAs?
机器人：The TAs are Paul Baumstarck, Catie Chang, ...

用户：what are their majors?
机器人：Paul is studying machine learning and computer vision,
        while Catie is actually a neuroscientist.
```

→ 追问"他们的专业是什么"完美承接"TA 是谁"——**对话连续性已建立**。

---

## 9. 整门课程总结

### 9.1 整体回顾

| 阶段 | 学到了什么 |
|------|-----------|
| **L02 文档加载** | 80+ 种加载器（PDF / YouTube / URL / Notion ...） |
| **L03 文档切分** | 字符 / 递归 / Token / 标题感知 4 类分割器；chunk_size / overlap 的细节 |
| **L04 向量存储与嵌入** | OpenAI Embeddings + Chroma；点积相似度；两类失败模式 |
| **L05 高级检索** | MMR、Self-Query、Compression、SVM/TF-IDF |
| **L06 问答** | RetrievalQA + Stuff/Map-Reduce/Refine 三种链类型 |
| **L07 对话** | Memory + ConversationalRetrievalChain（重写独立问题）+ 完整 ChatBot |

### 9.2 Harrison 的鼓励与展望

> "你已经构建出了一个端到端的、和你的数据对话的聊天机器人。"

- 鼓励上传自己的文档继续探索
- 如果你发现新的技巧或玩法，欢迎在 Twitter 分享，或给 LangChain 提 PR
- 这是一个**飞速发展**的领域，正是激动人心的构建时代

---

## 10. 本课小结

### 10.1 核心收获

| 主题 | 要点 |
|------|------|
| **痛点** | RetrievalQA 没有对话状态，无法处理追问 |
| **解决方案** | `ConversationBufferMemory` + `ConversationalRetrievalChain` |
| **关键机制** | 用 LLM 把"历史 + 追问"重写为**独立问题**，再做检索 |
| **GUI 实践** | Panel + Param 构建多标签页 ChatBot |
| **外部管理记忆** | 在 GUI 场景下，由外部维护 `chat_history` 列表，每次调用显式传入 |

### 10.2 灵活组合

`ConversationalRetrievalChain` 支持：

- 不同的 `chain_type`（stuff / map_reduce / refine / map_rerank）
- 不同的 retriever（普通向量检索、MMR、Self-Query、Compression）
- 不同的 Memory 类型
- 不同的"问题重写" prompt 模板

→ **整个 LangChain 生态都可以模块化拼接**。

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
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain

# === 1. 准备 vectordb + LLM ===
vectordb = Chroma(persist_directory='docs/chroma/', embedding_function=OpenAIEmbeddings())
llm = ChatOpenAI(model_name=llm_name, temperature=0)

# === 2. Memory ===
memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

# === 3. ConversationalRetrievalChain ===
qa = ConversationalRetrievalChain.from_llm(
    llm,
    retriever=vectordb.as_retriever(),
    memory=memory
)

result = qa({"question": "Is probability a class topic?"})
print(result['answer'])

result = qa({"question": "why are those prerequesites needed?"})
print(result['answer'])   # 答案与前一轮无缝衔接

# === 4. 端到端 ChatBot 工厂函数 ===
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import DocArrayInMemorySearch
from langchain.document_loaders import PyPDFLoader

def load_db(file, chain_type, k):
    documents = PyPDFLoader(file).load()
    docs = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150).split_documents(documents)
    db = DocArrayInMemorySearch.from_documents(docs, OpenAIEmbeddings())
    retriever = db.as_retriever(search_type="similarity", search_kwargs={"k": k})
    return ConversationalRetrievalChain.from_llm(
        llm=ChatOpenAI(model_name=llm_name, temperature=0),
        chain_type=chain_type,
        retriever=retriever,
        return_source_documents=True,
        return_generated_question=True,
    )

# === 5. 外部维护 chat_history（GUI 场景） ===
qa = load_db("docs/cs229_lectures/MachineLearning-Lecture01.pdf", "stuff", 4)
chat_history = []

result = qa({"question": "Who are the TAs?", "chat_history": chat_history})
chat_history.append((result["question"] if "question" in result else "Who are the TAs?", result["answer"]))

result = qa({"question": "what are their majors?", "chat_history": chat_history})
print(result["answer"])
```
