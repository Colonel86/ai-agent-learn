"""L7 工具模块: 带 Phoenix 埋点的数据分析 agent (project=evaluating-agent)。

与 L5 的 agent 相同, 打包成模块供 main.py 的评估流程复用。
本地化: DeepSeek 兼容 API (见 code/local_stack.py), 结构化输出走 json_object。
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import duckdb
import pandas as pd
from pydantic import BaseModel, Field

from local_stack import PHOENIX_ENDPOINT, clip, ds_chat, ensure_phoenix

ensure_phoenix()

from openinference.instrumentation.openai import OpenAIInstrumentor
from opentelemetry.trace import StatusCode
from phoenix.otel import register

PROJECT_NAME = "evaluating-agent"

tracer_provider = register(
    project_name=PROJECT_NAME,
    endpoint=PHOENIX_ENDPOINT + "v1/traces",
)
OpenAIInstrumentor().instrument(tracer_provider=tracer_provider)
tracer = tracer_provider.get_tracer(__name__)

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
    formatted_prompt = SQL_GENERATION_PROMPT.format(
        prompt=prompt, columns=columns, table_name=table_name
    )
    response = ds_chat(messages=[{"role": "user", "content": formatted_prompt}])
    return response.choices[0].message.content


@tracer.tool()
def lookup_sales_data(prompt: str) -> str:
    """Implementation of sales data lookup from parquet file using SQL"""
    try:
        table_name = "sales"
        df = pd.read_parquet(TRANSACTION_DATA_FILE_PATH)
        duckdb.sql(f"CREATE TABLE IF NOT EXISTS {table_name} AS SELECT * FROM df")

        sql_query = generate_sql_query(prompt, df.columns, table_name)
        sql_query = sql_query.strip().replace("```sql", "").replace("```", "")

        with tracer.start_as_current_span(
            "execute_sql_query", openinference_span_kind="chain"
        ) as span:
            span.set_input(sql_query)
            result = duckdb.sql(sql_query).df()
            span.set_output(value=str(result))
            span.set_status(StatusCode.OK)

        return result.to_string()
    except Exception as e:
        return f"Error accessing data: {str(e)}"


# ---------------------------------------------------------------- 工具 2: 数据分析

DATA_ANALYSIS_PROMPT = """
Analyze the following data: {data}
Your job is to answer the following question: {prompt}
"""


@tracer.tool()
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


@tracer.chain()
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


@tracer.chain()
def create_chart(config: dict) -> str:
    """Create a chart based on the configuration"""
    formatted_prompt = CREATE_CHART_PROMPT.format(config=config)
    response = ds_chat(messages=[{"role": "user", "content": formatted_prompt}])
    code = response.choices[0].message.content
    code = code.replace("```python", "").replace("```", "").strip()
    return code


@tracer.tool()
def generate_visualization(data: str, visualization_goal: str) -> str:
    """Generate a visualization based on the data and goal"""
    config = extract_chart_config(data, visualization_goal)
    code = create_chart(config)
    return code


# ---------------------------------------------------------------- Router

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


@tracer.chain()
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
        with tracer.start_as_current_span(
            "router_call", openinference_span_kind="chain"
        ) as span:
            span.set_input(value=messages)
            response = ds_chat(messages=messages, tools=tools)
            message = response.choices[0].message
            messages.append(message.model_dump(exclude_none=True))
            tool_calls = message.tool_calls
            span.set_status(StatusCode.OK)

            if tool_calls:
                messages = handle_tool_calls(tool_calls, messages)
                span.set_output(value=tool_calls)
            else:
                span.set_output(value=message.content)
                return message.content


def start_main_span(messages):
    with tracer.start_as_current_span("AgentRun", openinference_span_kind="agent") as span:
        span.set_input(value=messages)
        ret = run_agent(messages)
        span.set_output(value=ret)
        span.set_status(StatusCode.OK)
        return ret
