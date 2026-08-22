"""演示 1: trace 是可程序化查询的数据集 — 同一批 span, 按不同条件切出不同的'表'"""
import pandas as pd
from phoenix.client import Client
from phoenix.client.types.spans import SpanQuery

pd.set_option("display.max_colwidth", 60)
pd.set_option("display.width", 200)

client = Client(base_url="http://localhost:6006")
PROJECT = "evaluating-agent"

print("=" * 70)
print("查法① 宽条件: 项目里所有 span (只取 span_kind 一列, 看全貌)")
df = client.spans.get_spans_dataframe(
    query=SpanQuery().where("span_kind in ('AGENT','CHAIN','LLM','TOOL')").select("span_kind"),
    project_name=PROJECT,
    timeout=120,
)
print(f"   -> DataFrame: {df.shape[0]} 行 x {df.shape[1]} 列")
print(f"   -> 索引是什么: {df.index.name}, 例如 {df.index[0]}")
print(f"   -> span 种类分布:\n{df.iloc[:, -1].value_counts().to_string()}")

print()
print("=" * 70)
print("查法② where 过滤 + select 投影: 只要 AGENT span 的问题和最终回答")
q = SpanQuery().where("span_kind == 'AGENT'").select("input.value", "output.value")
agent_df = client.spans.get_spans_dataframe(query=q, project_name=PROJECT, timeout=120)
print(f"   -> {agent_df.shape[0]} 行 x {agent_df.shape[1]} 列 (列被裁成 select 的两个)")
print(agent_df.head(3).to_string())

print()
print("=" * 70)
print("查法③ 按 span 名字过滤: 只要画图工具的输出 (= Runnable Code Eval 的输入)")
q = SpanQuery().where("name == 'generate_visualization'").select("output.value")
viz_df = client.spans.get_spans_dataframe(query=q, project_name=PROJECT, timeout=120)
print(f"   -> {viz_df.shape[0]} 行")
print("   -> 第一行 output.value 前 120 字符:")
print("      " + str(viz_df.iloc[0, 0])[:120].replace("\n", " / "))

print()
print("=" * 70)
print("查法④ 字符串包含: 只要提示词里带 'Generate an SQL query' 的 LLM span")
q = SpanQuery().where("span_kind == 'LLM' and 'Generate an SQL query' in input.value")
sql_df = client.spans.get_spans_dataframe(query=q, project_name=PROJECT, timeout=120)
print(f"   -> {sql_df.shape[0]} 行 (同一批 trace, 换个条件就切出另一张表)")
