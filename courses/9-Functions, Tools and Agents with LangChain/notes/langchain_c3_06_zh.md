# Functions, Tools and Agents with LangChain — 第 06 课：Tools、OpenAPI 与 Routing（中文整理）

> 来源：`subtitles/langchain_c3_06_en.vtt` + `code/L6-tools-routing-apis-student.md`
> 本课目标：掌握 **Tool 抽象**（`@tool` 装饰器）、从 **OpenAPI spec** 批量生成工具、以及用模型 + Output Parser 实现**Routing（在多个工具间自动路由）**。

---

## 一、Tool 是什么

让 LLM "用函数" 实际上包含两件事：

1. **选** —— 模型决定调哪个函数、传什么参数；
2. **做** —— 有人真的去执行那个函数。

**LangChain Tool** 就是这两件事的统一抽象：
- 一个函数 + 一段描述 + 一个 args schema；
- 可以**自动**转成 OpenAI function 定义；
- 可以**直接 run** 执行。

LangChain 自带不少 Tool（搜索、数学、SQL 等），**但实战中 90% 的 tool 都是你自己写的**，因为业务场景太特化。所以本课重点是"怎么方便地造工具"。

---

## 二、`@tool` 装饰器：一行变工具

### 最简例子

```python
from langchain.agents import tool

@tool
def search(query: str) -> str:
    """Search for weather online"""
    return "42f"
```

**自动完成**：

```python
search.name         # 'search'
search.description  # 'search(query: str) -> str - Search for weather online'
search.args         # {'query': {'title': 'Query', 'type': 'string'}}
```

docstring 变成工具描述，参数类型注解变成 schema。

### 用 Pydantic 给参数更清晰的描述

```python
from pydantic import BaseModel, Field

class SearchInput(BaseModel):
    query: str = Field(description="Thing to search for")

@tool(args_schema=SearchInput)
def search(query: str) -> str:
    """Search for the weather online."""
    return "42f"

search.args
# {'query': {'title': 'Query', 'description': 'Thing to search for', 'type': 'string'}}
```

> **Field 描述 ≈ prompt**。这段文字直接影响模型能不能**正确**填参数。

### 工具能直接 `run`

```python
search.run("sf")   # → '42f'
```

---

## 三、造一个真工具：`get_current_temperature`（用 Open-Meteo API）

### 输入 schema

```python
import requests, datetime
from pydantic import BaseModel, Field

class OpenMeteoInput(BaseModel):
    latitude: float = Field(..., description="Latitude of the location to fetch weather data for")
    longitude: float = Field(..., description="Longitude of the location to fetch weather data for")
```

### 工具函数

```python
@tool(args_schema=OpenMeteoInput)
def get_current_temperature(latitude: float, longitude: float) -> dict:
    """Fetch current temperature for given coordinates."""

    BASE_URL = "https://api.open-meteo.com/v1/forecast"
    params = {
        'latitude': latitude,
        'longitude': longitude,
        'hourly': 'temperature_2m',
        'forecast_days': 1,
    }

    response = requests.get(BASE_URL, params=params)
    if response.status_code == 200:
        results = response.json()
    else:
        raise Exception(f"API Request failed with status code: {response.status_code}")

    current_utc_time = datetime.datetime.utcnow()
    time_list = [datetime.datetime.fromisoformat(t.replace('Z', '+00:00'))
                 for t in results['hourly']['time']]
    temperature_list = results['hourly']['temperature_2m']

    closest_time_index = min(range(len(time_list)), key=lambda i: abs(time_list[i] - current_utc_time))
    current_temperature = temperature_list[closest_time_index]

    return f'The current temperature is {current_temperature}°C'
```

### 转成 OpenAI function 定义

```python
from langchain.tools.render import format_tool_to_openai_function

format_tool_to_openai_function(get_current_temperature)
# → {'name': 'get_current_temperature', 'description': '...', 'parameters': {...}}
```

**一键**转换。后面把这个直接丢给 `model.bind(functions=[...])` 就行。

### 直接跑一下（会真的打 API）

```python
get_current_temperature({"latitude": 13, "longitude": 14})
# → 'The current temperature is 22.9°C'
```

---

## 四、再造一个：`search_wikipedia`

```python
import wikipedia

@tool
def search_wikipedia(query: str) -> str:
    """Run Wikipedia search and get page summaries."""
    page_titles = wikipedia.search(query)
    summaries = []
    for page_title in page_titles[:3]:
        try:
            wiki_page = wikipedia.page(title=page_title, auto_suggest=False)
            summaries.append(f"Page: {page_title}\nSummary: {wiki_page.summary}")
        except (
            self.wiki_client.exceptions.PageError,
            self.wiki_client.exceptions.DisambiguationError,
        ):
            pass
    if not summaries:
        return "No good Wikipedia Search Result was found"
    return "\n\n".join(summaries)
```

```python
search_wikipedia({"query": "langchain"})
# → 三条 Wikipedia 页面摘要
```

---

## 五、从 OpenAPI Spec 批量生成工具

很多业务功能都在 API 后面，这些 API 一般有 **OpenAPI（Swagger）规范**。LangChain 能把一份 spec 自动转成多个 OpenAI function。

