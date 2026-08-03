"""L11 · Lab 5: 把所有评估编排进一个大实验 (本地化: arize-phoenix-client 2.x + DeepSeek judge)

一个数据集(带期望输出) + 5 个评估器一次挂到实验上:
① function_calling_eval   Router 选工具 (LLM judge)
② evaluate_sql_result     SQL 结果与期望对数字 (代码)
③ evaluate_clarity        回答清晰度 (LLM judge)
④ evaluate_entity_correctness 实体正确性 (LLM judge)
⑤ code_is_runnable        画图代码可运行 (代码)

然后演示 EDD: 改 SQL 生成 prompt -> 重跑实验 -> 在 Phoenix UI 对比 v1/v2。

运行: cd L11 && ../.venv/bin/python main.py  (需要本地 phoenix serve 已启动)
"""

import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd

from local_stack import EVAL_KWARGS, PHOENIX_ENDPOINT, banner, make_eval_llm, phoenix_client, run_chart_code

from utils import get_sql_gen_prompt, process_messages, run_agent, tools, update_sql_gen_prompt  # noqa: E402

from phoenix.evals.evaluators import ClassificationEvaluator  # noqa: E402

px_client = phoenix_client()
eval_llm = make_eval_llm()

LESSON_DIR = Path(__file__).resolve().parent

# ---------------------------------------------------------------- 数据集 (带期望输出)

overall_experiment_questions = [
    {
        "question": "What was the most popular product SKU?",
        "sql_result": "   SKU_Coded  Total_Qty_Sold 0    6200700         52262.0",
        "sql_generated": "```sql\nSELECT SKU_Coded, SUM(Qty_Sold) AS Total_Qty_Sold\nFROM sales\nGROUP BY SKU_Coded\nORDER BY Total_Qty_Sold DESC\nLIMIT 1;\n```",
    },
    {
        "question": "What was the total revenue across all stores?",
        "sql_result": "   Total_Revenue 0   1.327264e+07",
        "sql_generated": "```sql\nSELECT SUM(Total_Sale_Value) AS Total_Revenue\nFROM sales;\n```",
    },
    {
        "question": "Which store had the highest sales volume?",
        "sql_result": "   Store_Number  Total_Sales_Volume 0          2970             59322.0",
        "sql_generated": "```sql\nSELECT Store_Number, SUM(Total_Sale_Value) AS Total_Sales_Volume\nFROM sales\nGROUP BY Store_Number\nORDER BY Total_Sales_Volume DESC\nLIMIT 1;\n```",
    },
    {
        "question": "Create a bar chart showing total sales by store",
        "sql_result": "    Store_Number    Total_Sales 0            880  420302.088397 1           1650  580443.007953 2           4180  272208.118542 3            550  229727.498752 4           1100  497509.528013 5           3300  619660.167018 6           3190  335035.018792 7           2970  836341.327191 8           3740  359729.808228 9           2530  324046.518720 10          4400   95745.620250 11          1210  508393.767785 12           330  370503.687331 13          2750  453664.808068 14          1980  242290.828499 15          1760  350747.617798 16          3410  410567.848126 17           990  378433.018639 18          4730  239711.708869 19          4070  322307.968330 20          3080  495458.238811 21          2090  309996.247965 22          1320  592832.067579 23          2640  308990.318559 24          1540  427777.427815 25          4840  389056.668316 26          2860  132320.519487 27          2420  406715.767402 28           770  292968.918642 29          3520  145701.079372 30           660  343594.978075 31          3630  405034.547846 32          2310  412579.388504 33          2200  361173.288199 34          1870  401070.997685",
        "sql_generated": "```sql\nSELECT Store_Number, SUM(Total_Sale_Value) AS Total_Sales\nFROM sales\nGROUP BY Store_Number;\n```",
    },
    {
        "question": "What percentage of items were sold on promotion?",
        "sql_result": "   Promotion_Percentage 0              0.625596",
        "sql_generated": "```sql\nSELECT \n    (SUM(CASE WHEN On_Promo = 'Yes' THEN 1 ELSE 0 END) * 100.0) / COUNT(*) AS Promotion_Percentage\nFROM \n    sales;\n```",
    },
    {
        "question": "What was the average transaction value?",
        "sql_result": "   Average_Transaction_Value 0                  19.018132",
        "sql_generated": "```sql\nSELECT AVG(Total_Sale_Value) AS Average_Transaction_Value\nFROM sales;\n```",
    },
    {
        "question": "Create a line chart showing sales in 2021",
        "sql_result": "  sale_month  total_quantity_sold  total_sales_value 0 2021-11-01              43056.0      499984.428193 1 2021-12-01              75724.0      910982.118423",
        "sql_generated": "```sql\nSELECT MONTH(Sold_Date) AS Month, SUM(Total_Sale_Value) AS Total_Sales\nFROM sales\nWHERE YEAR(Sold_Date) = 2021\nGROUP BY MONTH(Sold_Date)\nORDER BY MONTH(Sold_Date);\n```",
    },
]

