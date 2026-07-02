# L7：实操——给 Router 和 Skills 加评估

本节实操：用 LLM-as-a-judge 和 Code-based 给智能体的各个部分加评估，并把结果回写到 Phoenix 上展示。

## 准备

```python
import phoenix as px
from phoenix.evals import (
    TOOL_CALLING_PROMPT_TEMPLATE,
    llm_classify,
    OpenAIModel,
)
from phoenix.trace import SpanEvaluations
from phoenix.trace.dsl import SpanQuery
from openinference.instrumentation import suppress_tracing

import nest_asyncio
nest_asyncio.apply()

PROJECT_NAME = "evaluating-agent"
from utils import run_agent, start_main_span, tools
```

> **`nest_asyncio`**：让 `llm_classify` 能在 Notebook 里**并发**跑 LLM 调用，大幅加速大批量评估。
>
> 上一节构造好的智能体被搬到了 `utils.py`，本节直接 import。

## 跑一批真实查询作为评估基线

```python
agent_questions = [
    "What was the most popular product SKU?",
    "What was the total revenue across all stores?",
    "Which store had the highest sales volume?",
    "Create a bar chart showing total sales by store",
    "What percentage of items were sold on promotion?",
    "What was the average transaction value?",
]
for q in agent_questions:
    start_main_span([{"role": "user", "content": q}])
```

此后在 Phoenix 的 `evaluating-agent` 项目下能看到 6 条 Trace。

## Phoenix 评估的通用流程

> **导出 Span → 用 LLM-as-a-judge 或代码加标签 → 把标签回写 Phoenix**

## 评估 1：Router 函数调用（LLM-as-a-judge）

Phoenix 提供了现成的 `TOOL_CALLING_PROMPT_TEMPLATE`，它要求两个占位变量 `question`、`tool_call`，以及 `{tool_definitions}`。

### 第 1 步：导出相关 Span

用 `SpanQuery` DSL 过滤：

```python
query = (
    SpanQuery()
    .where("span_kind == 'LLM'")
    .select(question="input.value", tool_call="llm.tools")
)
tool_calls_df = (
    px.Client().query_spans(query, project_name=PROJECT_NAME)
    .dropna(subset=["tool_call"])
)
```

`select` 中的别名要**精确对齐模板里的占位变量**。`dropna` 用来剔除非路由器的 LLM Span。

### 第 2 步：跑 `llm_classify`

```python
with suppress_tracing():
    tool_call_eval = llm_classify(
        dataframe=tool_calls_df,
        template=TOOL_CALLING_PROMPT_TEMPLATE.template.replace(
            "{tool_definitions}", json.dumps(tools)
        ),
        rails=["correct", "incorrect"],
        model=OpenAIModel(model="gpt-4o"),
        provide_explanation=True,
    )
tool_call_eval["score"] = (tool_call_eval.label == "correct").astype(int)
```

要点：

- **`suppress_tracing()`** 包住整个评估调用——不然 Judge 自己的 OpenAI 调用也会被自动埋点污染项目数据
- **`rails`** 把模型输出强制收敛到指定标签（避免大小写、变体）
- **`provide_explanation=True`** 让 Judge 多产出一段解释，便于排错
- 计算一个 0/1 的 **score** 列，便于 Phoenix UI 显示百分比

### 第 3 步：回写 Phoenix

```python
px.Client().log_evaluations(
    SpanEvaluations(eval_name="Tool Calling Eval", dataframe=tool_call_eval),
)
```

刷新 Phoenix，你会看到顶部多了 `Tool Calling Eval` 的整体百分比。点进任意 Router Span，**Feedback** Tab 里能看到标签 + 解释。还能在 Spans 视图按"Eval = Tool Calling Eval & 标签 = incorrect"过滤，专门看错例。

## 评估 2：可视化工具的代码可运行性（Code-based）

```python
query = (
    SpanQuery()
    .where("name == 'generate_visualization'")
    .select(generated_code="output.value")
)
codegen_df = px.Client().query_spans(query, project_name=PROJECT_NAME)

def code_is_runnable(output: str) -> bool:
    output = output.strip().replace("```python", "").replace("```", "")
    try:
        exec(output)
        return True
    except Exception:
        return False

codegen_df["label"] = codegen_df.generated_code.apply(
    lambda c: "runnable" if code_is_runnable(c) else "not_runnable"
)
codegen_df["score"] = (codegen_df.label == "runnable").astype(int)

px.Client().log_evaluations(
    SpanEvaluations(eval_name="Runnable Code Eval", dataframe=codegen_df),
)
```

> 完全不用 LLM——简单跑一遍 `exec` 看是否抛错。

## 评估 3：分析清晰度（自定义 LLM-as-a-judge）

Phoenix 里没有现成的 "Clarity" 模板，自己写一个：

```python
CLARITY_LLM_JUDGE_PROMPT = """
In this task, you will be presented with a query and an answer. Your objective is to
evaluate the clarity of the answer in addressing the query...

Query: {query}
Answer: {response}

Respond with a single word, either "clear" or "unclear".
"""
```

导出顶层 Agent Span（包含最终输出）：

```python
query = (
    SpanQuery()
    .where("name == 'AgentRun'")
    .select(query="input.value", response="output.value")
)
clarity_df = px.Client().query_spans(query, project_name=PROJECT_NAME)

with suppress_tracing():
    clarity_eval = llm_classify(
        dataframe=clarity_df,
        template=CLARITY_LLM_JUDGE_PROMPT,
        rails=["clear", "unclear"],
        model=OpenAIModel(model="gpt-4o"),
        provide_explanation=True,
    )
clarity_eval["score"] = (clarity_eval.label == "clear").astype(int)

px.Client().log_evaluations(
    SpanEvaluations(eval_name="Response Clarity", dataframe=clarity_eval),
)
```

## 评估 4：SQL 生成正确性（自定义 LLM-as-a-judge）

只挑出 SQL 生成那一类 LLM 调用——可以**字符串过滤**：

```python
query = (
    SpanQuery()
    .where("span_kind == 'LLM' and 'Generate a SQL query' in input.value")
    .select(question="input.value", sql_generated="output.value")
)
```

写一个 SQL 评估 Prompt，让 Judge 判断"该 SQL 是否能回答用户问题"，跑 `llm_classify` 后 `log_evaluations` 回写即可。

> **设计评估时最难的一步往往是"过滤出正确的那批 Span"**——`SpanQuery` 可以基于任意属性、字符串包含、span 名称、span_kind 等做组合过滤。

## 小结

至此你为智能体的每个核心部位都配了至少一个评估器：

- Router：`Tool Calling Eval`
- Lookup 工具：`SQL Generation Eval`
- 分析工具：`Response Clarity`
- 可视化工具：`Runnable Code Eval`

这些数字虽然只是方向性的，但已经能让你判断各种查询下智能体的表现差异，为接下来的"轨迹评估"和"结构化实验"打好底。
