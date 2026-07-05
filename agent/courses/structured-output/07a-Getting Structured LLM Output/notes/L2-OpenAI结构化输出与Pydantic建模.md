# L2 用 OpenAI 结构化输出 + Pydantic 建一个社交媒体客服 Agent

## 核心工具:用 Pydantic 代替手写 JSON Schema

JSON Schema 本身冗长、手写易错。AI 工程里通常改用 Pydantic:继承 `BaseModel`,用类型注解描述字段,Pydantic 自动生成底层 schema。

```python
from pydantic import BaseModel
from typing import Optional

class User(BaseModel):
    name: str
    age: int
    email: Optional[str] = None   # 可为空
```

调用方式是 `client.beta.chat.completions.parse(..., response_format=User)`,拿到的 `completion.choices[0].message.parsed` 直接就是一个类型安全的 Python 对象:

```python
completion = client.beta.chat.completions.parse(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Make up a user."},
    ],
    response_format=User,
)
user = completion.choices[0].message.parsed   # -> User(name=..., age=..., email=...)
```

注意一个供应商差异:OpenAI 结构化输出**不支持约束字段格式**(比如强制邮箱匹配某个正则),这类更精细的约束要靠 Instructor(L3)或 Outlines(L4/L5)。

## 实战:社交媒体评论处理 Agent

定义一个 `Mention` 结构,关键在于**用 `Literal` 限定选项、用 `Optional` 表达"可能没有"**:

```python
from typing import Literal, Optional

class Mention(BaseModel):
    product: Literal['app', 'website', 'not_applicable']    # 只能三选一
    sentiment: Literal['positive', 'negative', 'neutral']
    needs_response: bool                                     # 是否需要回复
    response: Optional[str]                                  # 需要时才生成回复正文
    support_ticket_description: Optional[str]               # 有问题时才生成工单描述
```

三个设计要点:

1. **用 `Literal` 而不是裸 `str` 约束模型的选择范围**,防止模型编造出预期之外的分类值。
2. **给模型一个可调节的 `personality` 参数**——通过 system prompt 里插入不同人设(friendly / rude),同一套结构化字段能生成不同语气的回复。说明**结构化输出和内容风格是正交的两件事**。
3. **拿到的对象可以直接批量处理、转 dict、拼进 DataFrame**——这是"结构化输出让 LLM 输出变成可编程数据"的落地:不写任何解析逻辑,直接 Python 原生操作。

```python
import pandas as pd

rows = []
for mention in mentions:
    processed = analyze_mention(mention)      # 返回 Mention 对象
    d = processed.model_dump()                # Pydantic -> dict
    d['mention'] = mention
    rows.append(d)
df = pd.DataFrame(rows)                        # 直接成表,零解析代码
```

## 一个容易忽略但重要的点

即便用了结构化输出 API,底层传输的仍是一段 JSON 文本(`processed.model_dump_json(indent=2)` 可打印出原始文本),Pydantic 只是在这段文本和类型化对象之间做了一层自动转换。理解这点有助于排查"为什么结构化输出偶尔还是会报解析错误"。
