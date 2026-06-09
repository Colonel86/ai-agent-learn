# 第 2 课：Pydantic 基础 —— 用户输入验证

> 课程：Pydantic for LLM Workflows · Lesson 2
> 原文件：
> - `subtitles/sc-Pydantic-C1-L2.vtt`
> - `code/lesson_2.md`

---

## 一、本课目标

> **通过给客户支持系统做"用户输入验证"，掌握 Pydantic 数据模型的所有基础机制。**

### 学完你能：
- ✅ 定义 Pydantic 模型来验证用户输入
- ✅ 用 try/except 捕获 `ValidationError` 优雅报错
- ✅ 使用**可选字段**和**字段约束**
- ✅ 用 JSON 数据验证的两种方式（两步 vs 一步）

---

## 二、起步：定义第一个 Pydantic 模型

### 2.1 核心导入

```python
from pydantic import BaseModel, ValidationError, EmailStr
import json
```

| 导入项 | 作用 |
|--------|------|
| **`BaseModel`** | **所有 Pydantic 模型的基类**——继承它才有验证能力 |
| **`ValidationError`** | 验证失败时抛出的异常类 |
| **`EmailStr`** | 内置的邮箱格式校验类型 |
| `json` | 用于解析 JSON 字符串 |

### 2.2 定义 UserInput 模型

```python
class UserInput(BaseModel):
    name: str
    email: EmailStr
    query: str
```

> 🧠 **仅此而已**——3 行代码就定义了一个有完整校验逻辑的数据模型。

### 2.3 创建实例（成功）

```python
user_input = UserInput(
    name="Joe User",
    email="joe.user@example.com",
    query="I forgot my password."
)
print(user_input)
```

**幕后发生了什么？**

> Pydantic 在**创建实例的那一刻**就完成了验证：
> - `name` 是不是 string？
> - `email` 符不符合邮箱格式？
> - `query` 是不是 string？

创建成功 = 你手里拿到的一定是**通过验证的数据**。

---

## 三、验证失败的调试之旅（EmailStr 探秘）

### 🧪 通过故意传错邮箱，反向理解 EmailStr 的校验规则

#### 尝试 1：`"not-an-email"`

```python
UserInput(name="Joe", email="not-an-email", query="...")
```

**错误信息**：`email: An email address must have an @-sign.`
→ 了解：**邮箱必须有 `@`**。

#### 尝试 2：`"joe@notvalid"`

**错误信息**：`The part after the @-sign is not valid, it should have a period.`
→ 了解：**`@` 后面必须有 `.`**。

#### 尝试 3：`"joe@notvalid."`

**错误信息**：`An email address cannot end with a period.`
→ 了解：**`.` 后面还必须有内容**。

#### 尝试 4：`"joe@notvalid.com"` ✅

### 🎯 关键结论

> **`EmailStr` 只验证"格式"，不验证"这个邮箱真的存在"。**
>
> 若要检查邮箱真实可达，需要另外做外部验证（如发送验证邮件）。

---

## 四、生产级写法：封装验证函数

### 4.1 通用验证函数（异常捕获）

```python
def validate_user_input(input_data):
    try:
        # **input_data 把 dict 解包成关键字参数
        user_input = UserInput(**input_data)
        print(f"✅ Valid user input created:")
        print(f"{user_input.model_dump_json(indent=2)}")
        return user_input
    except ValidationError as e:
        # 把错误格式化成人类可读
        print(f"❌ Validation error occurred:")
        for error in e.errors():
            print(f"  - {error['loc'][0]}: {error['msg']}")
        return None
```

### 📌 关键点

| 技巧 | 说明 |
|------|------|
| `UserInput(**input_data)` | 字典解包——dict 的 key/value 直接映射到字段 |
| `e.errors()` | `ValidationError` 提供结构化错误信息列表 |
| `error['loc'][0]` | 出错字段名 |
| `error['msg']` | 人类可读的错误描述 |
| `model_dump_json(indent=2)` | 把模型实例导出为格式化的 JSON |

