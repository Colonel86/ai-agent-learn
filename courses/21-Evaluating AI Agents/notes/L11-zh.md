# L11：把所有评估编排进一个大实验

本节把之前的所有评估器拼装进同一个 `run_experiment` 调用，实现"一次跑、一次评、一次对比"的迭代节奏。

## 准备

```python
import phoenix as px
from phoenix.evals import OpenAIModel, llm_classify, TOOL_CALLING_PROMPT_TEMPLATE
from phoenix.experiments import run_experiment, evaluate_experiment
from phoenix.experiments.evaluators import create_evaluator
from utils import (
    get_phoenix_endpoint, run_agent, tools,
    process_messages, update_sql_gen_prompt,
)

eval_model = OpenAIModel(model="gpt-4o")
px_client = px.Client()
```

## 数据集：同时携带多种 Ground Truth

测试用例既有问题，也带着**预期的 SQL 结果**与**预期 SQL 文本**，方便后面 SQL 工具的 Code-based 评估：

```python
overall_experiment_questions = [
    {"question": "What was the most popular product SKU?",
     "sql_result": "...52262.0...",
     "sql_generated": "```sql\nSELECT SKU_Coded, SUM(Qty_Sold) ... ```"},
    # ... 共 7 条
]
overall_experiment_df = pd.DataFrame(overall_experiment_questions)

dataset = px_client.upload_dataset(
    dataframe=overall_experiment_df,
    dataset_name=f"overall_experiment_inputs-{now}",
    input_keys=["question"],
    output_keys=["sql_result", "sql_generated"],
)
```

> 没有给 `analyze_sales_data` 和 `generate_visualization` 写 ground truth——因为这两步用 LLM-as-a-judge 评估，不需要预期输出。

## 评估器一：Router 函数调用

```python
def function_calling_eval(input, output) -> float:
    if output is None:
        return 0.0
    tool_calls = [t for m in output["messages"] for t in m.get("tool_calls", [])]
    df = pd.DataFrame({
        "question": [input["question"]] * len(tool_calls),
        "tool_call": tool_calls,
    })
    eval_df = llm_classify(
        dataframe=df,
        template=TOOL_CALLING_PROMPT_TEMPLATE.template.replace(
            "{tool_definitions}", json.dumps(tools)
        ),
        rails=["correct", "incorrect"],
        model=eval_model,
        provide_explanation=True,
    )
    return (eval_df.label == "correct").astype(int).mean()
```

返回 mean 是因为**一次回答可能调用了多个工具**，需要汇总成一个分数。

## 评估器二：SQL Result 比对（Code-based）

```python
def evaluate_sql_result(output, expected) -> bool:
    sql_result = None
    for m in output["messages"]:
        for t in m.get("tool_calls", []):
            if t["name"] == "lookup_sales_data":
                sql_result = t["response"]
    if sql_result is None:
        return False
    # 抽出数字做比对，避免列名差异
    actual_nums = re.findall(r"\d+\.?\d*", sql_result)
    expected_nums = re.findall(r"\d+\.?\d*", expected["sql_result"])
    return actual_nums == expected_nums
```

> 抽数字比对是为了规避**SQL 列名差异**——只要数值结果一样就算对。

## 评估器三：分析清晰度（LLM-as-a-judge）

```python
def evaluate_clarity(output, input) -> bool:
    df = pd.DataFrame({"query": [input["question"]], "response": [output["final_output"]]})
    eval_df = llm_classify(
        dataframe=df,
        template=CLARITY_LLM_JUDGE_PROMPT,
        rails=["clear", "unclear"],
        model=eval_model,
        provide_explanation=True,
    )
    return eval_df.label.iloc[0] == "clear"
```

## 评估器四：实体正确性（LLM-as-a-judge）

确保智能体没把 `SKU` 列错叫成 `store_id` 之类：

```python
def evaluate_entity_correctness(output, input) -> bool:
    ...
    eval_df = llm_classify(
        dataframe=df,
        template=ENTITY_CORRECTNESS_LLM_JUDGE_PROMPT,
        rails=["correct", "incorrect"],
        model=eval_model,
    )
    return eval_df.label.iloc[0] == "correct"
```

## 评估器五：代码可运行性（Code-based）

```python
def code_is_runnable(output) -> bool:
    code = None
    for m in output["messages"]:
        for t in m.get("tool_calls", []):
            if t["name"] == "generate_visualization":
                code = t["response"]
    if not code:
        return False
    code = code.strip().replace("```python", "").replace("```", "")
    try:
        exec(code)
        return True
    except Exception:
        return False
```

## Task：跑智能体并整理输出

```python
def run_agent_task(example):
    messages = [{"role": "user", "content": example.input["question"]}]
    messages = run_agent_messages(messages)
    return {
        "messages": process_messages(messages),
        "final_output": messages[-1]["content"],
    }
```

## 跑大实验

```python
experiment = run_experiment(
    dataset=dataset,
    task=run_agent_task,
    evaluators=[
        function_calling_eval,
        evaluate_sql_result,
        evaluate_clarity,
        evaluate_entity_correctness,
        code_is_runnable,
    ],
    experiment_name="Overall Experiment",
)
```

7 个用例 × 5 个评估器 = 35 次评估。Phoenix UI 里能看到每条用例每个评估维度的得分，一眼定位短板。

## 迭代：改了 Prompt 再跑一次

比方说 SQL 评估很糟，那就改 SQL 生成 Prompt：

```python
NEW_SQL_PROMPT = """
... think step-by-step before you respond ...
"""
update_sql_gen_prompt(NEW_SQL_PROMPT)

run_experiment(
    dataset=dataset,
    task=run_agent_task,
    evaluators=[...],
    experiment_name="Overall Experiment V2 - SQL prompt tweak",
)
```

Phoenix 会把 V2 和 V1 并排显示——这就是 **EDD 的"苹果对苹果"对比**。

> 7 条用例的样本量很小，单次实验结论别太当真。**多跑几次取统计稳健性**。

## 不写代码也能改：Prompt Playground

数据集页面有 "Playground" 按钮，能把数据集直接带进交互式 Prompt 测试界面：

- 复制 SQL 生成 Prompt 进去
- 用 `{question}` 引用数据集列
- 用 **Compare** 按钮并排对比两个 Prompt 在同一批输入上的表现
- 切换不同模型（如 GPT-4o-mini）

适合**快速实验 Prompt**，确定方向后再把改动落到代码里。

## 小结

EDD 的关键产物就是这样的 HUD：每次改动都能定量比较；每次回归都能精准定位；Prompt 迭代既可在代码里、也可在 Playground 里完成。
