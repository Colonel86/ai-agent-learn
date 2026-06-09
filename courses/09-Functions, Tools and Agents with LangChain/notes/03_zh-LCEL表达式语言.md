# Functions, Tools and Agents with LangChain — 第 03 课：LangChain Expression Language（LCEL）（中文整理）

> 来源：`subtitles/langchain_c3_03_en.vtt` + `code/L3-lcel-student.md`
> 本课目标：掌握 **LCEL（LangChain Expression Language）** —— 用 `|` 管道符把组件拼成 chain，享受 **async、batch、streaming、并行、fallback、日志**等开箱即用的特性。

---

## 一、LCEL 是什么，为什么用它

LangChain 的威力来自**组件组合**。LCEL 是一种**新的组合语法 + Runnable 协议**，它定义了：

1. **允许的输入类型** —— 每种组件可以接收什么；
2. **一组标准方法** —— 所有"Runnable"都有同样的接口；
3. **修改运行时参数的方式** —— 比如 `bind(...)` 绑定函数；
4. **统一 schema** —— 每个 Runnable 都有 `input_schema` 和 `output_schema`。

### 所有 Runnable 都有的标准方法

| 方法 | 说明 |
|------|------|
| `invoke` | 单个输入，同步执行 |
| `stream` | 单个输入，流式返回 |
| `batch` | 输入列表，并行执行 |
| `ainvoke` / `astream` / `abatch` | 以上 3 个的 async 版本 |

### 为什么用 LCEL

1. **开箱即用**的 async / batch / streaming 支持；
2. **Fallback 简单**：不仅可以给单个 LLM 加 fallback，也可以给**整条 chain** 加；
3. **并行执行**：LCEL 能自动并行 batch 里的调用；
4. **天然日志**：复杂的 chain/agent 里每一步的 input/output 都会被记录。

---

## 二、最小例子：一条三段 chain

### 导入

```python
from langchain.prompts import ChatPromptTemplate
from langchain.chat_models import ChatOpenAI
from langchain.schema.output_parser import StrOutputParser
```

### 三个组件

```python
prompt = ChatPromptTemplate.from_template(
    "tell me a short joke about {topic}"
)
model = ChatOpenAI()
output_parser = StrOutputParser()
```

### 用 `|` 拼起来

```python
chain = prompt | model | output_parser
```

### 调用

```python
chain.invoke({"topic": "bears"})
# → "Why don't bears ever get caught in traffic?
#    Because they always take the beariest best routes."
```

**解读**：`{"topic": "bears"}` → prompt 填充 → 发给 model → 拿到 ChatMessage → output_parser 转成字符串。

---

## 三、RunnableMap：把多路数据并行送给下一个环节

### 场景：RAG 风格的"先检索再回答"

```python
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import DocArrayInMemorySearch

vectorstore = DocArrayInMemorySearch.from_texts(
    ["harrison worked at kensho", "bears like to eat honey"],
    embedding=OpenAIEmbeddings(),
)
retriever = vectorstore.as_retriever()
```

### prompt 需要两个变量

```python
template = """Answer the question based only on the following context:
{context}

Question: {question}
"""
prompt = ChatPromptTemplate.from_template(template)
```

我们希望：**用户只给 `question`**，自动补齐 `context`。

### 用 `RunnableMap` 构造多路输入

```python
from langchain.schema.runnable import RunnableMap

chain = RunnableMap({
    "context": lambda x: retriever.get_relevant_documents(x["question"]),
    "question": lambda x: x["question"],
}) | prompt | model | output_parser

chain.invoke({"question": "where did harrison work?"})
# → "Harrison worked at Kensho."
```

**机制**：RunnableMap 接到 `{"question": ...}` 后，**并行**执行两个 lambda，产出 `{"context": ..., "question": ...}` 再喂给 prompt。

### 单独观察 RunnableMap

```python
inputs = RunnableMap({
    "context": lambda x: retriever.get_relevant_documents(x["question"]),
    "question": lambda x: x["question"]
})

inputs.invoke({"question": "where did harrison work?"})
# → {"context": [Document(...), ...], "question": "where did harrison work?"}
```

