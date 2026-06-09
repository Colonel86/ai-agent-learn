# 第 2 课：工具调用（Tool Calling）

## 从路由到工具调用：再进一步

在基础 RAG 流水线里，LLM 只用于**最终的综合（synthesis）**。第 1 课让 LLM 升级了一档——**挑选合适的查询管道**来回答用户问题，这其实已经是一种简化版的"工具调用"。

本课要再进一步：**让 LLM 不仅选择要调用的函数，还要推断（infer）传给该函数的参数**。这样一来，LLM 不只是消费向量数据库的输出，而是真正"知道怎么用"向量数据库——用户因此能得到比标准 RAG 更精准的结果。

## 基础：FunctionTool 与 predict_and_call

LlamaIndex 中工具调用的核心抽象是 **`FunctionTool`**，它能把任意 Python 函数包装成一个工具：

```python
from llama_index.core.tools import FunctionTool

def add(x: int, y: int) -> int:
    """Adds two integers together."""
    return x + y

def mystery(x: int, y: int) -> int:
    """Mystery function that operates on top of two numbers."""
    return (x + y) * (x + y)

add_tool = FunctionTool.from_defaults(fn=add)
mystery_tool = FunctionTool.from_defaults(fn=mystery)
```

**注意类型注解（type annotation）和 docstring 不只是写着好看**——它们会被作为提示词喂给 LLM，决定它能否正确选工具、传参数。

`FunctionTool` 原生对接 OpenAI 等模型的 function calling 能力。调用方式很简洁：

```python
from llama_index.llms.openai import OpenAI

llm = OpenAI(model="gpt-3.5-turbo")
response = llm.predict_and_call(
    [add_tool, mystery_tool],
    "Tell me the output of the mystery function on 2 and 9",
    verbose=True,
)
```

`predict_and_call` 接收一组工具和一段 prompt（或一系列 chat messages），它会：

1. 决定调用哪个工具
2. 调用该工具
3. 返回最终响应

中间日志显示：LLM 调用了 `mystery(x=2, y=9)`，返回 `121`（即 `11 × 11`）——工具选对了，参数也推断对了。这其实就是路由器的**升级版**：不仅选工具，还会给工具准备参数。

## 把这个能力套到向量检索上：自动元数据过滤

现在把这个思路用在更有意思的场景里——让 LLM 不只选向量搜索，**还能推断元数据过滤器（metadata filters）**，从而得到更精确的检索结果。

### 加载并切分文档（同上一课）

```python
from llama_index.core import SimpleDirectoryReader
from llama_index.core.node_parser import SentenceSplitter

documents = SimpleDirectoryReader(input_files=["metagpt.pdf"]).load_data()
splitter = SentenceSplitter(chunk_size=1024)
nodes = splitter.get_nodes_from_documents(documents)
```

### 观察节点上的元数据

```python
print(nodes[0].get_content(metadata_mode="all"))
```

`metadata_mode="all"` 会同时打印出节点内容**和**附在文档上、传播到每个节点的元数据。你会看到诸如：

- `page_label = 1`
- `file_name = metagpt.pdf`
- `file_type`、`file_size`、创建/修改日期……

不同节点的 `page_label` 不同——也就是说每个 chunk 自带页码标注。这是后面过滤的基础。

### 手动元数据过滤示例

```python
from llama_index.core import VectorStoreIndex
from llama_index.core.vector_stores import MetadataFilters

vector_index = VectorStoreIndex(nodes)

query_engine = vector_index.as_query_engine(
    similarity_top_k=2,
    filters=MetadataFilters.from_dicts(
        [{"key": "page_label", "value": "2"}]
    ),
)

response = query_engine.query("What are some high-level results of MetaGPT?")

for n in response.source_nodes:
    print(n.metadata)  # 全部 page_label == "2"
```

可以看到，搜索结果被严格限制在 **page 2** 的节点之内。

## 让 LLM 自动推断过滤器

接下来就是把这一切包装成一个工具，**让 LLM 自己来决定要过滤哪些页码**，而不是用户手动指定：

```python
from typing import List
from llama_index.core.vector_stores import FilterCondition

def vector_query(
    query: str,
    page_numbers: List[str]
) -> str:
    """Perform a vector search over an index.

    query (str): the string query to be embedded.
    page_numbers (List[str]): Filter by set of pages. Leave BLANK if we want
        to perform a vector search over all pages. Otherwise, filter by the
        set of specified pages.
    """
    metadata_dicts = [
        {"key": "page_label", "value": p} for p in page_numbers
    ]
    query_engine = vector_index.as_query_engine(
        similarity_top_k=2,
        filters=MetadataFilters.from_dicts(
            metadata_dicts,
            condition=FilterCondition.OR,
        ),
    )
    return query_engine.query(query)

vector_query_tool = FunctionTool.from_defaults(
    name="vector_tool",
    fn=vector_query,
)
```

注意 docstring 里**显式告诉 LLM 怎么用 `page_numbers`**——这是让推断准确的关键。

测试一下：

```python
llm = OpenAI(model="gpt-3.5-turbo", temperature=0)
response = llm.predict_and_call(
    [vector_query_tool],
    "What are the high-level results of MetaGPT as described on page 2?",
    verbose=True,
)
```

LLM 不但形成了正确的语义 query，还推断出 `page_numbers=["2"]`。来源节点验证显示它们全部来自 page 2。

> 元数据并不局限于页码：你可以加 section ID、headers、footers……越强的模型（如 GPT-4）越能用好多元过滤。

## 组合多个工具：让 LLM 做更艰难的选择

把第 1 课里的 **summary_tool** 拿回来，和 **vector_query_tool** 一起交给 LLM，让它根据问题挑工具，同时推断参数：

```python
from llama_index.core import SummaryIndex
from llama_index.core.tools import QueryEngineTool

summary_index = SummaryIndex(nodes)
summary_query_engine = summary_index.as_query_engine(
    response_mode="tree_summarize",
    use_async=True,
)
summary_tool = QueryEngineTool.from_defaults(
    name="summary_tool",
    query_engine=summary_query_engine,
    description="Useful if you want to get a summary of MetaGPT",
)
```

### 问"具体细节" → vector_tool + 页码

```python
response = llm.predict_and_call(
    [vector_query_tool, summary_tool],
    "What are the MetaGPT comparisons with ChatDev described on page 8?",
    verbose=True,
)
```

LLM 调用 `vector_tool`，并推断 `page_numbers=["8"]`，返回的来源节点页码也确实是 8。

### 问"整体摘要" → summary_tool

```python
response = llm.predict_and_call(
    [vector_query_tool, summary_tool],
    "What is a summary of the paper?",
    verbose=True,
)
```

这一次 LLM 正确切换到 `summary_tool`。

---

**小结**：本课让 LLM 学会了"**选工具 + 填参数**"。下一课我们再上一个台阶——**完整的智能体推理循环（Agent Reasoning Loop）**，让 LLM 在多个工具上完成多步推理，并维护对话记忆。
