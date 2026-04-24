# Functions, Tools and Agents with LangChain — 第 02 课：OpenAI Function Calling 原理（中文整理）

> 来源：`subtitles/langchain_c3_02_en.vtt` + `code/L2-openai_functions_student.md`
> 本课目标：直接用 **OpenAI SDK**（不经过 LangChain）把 Function Calling 这件事讲透：参数怎么定义、返回什么、如何强制 / 禁止调用、怎么把函数结果回传给模型。

---

## 一、OpenAI 给最新模型新增的能力

OpenAI 在自家较新的模型（本课用 `gpt-3.5-turbo` 替代已弃用的 `gpt-3.5-turbo-0613`）上做了**微调**，让它们能：

- **接受一个新参数 `functions`**，里面放若干函数定义；
- **判断**：用户问题是否需要调用某个函数；
- 如果需要 → **返回 `function_call`**（函数名 + JSON 参数）；
- 否则 → 正常返回自然语言回答。

> 注意：**OpenAI 不会真的执行函数**，它只决定"调什么、传什么"。真正执行仍由你的代码完成。

---

## 二、环境准备

```python
import os
import openai

from dotenv import load_dotenv, find_dotenv
_ = load_dotenv(find_dotenv())   # 读取本地 .env
openai.api_key = os.environ['OPENAI_API_KEY']
```

---

## 三、定义一个"有用"的函数

本课用 OpenAI 官方示例 —— `get_current_weather`，因为**天气是 LLM 自己答不出的**（要连到外部 API）。

```python
import json

# 示例函数，生产中可以换成真实的天气 API
def get_current_weather(location, unit="fahrenheit"):
    """Get the current weather in a given location"""
    weather_info = {
        "location": location,
        "temperature": "72",
        "unit": unit,
        "forecast": ["sunny", "windy"],
    }
    return json.dumps(weather_info)
```

---

## 四、把函数**"描述"** 给模型

这是最关键的部分。函数描述是一个 JSON 列表，每个元素大致是：

```python
functions = [
    {
        "name": "get_current_weather",
        "description": "Get the current weather in a given location",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "The city and state, e.g. San Francisco, CA",
                },
                "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]},
            },
            "required": ["location"],
        },
    }
]
```

字段说明：

| 字段 | 作用 |
|------|------|
| `name` | 函数名（模型返回时也会用这个名字） |
| `description` | **非常重要** —— 模型靠这段文字判断什么情况下该调用这个函数 |
| `parameters.properties` | 每个参数的 `type` + `description`，也可用 `enum` 限定取值 |
| `parameters.required` | 哪些参数必填 |

> 核心心法：**这些描述本质就是 prompt**。你希望模型看到什么信息才好决策，就写在 `description` / `enum` / 参数描述里。

---

## 五、发起 Chat Completion 调用

```python
messages = [
    {"role": "user", "content": "What's the weather like in Boston?"}
]

response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=messages,
    functions=functions,
)

print(response)
```

返回的 message 大致是：

```python
{
    "role": "assistant",
    "content": None,                         # ← 关键：正常答案是 None
    "function_call": {
        "name": "get_current_weather",       # ← 模型决定调这个函数
        "arguments": '{"location": "Boston"}'  # ← JSON 字符串
    }
}
```

### 取出来用

```python
response_message = response["choices"][0]["message"]
response_message["content"]         # None
response_message["function_call"]   # dict: name + arguments(str)

# arguments 是 JSON 字符串，需要解析
args = json.loads(response_message["function_call"]["arguments"])
get_current_weather(args)           # ← 真正由你来调
```

---

## 六、当问题和函数无关时会怎样

```python
messages = [{"role": "user", "content": "hi!"}]

response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=messages,
    functions=functions,
)
```

返回正常的 content（如 *"Hello! How can I assist you today?"*），**没有 `function_call` 字段**。

→ 模型**自己判断**当下不需要调函数。

---

## 七、`function_call` 参数：控制"调 / 不调"

| 取值 | 行为 |
|------|------|
| `"auto"` | **默认**，模型自主决定 |
| `"none"` | **强制不调用** 任何函数 |
| `{"name": "..."}` | **强制调用** 指定函数 |

### 示例：禁止调用

```python
response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[{"role": "user", "content": "What's the weather in Boston?"}],
    functions=functions,
    function_call="none",
)
```

即便问的是天气，也不会触发函数 —— 模型只能用内部知识回答。

### 示例：强制调用

```python
response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[{"role": "user", "content": "hi!"}],
    functions=functions,
    function_call={"name": "get_current_weather"},
)
```

注意：强制调用时如果用户输入根本没提地点，模型会**自己编一个**（比如 "San Francisco, California"）—— 这是强制模式的副作用。

---

## 八、把函数执行结果回传给模型（完整闭环）

典型工作流：**模型选函数 → 你执行 → 把结果再喂回去 → 模型给出自然语言答案**。

### 1) 用户提问，模型返回 `function_call`

```python
messages = [{"role": "user", "content": "What's the weather like in Boston!"}]

response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=messages,
    functions=functions,
    function_call={"name": "get_current_weather"},
)
```

### 2) 把模型的回复追加到 messages

```python
messages.append(response["choices"][0]["message"])
```

### 3) 自己执行函数

```python
args = json.loads(response["choices"][0]["message"]['function_call']['arguments'])
observation = get_current_weather(args)
```

### 4) 用 `role="function"` 的新消息把结果告诉模型

```python
messages.append({
    "role": "function",                    # ← 关键
    "name": "get_current_weather",         # 对应函数名
    "content": observation,                # 函数返回的字符串
})
```

### 5) 再次请求模型 → 得到自然语言答复

```python
response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=messages,
)
print(response)
# → "The current weather in Boston is 72°F with a sunny and windy forecast."
```

> 这个"**函数选择 → 执行 → 观察 → 再次询问**"的循环，就是后面 Agent 的雏形。

---

## 九、几个值得记住的小细节

1. **返回的 `arguments` 是 JSON 字符串**，必须 `json.loads` 才能当 dict 用。
2. **虽然训练过要输出 JSON，但并非强保证**，极少数情况下可能非合法 JSON，需要自己做兜底 / 重试。
3. **函数定义也算 token**：`functions` + `function_call` 会把 prompt tokens 推上去。课里演示：注释掉 functions 后 prompt tokens 从数十 → **15**。注意 token 上限！
4. **描述文字质量 ≈ 成功率**：函数描述写得越清晰，模型选函数越准。

---

## 十、本课小结

- 你已掌握**直接用 OpenAI SDK** 使用 Function Calling 的全部基本机制；
- 核心三件事：**定义 functions → 解析 `function_call` → 用 `role="function"` 回传结果**；
- 三种 `function_call` 取值：`auto / none / {"name": ...}`；
- 这是后续一切 LangChain tool / agent 的底层机制。

## 十一、下一课预告

下一课不再直接用 OpenAI SDK，而是引入 **LangChain Expression Language（LCEL）** —— 用管道式语法 (`prompt | model | output_parser`) 把组件串起来，让这套流程更干净、更可组合。
