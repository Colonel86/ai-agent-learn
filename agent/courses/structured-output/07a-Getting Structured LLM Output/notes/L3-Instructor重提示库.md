# L3 Instructor:跨供应商的重提示(re-prompting)方案

## 工作原理

Instructor 的核心逻辑:调用模型 → 校验返回内容是否匹配目标 Pydantic 结构 → 若不匹配,把错误信息连同原输出附回 prompt,重新请求 → 直到拿到合法结构,或达到最大重试次数后放弃。

用法上和 OpenAI 原生几乎一样,只是把客户端包一层,参数从 `response_format=` 换成 `response_model=`:

```python
import instructor
from openai import OpenAI

# 大多数推理服务商(Together / Fireworks 等)都兼容 OpenAI SDK,只需换 base_url + key
together_client = OpenAI(base_url="https://api.together.xyz/v1", api_key=...)
instructor_client = instructor.from_openai(together_client)

class Greeting(BaseModel):
    hello: str

resp = instructor_client.chat.completions.create(
    model="meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
    messages=[{"role": "user", "content": "sup"}],
    response_model=Greeting,     # 注意:OpenAI 用 response_format,Instructor 用 response_model
)
```

因为大多数服务商都兼容 OpenAI 接口规范,换供应商本质只是换 base_url 和 key,业务代码基本不动——这是 Instructor 相对供应商原生方案最大的优势:**代码可移植,不锁定单一供应商**。

## 相比 OpenAI 原生,支持更丰富的类型

课程用一个日历事件抽取的例子,字段里直接用了 Python 标准库的 `date` 类型和带正则约束的 `Field`:

```python
from pydantic import Field
from datetime import date
from typing import List

class CalendarEvent(BaseModel):
    name: str
    date: date                                   # OpenAI 原生不支持,会要求退化成 str
    participants: List[Person]
    state_code: str = Field(pattern=r'[A-Z]{2}') # 强制两位大写字母
    zip_code:   str = Field(pattern=r'\d{5}')    # 强制五位数字
```

这些 OpenAI 原生结构化输出目前不支持,但 Instructor 走的是"重提示+校验"路线,校验在 Pydantic 层,天然支持 Pydantic 全部能力。(有趣的副作用:模型还能根据地址推断出 prompt 里没给的邮编。)

## 代价:失败重试是真实成本

课程给了一个刻意"使坏"的例子——故意不告诉模型目标结构、还在 system prompt 里让它"别按我要的来",结果三次重试全部失败,token 消耗是原来的三倍(每次重试都要把完整 prompt 再发一遍)。可以用 hook 追踪重试次数和 token:

```python
instructor_client.on("completion:response", log_completion_kwargs)  # 每次返回都记账
# 失败时抛 instructor.exceptions.InstructorRetryException
```

结论:
- **Instructor 不保证成功**——复杂 schema + 模糊 prompt,可能永远凑不出合法输出。
- **重试是线性叠加成本**:每多一次重试,输入 token 就多算一遍,对长 prompt / 高频调用会被放大。
- **实践含义**:用 Instructor 时,即便 Pydantic 已定义结构,也应在 prompt 里尽量清楚地描述期望结构,减少重试。

## 选型判断(这一课的核心价值)

**对延迟/成本敏感、且能拿到 logits(自托管开源模型)→ 约束解码(L4 Outlines)更优;只能通过 API 调闭源模型、又要跨供应商可移植 → Instructor 这类重提示库是当前最实用的方案。**