# ---------------------------------------------------------------- LLM judge 模板

TOOL_CALLING_PROMPT = """
You are an evaluation assistant evaluating questions and tool calls to
determine whether the tool called would answer the question. It is your
job to decide whether the agent chose the right tool to call from the
tool definitions below.

    [BEGIN DATA]
    [Question]: {question}
    [Tool Called]: {tool_call}
    [END DATA]

"incorrect" means that the chosen tool would not answer the question.
"correct" means the correct tool call was chosen for the question.

    [Tool Definitions]: {tool_definitions}
"""

CLARITY_LLM_JUDGE_PROMPT = """
In this task, you will be presented with a query and an answer. Your objective is to evaluate the clarity
of the answer in addressing the query. A clear response is one that is precise, coherent, and directly
addresses the query without introducing unnecessary complexity or ambiguity. An unclear response is one
that is vague, disorganized, or difficult to understand, even if it may be factually correct.

"clear" indicates that the answer is well-structured, easy to understand, and
appropriately addresses the query. "unclear" indicates that the answer is ambiguous, poorly organized, or
not effectively communicated.

[BEGIN DATA]
Query: {query}
Answer: {response}
[END DATA]
"""

ENTITY_CORRECTNESS_LLM_JUDGE_PROMPT = """
In this task, you will be presented with a query and an answer. Your objective is to determine whether all
the entities mentioned in the answer are correctly identified and accurately match those in the query. An
entity refers to any specific person, place, organization, date, or other proper noun.

"correct" indicates that all entities mentioned in the answer match those in the
query and are properly identified. "incorrect" indicates that the answer contains errors or mismatches in
the entities referenced compared to the query.

[BEGIN DATA]
Query: {query}
Answer: {response}
[END DATA]
"""

tool_call_judge = ClassificationEvaluator(
    name="tool_calling",
    llm=eval_llm,
    prompt_template=TOOL_CALLING_PROMPT,
    choices={"correct": 1.0, "incorrect": 0.0},
    **EVAL_KWARGS,
)
clarity_judge = ClassificationEvaluator(
    name="clarity",
    llm=eval_llm,
    prompt_template=CLARITY_LLM_JUDGE_PROMPT,
    choices={"clear": 1.0, "unclear": 0.0},
    **EVAL_KWARGS,
)
entity_judge = ClassificationEvaluator(
    name="entity_correctness",
    llm=eval_llm,
    prompt_template=ENTITY_CORRECTNESS_LLM_JUDGE_PROMPT,
    choices={"correct": 1.0, "incorrect": 0.0},
    **EVAL_KWARGS,
)

TOOL_DEFINITIONS_JSON = json.dumps(tools, indent=2)

# ---------------------------------------------------------------- 5 个评估器


def function_calling_eval(input, output) -> float:
    """评估器 ①: Router 每次选工具是否正确, 取均值 (LLM judge)"""
    if output is None:
        return 0.0
    function_calls = output.get("tool_calls")
    if not function_calls:
        return 0.0
    scores = []
    for tool_call in function_calls:
        result = tool_call_judge.evaluate(
            eval_input={
                "question": input.get("question"),
                "tool_call": tool_call,
                "tool_definitions": TOOL_DEFINITIONS_JSON,
            }
        )
        scores.append(result[0].score or 0.0)
    return sum(scores) / len(scores)


