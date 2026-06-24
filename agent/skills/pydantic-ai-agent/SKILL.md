---
name: pydantic-ai-agent
description: Use when building Python AI agents with Pydantic as the type/validation backbone — structured output (response_format / tool_use schemas), Pydantic-modeled tool I/O, agent framework selection where Pydantic is the contract layer (PydanticAI / Instructor / OpenAI responses.parse / Anthropic tool_use), pydantic-evals, Logfire observability. TRIGGER when user code imports `pydantic_ai`, `instructor`, or uses `pydantic.BaseModel` together with `openai`/`anthropic`/`google.genai` LLM SDKs; or when user asks to "get JSON from LLM", "structured output", "tool calling", "validate LLM output", "build an agent" in Python. SKIP for non-Python agents, agents that deliberately avoid Pydantic (raw dict / TypedDict / dataclass-only), pure prompt-engineering questions, or non-agent single-shot generation tasks.
---

# Pydantic-centric AI Agent 开发指南（2026）

> 本 skill 的范围：以 **Pydantic 作为类型与契约核心**来构建 Agent。如果项目刻意不用 Pydantic（裸 dict / 仅 dataclass / TypedDict 风格），跳过本 skill。

This skill encodes battle-tested decisions for Pydantic-centric Python AI agent development. Follow the decision trees first, then the code templates. Do not improvise architecture before consulting them.

## 1. 三大核心决策

### 决策 A：Structured Output 怎么拿？

```
要不要做 Agent（多步 / 工具调用）？
├── 否，只要单次拿 JSON
│    ├── 仅 OpenAI    → client.responses.parse + Pydantic
│    │                  （或 chat.completions.parse，无 beta）
│    ├── 仅 Anthropic → tool_use + tool_choice 强制单工具 + Pydantic 校验
│    ├── 跨 provider  → instructor 库
│    └── 自托管模型   → vLLM / SGLang + xgrammar (guided_json=schema)
└── 是，要做 Agent → 跳到决策 B
```

**禁止**：
- ❌ 在 prompt 里求 JSON 然后 `json.loads()` —— 没有 schema 保证
- ❌ 用 `openai.beta.chat.completions.parse` —— Structured Outputs 已毕业，去掉 `beta`
- ❌ 手搓 retry 循环，除非有特殊原因（教学/调试除外）

### 决策 B：Agent 框架怎么选？

```
团队主语言是 Python？
├── 否 → 跳出本 skill 范围（Vercel AI SDK / Mastra）
└── 是 → 锁定一家厂商吗？
         ├── 只用 OpenAI       → OpenAI Agents SDK
         ├── 只用 Anthropic    → Claude Agent SDK
         ├── 跨 provider 或追求工程化 → PydanticAI（推荐默认）
         └── 已深度投入 LangChain → LangGraph（迁移成本高才坚持）
```

**为什么默认 PydanticAI**：类型贯穿、依赖注入（DI）、pydantic-evals、Logfire（OTel 原生）、跨 provider。除非有强约束，新项目首选它。

### 决策 C：工具协议用什么？

```
工具是项目内部 Python 函数？
└── 用框架原生 @tool 装饰器（PydanticAI / Agents SDK / Claude SDK）

工具要跨进程 / 跨语言 / 复用给多个 agent？
└── 用 MCP（Model Context Protocol）—— 2025 已成事实标准
   - 暴露端：写 MCP Server
   - 消费端：客户端连接 MCP Server
```

**禁止**：用 LangChain `Tool` 包装本可直接用框架原生装饰器的纯函数。

---

## 2. 必须遵守的工程规则

