# L3：动手构建数据分析智能体

本节是代码实操：从零写出整个数据分析智能体——三个工具 + 一个路由器，并跑通端到端。

## 准备：导入依赖与初始化客户端

```python
from openai import OpenAI
import pandas as pd
import json
import duckdb
from pydantic import BaseModel, Field
from IPython.display import Markdown
from helper import get_openai_api_key

client = OpenAI(api_key=get_openai_api_key())
MODEL = "gpt-4o-mini"
```

其中 **`duckdb`** 是关键——它能把一个 pandas DataFrame **就地当成 SQL 数据库使用**，无需启动外部数据库进程，非常适合在 Notebook 里模拟数据查询场景。

## 工具一：`lookup_sales_data`——数据查询

模拟数据来自一个 parquet 文件 `store_sales_price_elasticity_promotions_data.parquet`，包含每次销售的 SKU、促销标记、价格、成本等字段。

### 第 1 步：用 Prompt 生成 SQL

```python
SQL_GENERATION_PROMPT = """
Generate a SQL query based on a prompt. Do not reply with anything besides the SQL query.
The prompt is: {prompt}

The available columns are: {columns}
The table name is: {table_name}
"""

def generate_sql_query(prompt: str, columns: list, table_name: str) -> str:
    formatted_prompt = SQL_GENERATION_PROMPT.format(
        prompt=prompt, columns=columns, table_name=table_name
    )
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": formatted_prompt}],
    )
    return response.choices[0].message.content
```

把"可用列"和"表名"也注入 Prompt——LLM 必须知道这些才能写出合法 SQL。

### 第 2 步：组合成工具函数

```python
def lookup_sales_data(prompt: str) -> str:
    try:
        # 把 parquet 读入 DataFrame，再让 duckdb 在内存中建表
        df = pd.read_parquet(SALES_DATA_FILE_PATH)
        duckdb.sql("CREATE TABLE IF NOT EXISTS sales AS SELECT * FROM df")

        sql_query = generate_sql_query(prompt, df.columns, "sales")
        # 去掉模型可能加的 ```sql 包裹
        sql_query = sql_query.strip().replace("```sql", "").replace("```", "")

        result = duckdb.sql(sql_query).df()
        return result.to_string()
    except Exception as e:
        return f"Error accessing database: {str(e)}"
```

> **小细节**：LLM 经常给 SQL 加上 ` ```sql ` 这种 Markdown 包裹，需要手动剥掉再交给 duckdb 执行。

测试一下：

```python
example_data = lookup_sales_data(
    "Show me the sales data for store 1320 on November 1st, 2021"
)
```

## 工具二：`analyze_sales_data`——分析数据

```python
DATA_ANALYSIS_PROMPT = """
Analyze the following data: {data}
Your job is to answer the following question: {prompt}
"""

def analyze_sales_data(prompt: str, data: str) -> str:
    formatted_prompt = DATA_ANALYSIS_PROMPT.format(data=data, prompt=prompt)
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": formatted_prompt}],
    )
    analysis = response.choices[0].message.content
    return analysis if analysis else "No analysis could be generated"
```

> 在智能体里**容错（Error Checking）比一般代码更重要**——某一步崩了不能让整个智能体级联崩溃。

## 工具三：`generate_visualization`——两步生成图表

### 第 1 步：抽取 Chart Config（结构化输出）

利用 Pydantic + OpenAI **Structured Outputs** 确保返回符合 schema：

```python
class VisualizationConfig(BaseModel):
    chart_type: str = Field(..., description="Type of chart to generate")
    x_axis: str = Field(..., description="Name of the x-axis column")
    y_axis: str = Field(..., description="Name of the y-axis column")
    title: str = Field(..., description="Title of the chart")

def extract_chart_config(data: str, visualization_goal: str) -> dict:
    formatted_prompt = CHART_CONFIGURATION_PROMPT.format(
        data=data, visualization_goal=visualization_goal
    )
    response = client.beta.chat.completions.parse(
        model=MODEL,
        messages=[{"role": "user", "content": formatted_prompt}],
        response_format=VisualizationConfig,
    )
    content = response.choices[0].message.content
    return {...}  # 转成 dict
```

### 第 2 步：基于 config 生成 Python 代码

```python
def create_chart(config: dict) -> str:
    formatted_prompt = CREATE_CHART_PROMPT.format(config=config)
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": formatted_prompt}],
    )
    code = response.choices[0].message.content
    code = code.replace("```python", "").replace("```", "")
    return code

def generate_visualization(data: str, visualization_goal: str) -> str:
    config = extract_chart_config(data, visualization_goal)
    code = create_chart(config)
    return code
```

> **安全提醒**：本课为了简洁不在智能体里直接执行 LLM 生成的代码。生产中若需要执行，**务必放进沙箱（Sandbox）**。

## 把工具喂给路由器

OpenAI function calling 要求一个特定 JSON schema：

```python
tools = [
    {
        "type": "function",
        "function": {
            "name": "lookup_sales_data",
            "description": "Look up data from store sales data",
            "parameters": {
                "type": "object",
                "properties": {
                    "prompt": {"type": "string", "description": "..."}
                },
                "required": ["prompt"],
            },
        },
    },
    # analyze_sales_data ...
    # generate_visualization ...
]

tool_implementations = {
    "lookup_sales_data": lookup_sales_data,
    "analyze_sales_data": analyze_sales_data,
    "generate_visualization": generate_visualization,
}
```

> **描述（description）是生死线**——描述不准，路由器要么不调用，要么调用错误。构建智能体时，反复打磨工具描述与参数描述常常是最花时间的事。

## 路由器：循环驱动

```python
SYSTEM_PROMPT = "You are a helpful assistant that can answer questions about the data."

def run_agent(messages):
    # 兼容字符串/字典两种输入
    if isinstance(messages, str):
        messages = [{"role": "user", "content": messages}]
    # 注入 system prompt
    if not any(m.get("role") == "system" for m in messages):
        messages = [{"role": "system", "content": SYSTEM_PROMPT}] + messages

    while True:
        response = client.chat.completions.create(
            model=MODEL, messages=messages, tools=tools,
        )
        if response.choices[0].message.tool_calls:
            messages.append(response.choices[0].message.model_dump())
            messages = handle_tool_calls(response.choices[0].message.tool_calls, messages)
        else:
            return response.choices[0].message.content
```

### 处理工具调用

```python
def handle_tool_calls(tool_calls, messages):
    for tool_call in tool_calls:
        function = tool_implementations[tool_call.function.name]
        args = json.loads(tool_call.function.arguments)
        result = function(**args)
        messages.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": str(result),
        })
    return messages
```

> OpenAI 的规则：当模型返回了 `tool_call_id`，**下一轮请求里必须给出对应的 tool 角色消息**，否则报错。

## 跑一个端到端示例

```python
result = run_agent(
    "Show me the code for graph of sales by store in November 2021, "
    "and tell me what trends you see."
)
```

你会看到路由器多次循环：调用 `lookup_sales_data` → `analyze_sales_data` → `generate_visualization`，最后返回包含趋势分析与绘图代码的回答。至此，智能体已能工作——下一步就是给它加上**可观测性**与**评估**。
