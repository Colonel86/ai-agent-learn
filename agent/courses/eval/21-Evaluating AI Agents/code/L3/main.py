"""L3 · Lab 1: 构建数据分析智能体 (本地化: DeepSeek + openai 2.x)

课程原版: gpt-4o-mini + client.beta.chat.completions.parse(json_schema)。
本地化差异:
- 模型换 DeepSeek (openai 2.x SDK, 兼容 API)
- DeepSeek 不支持 json_schema → 图表配置改走 json_object + pydantic 手动校验
- exec 画图代码时 plt.show() 落盘为 chart_demo.png

运行: cd L3 && ../.venv/bin/python main.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import duckdb
import pandas as pd
from pydantic import BaseModel, Field

from local_stack import banner, clip, ds_chat, run_chart_code, MODEL

LESSON_DIR = Path(__file__).resolve().parent
TRANSACTION_DATA_FILE_PATH = str(LESSON_DIR / "data/Store_Sales_Price_Elasticity_Promotions_Data.parquet")

# ---------------------------------------------------------------- 工具 1: SQL 查数

SQL_GENERATION_PROMPT = """
Generate an SQL query based on a prompt. Do not reply with anything besides the SQL query.
The prompt is: {prompt}

The available columns are: {columns}
The table name is: {table_name}
"""


def generate_sql_query(prompt: str, columns: list, table_name: str) -> str:
    """Generate an SQL query based on a prompt"""
    formatted_prompt = SQL_GENERATION_PROMPT.format(
        prompt=prompt, columns=columns, table_name=table_name
    )
    response = ds_chat(messages=[{"role": "user", "content": formatted_prompt}])
    return response.choices[0].message.content


def lookup_sales_data(prompt: str) -> str:
    """Implementation of sales data lookup from parquet file using SQL"""
    try:
        table_name = "sales"
        df = pd.read_parquet(TRANSACTION_DATA_FILE_PATH)
        duckdb.sql(f"CREATE TABLE IF NOT EXISTS {table_name} AS SELECT * FROM df")

        sql_query = generate_sql_query(prompt, df.columns, table_name)
        sql_query = sql_query.strip().replace("```sql", "").replace("```", "")

        result = duckdb.sql(sql_query).df()
        return result.to_string()
    except Exception as e:
        return f"Error accessing data: {str(e)}"


# ---------------------------------------------------------------- 工具 2: 数据分析

DATA_ANALYSIS_PROMPT = """
Analyze the following data: {data}
Your job is to answer the following question: {prompt}
"""


def analyze_sales_data(prompt: str, data: str) -> str:
    """Implementation of AI-powered sales data analysis"""
    formatted_prompt = DATA_ANALYSIS_PROMPT.format(data=data, prompt=prompt)
    response = ds_chat(messages=[{"role": "user", "content": formatted_prompt}])
    analysis = response.choices[0].message.content
    return analysis if analysis else "No analysis could be generated"


# ---------------------------------------------------------------- 工具 3: 可视化代码生成

CHART_CONFIGURATION_PROMPT = """
Generate a chart configuration based on this data: {data}
The goal is to show: {visualization_goal}

