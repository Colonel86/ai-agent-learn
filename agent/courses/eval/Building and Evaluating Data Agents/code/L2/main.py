"""L2 · 构建多 Agent 工作流 (planner/executor + web/chart/synthesizer)

课程原版 o3+gpt-4o+Tavily; 本地化 DeepSeek+ddgs, 结构一致:
planner 产出 JSON 计划 -> executor 逐步派发(可 replan) -> 各 agent 干活 -> 汇总。

运行: cd L2 && ../.venv/bin/python main.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from local_stack import banner
from workflow import build_graph, run_query

L2_AGENTS = ["web_researcher", "chart_generator", "chart_summarizer", "synthesizer"]


def main():
    banner("①", "构建图: planner -> executor -> {web/chart/synthesizer}")
    print("  本课 enabled_agents 不含数据 agent (cortex_researcher), L3 才启用")
    graph = build_graph()
    print("  节点:", list(graph.get_graph().nodes.keys()))

    banner("②", "跑 query 1: 查数据并画图 (web -> chart -> chart_summarizer)")
    result = run_query(
        graph,
        "Chart the current market capitalization of the top 5 banks in the US?",
        enabled_agents=L2_AGENTS,
    )

    banner("③", "跑 query 2: 纯研究问题 (web -> synthesizer)")
    result = run_query(
        graph,
        "Identify current regulatory changes for the financial services industry in the US.",
        enabled_agents=L2_AGENTS,
    )

    banner("④", "本课结论")
    print("""  planner 只管出计划(JSON), executor 只管派发与 replan 决策,
  各 agent 只做一件事 —— 职责单一是后面能逐层评估的前提""")


if __name__ == "__main__":
    main()