---

## 四、`bind`：把 OpenAI Functions 绑到模型上

`.bind(...)` 把参数**"附着"** 在 Runnable 上，调用时自动带上，不用每次传。

### 单函数

```python
functions = [
    {
        "name": "weather_search",
        "description": "Search for weather given an airport code",
        "parameters": {
            "type": "object",
            "properties": {
                "airport_code": {
                    "type": "string",
                    "description": "The airport code to get the weather for",
                },
            },
            "required": ["airport_code"],
        },
    }
]

prompt = ChatPromptTemplate.from_messages([("human", "{input}")])
model = ChatOpenAI(temperature=0).bind(functions=functions)   # ← 绑定

runnable = prompt | model
runnable.invoke({"input": "what is the weather in sf"})
```

### 多函数：让模型自己挑

```python
functions = [
    {"name": "weather_search", "description": "...", "parameters": {...}},
    {"name": "sports_search",  "description": "...", "parameters": {...}},
]

model = model.bind(functions=functions)      # 重新绑定覆盖旧的
runnable = prompt | model

runnable.invoke({"input": "how did the patriots do yesterday?"})
# → 模型选 sports_search
```

---

## 五、Fallbacks：整条 chain 级别的容错

### 场景：旧模型不总能输出合法 JSON

```python
from langchain.llms import OpenAI
import json

simple_model = OpenAI(
    temperature=0,
    max_tokens=1000,
    model="gpt-3.5-turbo-instruct",    # 较老/相对弱的补全模型
)
simple_chain = simple_model | json.loads  # ← 解析失败就会报错
```

### 故意给一个困难任务

```python
challenge = "write three poems in a json blob, where each poem is a json blob of a title, author, and first line"

simple_chain.invoke(challenge)
# → JSONDecodeError（非法 JSON）
```

### 用 Chat 模型做同样任务

```python
from langchain.schema.output_parser import StrOutputParser

model = ChatOpenAI(temperature=0)
chain = model | StrOutputParser() | json.loads

chain.invoke(challenge)
# → 正常返回 dict
```

### 加 fallback：主链失败就走备链

```python
final_chain = simple_chain.with_fallbacks([chain])

final_chain.invoke(challenge)
# → 主链失败 → 自动切换到备链 → 成功返回
```

`with_fallbacks([...])` 接受一个**按顺序**尝试的 Runnable 列表。

---

## 六、Runnable 的标准接口一览

回到最开始的那条 chain：

```python
prompt = ChatPromptTemplate.from_template("Tell me a short joke about {topic}")
model = ChatOpenAI()
output_parser = StrOutputParser()
chain = prompt | model | output_parser
```

### `invoke` —— 单输入同步

```python
chain.invoke({"topic": "bears"})
```

### `batch` —— 列表并行

```python
chain.batch([{"topic": "bears"}, {"topic": "frogs"}])
# 内部会尽量并行执行
```

### `stream` —— 流式输出

```python
for t in chain.stream({"topic": "bears"}):
    print(t)
```

### `ainvoke` —— 异步

```python
response = await chain.ainvoke({"topic": "bears"})
```

批量 / 流式 / 异步，**一切组件共享同一套接口**。

---

## 七、关键要点总结

1. **LCEL 的精髓是 `|`**：把组件当作管道节点，输入输出类型自动接上。
2. **RunnableMap**：并行构建多路输入，典型用来拼 prompt 模板需要的多个变量。
3. **`.bind(...)`**：把诸如 `functions=`、`stop=` 等参数"黏"到模型上。
4. **`.with_fallbacks([...])`**：把容错从单个组件抬升到整条链。
5. **统一接口 invoke / batch / stream + async**：一次写成，多种调用方式都能用。
6. LangChain 实战里会见到**几百个组件串起来**的 chain，LCEL 让这件事变得可控。

---

## 八、下一课预告

下一课会把 **LCEL 和 OpenAI Functions** 结合起来，并引入 **Pydantic** —— 用 Python 类声明 function schema，彻底摆脱手写那个难读的 JSON blob。
