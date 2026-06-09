# 第 4 课：把 Pydantic 模型**直接传给 API** —— 结构化输出的优雅方案

> 课程：Pydantic for LLM Workflows · Lesson 4
> 原文件：
> - `subtitles/sc-Pydantic-C1-L4.vtt`
> - `code/lesson_4.md`

---

## 一、本课目标

> **抛弃上一课手搓的 retry 循环，直接把 Pydantic 模型作为"响应格式"传给 LLM API。**

### 🎯 核心发现

**无论用哪个 LLM 提供商、哪个 Agent 框架**，用 Pydantic 拿结构化输出的**写法几乎一致**——这是业界已经收敛的标准范式。

---

## 二、四种主流方案全景对比

| 方案 | 入口 | 后端实现 | 返回类型 |
|------|------|----------|----------|
| **① Instructor + Anthropic** | 第三方库包裹 | 自动 retry + validate | ✅ 直接返回 Pydantic 实例 |
| **② OpenAI Beta `chat.completions.parse`** | 原生 API | **Constrained Generation** | JSON 字符串，需手动 validate |
| **③ OpenAI `responses.parse`** | 原生 API（新版） | Constrained Generation + 自动校验 | ✅ 直接返回 Pydantic 实例 |
| **④ PydanticAI Agent** | Pydantic 官方 Agent 框架 | 统一封装多家 LLM | ✅ 直接返回 Pydantic 实例 |

---

## 三、环境准备（统一的起点）

```python
from pydantic import BaseModel, Field, EmailStr
from typing import List, Literal, Optional
from openai import OpenAI
import instructor
import anthropic
from dotenv import load_dotenv
from datetime import date
```

### 定义模型（沿用上一课）

```python
class UserInput(BaseModel):
    name: str
    email: EmailStr
    query: str
    order_id: Optional[int] = Field(None, description="...", ge=10000, le=99999)
    purchase_date: Optional[date] = None


class CustomerQuery(UserInput):
    priority: str = Field(..., description="Priority level: low, medium, high")
    category: Literal[
        'refund_request', 'information_request', 'other'
    ] = Field(..., description="Query category")
    is_complaint: bool = Field(..., description="Whether this is a complaint")
    tags: List[str] = Field(..., description="Relevant keyword tags")
```

### 构造 Prompt（极简版）

```python
user_input = UserInput.model_validate_json(user_input_json)

prompt = (
    f"Analyze the following customer query {user_input} "
    f"and provide a structured response."
)
```

> ⚠️ 注意这里的 prompt **完全没写"请返回 JSON"之类的话**——因为有 Pydantic 模型做背书，LLM API 会自己处理格式要求。

---

## 四、🅰 方案一：Instructor + Anthropic

### 4.1 原理

> **Instructor 是一个第三方库**，包装了几乎所有主流 LLM 提供商。它的内部实现**和上一课你手搓的几乎一样**：
>
> 1. 从 Pydantic 模型提取 JSON Schema
> 2. 构造 prompt 发给 LLM
> 3. 拿到响应后做 validate
> 4. 失败就自动 retry

### 4.2 代码

```python
load_dotenv()

anthropic_client = instructor.from_anthropic(anthropic.Anthropic())

response = anthropic_client.messages.create(
    model="claude-3-7-sonnet-latest",
    max_tokens=1024,
    messages=[{"role": "user", "content": prompt}],
    response_model=CustomerQuery,        # 🔑 直接传 Pydantic 类
)

print(type(response))                    # <class '__main__.CustomerQuery'> ✅
print(response.model_dump_json(indent=2))
```

### 🎯 拿到的就是 Pydantic 实例

不再需要做 `model_validate_json()`——**Instructor 已经帮你做完**。

### 4.3 优势

- ✅ **跨 LLM 厂商通用**（OpenAI / Anthropic / Gemini / 开源模型）
- ✅ 直接返回 Pydantic 实例
- ✅ 自动重试 + 校验

---

## 五、🅱 方案二：OpenAI `beta.chat.completions.parse`

### 5.1 原理：**Constrained Generation**（约束生成）

> **OpenAI 在 token 级别限制模型只能生成合法 JSON**——不是事后校验，而是**生成时就强制合规**。

