# Pydantic for LLM Workflows —— 总结回顾

> 课程：**Pydantic for LLM Workflows**（DeepLearning.AI 短课）
> 用途：一页式快速回顾。逐课详记见各 `sc-Pydantic-C1-L*` 笔记；PydanticAI 框架深度见[补充章节](./sc-Pydantic-C1-补充-PydanticAI生态深度.md)。

---

## 一句话主线

> **LLM 默认吐自由文本，没法可靠地接进软件系统。用 Pydantic 给输入、LLM 输出、工具参数、最终结果每一道关口都定契约、做校验，LLM 就成了系统里可信的数据生产者。**

全课围绕一个**客户支持系统**贯穿始终：用户请求 →（分类）→（决定调工具）→（生成工单），每一步都有 Pydantic 守门。

---

## 核心问题与解法（L0–L1）

- **痛点**：直接在 prompt 里「求」JSON，LLM 经常差一口气——加前缀、包 Markdown 代码块、漏字段、枚举值/邮箱格式不对。输出**不可预测 → 生产不可用**。
- **Pydantic = 数据契约**：用 Python 类（继承 `BaseModel`）声明字段名+类型，所有数据都得「签这份合同」。
- **两条技术路线**（全课主干）：
  1. **提示 + 校验 + 重试**（通用、土办法，L3 手搓）
  2. **把 Pydantic 模型直接传给 API**（优雅、现代，L4）
- **第三大应用**：**Tool Calling**——用 Pydantic 定义工具参数 schema（L5）。

---

## 逐课速查

### L2 — Pydantic 基础（验证用户输入）
| 能力 | 关键写法 |
|---|---|
| 定义模型 | `class UserInput(BaseModel): name: str; email: EmailStr` |
| 可选字段 | `Optional[int] = None`（光 `Optional` 不够，**必须给默认值**否则仍必填） |
| 字段约束 | `Field(None, ge=10000, le=99999, description=...)` |
| 错误捕获 | `try ... except ValidationError as e`，`e.errors()` 取结构化错误 |
| 构造 | `Model(**dict)` / `Model.model_validate_json(json_str)` |
| 导出 | `model_dump_json(indent=2)`（JSON）/ `model_dump()`（dict） |

**两个易错点**：
- **多余字段默认被忽略**（要禁止用 `extra='forbid'`）——这正是常见用法：上游一大堆字段，只取关心的几个。
- **类型自动转换是单向的**：`"123"→int`✅、`"2025-12-31"→date`✅，但反向 ❌。要禁用转换上 strict mode。

### L3 — Prompt + 校验 + 重试（手搓反馈循环）
- 流程：`call_llm → model_validate_json → 失败则把 error 拼进 retry prompt 再问 →` 最多 N 次。
- retry prompt 三要素：**原始 prompt + 上次错误输出 + 错误信息**，用 `<xml>` 标签分块。
- **关键优化**：用 `model_json_schema()` 生成的**完整 schema** 替代「示例」喂给 LLM——LLM 才知道枚举值/范围/必填，首次成功率大幅提升。
- 心法：**这就是 Instructor / OpenAI Structured Output 幕后做的事**，手搓一遍再看库就秒懂。
- `Field(..., ...)` 的 `...`（Ellipsis）= **必填**。

### L4 — 把 Pydantic 模型直接传给 API（四方案）
| 方案 | 后端机制 | 返回 | 跨厂商 |
|---|---|---|---|
| ① Instructor | retry + validate | Pydantic 实例 ✅ | ✅ |
| ② OpenAI `chat.completions.parse` | Constrained Generation | JSON 字符串（要手动 validate）⚠️ | ❌ 仅 OpenAI |
| ③ OpenAI `responses.parse` | Constrained Gen + 自动校验 | Pydantic 实例 ✅ | ❌ 仅 OpenAI |
| ④ PydanticAI Agent | 统一抽象 | Pydantic 实例 ✅ | ✅ |

