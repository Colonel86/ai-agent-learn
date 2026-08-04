"""L6 · 提升 agent 的 GPA: 内联评估 + 计划 prompt 改写, v1/v2 对比

两个改进手段 (与课程一致):
1. inline_evaluation(f_context_relevance): 检索节点跑完立即评上下文相关性, 分数进 trace
2. 计划 prompt 升级: 每步加 pre_conditions / post_conditions / goal 字段

本地化说明: 课程在 TruLens dashboard 里对比 v1/v2 的 GPA;
脚本演示改为从消息轨迹构造 trace 文本、同步调 GPA provider ——
后台线程计算 trace 级 feedback 在无 dashboard 的脚本场景下完成时机不可控。

运行: cd L6 && ../.venv/bin/python main.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from langchain_core.messages import HumanMessage

import prompts
from local_stack import banner, make_tru_provider
from workflow import (
    build_graph,
    cortex_agents_research_node,
    run_query,
    web_research_node,
)

QUERY = "What are our top 3 client deals? Chart the deal value for each."
provider = make_tru_provider()
GPA_FNS = {
    "Plan Quality": "plan_quality_with_cot_reasons",
    "Plan Adherence": "plan_adherence_with_cot_reasons",
    "Execution Efficiency": "execution_efficiency_with_cot_reasons",
    "Logical Consistency": "logical_consistency_with_cot_reasons",
}


def trace_text(result) -> str:
    """把一次运行的消息轨迹压成 GPA 评估用的 trace 文本"""
    lines = [f"User Query: {result.get('user_query', '')}"]
    for m in result.get("messages", []):
        name = getattr(m, "name", None) or getattr(m, "type", "message")
        content = str(m.content)
        if len(content) > 1200:
            content = content[:1200] + " ...[truncated]"
        lines.append(f"[{name}] {content}")
    return "\n\n".join(lines)


def gpa_scores(trace: str) -> dict:
    scores = {}
    for label, fn in GPA_FNS.items():
        score, _reasons = getattr(provider, fn)(trace)
        scores[label] = round(score, 2)
        print(f"    {label}: {score:.2f}")
    return scores


def main():
    from trulens.apps.langgraph import TruGraph
    from trulens.apps.langgraph.inline_evaluations import inline_evaluation
    from trulens.core.session import TruSession

    from evals import f_context_relevance

    # 独立 DB, 不碰课程自带的 default.sqlite (预录对照数据)
    session = TruSession(database_url="sqlite:///local_demo.sqlite")
    session.reset_database()

    banner("①", "v1 基线: 原计划 prompt, 无内联评估")
    graph_v1 = build_graph()
    rec_v1 = TruGraph(graph_v1, app_name="Data agent", app_version="v1")
    with rec_v1 as recording:
        result_v1 = run_query(graph_v1, QUERY)
    print("\n  v1 GPA (同步计算):")
    scores_v1 = gpa_scores(trace_text(result_v1))

    banner("②", "改进 1: 检索节点包 inline_evaluation(context_relevance)")
    web_v2 = inline_evaluation(f_context_relevance)(web_research_node)
    data_v2 = inline_evaluation(f_context_relevance)(cortex_agents_research_node)
    print("  web_researcher / cortex_researcher 已包内联评估")

    banner("③", "改进 2: 计划 prompt 加 pre/post_conditions + goal 字段")
    _orig_plan_prompt = prompts.plan_prompt

    def patched_plan_prompt(state):
        base = _orig_plan_prompt(state).content
        insertion = (
            '"action": "string",\n'
            '            "pre_conditions": ["string", ...],\n'
            '            "post_conditions": ["string", ...],\n'
            '            "goal": "string",'
        )
        return HumanMessage(content=base.replace('"action": "string",', insertion))

    prompts.plan_prompt = patched_plan_prompt
    print("  planner 现在必须为每步声明前置/后置条件与子目标")

    banner("④", "v2 运行: 同一 query, 新 prompt + 内联评估")
    graph_v2 = build_graph(web_node=web_v2, data_node=data_v2)
    rec_v2 = TruGraph(graph_v2, app_name="Data agent", app_version="v2")
    with rec_v2 as recording:
        result_v2 = run_query(graph_v2, QUERY)
    print("\n  v2 GPA (同步计算):")
    scores_v2 = gpa_scores(trace_text(result_v2))

    banner("⑤", "v1 vs v2 对比")
    print(f"  {'维度':<24} {'v1':>6} {'v2':>6}")
    for label in GPA_FNS:
        print(f"  {label:<24} {scores_v1[label]:>6.2f} {scores_v2[label]:>6.2f}")
    records, _ = session.get_records_and_feedback()
    if "Context Relevance" in records.columns:
        ctx = records[records["app_version"] == "v2"]["Context Relevance"].dropna()
        if len(ctx):
            print(f"  {'Context Relevance(内联,v2)':<24} {'—':>6} {ctx.mean():>6.2f}")

    banner("⑥", "本课结论")
    print("""  改进循环 = L4 观测(发现哪个维度弱) -> L5 定位(GPA 指到 planner/executor)
  -> L6 干预(prompt 结构化 + 内联评估) -> 重测对比 —— 评估驱动的 agent 迭代""")


if __name__ == "__main__":
    main()