### 4.2 试验必需字段缺失

```python
input_data = {"name": "Joe User", "email": "joe.user@example.com"}
validate_user_input(input_data)
# ❌ query: Field required
```

> ⚠️ **Pydantic 默认所有字段都是必填的**。

---

## 五、字段进阶：可选字段 + 约束

### 5.1 增强版 UserInput 模型

```python
from pydantic import Field
from typing import Optional
from datetime import date


class UserInput(BaseModel):
    name: str
    email: EmailStr
    query: str
    order_id: Optional[int] = Field(
        None,                                         # 默认值
        description="5-digit order number (cannot start with 0)",
        ge=10000,                                     # greater-equal
        le=99999                                      # less-equal
    )
    purchase_date: Optional[date] = None
```

### 5.2 三个新概念

#### 📦 `Optional[X]`

来自 `typing` 模块，等价于 `X | None`——告诉 Pydantic 这个字段**可以不传**（或传 `None`）。

> ⚠️ **仅靠 `Optional[int]` 还不够**，必须给它一个默认值（如 `= None` 或 `= Field(None, ...)`），否则仍然算必填。

#### 📦 `Field(...)`

Pydantic 的**字段元数据定义器**，可以设置：

| 参数 | 作用 | 示例 |
|------|------|------|
| 第一个位置参数 | **默认值** | `Field(None, ...)` |
| `description` | 字段说明（会出现在 JSON Schema 里） | `"5-digit order number"` |
| `ge` / `le` | 数值范围（≥ / ≤） | `ge=10000, le=99999` |
| `gt` / `lt` | 严格大小于 | `gt=0` |
| `min_length` / `max_length` | 字符串/列表长度 | `max_length=100` |

#### 📦 `datetime.date`

Python 标准库的日期类型。Pydantic 能自动处理多种日期格式（见下文 Data Type Coercion）。

---

## 六、🔍 JSON vs Python 表示的差异

### 6.1 `model_dump_json()` vs `print(instance)`

```python
user_input = UserInput(
    name="Joe", email="joe@a.com", query="...",
    purchase_date=date(2025, 12, 31)
)

print(user_input.model_dump_json(indent=2))
# "purchase_date": "2025-12-31"    ← JSON 字符串表示

print(user_input)
# purchase_date=datetime.date(2025, 12, 31)   ← Python 对象表示
```

| 方法 | 用途 |
|------|------|
| `model_dump_json()` | 导出为 JSON 字符串（发给 API/前端/存盘） |
| `model_dump()` | 导出为 Python dict |
| `print(instance)` | Python 对象原貌 |

### 6.2 `None` vs `null`

| Python | JSON |
|--------|------|
| `None` | `null` |

---

## 七、🆕 多余字段会被默默忽略

```python
input_data = {
    "name": "Joe", "email": "joe@a.com", "query": "...",
    "order_id": 12345, "purchase_date": date(2025, 12, 31),
    "system_message": "extra field 1",   # 🆕 不在模型里
    "iteration": 1                       # 🆕 不在模型里
}
validate_user_input(input_data)
# ✅ 成功——多余字段被忽略
```

### 🎯 这是 Pydantic 的常见使用方式

> 从上游拿到一份**字段很多的 dict/JSON**，你**只关心其中几个字段**——定义好 Pydantic 模型，**其他字段会被自动过滤**。

（若想严格禁止多余字段，可以在 `Config` 里设 `extra='forbid'`，后续课程会讲。）

---

## 八、🪄 Data Type Coercion（数据类型自动转换）

### 8.1 日期字符串自动转 `date`

```python
input_data = {
    ...,
    "purchase_date": "2025-12-31"    # 传字符串
}
validate_user_input(input_data)
# ✅ 成功！Pydantic 自动 parse 成 datetime.date
```

### 8.2 字符串数字自动转 int

```python
input_data = {
    ...,
    "order_id": "12345"              # 传字符串
}
validate_user_input(input_data)
# ✅ 成功！"12345" → 12345
```