- **两种底层范式**：
  - **自动 Retry 派**（Instructor）——生成后校验失败重试，多数能成但可能慢/失败。
  - **Constrained Generation 派**（OpenAI 新版、vLLM、llama.cpp）——**token 级别强制只输出合法 JSON，100% 结构合规、无需重试**。
- 最大洞察：**"It's Pydantic models all the way down."** 你发出去的 schema 是 Pydantic，OpenAI 拿回来的响应本身也是 Pydantic。学会它 = 学会 LLM 工作流的通用语言。
- ⚠️ 本课把 PydanticAI 当「四方案之一」是**低估**——它是完整 Agent 框架，详见补充章节。

### L5 — Tool Calling（综合实战：三段式流水线）
- **3 次 LLM 调用横跨 3 家厂商**（Gemini 分类 → OpenAI 决定调工具 → Anthropic 生成工单），故意演示**厂商可互换**。
- **Pydantic 在 Tool Calling 的三重角色**：① `model_json_schema()` 把模型转成工具定义给 LLM；② `model_validate_json()` 校验 LLM 返回的参数；③ Python 工具函数签名直接用该模型。
- 新 API/能力：
  - `@field_validator("字段")` — 自定义校验（正则订单号、安全过滤、业务规则）。
  - **嵌套模型**（字段类型是另一个 `BaseModel`）+ **继承模型**（`SupportTicket(CustomerQuery)`）。
  - `tools=[...]` + `tool_choice="auto"` — 让 LLM 自己决定是否调工具。
- 核心思想：**Validation at Every Stage**——用户输入、每次 LLM 输出、工具参数，每道门都有 Pydantic 守卫。
- 收尾细节：`creation_date` 由 **Python 侧补**（`datetime.now()`），说明字段不必全由 LLM 填。

### L6 — 结语
- 收获分两层：**LLM 层**（结构/可靠性/校验）+ **通用工程层**（任何组件间数据契约都能用）。
- 未覆盖的进阶方向：strict mode、`@model_validator(before/after)`、`Annotated[int, Field(gt=0)]`、自定义类型、`pydantic-settings`、V2 Rust 内核、**PydanticAI**。

---

## 关键 API 速查

| API | 用途 |
|---|---|
| `class X(BaseModel)` | 定义数据契约 |
| `EmailStr` / `Literal[...]` | 邮箱校验 / 枚举限定 |
| `Field(..., ge=, le=, description=)` | 约束与元数据；`...`=必填 |
| `@field_validator("f")` | 自定义字段校验 |
| `Model.model_validate_json(s)` | JSON 字符串 → 校验 → 实例 |
| `Model.model_json_schema()` | 模型 → JSON Schema（喂 LLM / 工具定义） |
| `inst.model_dump_json()` / `model_dump()` | 实例 → JSON / dict |
| `ValidationError` + `e.errors()` | 捕获并读结构化错误 |

---

## 架构师视角的三个要点

1. **「先 Constrained Generation，retry 兜底」**——能用约束生成的（OpenAI 新 API / vLLM）就别靠重试，可靠性是数量级差异；跨厂商或不支持时再退回 Instructor 的 retry 范式。
2. **Pydantic 是 LLM 生态的「数据契约通用语」**——schema 喂进去、响应是它、工具参数也是它，厂商因此变成可互换的零件。投资 Pydantic 的回报跨框架。
3. **校验要布在每一道边界，不是只校最终输出**——L5 的「Validation at Every Stage」是把 LLM 接进生产系统的核心纪律，和课程 8「Evals 是成功最大预测因子」同源：**可靠性来自纪律，不是来自模型**。

---

## 后续衔接
- 想真正用 Agent（工具/多步/编排/观测）→ 读[补充章节：PydanticAI 生态深度](./sc-Pydantic-C1-补充-PydanticAI生态深度.md)（DI / pydantic-graph / pydantic-evals / Logfire）。
- 配套巩固：官方新增的 **L7 Bonus** 交互式项目实操。
