"""L5 · 测 agent 的 GPA (Goal-Plan-Act 对齐度)

四种失败模式的单点演示 (合成 goal/plan/actions 样本, 与课程一致):
  1 Plan Quality       计划本身好不好 (泛泛拉数据 vs 精准过滤排序)
  2 Plan Adherence     执行是否忠实于计划 (跳步/偷工 vs 逐步执行)
  3 Execution Efficiency 有没有冗余动作 (重复取数/多余导出)
  4 Logical Consistency  步骤间是否自洽 (过滤后数量反而变多 = 不自洽)

然后把 4 个 GPA feedback 挂到真实 agent 的 trace 级评估上。

运行: cd L5 && ../.venv/bin/python main.py
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from local_stack import banner, make_tru_provider
from workflow import build_graph, run_query

provider = make_tru_provider()


def show(label, score, reasons):
    reason_text = reasons.get("reason", str(reasons)) if isinstance(reasons, dict) else str(reasons)
    reason_text = re.sub(r"\s*Score:\s*-?\d+(?:\.\d+)?\s*$", "", reason_text.strip())
    print(f"\n  [{label}] score = {score:.2f}")
    print("  " + reason_text[:400].replace("\n", "\n  "))


goal_and_plan = """
User Query: Which sales leads should we prioritize this week,
and what specific action items should we take for each?

Plan:
1. Pull all sales leads from the past 12 months from the CRM.
2. For the largest 20 leads, compile any notes, call logs,
and related tasks from the CRM.
3. Summarize each lead's current stage in the pipeline.
4. Present the summary and recommendations in a single table.
"""

goal_and_better_plan = """
User Query: Which sales leads should we prioritize this week,
and what specific action items should we take for each?

Plan:
1. Pull all leads with open opportunities from the CRM that have
a next action date within the next 14 days or no next action assigned.
2. Filter to leads with deal value > $10k or high lead score.
3. Sort by deal stage urgency and potential revenue impact.
4. For each prioritized lead: retrieve latest interaction notes,
key decision-maker info, and current blockers.
5. Identify overdue or missing action items.
6. Propose specific, high-impact next steps.
7. Group recommendations into this week's priority list with owner
assignments and deadlines.
8. Present results in a table with columns: Lead Name, Value, Stage,
Urgency Score, Next Action, Due Date, Owner.
"""

sloppy_actions = """
[STEP 1] Pulled all open opportunities from the CRM without applying a next action date filter.
[STEP 2] Applied deal value filter only; skipped the lead score filter.
[STEP 3] Sorted leads solely by deal value (descending).
[STEP 4] Retrieved latest notes and contact names but skipped blockers.
[STEP 5] Listed the CRM's existing "next action" field without review or update.
[STEP 6] Output a table with Lead Name, Value, Stage, and Next Action.
"""

faithful_actions = """
[STEP 1] Pulled all leads with open opportunities and either a next action date within 14 days or no next action assigned.
[STEP 2] Filtered to leads with deal value over $10k or high lead score.
[STEP 3] Sorted leads by deal stage urgency and potential revenue impact.
[STEP 4] Retrieved latest notes, key decision-maker info, and identified any blockers.
[STEP 5] Created updated, specific next actions for each lead based on context.
[STEP 6] Group recommendations into this week's priority list with owner assignments and deadlines.
[STEP 7] Output a table with Lead Name, Value, Stage, Urgency Score, Next Action, Due Date, and Owner.
"""

redundant_actions = """
[STEP 1] Pulled all leads with open opportunities and either a next action date within 14 days or no next action assigned.
    -> Retrieved 96 leads.
[STEP 2] Filtered to leads with deal value over $10k or high lead score.
    -> Applied filter, yielding 54 leads.
[STEP 3] Sorted leads by deal stage urgency and potential revenue impact.
[STEP 4] Retrieved latest notes, key decision-maker info, and blockers.
    -> Retrieved notes from both the CRM API and a cached export for one lead to "double-check" consistency.
