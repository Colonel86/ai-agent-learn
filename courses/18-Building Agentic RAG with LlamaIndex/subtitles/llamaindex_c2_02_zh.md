# 第 1 课：路由查询引擎（Router Query Engine）

本课从**最简单的 Agentic RAG 形态——路由器（Router）**开始。给定一个用户查询，路由器会**在多个查询引擎（Query Engine）中挑选合适的一个**去执行，从而获得初步的"动态查询理解"能力。

我们要在一篇 PDF 论文（MetaGPT，ICLR 2024 oral）上构建一个简单路由器，让它既能做**问答（QA）**，也能做**摘要（Summarization）**。前三节课都是基于单文档展开，最后一课才会推广到多文档。

## 环境准备

```python
from helper import get_openai_api_key
OPENAI_API_KEY = get_openai_api_key()

import nest_asyncio
nest_asyncio.apply()
```

`nest_asyncio` 是必须的：Jupyter 自身在背后运行了一个事件循环，而 LlamaIndex 的许多模块用到 async，要让二者和谐共存就得打这个补丁。

## 加载文档并切分

使用 LlamaIndex 的 `SimpleDirectoryReader` 把 PDF 解析为文档对象，再用 `SentenceSplitter` 按句子边界切成 chunk_size=1024 的均匀分块（节点 nodes）。

```python
from llama_index.core import SimpleDirectoryReader
from llama_index.core.node_parser import SentenceSplitter

documents = SimpleDirectoryReader(input_files=["metagpt.pdf"]).load_data()
splitter = SentenceSplitter(chunk_size=1024)
nodes = splitter.get_nodes_from_documents(documents)
```

## 配置 LLM 与 Embedding 模型

通过全局 `Settings` 注入 LLM 与 embedding 模型——本课默认 `gpt-3.5-turbo` + `text-embedding-ada-002`，你也可以换成自己的模型。

```python
from llama_index.core import Settings
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding

Settings.llm = OpenAI(model="gpt-3.5-turbo")
Settings.embed_model = OpenAIEmbedding(model="text-embedding-ada-002")
```

## 在同一份数据上建立两个索引

**核心思想：索引（Index）可以看作是数据之上的一层元数据，不同索引拥有不同的检索行为。** 我们在同一组 nodes 上建立两个索引：

- **`VectorStoreIndex`（向量索引）**：用 embedding 表征节点，查询时返回与问题向量最相似的若干节点。这是 RAG 的核心抽象。
- **`SummaryIndex`（摘要索引）**：结构非常简单，查询时**返回索引中全部节点**，不依赖用户查询本身——非常适合做总览/摘要。

```python
from llama_index.core import SummaryIndex, VectorStoreIndex

summary_index = SummaryIndex(nodes)
vector_index = VectorStoreIndex(nodes)
```

## 从索引派生 Query Engine 再封装为 Query Tool

**Query Engine** 是基于某个索引的"完整查询接口"，它把 **检索 + LLM 综合（synthesis）** 组合在一起。

```python
summary_query_engine = summary_index.as_query_engine(
    response_mode="tree_summarize",
    use_async=True,
)
vector_query_engine = vector_index.as_query_engine()
```

`use_async=True` 借助异步能力加速摘要生成（因为摘要要遍历全部节点）。

**Query Tool = Query Engine + 元数据描述**。描述（description）会被作为提示词的一部分，告诉 LLM 这个工具适合回答什么样的问题——这就是路由器选择的依据。

```python
from llama_index.core.tools import QueryEngineTool

summary_tool = QueryEngineTool.from_defaults(
    query_engine=summary_query_engine,
    description="Useful for summarization questions related to MetaGPT",
)
vector_tool = QueryEngineTool.from_defaults(
    query_engine=vector_query_engine,
    description="Useful for retrieving specific context from the MetaGPT paper.",
)
```

## 定义路由器：RouterQueryEngine + LLMSingleSelector

LlamaIndex 提供多种 **Selector（选择器）** 来构建路由器，主要分两类：

- **LLM Selector**：用提示词让 LLM 输出 JSON，再解析出要选哪个索引。
- **Pydantic Selector**：不让 LLM 直接吐原始 JSON，而是借助像 OpenAI 这种支持 **函数调用 API（function calling）** 的模型，直接产出结构化的 Pydantic 选择对象。

每一类还可以是 **single（单选）** 或 **multi（多选）**——多选意味着可以同时路由到多个索引并合并结果。

本课先用最简单的 `LLMSingleSelector`：

```python
from llama_index.core.query_engine.router_query_engine import RouterQueryEngine
from llama_index.core.selectors import LLMSingleSelector

query_engine = RouterQueryEngine(
    selector=LLMSingleSelector.from_defaults(),
    query_engine_tools=[summary_tool, vector_tool],
    verbose=True,
)
```

## 实际测试

### 摘要类问题 → 命中 summary_tool

```python
response = query_engine.query("What is the summary of the document?")
```

`verbose=True` 会打印中间步骤。可以看到路由选择了 **query engine 0**（summary_tool），因为它的描述是"Useful for summarization questions related to MetaGPT"。返回的回答正是对论文的整体概括：MetaGPT 是一个面向 LLM 多智能体协作的元编程框架。

验证一下来源节点的数量：

```python
print(len(response.source_nodes))  # 34
```

**34 恰好等于整篇文档被切成的 chunk 数**——这印证了摘要查询确实遍历了索引中的所有节点。

### 细节类问题 → 命中 vector_tool

```python
response = query_engine.query(
    "How do agents share information with other agents?"
)
```

这次路由命中 **query engine 1**（vector_tool）。LLM 给出的理由是：这个问题需要"从 MetaGPT 论文中检索具体上下文"，因为相关信息很可能集中在某一段里。最终它准确地返回了答案——智能体通过共享消息池发布结构化消息进行协作。

## 整合为辅助函数

上述全部逻辑可以打包成一个工具函数，方便你在自己的 PDF 上复用：

```python
from utils import get_router_query_engine

query_engine = get_router_query_engine("metagpt.pdf")
response = query_engine.query("Tell me about the ablation study results?")
print(str(response))
```

消融实验是论文中的具体细节，路由器会选择 vector 工具来定位相关段落并给出答案。

---

**小结**：本课让你看到了 Agentic RAG 的最简形态——**LLM 不再只是综合答案，而是介入决策**，在多个查询引擎间做选择。下一课我们会把决策权进一步扩大：让 LLM 不仅选工具，还能为工具**生成参数**。