这意味着：
- ✅ 永远不会有 "这是 JSON：{...}" 这种前后缀
- ✅ 永远不会有 Markdown 代码块包裹
- ✅ JSON 本身 100% 保证有效

### 5.2 代码

```python
openai_client = OpenAI()

response = openai_client.beta.chat.completions.parse(
    model="gpt-4o",
    messages=[{"role": "user", "content": prompt}],
    response_format=CustomerQuery,        # 🔑 Pydantic 类
)

response_content = response.choices[0].message.content
print(type(response_content))             # <class 'str'>
print(response_content)
```

### 5.3 ⚠️ 注意：这里拿到的是 JSON 字符串

```python
valid_data = CustomerQuery.model_validate_json(response_content)
# 手动再做一次 validate 才能变成 Pydantic 实例
```

> 🎯 **关键区分**：
> - **JSON 保证有效**（Constrained Generation 的成果）
> - **数据是否符合模型约束**（如 Literal 枚举值）→ 需要你自己 `model_validate_json`

---

## 六、🅲 方案三：OpenAI `responses.parse`（新版 API）

### 6.1 代码

```python
response = openai_client.responses.parse(
    model="gpt-4o",
    input=[{"role": "user", "content": prompt}],
    text_format=CustomerQuery,            # 🔑 注意参数名是 text_format
)

# 🎯 直接拿到 Pydantic 实例
print(response.output_parsed.model_dump_json(indent=2))
```

### 6.2 🧐 用 MRO 探索响应结构

```python
def print_class_inheritance(llm_response):
    for cls in type(llm_response).mro():
        print(f"{cls.__module__}.{cls.__name__}")

print_class_inheritance(response)
```

> 🐍 **`.mro()` = Method Resolution Order（方法解析顺序）** —— Python 里查看一个类的**继承链**。

**输出（部分）**：

```
openai.types.responses.response.Response
openai._models.BaseModel
pydantic.main.BaseModel           ← 🤯 OpenAI 自己的响应也是 Pydantic！
```

### 6.3 🤯 本课最重要的洞察

> **"It's Pydantic models all the way down."**
>
> **LLM 工作流里，Pydantic 模型无处不在**：
> - 你**发出去**的 Schema 是 Pydantic 模型
> - 你**拿回来**的响应**本身也是 Pydantic 模型**（OpenAI 内部也用它做校验）
> - 你的响应里**嵌套着**你自己的 Pydantic 模型

---

## 七、🅳 方案四：PydanticAI Agent 框架

### 7.1 PydanticAI 简介

> **由 Pydantic 官方团队出品的 Agent 框架**——切换 LLM 厂商**只需要改一个字符串**。

### 7.2 代码

```python
from pydantic_ai import Agent
import nest_asyncio
nest_asyncio.apply()                      # 让 async 能在 Jupyter 里跑

agent = Agent(
    model="google-gla:gemini-2.0-flash",
    output_type=CustomerQuery,            # 🔑 指定输出类型
)

response = agent.run_sync(prompt)

print(type(response.output))              # CustomerQuery ✅
print(response.output.model_dump_json(indent=2))
```

### 7.3 🪄 一行切换 LLM 厂商

```python
# Gemini
agent = Agent(model="google-gla:gemini-2.0-flash", output_type=CustomerQuery)

# OpenAI（只改模型字符串）
agent = Agent(model="openai:gpt-4o", output_type=CustomerQuery)

# Anthropic
agent = Agent(model="anthropic:claude-3-7-sonnet", output_type=CustomerQuery)
```

---

## 八、四种方案横向对比

| 维度 | Instructor | OpenAI `chat.parse` | OpenAI `responses.parse` | PydanticAI |
|------|-----------|----------------------|---------------------------|------------|
| **后端机制** | Retry + Validate | Constrained Gen | Constrained Gen + 自动校验 | 统一抽象 |
| **返回值** | Pydantic 实例 ✅ | JSON 字符串 ⚠️ | Pydantic 实例 ✅ | Pydantic 实例 ✅ |
| **跨 LLM** | ✅ 多厂商 | ❌ 仅 OpenAI | ❌ 仅 OpenAI | ✅ 多厂商 |
| **Agent 原生支持** | ❌ | ❌ | ❌ | ✅ |
| **手动再校验** | 不需要 | 需要 | 不需要 | 不需要 |

