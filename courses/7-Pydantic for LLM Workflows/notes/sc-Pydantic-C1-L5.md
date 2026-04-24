# 第 5 课：Tool Calling —— 用 Pydantic 串起完整客户支持系统

> 课程：Pydantic for LLM Workflows · Lesson 5
> 原文件：
> - `subtitles/sc-Pydantic-C1-L5.vtt`
> - `code/lesson_5.md`

---

## 一、本课目标

> **把前面学到的所有 Pydantic 能力，串成一条真实的生产级 Agent 流水线**——从用户输入到工具调用到最终工单。

### 🎯 本课 = 前四课的综合应用

- **Structured Output**（前课）+ **Tool Calling**（本课）= **Pydantic 在 LLM 工作流中的两大支柱**

---

## 二、🗺 系统全景：三次 LLM 调用的流水线

```
┌───────────────────────────────────────────────────────────────┐
│  用户输入（JSON）                                              │
│  { "name": "Joe", "email": "...", "query": "...",             │
│    "order_id": "ABC-12345" }                                   │
└──────────────┬────────────────────────────────────────────────┘
               ↓ ① validate_user_input()
     UserInput Pydantic 实例
               ↓ ② create_customer_query()   ← LLM #1 (Gemini)
     CustomerQuery Pydantic 实例
               ↓ ③ decide_next_action_with_tools()  ← LLM #2 (OpenAI)
     ┌─────────┴──────────┐
     │                    │
  tool_calls          可能没有 tool_calls
     │                    │
     ↓ ④ get_tool_outputs()
   Python 函数执行（check_order_status / lookup_faq_answer）
     │                    │
     └─────────┬──────────┘
               ↓ ⑤ generate_structured_support_ticket()  ← LLM #3 (Anthropic)
       SupportTicket Pydantic 实例（含所有字段 + 推荐动作）
```

**3 次 LLM 调用横跨 3 家厂商（Gemini / OpenAI / Anthropic）**——故意演示 Pydantic 的**厂商无关**特性。

---

## 三、🆕 新概念：`field_validator` —— 自定义字段校验

### 3.1 场景

`order_id` 格式要求：**3 个大写字母 + 短横线 + 5 位数字**（如 `ABC-12345`）

内置类型搞不定，用 **`field_validator`**：

```python
from pydantic import field_validator


class UserInput(BaseModel):
    order_id: Optional[str] = Field(None, description="Order ID (format: ABC-12345)")

    @field_validator("order_id")
    def validate_order_id(cls, order_id):
        import re
        if order_id is None:
            return order_id
        pattern = r"^[A-Z]{3}-\d{5}$"
        if not re.match(pattern, order_id):
            raise ValueError(
                "order_id must be in format ABC-12345 "
                "(3 uppercase letters, dash, 5 digits)"
            )
        return order_id
```

### 🎯 `field_validator` 的三大用途

| 用途 | 举例 |
|------|------|
| **格式校验** | 正则匹配订单号、身份证号等 |
| **安全过滤** | 防 SQL Injection、XSS |
| **业务规则** | 比如"出生日期必须在今天之前" |

---

## 四、🔑 本课的核心概念：Tool Calling

### 4.1 Tool Calling 的工作机制

```
LLM 看到问题 + 可用工具列表
     ↓
LLM 判断："我需要调用工具才能回答"
     ↓
LLM 不直接回答，而是**返回要调用哪个工具 + 参数**
     ↓
你的代码：验证参数 → 执行 Python 函数 → 拿到结果
     ↓
（可选）把结果再给 LLM，让它基于真实数据生成最终回复
```

### 4.2 Pydantic 在 Tool Calling 的三重角色

| 阶段 | Pydantic 作用 |
|------|---------------|
| **① 定义工具** | 用 Pydantic 模型描述参数 → 转 JSON Schema 给 LLM |
| **② 收到 LLM 返回的参数** | 用 Pydantic 验证参数是否合法 |
| **③ 生产函数签名** | Python 函数的参数类型就是 Pydantic 模型 |