def evaluate_sql_result(output, expected) -> bool:
    """评估器 ②: lookup_sales_data 的结果和期望结果对数字 (代码评估)"""
    if output is None:
        return False
    sql_result = output.get("tool_responses")
    if not sql_result:
        return True
    sql_result = next((r for r in sql_result if r.get("tool_name") == "lookup_sales_data"), None)
    if not sql_result:
        return True
    sql_result = sql_result.get("tool_response", "") or ""

    result_nums = "".join(filter(str.isdigit, sql_result))
    expected_nums = "".join(filter(str.isdigit, expected.get("sql_result")))
    return result_nums == expected_nums


def evaluate_clarity(output, input) -> bool:
    """评估器 ③: 最终回答清晰度 (LLM judge)"""
    if output is None:
        return False
    result = clarity_judge.evaluate(
        eval_input={"query": input.get("question"), "response": str(output.get("final_output"))}
    )
    return result[0].label == "clear"


def evaluate_entity_correctness(output, input) -> bool:
    """评估器 ④: 回答中的实体与问题是否一致 (LLM judge)"""
    if output is None:
        return False
    result = entity_judge.evaluate(
        eval_input={"query": input.get("question"), "response": str(output.get("final_output"))}
    )
    return result[0].label == "correct"


def code_is_runnable(output) -> bool:
    """评估器 ⑤: generate_visualization 生成的代码能不能跑 (代码评估)"""
    if output is None:
        return False
    generated_code = output.get("tool_responses")
    if not generated_code:
        return True
    generated_code = next(
        (r for r in generated_code if r.get("tool_name") == "generate_visualization"), None
    )
    if not generated_code:
        return True
    generated_code = (generated_code.get("tool_response", "") or "").strip()
    generated_code = generated_code.replace("```python", "").replace("```", "")
    return run_chart_code(generated_code, str(LESSON_DIR / "chart_eval_tmp.png"))


def run_agent_task(input):
    """实验 task: 跑 agent, 把轨迹拆成结构化输出供评估器用"""
    messages = [{"role": "user", "content": input.get("question")}]
    ret = run_agent(messages)
    return process_messages(ret)


EVALUATORS = [
    function_calling_eval,
    evaluate_sql_result,
    evaluate_clarity,
    evaluate_entity_correctness,
    code_is_runnable,
]


def main():
    banner("①", f"上传数据集: {len(overall_experiment_questions)} 问 + 期望 SQL/结果")
    overall_experiment_df = pd.DataFrame(overall_experiment_questions)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    dataset = px_client.datasets.create_dataset(
        name=f"overall_experiment_inputs-{now}",
        dataframe=overall_experiment_df,
        input_keys=["question"],
        output_keys=["sql_result", "sql_generated"],
    )
    print(f"  dataset id={dataset.id}, {dataset.example_count} 条")

    banner("②", "跑综合实验 v1: 1 个 task + 5 个评估器")
    px_client.experiments.run_experiment(
        dataset=dataset,
        task=run_agent_task,
        evaluators=EVALUATORS,
        experiment_name="Overall Experiment",
        experiment_description="Evaluating the overall experiment",
        timeout=600,
    )

    banner("③", "EDD: 改 SQL 生成 prompt (加一句 Think before you respond)")
    new_prompt = """
Generate an SQL query based on a prompt.
Do not reply with anything besides the SQL query.
The prompt is: {prompt}

The available columns are: {columns}
The table name is: {table_name}

Think before you respond.
"""
    update_sql_gen_prompt(new_prompt)
    print(get_sql_gen_prompt()[:300])

    banner("④", "重跑综合实验 v2 (同一数据集, 同 5 个评估器)")
    px_client.experiments.run_experiment(
        dataset=dataset,
        task=run_agent_task,
        evaluators=EVALUATORS,
        experiment_name="Overall Experiment v2",
        experiment_description="Evaluating the overall experiment, with changes to sql prompt",
        timeout=600,
    )

    banner("⑤", "完成")
    print(f"  到 {PHOENIX_ENDPOINT}datasets 打开该数据集, 并排对比 v1/v2 两次实验的 5 项分数")


if __name__ == "__main__":
    main()
