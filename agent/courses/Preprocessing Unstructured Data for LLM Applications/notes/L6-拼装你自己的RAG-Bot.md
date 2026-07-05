# L6 · 拼装你自己的 RAG Bot（异构语料 → 清洗 → chunk → Chroma → 混合检索）

> 课程：Preprocessing Unstructured Data for LLM Applications（DeepLearning.AI × Unstructured）
> 本课任务：把 L2–L5 的全部预处理技能拼成一个端到端 RAG bot——语料是关于 **Donut 模型**的一批异构文档（PDF 论文 + PPTX 幻灯 + Markdown README），支持问答与按来源过滤。

## 0. 承上：从"零件"到"整机"

前四课造了一堆零件：多格式规范化、metadata、视觉抽取、表格结构。本课是**集成课**——目标应用是"围绕 Donut 模型文档的问答机器人"。整机流水线：

```
异构语料 → 分类型预处理 → 元数据清洗 → chunk_by_title → 向量化入库(Chroma)
        → 检索(similarity / 带 filter) → prompt 模板 → LLM → 带来源的回答
```

## 1. 异构语料的分类型摄取

语料三份，**每种格式用对应的 partition 函数**（这正是 L2 规范化的兑现）：

| 文档 | 内容 | 摄取方式 |
|---|---|---|
| `donut_paper.pdf` | Donut 论文，含复杂表格 | Unstructured **API** + YOLOX（model-based） |
| `donut_slide.pptx` | 介绍 Donut 的幻灯 | `partition_pptx`（本地开源库，规则解析） |
| `donut_readme.md` | GitHub README | `partition_md`（本地开源库） |

```python
from unstructured.partition.pptx import partition_pptx
from unstructured.partition.md import partition_md
from unstructured.chunking.title import chunk_by_title

# PDF：走 API，hi_res + yolox，并开启表格结构推断（沿用 L5）
req = shared.PartitionParameters(
    files=files, strategy="hi_res", hi_res_model_name="yolox",
    pdf_infer_table_structure=True, skip_infer_table_types=[],
)
pdf_elements = dict_to_elements(s.general.partition(req).elements)

pptx_elements = partition_pptx(filename="example_files/donut_slide.pptx")  # 规则解析
md_elements   = partition_md(filename="example_files/donut_readme.md")     # 规则解析
```

要点：**PDF 这类 model-based 走 API，规则可解析的（PPTX/MD）走本地开源库**——按需付费的分工。若要再加 Word，只需 `partition_docx`，语料可无限扩展。

> **对比课程 04 的 document loading（L3 metadata & chunking）**：L3 教的是"抽了 element 后怎么加元数据、按标题分块"；本课证明了**为什么 L2/L3 要坚持"统一 element 抽象"**——PDF、PPTX、MD 三种来源被各自的 partition 函数收敛成同一种 element 结构后，下游 `chunk_by_title`、入库、检索的代码**完全不区分它们的原始格式**。规范化的红利在集成这一刻才真正兑现：加一种新格式不牵动下游任何逻辑。

## 2. 元数据清洗：删掉不该被检索的内容

论文里有些内容不该进检索库。用 L3 的 metadata 精准剔除两类：

**① References 段落——按 `parent_id` 层级删**：

```python
# 找到 "References" 这个 Title element，拿它的 id
reference_title = [el for el in pdf_elements
                   if el.text == "References" and el.category == "Title"][0]
references_id = reference_title.id

# 凡是 parent_id 指向 References 的，都是参考文献条目 → 整段剔除
pdf_elements = [el for el in pdf_elements
                if el.metadata.parent_id != references_id]
```

**② 页眉——按 `category` 删**：页眉是"文档标题 + 页码"，会打断叙事结构、污染检索。

```python
pdf_elements = [el for el in pdf_elements if el.category != "Header"]
```

要点：**清洗发生在入库前、基于结构化 metadata**（parent_id 的父子关系、category 的类型）——这比事后用正则去噪精准得多，是 L3 元数据的直接变现。

## 3. 合并语料并 chunk

三种来源合成一个语料，用 L3 的 `chunk_by_title` 分块（在标题边界切，保持语义完整）：

```python
elements = chunk_by_title(pdf_elements + pptx_elements + md_elements)
```