---

## 九、💡 深度洞察

### 9.1 两种底层实现的本质差异

| 机制 | 核心 | 可靠性 |
|------|------|--------|
| **自动 Retry 派**（Instructor、早期 OpenAI） | 生成后校验，失败重试 | 大多数时候能成功，但可能失败或变慢 |
| **Constrained Generation 派**（OpenAI 新版、vLLM、llama.cpp） | 生成时 token 级别约束只能输出合法 JSON | **结构上 100% 合规**，无需重试 |

### 9.2 "Pydantic 模型无处不在"的意义

> LLM 提供商自己就用 Pydantic 做响应校验——这反映了**整个生态都在围绕 Pydantic 构建数据契约**。

学会 Pydantic = 学会了 LLM 工作流的**通用语言**。

### 9.3 跨厂商切换几乎零成本

> 无论换成 OpenAI、Anthropic、Gemini、本地 Llama，用**同一个 Pydantic 模型**即可。

---

## 十、📝 速查表

### 10.1 四种方案的代码模板

```python
# ================ 方案 ①：Instructor ================
import instructor, anthropic
client = instructor.from_anthropic(anthropic.Anthropic())
response = client.messages.create(
    model="claude-3-7-sonnet-latest", max_tokens=1024,
    messages=[{"role": "user", "content": prompt}],
    response_model=MyModel,
)
# response 是 MyModel 实例


# ================ 方案 ②：OpenAI chat.completions.parse ================
from openai import OpenAI
client = OpenAI()
response = client.beta.chat.completions.parse(
    model="gpt-4o",
    messages=[{"role": "user", "content": prompt}],
    response_format=MyModel,
)
valid_data = MyModel.model_validate_json(response.choices[0].message.content)


# ================ 方案 ③：OpenAI responses.parse ================
response = client.responses.parse(
    model="gpt-4o",
    input=[{"role": "user", "content": prompt}],
    text_format=MyModel,
)
# response.output_parsed 是 MyModel 实例


# ================ 方案 ④：PydanticAI Agent ================
from pydantic_ai import Agent
agent = Agent(model="openai:gpt-4o", output_type=MyModel)
response = agent.run_sync(prompt)
# response.output 是 MyModel 实例
```

### 10.2 选型决策树

```
需要跨 LLM 厂商？
 ├── 是 → 需要 Agent 框架？
 │        ├── 是 → 🅳 PydanticAI
 │        └── 否 → 🅰 Instructor
 └── 否（仅 OpenAI）→ 用新版 API？
          ├── 是 → 🅲 responses.parse
          └── 否 → 🅱 chat.completions.parse
```

### 10.3 核心概念术语速查

| 术语 | 含义 |
|------|------|
| **Constrained Generation** | token 级别限制，生成时就保证 JSON 合规 |
| **Response Model / Output Type** | API 参数名，用于接收 Pydantic 类 |
| **`.mro()`** | Python 查看类继承链 |
| **`response.output_parsed`** | OpenAI 新 API 中拿到 Pydantic 实例的字段 |
| **`response.output`** | PydanticAI 中拿到 Pydantic 实例的字段 |

---

## 📎 补充阅读（2026 更新）

> ⚠️ 本课把 PydanticAI 当作"四个 Structured Output 方案之一"是**严重低估**了。
> 它实际上是一个**完整的 Agent 框架**，含 DI / Graph / Evals / Logfire 整套生态。
>
> 详见：[`sc-Pydantic-C1-补充-PydanticAI生态深度.md`](./sc-Pydantic-C1-补充-PydanticAI生态深度.md)

---

## 🎯 下一课预告

> **Lesson 5 · Tool Calling**
>
> Pydantic 在 LLM 工作流中的**第二大应用场景**——定义工具（Python 函数）的参数 Schema。
>
> 你会看到：**LLM 通过返回结构化的工具参数来调用你的函数**——这是 Agent 能做事情的根本机制。