1. **所有 LLM I/O 都用 Pydantic 模型**——输入、输出、工具入参全部 `BaseModel`。绝不用裸 `dict` 在组件间传递 LLM 数据。
2. **工具签名只暴露 LLM 关心的参数**。数据库连接、HTTP client、user_id 等通过 DI / RunContext 注入，不进入 LLM 的 schema。
3. **必须有 evals**。任何提交到 main 的 agent 代码必须有 ≥ 20 条 golden case + CI 自动跑分（用 `pydantic-evals` 或等价物）。
4. **必须有 OTel trace**。生产 agent 必须接入 Logfire 或等价 OTel 后端，每个 LLM 调用、工具调用、校验失败都要有 span。
5. **模型名集中配置**。绝不在业务代码硬编码 `"gpt-5"` / `"claude-sonnet-4-7"`，从 settings / env 读取，方便切换。
6. **工具函数必须有 docstring 和类型注解**——这是 LLM 决定何时调用工具的依据。
7. **结构化输出不等于无错**。即便用了 strict mode，输出值的语义正确性仍要靠 evals 验证（schema 合规 ≠ 答案正确）。

---

## 3. 反模式（看到立即纠正）

| 反模式 | 正确做法 |
| --- | --- |
| 在 prompt 里写 "Return JSON in this format: {...}" 然后手动解析 | 用 `response_format=PydanticModel` 或 `tool_use` |
| 工具函数签名带 `db: Session` 等基础设施参数 | 用 DI / RunContext，工具签名只留 LLM 入参 |
| `openai.beta.chat.completions.parse` | `openai.chat.completions.parse`（去掉 beta） |
| `claude-3-7-sonnet`、`gpt-4o`、`gemini-2.0-flash` 硬编码 | 从配置读取，默认用最新稳定版 |
| `langchain` 用作 LLM 调用的薄包装 | 直接用厂商 SDK 或 PydanticAI |
| 没有评测，只靠"我看了几条都对"上线 | pydantic-evals + CI |
| LLM 调用没有 trace，出错只能看日志 | 接 Logfire，1 行 `instrument_pydantic_ai()` |
| Tool calling 后不校验工具返回值 | 工具返回值也要 Pydantic 模型 |

---

## 4. 代码骨架模板

### 4.1 PydanticAI 标准 Agent（默认方案）

```python
from dataclasses import dataclass
from typing import Literal
from pydantic import BaseModel
from pydantic_ai import Agent, RunContext
import logfire

# === 0. 观测 ===
logfire.configure()
logfire.instrument_pydantic_ai()

# === 1. 输出契约 ===
class SupportTicket(BaseModel):
    priority: Literal["low", "medium", "high"]
    category: str
    summary: str

# === 2. 依赖（DI 容器） ===
@dataclass
class Deps:
    db: "DatabaseConn"
    http: "httpx.AsyncClient"
    user_id: str

# === 3. Agent 定义 ===
agent = Agent(
    model=settings.model_name,           # 配置驱动，不硬编码
    output_type=SupportTicket,
    deps_type=Deps,
    system_prompt="You are a support agent. Classify the user request.",
)

# === 4. 工具：签名只暴露 LLM 入参 ===
@agent.tool
async def query_orders(ctx: RunContext[Deps], status: str) -> list[dict]:
    """Query the current user's orders by status."""
    return await ctx.deps.db.fetch(
        "SELECT * FROM orders WHERE user_id=$1 AND status=$2",
        ctx.deps.user_id, status,
    )

# === 5. 调用 ===
async def handle(query: str, deps: Deps) -> SupportTicket:
    result = await agent.run(query, deps=deps)
    return result.output
```

### 4.2 OpenAI 单次 Structured Output（不需要 Agent）

```python
from openai import OpenAI
from pydantic import BaseModel

class CustomerQuery(BaseModel):
    name: str
    category: Literal["billing", "technical", "general"]
    priority: Literal["low", "medium", "high"]

client = OpenAI()

response = client.responses.parse(    # 注意：不是 beta.chat.completions.parse
    model=settings.model_name,
    input=[{"role": "user", "content": user_text}],
    text_format=CustomerQuery,
)
query: CustomerQuery = response.output_parsed
```