## 4. 入库 Chroma：把 source 写进 metadata

转成 LangChain `Document`，**把文件名塞进 `source` 元数据**（后面混合检索要用），再用 OpenAI embeddings 灌进 Chroma：

```python
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings

documents = []
for el in elements:
    meta = el.metadata.to_dict()
    del meta["languages"]
    meta["source"] = meta["filename"]        # 关键：留下来源，供按来源过滤
    documents.append(Document(page_content=el.text, metadata=meta))

embeddings = OpenAIEmbeddings()
# filter_complex_metadata：Chroma 不吃嵌套/复杂元数据，先过滤掉
vectorstore = Chroma.from_documents(utils.filter_complex_metadata(documents), embeddings)
```

## 5. 检索 + prompt + 对话链

**检索器**取 top-6；**prompt 模板**约束"不知道就说不知道、非 Donut 问题礼貌拒答"（抑制幻觉）：

```python
retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 6})

template = """You are an AI assistant for answering questions about the Donut ...
If you don't know the answer, just say "Hmm, I'm not sure." Don't make up an answer.
If the question is not about Donut, politely inform them ...
Question: {question}
=========
{context}
=========
Answer in Markdown:"""
```

用 `ConversationalRetrievalChain` 串起来提问：

```python
qa_chain.invoke({
    "question": "How does Donut compare to other document understanding models?",
    "chat_history": []
})["answer"]
```

回答正确指出 **Donut 是不依赖 OCR 的文档理解模型**，并且——因为入库时写了 `source` 元数据——能**引用来源**（Donut 论文 + 幻灯）。来源可追溯的前提，正是 L4/L5 一路保下来的 metadata。

## 6. 混合检索：按来源过滤（metadata filter）

有时你明确知道答案在某个文件里，就把 similarity search **叠加一个 metadata filter**（L3 讲的 hybrid search）：

```python
filter_retriever = vectorstore.as_retriever(
    search_type="similarity",
    search_kwargs={"k": 1, "filter": {"source": "donut_readme.md"}}  # 只在 README 里找
)
# 用它重建一条链，再问 "How do I classify documents with Donut?"
# → 答案严格来自 README 的内容
```

要点：**hybrid search = 语义相似（向量）+ 结构过滤（metadata）**。当语料混杂多来源、多类型时，能按 `source`/`category`/`page` 缩小检索域，是精度与可控性的关键抓手。

> **架构师视角**：这个 bot 麻雀虽小，五脏俱全，但也暴露了"教学 RAG"与"生产 RAG"的差距——**没有 eval、没有增量更新、没有引用校验、chunk 策略未调优、embedding/LLM 型号写死**。从 demo 到生产，真正的工作量不在"跑通 pipeline"，而在这些被省略的部分。作为架构师，看到一条能跑的 RAG 链，第一反应应是问"它怎么被评测、怎么更新、错了怎么归因"，而不是"它答对了这道题"。

## 7. 本课总结

| 要点 | 一句话 |
|---|---|
| 分类型摄取 | PDF 走 API+YOLOX，PPTX/MD 走本地 partition，统一成 element |
| 结构化清洗 | 按 parent_id 删 References、按 category 删 Header，入库前净化 |
| 统一 chunk | 三源合并 `chunk_by_title`，下游不区分原格式 |
| source 元数据 | 入库时写 filename→source，换来"引用来源 + 按来源过滤" |
| 混合检索 | similarity + metadata filter，缩小检索域提精度 |

> **记忆点（引出 L7）**：一个能问答、能引用、能按来源过滤的 RAG bot 已经跑通。L7 是收官——回望整门课从"摄取归一化"到"RAG bot"的主线，并从架构师视角裁决：文档预处理在 RAG 管线里到底是什么地位，Unstructured 库 vs 自建解析该怎么取舍。

## 与我的资产映射

- 检索层：`agent/skills/agent-selection/3-retrieval.md`（hybrid search = 向量 + metadata filter；多源语料的入库清洗）
- 记忆/框架层：LangChain `ConversationalRetrievalChain` 作为 RAG 编排的一种现成实现，可入框架选型对照
- 面试包：`agent/interview/jd-senior-agent-engineer/`（"从 demo RAG 到生产 RAG 缺什么" 是高频追问）
- [[project_selection_matrix]]
