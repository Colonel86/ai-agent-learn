# L02 定制化 RAG（Customized RAG）

> 原始字幕：`subtitles/haystack_c1_L2.vtt`
> 配套代码：`code/Lesson_2.md`

---

## 一、把 L01 的 RAG 升级成"可定制"

L01 是检索 → 返回文档。L02 让它**生成答案**，并能：
- 引用文档来源 URL
- 切换输出语言
- 替换 Embedder（Cohere）和 Generator（OpenAI / Together / Llama-3）

---

## 二、Indexing：从 URL 抓 → HTML → Embed

新组件登场：**LinkContentFetcher + HTMLToDocument**。

```python
fetcher   = LinkContentFetcher()
converter = HTMLToDocument()
embedder  = CohereDocumentEmbedder(model="embed-english-v3.0", api_base_url=os.getenv("CO_API_URL"))
writer    = DocumentWriter(document_store=document_store)

indexing.connect("fetcher.streams", "converter.sources")
indexing.connect("converter", "embedder")
indexing.connect("embedder",  "writer")

indexing.run({"fetcher": {"urls": [...]}})
```

- Embedder 切换成 Cohere 只改一行——这就是 L00 提到的"统一接口"的红利。
- 每个 Document 的 `meta` 自动带 `url`，后面 Prompt 里能引用。

---

## 三、RAG 的灵魂：PromptBuilder + Jinja 模板

Haystack 的 `PromptBuilder` 用 **Jinja2** 做模板：

```python
prompt = """
Answer the question based on the provided context.
Context:
{% for doc in documents %}
   {{ doc.content }}
{% endfor %}
Question: {{ query }}
"""
```

完整 RAG 拓扑：

```
query_embedder → retriever → prompt(documents=…, query=…) → generator
```

```python
rag.connect("query_embedder.embedding", "retriever.query_embedding")
rag.connect("retriever.documents",      "prompt.documents")
rag.connect("prompt",                   "generator")
```

运行时按入口组件传参：

```python
rag.run({
    "query_embedder": {"text": question},
    "retriever":      {"top_k": 1},
    "prompt":         {"query": question},   # 模板里出现的非连接变量必须显式传
})
```

---

## 四、定制行为：参数化模板

把 prompt 改成"引用 URL + 指定语言"：

```python
prompt = """
You will be provided some context, followed by the URL that this context comes from.
Answer the question based on the context, and reference the URL.
Your answer should be in {{ language }}.
Context:
{% for doc in documents %}
   {{ doc.content }}
   URL: {{ doc.meta['url']}}
{% endfor %}
Question: {{ query }}
Answer:
"""

rag.run({
    "query_embedder": {"text": question},
    "retriever":      {"top_k": 1},
    "prompt":         {"query": question, "language": "French"},
})
```

> Jinja 变量被 `PromptBuilder` 自动识别为该组件的**输入端口**。这就是 Haystack 的精巧之处：**模板的变量名 = Pipeline 的接线点**。

---

## 五、换 Generator 的方式

OpenAI Compatible 接口让换模型极简：

```python
generator = OpenAIGenerator(
    api_key=Secret.from_env_var("TOGETHER_AI_API"),
    model="meta-llama/Llama-3-70b-chat-hf",
    api_base_url="https://api.together.xyz/v1",
)
```

`Secret.from_env_var` 是 Haystack 的密钥抽象（也支持 `from_token`），避免把 key 硬编码进序列化的 Pipeline。

---

## 六、架构取舍

- **为什么把 prompt 拆成独立组件？** —— 把"提示工程"从 LLM 调用里分离，便于 A/B、版本管理、可视化检查。Prompt 也是一种"资产"。
- **Jinja vs f-string** —— Jinja 支持循环/条件，原生适配"文档列表"这种 RAG 数据形态；f-string 做不到。
- **Embedder 解耦给了什么自由度？** —— Cohere、OpenAI、Sentence-Transformers、Jina、Nvidia NIM 可在不动 Pipeline 拓扑的前提下互换；评测不同 embedding 模型成本极低。

---

## 七、本节要点

- RAG = Retriever + PromptBuilder(Jinja) + Generator 的三段式管道。
- PromptBuilder 的模板变量自动暴露为组件输入，是"模板驱动接线"。
- Embedder / Generator 换实现只改初始化，Pipeline 拓扑不变。
- 用 `meta` 把 URL/标题等元数据带过整条管道，方便最终在答案中引用来源。
