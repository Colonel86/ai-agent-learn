# L5：用 Phoenix 给智能体加埋点

这一节实操：把 **Arize Phoenix + OpenInference + OpenTelemetry** 接到你的智能体上，捕捉 Trace 与 Span。

## 导入与连接 Phoenix

```python
import phoenix as px
from phoenix.otel import register
from openinference.instrumentation.openai import OpenAIInstrumentor
from openinference.semconv.trace import SpanAttributes
from opentelemetry.trace import Status, StatusCode
```

> **OpenInference** 是 Arize 团队维护的库，把 OpenTelemetry 的通用概念翻译成"更适合 LLM 工作流"的语义（如 LLM/Tool/Chain/Agent 等 span kind）。

### 注册 TracerProvider

Phoenix 用**项目（Project）**来隔离不同应用/智能体的 Trace。

```python
PROJECT_NAME = "tracing-agent"
tracer_provider = register(
    project_name=PROJECT_NAME,
    endpoint=get_phoenix_endpoint() + "v1/traces"
)
```

Phoenix 可以本地跑（`px.launch_app()`）、Docker、或 Arize 云端。本课环境里 Phoenix 已经为你启动好。

## 自动埋点：一行接管 OpenAI 调用

```python
OpenAIInstrumentor().instrument(tracer_provider=tracer_provider)
```

从此以后所有 `openai` 库的调用都会被自动追踪为 LLM Span，**Prompt、响应、Tool 定义、Token 使用**等属性自动写入。如果你只用 OpenAI，这一行就够了。

## 手动埋点：拿到 Tracer

但智能体里还有工具调用、其他逻辑要追踪，所以再获取一个 Tracer：

```python
tracer = tracer_provider.get_tracer(__name__)
```

## 埋点策略：从外到内

**先打最外层的 Span，再逐层向内细化**，这样能保证整体视图完整。

### 1. 顶层 Agent Span

新建一个外层方法 `start_main_span` 包装 `run_agent`，并在内部开一个类型为 `agent` 的 Span：

```python
def start_main_span(messages):
    with tracer.start_as_current_span(
        "AgentRun",
        openinference_span_kind="agent",
    ) as span:
        span.set_input(value=messages)
        ret = run_agent(messages)
        span.set_output(value=ret)
        span.set_status(StatusCode.OK)
        return ret
```

### 2. Router Span（chain 类型）

进入 `run_agent` 的 while 循环，每次调用路由器都开一个 Span：

```python
while True:
    with tracer.start_as_current_span(
        "router_call",
        openinference_span_kind="chain",
    ) as span:
        span.set_input(value=messages)
        response = client.chat.completions.create(model=MODEL, messages=messages, tools=tools)
        # ... 处理 tool calls 或最终响应
        span.set_output(value=...)
        span.set_status(StatusCode.OK)
```

> Chain 类型相当于"默认普通逻辑步骤"，没特别归类时都可以用它。

### 3. 用装饰器追踪 `handle_tool_calls`

如果一个方法是自包含的，**装饰器（Decorator）**比 `with` 写起来更省事：

```python
@tracer.chain
def handle_tool_calls(tool_calls, messages):
    ...
```

装饰器会自动把入参作为 input、返回值作为 output 写入 Span。也有 `@tracer.tool` 和 `@tracer.agent` 等不同类型可选。

## 给每个工具加埋点

每个工具用 `@tracer.tool` 装饰：

```python
@tracer.tool
def lookup_sales_data(prompt: str) -> str:
    ...
```

对于工具内部仍需细分的步骤（如 SQL 执行），再用 `with` 嵌一层 chain Span：

```python
@tracer.tool
def lookup_sales_data(prompt: str) -> str:
    df = pd.read_parquet(...)
    duckdb.sql("CREATE TABLE IF NOT EXISTS sales AS SELECT * FROM df")
    sql_query = generate_sql_query(prompt, df.columns, "sales")
    sql_query = sql_query.strip().replace("```sql", "").replace("```", "")

    with tracer.start_as_current_span(
        "execute_sql_query",
        openinference_span_kind="chain",
    ) as span:
        span.set_input(value=sql_query)
        result = duckdb.sql(sql_query).df()
        span.set_output(value=result)
        span.set_status(StatusCode.OK)
    return result.to_string()
```

这样如果 SQL 生成正确但执行失败（连接问题等），你能**精确定位**到底是哪一层挂了。

对 `analyze_sales_data` 同样用 `@tracer.tool`；对 `generate_visualization`，内部的 `extract_chart_config` 和 `create_chart` 用 `@tracer.chain`（它们是工具的子步骤，不是工具本身），最外层 `generate_visualization` 用 `@tracer.tool`。

## 跑一遍看效果

```python
ret = start_main_span([{"role": "user", "content": "..."}])
```

打开 Phoenix UI，进入 `tracing-agent` 项目，你会看到：

- 顶层一行 **AgentRun**（紫色 / agent）
- 内部一连串 **router_call**（蓝色 / chain）
- 每次工具调用：**lookup_sales_data**、**generate_visualization** 等（黄色 / tool）
- 工具内部的 **execute_sql_query**、**extract_chart_config**（蓝色 / chain）
- 由自动埋点产生的 **LLM Span**（橙色），自动带有 prompt、system prompt、output、tools 定义

每一个 Span 都可以展开看 attributes：完整的输入、输出、错误状态。**至此你已经能精确看见智能体每一步**，下一节就把评估器加上去。
