# Functions, Tools and Agents with LangChain — 第 04 课：OpenAI Functions + LangChain + Pydantic（中文整理）

> 来源：`subtitles/langchain_c3_04_en.vtt` + `code/L4-function-calling-student.md`
> 本课目标：用 **Pydantic** 代替手写 JSON schema 来声明 OpenAI Function，并把它和 **LCEL** 整合起来。

---

## 一、为什么要用 Pydantic

回忆 L2：OpenAI function 的定义是**一大坨嵌套 JSON**（name / description / parameters.properties / required …），手写容易出错且难维护。

**Pydantic** 是 Python 的数据校验库：

- 用类似 Python 类的语法**声明数据结构**；
- 自动**类型校验**（传错类型直接报错）；
- 可以**导出为 JSON Schema** —— 恰好就是 OpenAI function 想要的格式。

> 本课的 Pydantic 类**不是用来实例化干活的**，只是为了"顺便"生成那段 function JSON。

---

## 二、Pydantic 快速入门

### 导入

```python
from typing import List
from pydantic import BaseModel, Field
```

### 和原生 Python class 对比

```python
# 原生 Python 类
class User:
    def __init__(self, name: str, age: int, email: str):
        self.name = name
        self.age = age
        self.email = email
```

原生类的问题：**类型注解只是装饰**，实际运行时传错类型也不会报错。

```python
foo = User(name="Joe", age="bar", email="joe@gmail.com")  # "bar" 不是 int
foo.age   # 仍然被接受
```

### 换成 Pydantic

```python
class pUser(BaseModel):
    name: str
    age: int
    email: str

foo_p = pUser(name="Jane", age=32, email="jane@gmail.com")   # OK

pUser(name="Jane", age="bar", email="jane@gmail.com")        # ← 抛 ValidationError
```

不仅校验 + 打印也更友好，print 出来一目了然。

### 可嵌套

```python
class Class(BaseModel):
    students: List[pUser]

obj = Class(
    students=[pUser(name="Jane", age=32, email="jane@gmail.com")]
)
```

---

## 三、Pydantic 类 → OpenAI Function 定义

### 定义 Pydantic 类 + docstring + Field 描述

```python
class WeatherSearch(BaseModel):
    """Call this with an airport code to get the weather at that airport"""
    airport_code: str = Field(description="airport code to get weather for")
```

- `class` 名 → OpenAI function 的 **name**；
- `"""..."""` docstring → **description**（**强制要求**，后面会说明为什么）；
- 字段类型注解 → parameters 的 type；
- `Field(description=...)` → 参数的 description。

### 一行转换

```python
from langchain.utils.openai_functions import convert_pydantic_to_openai_function

weather_function = convert_pydantic_to_openai_function(WeatherSearch)
weather_function
```

输出就是 L2 里那段 JSON（name / description / parameters.properties / required）。

### 没写 docstring 会怎样？

```python
class WeatherSearch1(BaseModel):
    airport_code: str = Field(description="airport code to get weather for")

convert_pydantic_to_openai_function(WeatherSearch1)
# → 抛错：缺少 description
```

**LangChain 强制你写 docstring**，因为"**function 描述本质上就是 prompt**"，没有描述模型就无法做选择。

### 参数描述是可选的

```python
class WeatherSearch2(BaseModel):
    """Call this with an airport code to get the weather at that airport"""
    airport_code: str     # ← 没写 Field(description=...)

convert_pydantic_to_openai_function(WeatherSearch2)   # ← 允许
```

类级别 docstring 必填，**字段级别描述可选**。

---

## 四、把 function 挂到模型上：三种姿势

### 姿势 1：调用时临时传

```python
from langchain.chat_models import ChatOpenAI

model = ChatOpenAI()
model.invoke("what is the weather in SF today?", functions=[weather_function])
```

返回的 AIMessage 里：
- `content` 为 None；
- `additional_kwargs.function_call` 为 `{"name": "WeatherSearch", "arguments": "{...SFO...}"}`。

### 姿势 2：`.bind()` 绑住（推荐）

```python
model_with_function = model.bind(functions=[weather_function])
model_with_function.invoke("what is the weather in sf?")
```

好处：**把"带了这堆函数的模型"当成一个对象到处传**，调用方就不必每次都记得传 `functions=`。

### 姿势 3：强制调用指定函数

```python
model_with_forced_function = model.bind(
    functions=[weather_function],
    function_call={"name": "WeatherSearch"},    # ← 强制
)

model_with_forced_function.invoke("what is the weather in sf?")   # 会调
model_with_forced_function.invoke("hi!")                           # 仍然会调（强制）
```

---

## 五、把绑好函数的模型接进 LCEL chain

```python
from langchain.prompts import ChatPromptTemplate

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant"),
    ("user", "{input}"),
])

chain = prompt | model_with_function
chain.invoke({"input": "what is the weather in sf?"})
```

**它和普通 model 用法完全一样**，这就是 LCEL 的均匀接口的好处。

---

## 六、多函数场景：让模型自己挑

### 再定义一个 Pydantic 类

```python
class ArtistSearch(BaseModel):
    """Call this to get the names of songs by a particular artist"""
    artist_name: str = Field(description="name of artist to look up")
    n: int = Field(description="number of results")
```

### 一次性注册多个函数

```python
functions = [
    convert_pydantic_to_openai_function(WeatherSearch),
    convert_pydantic_to_openai_function(ArtistSearch),
]

model_with_functions = model.bind(functions=functions)
```

### 观察模型自行路由

```python
model_with_functions.invoke("what is the weather in sf?")
# → function_call: WeatherSearch

model_with_functions.invoke("what are three songs by taylor swift?")
# → function_call: ArtistSearch, args {artist_name: "Taylor Swift", n: 3}

model_with_functions.invoke("hi!")
# → 普通回答，没有 function_call
```

**这就是"tool selection"的雏形**。后面 L6 / L7 会把它扩展成完整的 Agent loop。

---

## 七、关键要点总结

1. **Pydantic 是 OpenAI function 的事实声明方式**：简洁、类型安全、可演化。
2. **docstring 必填**：LangChain 用它填充 function description，不写会被阻断。
3. **`convert_pydantic_to_openai_function`** 是两个世界的桥。
4. **三种使用姿势**：直接传 / `.bind()` / `.bind(function_call={"name":...})` 强制。
5. **多函数场景下模型自主选函数**，已经接近 Agent 的路由逻辑。
6. LCEL 对这一切**保持接口一致**：绑好函数的模型仍然可以写成 `prompt | model`。

---

## 八、下一课预告

接下来会把这套机制用到两类**最实用**的场景：

- **Tagging** —— 用 function calling 给一段文字打结构化标签（sentiment、language…）；
- **Extraction** —— 从一段文字中抽取**结构化实体列表**（比如文章里提到的所有论文）。