---

## 五、代码实战（逐步构建）

### 5.1 定义工具参数模型

```python
class FAQLookupArgs(BaseModel):
    query: str = Field(..., description="User's query")
    tags: List[str] = Field(..., description="Relevant keyword tags")


class CheckOrderStatusArgs(BaseModel):
    order_id: str = Field(..., description="Customer's order ID (ABC-12345)")
    email: EmailStr = Field(..., description="Customer's email address")

    @field_validator("order_id")
    def validate_order_id(cls, order_id):
        import re
        if not re.match(r"^[A-Z]{3}-\d{5}$", order_id):
            raise ValueError("order_id must be in format ABC-12345")
        return order_id
```

### 5.2 模拟数据源（假 DB）

```python
faq_db = [
    {
        "question": "How can I reset my password?",
        "answer": "To reset your password, click 'Forgot Password'...",
        "keywords": ["password", "reset", "account"]
    },
    # ...
]

order_db = {
    "ABC-12345": {"status": "shipped", "estimated_delivery": "2025-12-05",
                  "purchase_date": "2025-12-01", "email": "joe@example.com"},
    # ...
}
```

### 5.3 真正的工具函数（接收 Pydantic 实例做参数）

```python
def lookup_faq_answer(args: FAQLookupArgs) -> str:
    """用 tags 和 query 关键词在 FAQ 库里做匹配"""
    query_words = set(w.lower() for w in args.query.split())
    tag_set = set(t.lower() for t in args.tags)
    best_match, best_score = None, 0

    for faq in faq_db:
        keywords = set(k.lower() for k in faq["keywords"])
        score = len(keywords & tag_set) + len(keywords & query_words)
        if score > best_score:
            best_score = score
            best_match = faq

    if best_match and best_score > 0:
        return best_match["answer"]
    return "Sorry, I couldn't find an FAQ answer for your question."


def check_order_status(args: CheckOrderStatusArgs):
    """根据 order_id 查状态，用 email 做二次校验"""
    order = order_db.get(args.order_id)
    if not order:
        return {"order_id": args.order_id, "status": "not found", ...}
    if args.email.lower() != order["email"].lower():
        return {"order_id": args.order_id, "status": order["status"],
                "note": "order_id found but email mismatch"}
    return {"order_id": args.order_id, "status": order["status"],
            "estimated_delivery": order["estimated_delivery"],
            "note": "order_id and email match"}
```

> 💡 **注意**：函数签名直接用 `args: FAQLookupArgs` —— **Pydantic 模型既是 Schema 又是运行时类型**。

### 5.4 🔑 核心：定义 Tool Schema（给 LLM 看的）

```python
tool_definitions = [
    {
        "type": "function",
        "function": {
            "name": "lookup_faq_answer",
            "description": "Look up an FAQ answer by matching tags to FAQ entry keywords.",
            "parameters": FAQLookupArgs.model_json_schema()    # 🔑 关键！
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_order_status",
            "description": "Check the status of a customer's order.",
            "parameters": CheckOrderStatusArgs.model_json_schema()
        }
    }
]
```

### 🎯 `model_json_schema()` 是关键桥梁

> **Pydantic 模型 → JSON Schema → LLM 的工具定义**
>
> 这一行代码打通了 Python 类型系统和 LLM 的工具调用协议。

---

## 六、🆕 嵌套 Pydantic 模型：最终的 SupportTicket

```python
class OrderDetails(BaseModel):
    status: str
    estimated_delivery: str
    note: str


class SupportTicket(CustomerQuery):             # 🔑 继承 CustomerQuery
    recommended_next_action: Literal[
        'escalate_to_agent',
        'send_faq_response',
        'send_order_status',
        'no_action_needed'
    ] = Field(..., description="LLM's recommended next action")

    order_details: Optional[OrderDetails] = Field(None, ...)      # 🆕 嵌套模型
    faq_response: Optional[str] = Field(None, ...)
    creation_date: datetime = Field(..., description="Ticket creation timestamp")
```

