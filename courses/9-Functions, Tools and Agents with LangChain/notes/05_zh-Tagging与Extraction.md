# Functions, Tools and Agents with LangChain — 第 05 课：Tagging 与 Extraction（中文整理）

> 来源：`subtitles/langchain_c3_05_en.vtt` + `code/L5-tagging-and-extraction-student.md`
> 本课目标：用 OpenAI Function Calling 做两类**最实用**的结构化输出任务 —— **Tagging（打标签）** 与 **Extraction（抽取实体）**，并用到真实网页文章上。

---

## 一、Tagging 与 Extraction 的区别

| 任务 | 输入 | 输出 | 典型例子 |
|------|------|------|----------|
| **Tagging** | 一段文本 + 结构描述 | **1 个**结构化对象 | 情感分析、语言检测 |
| **Extraction** | 一段文本 + 结构描述 | **一个列表**的结构化对象 | 从文章里抽取所有论文/人物 |

共同点：都依赖**用 Pydantic 描述"你想让 LLM 吐出什么结构"**，然后用 OpenAI Function Calling 让它必须吐这个结构。

---

## 二、Tagging：给文本打标签

### 环境准备

```python
import os, openai
from dotenv import load_dotenv, find_dotenv
_ = load_dotenv(find_dotenv())
openai.api_key = os.environ['OPENAI_API_KEY']

from typing import List
from pydantic import BaseModel, Field
from langchain.utils.openai_functions import convert_pydantic_to_openai_function
```

### 1) 用 Pydantic 描述标签结构

```python
class Tagging(BaseModel):
    """Tag the piece of text with particular info."""
    sentiment: str = Field(description="sentiment of text, should be `pos`, `neg`, or `neutral`")
    language: str = Field(description="language of text (should be ISO 639-1 code)")
```

- `Field.description` 里写清楚**取值范围**（`pos`/`neg`/`neutral`、ISO 639-1 代码）——模型据此决定如何填。

```python
convert_pydantic_to_openai_function(Tagging)
```

### 2) 构造 chain

```python
from langchain.prompts import ChatPromptTemplate
from langchain.chat_models import ChatOpenAI

model = ChatOpenAI(temperature=0)   # Tagging 应该确定性强，温度给 0

tagging_functions = [convert_pydantic_to_openai_function(Tagging)]

prompt = ChatPromptTemplate.from_messages([
    ("system", "Think carefully, and then tag the text as instructed"),
    ("user", "{input}"),
])

model_with_functions = model.bind(
    functions=tagging_functions,
    function_call={"name": "Tagging"},   # ← 强制调这个函数
)

tagging_chain = prompt | model_with_functions
```

### 3) 试跑

```python
tagging_chain.invoke({"input": "I love langchain"})
# → function_call: Tagging({"sentiment": "pos", "language": "en"})

tagging_chain.invoke({"input": "non mi piace questo cibo"})
# → function_call: Tagging({"sentiment": "neg", "language": "it"})
```

### 4) 用 Output Parser 把 arguments JSON 直接解析出来

目前返回的 AI message 里 `content=None`、`function_call` 是嵌套结构，下游用起来别扭。用内置解析器直接取 arguments：

```python
from langchain.output_parsers.openai_functions import JsonOutputFunctionsParser

tagging_chain = prompt | model_with_functions | JsonOutputFunctionsParser()

tagging_chain.invoke({"input": "non mi piace questo cibo"})
# → {"sentiment": "neg", "language": "it"}   ← 干净的 dict
```

---

## 三、Extraction：从文本抽取"实体列表"

### 1) 定义"一个实体"

```python
from typing import Optional

class Person(BaseModel):
    """Information about a person."""
    name: str = Field(description="person's name")
    age: Optional[int] = Field(description="person's age")
```

注意 `Optional[int]` —— 年龄**不一定**总能从文本里读出来。

### 2) 再包一层"信息容器"

因为 OpenAI function 期望一个"入口函数"，所以需要一个外壳让 `people` 是 list：