```python
from langchain.chains.openai_functions.openapi import openapi_spec_to_openai_fn
from langchain.utilities.openapi import OpenAPISpec

text = """
{
  "openapi": "3.0.0",
  "info": {"version": "1.0.0", "title": "Swagger Petstore", ...},
  "paths": {
    "/pets": {
      "get":  {"summary": "List all pets",  "operationId": "listPets",  ...},
      "post": {"summary": "Create a pet",   "operationId": "createPets", ...}
    },
    "/pets/{petId}": {
      "get":  {"summary": "Info for a specific pet", "operationId": "showPetById", ...}
    }
  },
  ...
}
"""

spec = OpenAPISpec.from_text(text)
pet_openai_functions, pet_callables = openapi_spec_to_openai_fn(spec)

pet_openai_functions   # ← 3 个函数定义：listPets / createPets / showPetById
```

返回两样东西：

- **function 定义**：直接给 OpenAI；
- **callables**：LangChain 生成的本地调用器（真实 spec 的话能直接打 API）。

### 让模型路由

```python
from langchain.chat_models import ChatOpenAI

model = ChatOpenAI(temperature=0).bind(functions=pet_openai_functions)

model.invoke("what are three pets names")
# → function_call: listPets(limit=3)

model.invoke("tell me about pet with id 42")
# → function_call: showPetById(petId="42")
```

> 一个 OpenAPI spec → 一组可被 LLM 路由调用的工具。后端 API 一下子全"可被 LLM 调用"。

---

## 六、Routing：让模型在自定义工具间选择并执行

### 1) 把两个工具格式化为 functions

```python
functions = [
    format_tool_to_openai_function(f) for f in [search_wikipedia, get_current_temperature]
]
model = ChatOpenAI(temperature=0).bind(functions=functions)
```

### 2) 直接问

```python
model.invoke("what is the weather in sf right now")
# → function_call: get_current_temperature(latitude=..., longitude=...)

model.invoke("what is langchain")
# → function_call: search_wikipedia(query="langchain")
```

### 3) 接上 prompt

```python
from langchain.prompts import ChatPromptTemplate

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are helpful but sassy assistant"),
    ("user", "{input}"),
])

chain = prompt | model
chain.invoke({"input": "what is the weather in sf right now"})
```

问题是：返回的 AIMessage 还是**嵌套的 function_call dict**，下游不好处理。

### 4) 用 `OpenAIFunctionsAgentOutputParser` 解析

```python
from langchain.agents.output_parsers import OpenAIFunctionsAgentOutputParser

chain = prompt | model | OpenAIFunctionsAgentOutputParser()
result = chain.invoke({"input": "what is the weather in sf right now"})
```

解析出来的是两类对象之一：

- **`AgentAction`**：模型决定调工具；含 `.tool`（工具名）和 `.tool_input`（**已解析为 dict**）
- **`AgentFinish`**：模型决定直接回答；`.return_values["output"]` 是最终文本

```python
type(result)         # AgentAction
result.tool          # 'get_current_temperature'
result.tool_input    # {'latitude': 37.7749, 'longitude': -122.4194}

# 直接塞进对应的工具
get_current_temperature(result.tool_input)
# → 'The current temperature is ... °C'
```

```python
result = chain.invoke({"input": "hi!"})
type(result)             # AgentFinish
result.return_values     # {'output': 'Hello! How can I assist you today?'}
```

### 5) 写一个 route 函数把"选"和"做"串起来

```python
from langchain.schema.agent import AgentFinish

def route(result):
    if isinstance(result, AgentFinish):
        return result.return_values['output']
    else:
        tools = {
            "search_wikipedia": search_wikipedia,
            "get_current_temperature": get_current_temperature,
        }
        return tools[result.tool].run(result.tool_input)

chain = prompt | model | OpenAIFunctionsAgentOutputParser() | route
```

### 6) 效果

```python
chain.invoke({"input": "What is the weather in san francisco right now?"})
# → "The current temperature is 22.9°C"

chain.invoke({"input": "What is langchain?"})
# → 来自 Wikipedia 的摘要

chain.invoke({"input": "hi!"})
# → "Hello! How can I assist you today?"
```

**单步 tool-call 的完整链**已经成型。

---

## 七、关键要点总结

1. **`@tool` 装饰器**把任意 Python 函数秒变 LangChain Tool，docstring = 描述，参数注解/Pydantic = args schema。
2. **`format_tool_to_openai_function`** 把 Tool 转成 OpenAI 需要的 JSON。
3. **OpenAPI Spec** 可以一次性导入一大批 API 工具（对接老系统神器）。
4. **`OpenAIFunctionsAgentOutputParser`** 把 AIMessage 结构化成 `AgentAction | AgentFinish` 两种明确语义。
5. **Routing = 选 + 做**：链式 `prompt | model | output_parser | route` 就够。

---

## 八、下一课预告

目前的 chain **只做一步 tool-call**。真实 Agent 需要能：

- 看到 tool 的 observation 后**继续推理**；
- 必要时**再调下一个 tool**；
- 直到模型说"我够了"（AgentFinish）才结束。

下一课会把这个**循环**补上，并加上**memory**，组装成一个接近 ChatGPT 体验的会话 Agent。