### 🎯 两个新用法

| 用法 | 代码 |
|------|------|
| **继承扩展** | `class SupportTicket(CustomerQuery)` 获得父类所有字段 |
| **嵌套模型** | `order_details: Optional[OrderDetails]` ——**字段类型就是另一个 Pydantic 模型** |

---

## 七、LLM 调用：决定是否调用工具

```python
client = OpenAI()


def decide_next_action_with_tools(customer_query: CustomerQuery):
    support_ticket_schema = json.dumps(SupportTicket.model_json_schema(), indent=2)

    system_prompt = f"""
        You are a helpful customer support agent. Your job is to determine
        what support action should be taken ...

        If more information on a particular order_id or FAQ response would
        be helpful, call the appropriate tool.
        If an order_id is present in the query, ALWAYS look up the order status.

        Here is the JSON schema for the SupportTicket model:
        {support_ticket_schema}
    """

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": str(customer_query.model_dump())}
    ]

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        tools=tool_definitions,          # 🔑 告诉 LLM 有哪些工具
        tool_choice="auto"                # 🔑 让 LLM 自己判断是否用工具
    )

    message = response.choices[0].message
    tool_calls = getattr(message, "tool_calls", None)
    return message, tool_calls, messages
```

### 🎯 关键设计：把 SupportTicket Schema 放进 system prompt

**为什么？**

> Schema **不是**这次调用的响应格式（这次是决定是否调工具）。
>
> 但让 LLM 知道**最终目标**（要生成一个什么样的 Ticket），它才能做出更合理的工具调用决策。

---

## 八、执行工具 + 验证 LLM 返回的参数

```python
def get_tool_outputs(tool_calls):
    tool_outputs = []
    if not tool_calls:
        return tool_outputs

    for tool_call in tool_calls:
        if tool_call.function.name == "lookup_faq_answer":
            # 🔑 关键：用 Pydantic 验证 LLM 给的参数
            args = FAQLookupArgs.model_validate_json(tool_call.function.arguments)
            result = lookup_faq_answer(args)
            tool_outputs.append({"tool_call_id": tool_call.id, "output": result})

        elif tool_call.function.name == "check_order_status":
            args = CheckOrderStatusArgs.model_validate_json(tool_call.function.arguments)
            result = check_order_status(args)
            tool_outputs.append({"tool_call_id": tool_call.id, "output": result})

    return tool_outputs
```

### 🎯 闭环校验

| 阶段 | Pydantic 干什么 |
|------|-----------------|
| **传给 LLM** | 用 `model_json_schema()` 告诉 LLM "参数应该长这样" |
| **LLM 返回参数** | 用 `model_validate_json()` 确认 LLM **真的**按规范返回了 |

**双向守护** → 工具不会被奇怪的参数调用。

---

## 九、最终 LLM 调用：生成 SupportTicket

```python
anthropic_client = instructor.from_anthropic(anthropic.Anthropic())


def generate_structured_support_ticket(customer_query, message, tool_outputs):
    tool_results_str = "\n".join([
        f"Tool: {out['tool_call_id']} Output: {json.dumps(out['output'])}"
        for out in tool_outputs
    ]) if tool_outputs else "No tool calls were made."

    prompt = f"""
        You are a support agent. Use all information below to generate
        a support ticket as a validated Pydantic model.

        Customer query: {customer_query.model_dump_json(indent=2)}
        LLM message: {str(message.content)}
        Tool results: {tool_results_str}
    """

    response = anthropic_client.messages.create(
        model="claude-3-7-sonnet-latest",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
        response_model=SupportTicket        # 🔑 Pydantic 模型作为响应格式
    )

    # Python 侧额外填充一个字段
    response.creation_date = datetime.now()
    return response
```

### 🎯 最后一步：Python 侧补字段