### 8.3 ⚠️ 但不是双向的

```python
input_data = {
    "name": 99999,                   # name 字段定义为 str
    ...
}
validate_user_input(input_data)
# ❌ name: Input should be a valid string
```

### 🎯 规则总结

| 方向 | 是否支持 |
|------|----------|
| `"12345"` → `int` | ✅ 自动 |
| `12345` → `str` | ❌ 拒绝 |
| `"2025-12-31"` → `date` | ✅ 自动 |
| `date(...)` → `str` | ❌ 拒绝 |

### 💡 需要更严格？

若要禁用自动转换，可用 **strict mode**（后续课程）。

---

## 九、JSON 数据验证：两种方式

### 方式 ①：先 parse JSON → 再塞给模型（两步）

```python
json_data = '''
{
    "name": "Joe User",
    "email": "joe.user@example.com",
    "query": "I bought a keyboard and mouse and was overcharged.",
    "order_id": 12345,
    "purchase_date": "2025-12-31"
}
'''

# Step 1: JSON → dict
input_data = json.loads(json_data)

# Step 2: dict → Pydantic
validate_user_input(input_data)
```

### 方式 ②：`model_validate_json()`（一步到位）

```python
user_input = UserInput.model_validate_json(json_data)
print(user_input.model_dump_json(indent=2))
```

### 两种错误类型的区别

| JSON 情况 | 错误提示 |
|-----------|----------|
| **JSON 合法，数据不符合模型** | 字段级 ValidationError（如 `order_id: should be >= 10000`）|
| **JSON 本身格式错**（缺括号等） | 解析级 ValidationError（如 `JSON end of file`）|

---

## 十、完整代码模板

```python
from pydantic import BaseModel, Field, ValidationError, EmailStr
from typing import Optional
from datetime import date
import json


# 1. 定义模型
class UserInput(BaseModel):
    name: str
    email: EmailStr
    query: str
    order_id: Optional[int] = Field(
        None,
        description="5-digit order number (cannot start with 0)",
        ge=10000, le=99999,
    )
    purchase_date: Optional[date] = None


# 2. 封装验证函数
def validate_user_input(input_data):
    try:
        user_input = UserInput(**input_data)
        print(f"✅ Valid: {user_input.model_dump_json(indent=2)}")
        return user_input
    except ValidationError as e:
        print(f"❌ Error:")
        for err in e.errors():
            print(f"  - {err['loc'][0]}: {err['msg']}")
        return None


# 3. 三种数据来源都能用

# dict
validate_user_input({"name": "Joe", "email": "joe@a.com", "query": "..."})

# JSON string（两步）
input_data = json.loads(json_str)
validate_user_input(input_data)

# JSON string（一步）
UserInput.model_validate_json(json_str)
```

---

## 十一、🔑 核心要点速查表

| 知识点 | 关键 API/用法 |
|--------|---------------|
| 定义模型 | `class X(BaseModel)` + 类型注解 |
| 邮箱校验 | `email: EmailStr` |
| 可选字段 | `Optional[int] = None` 或 `= Field(None, ...)` |
| 数值约束 | `Field(..., ge=10000, le=99999)` |
| 错误捕获 | `try ... except ValidationError as e` |
| 从 dict 构造 | `Model(**data_dict)` |
| 从 JSON 字符串构造 | `Model.model_validate_json(json_str)` |
| 导出 JSON | `instance.model_dump_json(indent=2)` |
| 导出 dict | `instance.model_dump()` |
| 多余字段 | **默认忽略**（可配置 `extra='forbid'`） |
| 自动类型转换 | `str→int` / `str→date` ✅，反向 ❌ |

---

## 🎯 下一课预告

> **Lesson 3**：把这份验证能力用到**真实 LLM 响应**上——LLM 返回 JSON，用 `model_validate_json()` 做验证，失败了就把错误信息反馈给 LLM 让它自我修正。
