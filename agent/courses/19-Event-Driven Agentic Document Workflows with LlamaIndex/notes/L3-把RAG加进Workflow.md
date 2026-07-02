# L3：把 RAG 加进 Workflow

本节目标：给 Workflow 接入一个**文档库**——用 **LlamaParse** 解析一份简历 PDF，灌入向量库（Vector Store），用 RAG 查询引擎回答问题，再把整套 RAG 封装成一个 Workflow。

## 1. 准备工作：nest_asyncio 与 API Key

这个 notebook 里既有 Workflow 的 async 调用，又会调用底层的 async 函数，需要**嵌套事件循环（nested event loop）**：

```python
import nest_asyncio
nest_asyncio.apply()
```

需要两把钥匙：

- **OpenAI API Key**：用作嵌入模型和 LLM；
- **LlamaCloud API Key**：用作 LlamaParse（可在 `cloud.llamaindex.ai` 免费申请）。

> **LlamaParse** 是一款高级文档解析器，支持 PDF、Word、PowerPoint、Excel 等格式，特别擅长把**复杂 PDF** 转成 LLM 易于理解的结构化文本。

## 2. 解析简历

LlamaParse 的一个亮点是可以**告诉它你在解析什么**，从而更聪明地组织内容：

```python
from llama_parse import LlamaParse

documents = LlamaParse(
    api_key=llama_cloud_api_key,
    base_url=os.getenv("LLAMA_CLOUD_BASE_URL"),
    result_type="markdown",
    content_guideline_instruction="This is a resume, gather related facts together and format it as bullet points with headers"
).load_data("data/fake_resume.pdf")
```

得到的是一组 **`Document`** 对象，每个 Document 默认包含：

- 文本（text）；
- `metadata`：附加注释字典；
- `relationships`：与其他 Document 的关系。

由于 `result_type="markdown"`，解析结果是带标题层级、项目符号的 Markdown，例如自动整理出 Projects、Company、Bullet Points 等结构。

## 3. 建立向量索引

把 Documents 喂给 **`VectorStoreIndex`**，它会用嵌入模型把文本切块并向量化：

```python
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core import VectorStoreIndex

index = VectorStoreIndex.from_documents(
    documents,
    embed_model=OpenAIEmbedding(model_name="text-embedding-3-small",
                                api_key=openai_api_key)
)
```

`text-embedding-3-small` 是 OpenAI 提供的轻量但效果很好的嵌入模型。返回的 `index` 是 RAG 应用的核心数据结构，可用来构建 Query Engine 或 Chat Engine。

## 4. 建立查询引擎

```python
from llama_index.llms.openai import OpenAI

llm = OpenAI(model="gpt-4o-mini")
query_engine = index.as_query_engine(llm=llm, similarity_top_k=5)
response = query_engine.query("What is this person's name and what was their most recent job?")
print(response)
```

- `similarity_top_k=5` 表示**只返回最相关的 5 段上下文**，再交给 LLM 做生成。
- 课堂里假候选人叫 **Sarah Chen**，最近的工作是 **Senior Full Stack Developer @ TechFlow Solutions**。

## 5. 把索引持久化到磁盘

索引可以保存到磁盘，避免每次重复解析嵌入：

```python
storage_dir = "./storage"
index.storage_context.persist(persist_dir=storage_dir)
```

下次加载：

```python
from llama_index.core import StorageContext, load_index_from_storage

if os.path.exists(storage_dir):
    storage_context = StorageContext.from_defaults(persist_dir=storage_dir)
    restored_index = load_index_from_storage(storage_context)
else:
    print("Index not found on disk.")
```

> 生产环境会用托管向量库（hosted vector store），但本地 `persist()` 已经足够课程演示。

## 6. 把 RAG 变成 Agent 的工具

要让 Agent 调用 RAG，先把它包成一个**带描述的函数**：

```python
from llama_index.core.tools import FunctionTool
from llama_index.core.agent import FunctionCallingAgent

def query_resume(q: str) -> str:
    """Answers questions about a specific resume."""
    response = query_engine.query(
        f"This is a question about the specific resume we have in our database: {q}"
    )
    return response.response
```

函数的**名字、参数类型、返回类型、docstring** 都很重要——框架会把它们全部交给 LLM，LLM 据此判断"这工具是干嘛的、要不要用、怎么用"。

把函数变成工具，再装进一个 `FunctionCallingAgent`：

```python
resume_tool = FunctionTool.from_defaults(fn=query_resume)

agent = FunctionCallingAgent.from_tools(
    tools=[resume_tool],
    llm=llm,
    verbose=True,
)

response = agent.chat("How many years of experience does the applicant have?")
print(response)
```

`FunctionCallingAgent` 是 LlamaIndex 里特别能干、且和 OpenAI 配合很好的 Agent 类型。`verbose=True` 会打印 Agent 的全过程：加问题进 memory → 选工具 → 用参数调用 → 拿到输出 → 由 LLM 给出最终回答。

## 7. 把 RAG 封装进 Workflow

最后把整套 RAG 重写成一个 **`RAGWorkflow`**，从零开始、不依赖前面的实例。整个工作流只有两步：

1. **`set_up`**：由 `StartEvent` 触发，搭建 RAG（建立或恢复 index、构造 query engine），然后发射 `QueryEvent`；
2. **`ask_question`**：由 `QueryEvent` 触发，执行查询并发射 `StopEvent`。

```python
from llama_index.core.workflow import (
    StartEvent, StopEvent, Workflow, step, Event, Context
)

class QueryEvent(Event):
    query: str

class RAGWorkflow(Workflow):
    storage_dir = "./storage"
    llm: OpenAI
    query_engine: VectorStoreIndex

    @step
    async def set_up(self, ctx: Context, ev: StartEvent) -> QueryEvent:
        if not ev.resume_file:
            raise ValueError("No resume file provided")

        self.llm = OpenAI(model="gpt-4o-mini")

        if os.path.exists(self.storage_dir):
            storage_context = StorageContext.from_defaults(persist_dir=self.storage_dir)
            index = load_index_from_storage(storage_context)
        else:
            documents = LlamaParse(
                result_type="markdown",
                content_guideline_instruction="This is a resume, gather related facts together and format it as bullet points with headers"
            ).load_data(ev.resume_file)
            index = VectorStoreIndex.from_documents(
                documents,
                embed_model=OpenAIEmbedding(model_name="text-embedding-3-small")
            )
            index.storage_context.persist(persist_dir=self.storage_dir)

        self.query_engine = index.as_query_engine(llm=self.llm, similarity_top_k=5)
        return QueryEvent(query=ev.query)

    @step
    async def ask_question(self, ctx: Context, ev: QueryEvent) -> StopEvent:
        response = self.query_engine.query(
            f"This is a question about the specific resume we have in our database: {ev.query}"
        )
        return StopEvent(result=response.response)
```

运行方式和 L2 完全一致：

```python
w = RAGWorkflow(timeout=120, verbose=False)
result = await w.run(
    resume_file="./data/fake_resume.pdf",
    query="Where is the first place the applicant worked?"
)
print(result)
```

## 一个小坑

Laurie 留了个**潜在 Bug** 让你思考：如果换一份新简历再跑一次，由于代码看到 `./storage` 目录存在就直接复用，**新简历不会被重新解析**。你可以想想怎么修——例如把 `storage_dir` 与简历文件名做绑定（哈希、子目录等）。

## 小结

到这里，你已经搭好了一个能被 Agent 调用的 RAG 管道，并且把它整洁地封装进 Workflow。下一课，开始给 Agent 派**更复杂的任务**——解析职位申请表，并生成填表问题。
