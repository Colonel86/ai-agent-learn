"""L3 · 扩展数据能力: 本地数据 agent 替代 Snowflake Cortex Agent

课程原版: Cortex Analyst(text2sql, 语义模型) + Cortex Search(会议纪要检索),
经 cortex_agent_service 一次调用返回 text/sql/citations。
本地化: 同构拆成两个工具挂在 ReAct agent 上 ——
  query_deals_sql       (DeepSeek text2sql -> sqlite sales_deals 表)
  search_meeting_notes  (fastembed 本地向量检索, 5 篇合成销售纪要)

运行: cd L3 && ../.venv/bin/python main.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import sales_data
from local_stack import banner
from workflow import build_graph, data_agent, run_query


def main():
    banner("①", "探索数据: 结构化 deals 表 + 非结构化会议纪要 (均为本地合成)")
    sales_data.build_db()
    cols, rows = sales_data.run_sql("SELECT deal_id, customer, deal_value_usd, status FROM sales_deals")
    print("  " + " | ".join(cols))
    for r in rows:
        print("  " + " | ".join(map(str, r)))
    first = next(iter(sales_data.MEETING_NOTES.items()))
    print(f"\n  纪要示例 [{first[0]}]: {first[1][:120]}...")

    banner("②", "单独调数据 agent (ReAct: text2sql 工具 + 纪要检索工具)")
    resp = data_agent.invoke({"messages": "What are our top 3 deals by value?"})
    print(resp["messages"][-1].content)

    banner("③", "整图运行: pending deals + 监管变化 + 纪要提炼价值主张 (跨两库+web)")
    graph = build_graph()
    run_query(
        graph,
        "Identify our pending deals, research if they may be experiencing regulatory changes, "
        "and using the meeting notes for each customer, provide a new value proposition for each "
        "given the regulatory changes.",
    )

    banner("④", "整图运行: 会议纪要共同主题")
    run_query(graph, "Is there a common theme across our meeting notes?")

    banner("⑤", "本课结论")
    print("""  数据 agent 的价值: 把「懂业务数据」封装成一个可被编排的能力 ——
  planner 不需要知道 SQL 还是向量检索, 只需要知道「问数据找它」""")


if __name__ == "__main__":
    main()