```python
class Information(BaseModel):
    """Information to extract."""
    people: List[Person] = Field(description="List of info about people")

convert_pydantic_to_openai_function(Information)
```

### 3) 初版 chain

```python
extraction_functions = [convert_pydantic_to_openai_function(Information)]

extraction_model = model.bind(
    functions=extraction_functions,
    function_call={"name": "Information"},
)

extraction_model.invoke("Joe is 30, his mom is Martha")
# → people=[{"name":"Joe","age":30}, {"name":"Martha","age":0}]   ← 编造了 age=0
```

### 4) 通过 prompt 明确指示"别瞎猜"

```python
prompt = ChatPromptTemplate.from_messages([
    ("system", "Extract the relevant information, if not explicitly provided do not guess. Extract partial info"),
    ("human", "{input}"),
])

extraction_chain = prompt | extraction_model
extraction_chain.invoke({"input": "Joe is 30, his mom is Martha"})
# → Martha 不再有 age 字段
```

### 5) 接上 JSON Parser

```python
extraction_chain = prompt | extraction_model | JsonOutputFunctionsParser()
extraction_chain.invoke({"input": "Joe is 30, his mom is Martha"})
# → {"people": [{"name": "Joe", "age": 30}, {"name": "Martha"}]}
```

### 6) 更进一步：用 `JsonKeyOutputFunctionsParser` 直接拎出 `people`

我们的 `Information` 只是壳，真正关心的是里面的 `people` 列表：

```python
from langchain.output_parsers.openai_functions import JsonKeyOutputFunctionsParser

extraction_chain = prompt | extraction_model | JsonKeyOutputFunctionsParser(key_name="people")

extraction_chain.invoke({"input": "Joe is 30, his mom is Martha"})
# → [{"name": "Joe", "age": 30}, {"name": "Martha"}]   ← 纯粹的 list
```

---

## 四、实战：在真实文章上做 Tagging + Extraction

### 1) 用 LangChain Document Loader 拉取博客

```python
from langchain.document_loaders import WebBaseLoader

loader = WebBaseLoader("https://lilianweng.github.io/posts/2023-06-23-agent/")
documents = loader.load()

doc = documents[0]
page_content = doc.page_content[:10000]   # 先只取前 10000 字符
print(page_content[:1000])
```

这是 Lilian Weng 关于 LLM Powered Autonomous Agents 的经典长文。

### 2) Tagging：抽文章总览

```python
class Overview(BaseModel):
    """Overview of a section of text."""
    summary: str = Field(description="Provide a concise summary of the content.")
    language: str = Field(description="Provide the language that the content is written in.")
    keywords: str = Field(description="Provide keywords related to the content.")

overview_tagging_function = [convert_pydantic_to_openai_function(Overview)]

tagging_model = model.bind(
    functions=overview_tagging_function,
    function_call={"name": "Overview"},
)
tagging_chain = prompt | tagging_model | JsonOutputFunctionsParser()

tagging_chain.invoke({"input": page_content})
# → {"summary": "...LLM powered autonomous agents...",
#    "language": "English",
#    "keywords": "LLM, autonomous agents, planning, memory, tool use, ..."}
```

### 3) Extraction：抽取"文章引用的论文列表"

```python
class Paper(BaseModel):
    """Information about papers mentioned."""
    title: str
    author: Optional[str]

class Info(BaseModel):
    """Information to extract"""
    papers: List[Paper]

paper_extraction_function = [convert_pydantic_to_openai_function(Info)]

extraction_model = model.bind(
    functions=paper_extraction_function,
    function_call={"name": "Info"},
)
extraction_chain = prompt | extraction_model | JsonKeyOutputFunctionsParser(key_name="papers")

extraction_chain.invoke({"input": page_content})
# → [{"title": "LLM powered autonomous agents", "author": "Lilian Weng"}]
#   ← 尴尬：把文章本身当成 paper 抽了出来！
```

### 4) 改进 prompt：**显式指令**