[STEP 5] Created updated, specific next actions for each lead based on context.
[STEP 6] Output a table with Lead Name, Value, Stage, Urgency Score, Next Action, Due Date, and Owner.
    -> Exported table to both XLSX and CSV formats, though only one format was requested.
"""

inconsistent_actions = """
[STEP 1] Pulled all leads with open opportunities and either a next action date within 14 days or no next action assigned.
    -> Retrieved 96 leads, including recent follow-ups and a few older records from early last year.
[STEP 2] Filtered to leads with deal value over $10k or high lead score.
    -> Resulted in 113 leads after applying filters.
[STEP 3] Sorted leads by deal stage urgency and potential revenue impact.
    -> Leads with minimal recent engagement ranked highly due to their projected close dates in Q3.
[STEP 4] Retrieved latest notes, key decision-maker info, and blockers.
    -> Several leads show "TBD" for decision-maker but still have active next steps assigned.
[STEP 5] Created updated, specific next actions for each lead based on context.
    -> Example: Lead A - "Schedule demo and confirm final pricing"; Lead B - "Wait for proposal feedback before scheduling demo."
[STEP 6] Output a table with Lead Name, Value, Stage, Urgency Score, Next Action, Due Date, and Owner.
    -> Due dates range from last week to the end of the current month.
"""


def main():
    banner("①", "失败模式 1 · Plan Quality: 差计划 vs 好计划")
    show("差计划", *provider.plan_quality_with_cot_reasons(goal_and_plan))
    show("好计划", *provider.plan_quality_with_cot_reasons(goal_and_better_plan))

    banner("②", "失败模式 2 · Plan Adherence: 偷工执行 vs 忠实执行")
    show("偷工执行", *provider.plan_adherence_with_cot_reasons(goal_and_better_plan + sloppy_actions))
    show("忠实执行", *provider.plan_adherence_with_cot_reasons(goal_and_better_plan + faithful_actions))

    banner("③", "失败模式 3 · Execution Efficiency: 冗余动作(重复取数/多余导出)")
    show("冗余执行", *provider.execution_efficiency_with_cot_reasons(redundant_actions))

    banner("④", "失败模式 4 · Logical Consistency: 过滤后数量反而变多 = 不自洽")
    show("不自洽执行", *provider.logical_consistency_with_cot_reasons(inconsistent_actions))

    banner("⑤", "GPA 挂到真实 agent: trace 级评估一次完整运行")
    from trulens.core.session import TruSession

    # 独立 DB, 不碰课程自带的 default.sqlite (预录对照数据)
    session = TruSession(database_url=f"sqlite:///local_demo.sqlite")
    session.reset_database()
    from trulens.apps.langgraph import TruGraph

    from evals import GPA

    graph = build_graph()
    tru_recorder = TruGraph(graph, app_name="Data agent", app_version="v1", feedbacks=GPA)
    with tru_recorder as recording:
        run_query(graph, "What are our top 3 client deals by value?")

    import time

    names = ["Logical Consistency", "Execution Efficiency", "Plan Adherence", "Plan Quality"]
    records = None
    for _ in range(120):
        records, _ = session.get_records_and_feedback()
        have = [c for c in names if c in records.columns]
        if len(have) == len(names) and records[have].notna().all().all():
            break
        time.sleep(5)
    cols = [c for c in ["input"] + names if c in records.columns]
    with __import__("pandas").option_context("display.max_colwidth", 40, "display.width", 160):
        print(records[cols].to_string(index=False))

    banner("⑥", "本课结论")
    print("""  GPA 是轨迹级评估的结构化版本: 不只问「答对没」, 而是分别追责
  计划(quality) / 执行(adherence) / 效率(efficiency) / 自洽(consistency)
  —— 每个低分都能定位到 planner 或 executor 的具体环节""")


if __name__ == "__main__":
    main()