`creation_date` 不是由 LLM 生成的——Python 侧**在拿到 Pydantic 实例后直接赋值** `datetime.now()`。

展示：**Pydantic 模型不一定 LLM 要填满所有字段，你可以自己补充**。

---

## 十、端到端运行

```python
user_json = '''
{
    "name": "Joe User",
    "email": "joe@example.com",
    "query": "I'm really not happy with this product I bought",
    "order_id": "QWE-34567",
    "purchase_date": null
}
'''

# 一条龙
valid_user_json = validate_user_input(user_json).model_dump_json()
customer_query = create_customer_query(valid_user_json)
message, tool_calls, messages = decide_next_action_with_tools(customer_query)
tool_outputs = get_tool_outputs(tool_calls)
support_ticket = generate_structured_support_ticket(
    customer_query, message, tool_outputs
)

print(support_ticket.model_dump_json(indent=2))
```

**产出**：一个完整的 `SupportTicket` 实例，含：
- 用户信息（name / email / query）
- LLM 分析结果（priority / category / tags）
- 工具返回的订单详情（`order_details: OrderDetails`）
- LLM 推荐的动作（`recommended_next_action: "escalate_to_agent"`）
- 创建时间戳（Python 侧补）

---

## 十一、💎 本课核心洞察

### 11.1 Pydantic 在 LLM 工作流的完整角色图

```
用户输入 ──► UserInput 模型（validate）
                │
                ↓
           CustomerQuery 模型（LLM 填充 + validate）
                │
                ↓
        FAQLookupArgs / CheckOrderStatusArgs
        （Tool Schema + LLM 参数 validate + Python 函数签名）
                │
                ↓
          SupportTicket（含嵌套 OrderDetails，LLM 填充 + validate）
```

### 11.2 "Validation at Every Stage"（每一步都校验）

| 阶段 | 校验对象 |
|------|----------|
| 用户 → 系统 | 用户输入格式 |
| LLM #1 → 系统 | LLM 返回的 CustomerQuery |
| LLM #2 → 系统 | LLM 返回的**工具参数** |
| LLM #3 → 系统 | LLM 返回的 SupportTicket |

**每一道门都有 Pydantic 守卫** → 整个系统的数据**可信可控**。

### 11.3 三家厂商共存

> Gemini + OpenAI + Anthropic **同时出现在同一个流水线里**——Bill 故意这么设计是为了证明：
>
> **"Pydantic 让 LLM 厂商变成可互换的零件。"**

### 11.4 生产思考题（课程结尾提出）

> ❓ **如果 LLM 返回的工具参数验证失败了，你会怎么处理？**

选项：
- 重试 LLM
- 返回错误信息给用户
- 降级到默认行为
- 记录日志 + 告警

这就是 Pydantic 让你**有能力做决策**的体现。

---

## 十二、📝 速查表：本课新 API

| API | 用途 |
|-----|------|
| `@field_validator("field_name")` | 自定义字段校验器（正则、业务规则） |
| `Model.model_json_schema()` | 导出 JSON Schema（给 LLM 工具定义用） |
| `Model.model_validate_json(json_str)` | 从 JSON 字符串构造并校验 |
| **嵌套 Pydantic 模型** | `order_details: Optional[OrderDetails]` |
| **继承 Pydantic 模型** | `class SupportTicket(CustomerQuery):` |
| `tools=[...]` + `tool_choice="auto"` | OpenAI Tool Calling API |
| `tool_call.function.arguments` | 拿到 LLM 返回的工具参数（JSON 字符串） |

---

## 🎯 课程结语

> 🏆 **至此，你已经掌握了 Pydantic 在 LLM 工作流中的完整应用谱系：**
>
> - ✅ 基础验证（L2）
> - ✅ LLM 输出 + Retry（L3）
> - ✅ 直接传模型给 API（L4）
> - ✅ **Tool Calling + 三段式流水线（L5）**
>
> 接下来的 L6 / L7 会做课程总结、拓展与致谢。