Respond with a JSON object with exactly these keys:
chart_type, x_axis, y_axis, title
"""


class VisualizationConfig(BaseModel):
    chart_type: str = Field(..., description="Type of chart to generate")
    x_axis: str = Field(..., description="Name of the x-axis column")
    y_axis: str = Field(..., description="Name of the y-axis column")
    title: str = Field(..., description="Title of the chart")


def extract_chart_config(data: str, visualization_goal: str) -> dict:
    """结构化输出: DeepSeek 无 json_schema, 用 json_object 模式 + pydantic 校验"""
    formatted_prompt = CHART_CONFIGURATION_PROMPT.format(
        data=data, visualization_goal=visualization_goal
    )
    try:
        response = ds_chat(
            messages=[{"role": "user", "content": formatted_prompt}],
            response_format={"type": "json_object"},
        )
        content = VisualizationConfig.model_validate_json(response.choices[0].message.content)
        return {
            "chart_type": content.chart_type,
            "x_axis": content.x_axis,
            "y_axis": content.y_axis,
            "title": content.title,
            "data": data,
        }
    except Exception:
        return {
            "chart_type": "line",
            "x_axis": "date",
            "y_axis": "value",
            "title": visualization_goal,
            "data": data,
        }


CREATE_CHART_PROMPT = """
Write python code to create a chart based on the following configuration.
Only return the code, no other text.
config: {config}
"""


def create_chart(config: dict) -> str:
    """Create a chart based on the configuration"""
    formatted_prompt = CREATE_CHART_PROMPT.format(config=config)
    response = ds_chat(messages=[{"role": "user", "content": formatted_prompt}])
    code = response.choices[0].message.content
    code = code.replace("```python", "").replace("```", "").strip()
    return code


def generate_visualization(data: str, visualization_goal: str) -> str:
    """Generate a visualization based on the data and goal"""
    config = extract_chart_config(data, visualization_goal)
    code = create_chart(config)
    return code


# ---------------------------------------------------------------- Router (工具 schema + 主循环)

tools = [
    {
        "type": "function",
        "function": {
            "name": "lookup_sales_data",
            "description": "Look up data from Store Sales Price Elasticity Promotions dataset",
            "parameters": {
                "type": "object",
                "properties": {
                    "prompt": {"type": "string", "description": "The unchanged prompt that the user provided."}
                },
                "required": ["prompt"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_sales_data",
            "description": "Analyze sales data to extract insights",
            "parameters": {
                "type": "object",
                "properties": {
                    "data": {"type": "string", "description": "The lookup_sales_data tool's output."},
                    "prompt": {"type": "string", "description": "The unchanged prompt that the user provided."},
                },
                "required": ["data", "prompt"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "generate_visualization",
            "description": "Generate Python code to create data visualizations",
            "parameters": {
                "type": "object",
                "properties": {
                    "data": {"type": "string", "description": "The lookup_sales_data tool's output."},
                    "visualization_goal": {"type": "string", "description": "The goal of the visualization."},
                },
                "required": ["data", "visualization_goal"],
            },
        },
    },
]

tool_implementations = {
    "lookup_sales_data": lookup_sales_data,
    "analyze_sales_data": analyze_sales_data,
    "generate_visualization": generate_visualization,
}

SYSTEM_PROMPT = """
You are a helpful assistant that can answer questions about the Store Sales Price Elasticity Promotions dataset.
"""


def handle_tool_calls(tool_calls, messages):
    for tool_call in tool_calls:
        function = tool_implementations[tool_call.function.name]
        function_args = json.loads(tool_call.function.arguments)
        result = function(**function_args)
        messages.append({"role": "tool", "content": clip(result), "tool_call_id": tool_call.id})
    return messages


def run_agent(messages):
    if isinstance(messages, str):
        messages = [{"role": "user", "content": messages}]
    if not any(isinstance(m, dict) and m.get("role") == "system" for m in messages):
        messages.insert(0, {"role": "system", "content": SYSTEM_PROMPT})

    while True:
        print("  -> Router 调用 DeepSeek ...")
        response = ds_chat(messages=messages, tools=tools)
        message = response.choices[0].message
        messages.append(message.model_dump(exclude_none=True))
        tool_calls = message.tool_calls
        if tool_calls:
            print(f"  -> 工具调用: {[tc.function.name for tc in tool_calls]}")
            messages = handle_tool_calls(tool_calls, messages)
        else:
            print("  -> 无工具调用, 返回最终回答")
            return message.content


def main():
    banner("①", f"工具 1: SQL 查数 (duckdb + {MODEL} 生成 SQL)")
    example_data = lookup_sales_data("Show me all the sales for store 1320 on November 1st, 2021")
    print(example_data[:800])

    banner("②", "工具 2: LLM 数据分析")
    print(analyze_sales_data(prompt="what trends do you see in this data", data=example_data)[:800])

    banner("③", "工具 3: 可视化代码生成 (json_object 结构化输出 + 代码生成)")
    code = generate_visualization(
        example_data,
        "A bar chart of sales by product SKU. Put the product SKU on the x-axis and the sales on the y-axis.",
    )
    print(code)
    chart_path = str(LESSON_DIR / "chart_demo.png")
    if run_chart_code(code, chart_path):
        print(f"  [图已保存: {chart_path}]")

    banner("④", "组装 Router: 工具 schema + while 循环, 端到端跑一问")
    result = run_agent(
        "Show me the code for graph of sales by store in Nov 2021, and tell me what trends you see."
    )
    print("\n===== 最终回答 =====\n")
    print(result)


if __name__ == "__main__":
    main()