```python
template = """A article will be passed to you. Extract from it all papers that are mentioned by this article follow by its author.

Do not extract the name of the article itself. If no papers are mentioned that's fine - you don't need to extract any! Just return an empty list.

Do not make up or guess ANY extra information. Only extract what exactly is in the text."""

prompt = ChatPromptTemplate.from_messages([
    ("system", template),
    ("human", "{input}"),
])

extraction_chain = prompt | extraction_model | JsonKeyOutputFunctionsParser(key_name="papers")

extraction_chain.invoke({"input": page_content})
# → 返回文章引用的一组真实论文及作者（不再把文章本身当 paper）
```

### 5) Sanity check：无关输入应返回空列表

```python
extraction_chain.invoke({"input": "hi"})
# → []   （prompt 里就告诉它"没有就返回空 list"）
```

---

## 五、扩展到"全文"：分片 → 并行抽取 → 合并

前面只取了前 10000 字符。文章很长，**整篇塞不进 token 窗口**。解决方案：**分片 → map → flatten**。

### 1) 文本切分

```python
from langchain.text_splitter import RecursiveCharacterTextSplitter

text_splitter = RecursiveCharacterTextSplitter(chunk_overlap=0)
splits = text_splitter.split_text(doc.page_content)
len(splits)   # → 14
```

### 2) flatten 工具函数

```python
def flatten(matrix):
    flat_list = []
    for row in matrix:
        flat_list += row
    return flat_list

flatten([[1, 2], [3, 4]])   # → [1, 2, 3, 4]
```

### 3) 用 RunnableLambda 把 str 预处理成 `[{"input": chunk}, ...]`

```python
from langchain.schema.runnable import RunnableLambda

prep = RunnableLambda(
    lambda x: [{"input": doc} for doc in text_splitter.split_text(x)]
)

prep.invoke("hi")
# → [{"input": "hi"}]
```

因为它是**链条第一个**步骤，需要包成 RunnableLambda 让 LCEL 识别。

### 4) 组装完整 chain：**prep → extraction_chain.map() → flatten**

```python
chain = prep | extraction_chain.map() | flatten

chain.invoke(doc.page_content)
# → 全文所有论文的扁平列表
```

关键点：

- `.map()` 把 `extraction_chain` **对输入列表里每个元素分别调用一次**；
- LangChain **自动并行**（默认 5 路并发）；
- 每次调用返回一个 list → 整体是 list of lists → `flatten` 拍平。

---

## 六、小观察：长文抽取的有趣现象

最终列表里会看到类似 "Paper A, Author A" 这种占位样的条目。听起来像是模型在编，其实去看原文 Lilian Weng 那篇就会发现：**她在演示 prompting/citation 的例子里就用了 "Paper A / Author A" 这样的虚构引用**。

→ 模型把这些"虚构示例"也忠实抽出来了，**行为反而是正确的**。

> 提示：当做 QA 或 extraction 的材料本身就**谈论 prompt 或包含 prompt 示例**时，LLM 容易被"例子里的例子"干扰，要留心。

---

## 七、关键要点总结

1. **Tagging vs Extraction**：前者返回 1 个对象，后者返回对象列表；结构都用 Pydantic 声明。
2. **强制调用函数** + **force parse JSON** → 得到干净结构化输出的最短路径。
3. **两种 parser**：
   - `JsonOutputFunctionsParser` —— 解析为 dict；
   - `JsonKeyOutputFunctionsParser(key_name=...)` —— 直接拎出某个 key 的值。
4. **别让模型瞎编**：系统 prompt 明确告诉它"没找到就返回空"、"不要猜"。
5. **长文处理套路**：Splitter → RunnableLambda(预处理) → chain.map() → flatten。
6. **注意污染**：被抽取的文本本身包含 prompt 示例时，结果会被"例子里的例子"污染。

---

## 八、下一课预告

下一课会把 function calling 的第二大用途——**Tool Use**——讲透：

- 用 `@tool` 装饰器**一键把 Python 函数变成 LangChain Tool**；
- 把工具自动转为 OpenAI function 定义；
- 从 **OpenAPI spec**（如 Swagger 文档）一键生成工具；
- 用模型做 **Routing**（根据问题决定调哪个工具）。