### 4.3 Anthropic Structured Output（无需第三方库）

```python
import anthropic
from pydantic import BaseModel

class CustomerQuery(BaseModel):
    category: Literal["billing", "technical", "general"]
    priority: Literal["low", "medium", "high"]

client = anthropic.Anthropic()
schema = CustomerQuery.model_json_schema()

resp = client.messages.create(
    model=settings.model_name,
    max_tokens=1024,
    tools=[{
        "name": "extract",
        "description": "Extract structured query info",
        "input_schema": schema,
    }],
    tool_choice={"type": "tool", "name": "extract"},   # 强制调用此工具
    messages=[{"role": "user", "content": user_text}],
)
query = CustomerQuery.model_validate(resp.content[0].input)
```

### 4.4 pydantic-evals 测试集骨架

```python
from pydantic_evals import Case, Dataset
from pydantic_evals.evaluators import LLMJudge, IsInstance

dataset = Dataset(
    cases=[
        Case(
            name="forgot_password",
            inputs="我登不上去了",
            expected_output=SupportTicket(
                priority="medium", category="account", summary="..."
            ),
        ),
        # ≥ 20 条 golden
    ],
    evaluators=[
        IsInstance(type_name="SupportTicket"),
        LLMJudge(rubric="summary 是否抓住核心诉求"),
    ],
)

# 在 CI / pytest 里调用
async def test_agent_quality():
    report = await dataset.evaluate(lambda inp: agent.run(inp).output)
    assert report.pass_rate > 0.85
```

---

## 5. 排错检查清单

写完 agent 后逐项核对：

- [ ] 输出类型是 Pydantic `BaseModel`，不是 `dict` / `str`
- [ ] 工具函数有 docstring（LLM 用它判断何时调用）
- [ ] 数据库 / HTTP / user_id 通过 DI 注入，不在工具签名里
- [ ] 模型名从 settings 读取
- [ ] 至少 20 条 golden case
- [ ] Logfire 或等价观测已接入
- [ ] 跨 provider 切换试过（除非明确单 provider）
- [ ] 工具失败时 agent 行为已测试（不是只测 happy path）

---

## 6. 何时不要用 Agent

Agent 不是银弹。下列场景**不该上 Agent**：

- 单次输入→单次输出，没有工具/多步：直接 structured output
- 流程完全确定，只需要 LLM 做某一步：用 workflow（Temporal / Inngest），LLM 当节点
- 需要严格 SLA / 可预测性的关键路径：rule-based + LLM 兜底
- 数据敏感度极高、不能容忍幻觉：抽取 + 校验，不让 LLM 决策

> 参考 Anthropic [Building Effective Agents](https://www.anthropic.com/research/building-effective-agents) 的判断框架。

---

## 7. 当前推荐版本（2026-05）

- Pydantic：v2.x
- PydanticAI：1.x
- OpenAI Python SDK：最新（用 `responses.*` API）
- Anthropic SDK：最新（Claude 4.x 系列模型）
- Logfire：最新
- xgrammar：自托管时配 vLLM ≥ 0.6

模型默认推荐（具体版本号从 settings 读取）：
- 复杂推理 / 长上下文：Claude Opus 4.x 或 GPT-5
- 日常 agent / 工具调用：Claude Sonnet 4.x 或 GPT-5
- 高并发 / 低成本：Claude Haiku 4.x 或 GPT-5 mini

---

## 8. 当不确定时

- 不确定选哪个框架 → 默认 PydanticAI
- 不确定 schema 怎么设计 → 优先 `Literal` 收敛取值，必填字段用 `Field(..., description=...)`
- 不确定要不要重试 → 用框架内置重试，不要手搓
- 不确定怎么测 → pydantic-evals + 20 条 case + CI

**最后原则**：宁可少抽象，不要早抽象。先用框架原生写法跑通，再考虑封装。
