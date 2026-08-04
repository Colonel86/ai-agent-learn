"""L4 · 观测 agent 表现: TruLens 记录 + RAG Triad 评估

课程原版: TruGraph 注册 -> 记录 3 个 query -> dashboard 查看。
本地化: TruSession 存本地 sqlite; feedback 同步计算 (with_app 模式);
结果直接打印, dashboard 给出手动启动命令。

运行: cd L4 && ../.venv/bin/python main.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from local_stack import banner
from workflow import build_graph, run_query


def main():
    banner("①", "创建 TruLens session (本地 default.sqlite) + RAG Triad feedbacks")
    from trulens.core.session import TruSession

    # 独立 DB, 不碰课程自带的 default.sqlite (预录对照数据)
    session = TruSession(database_url=f"sqlite:///local_demo.sqlite")
    session.reset_database()  # demo 幂等: 每次运行从空库开始
    from evals import RAG_TRIAD

    print("  feedbacks:", [f.name for f in RAG_TRIAD])

    banner("②", "注册 agent: TruGraph(app=Data agent, v1)")
    from trulens.apps.langgraph import TruGraph

    graph = build_graph()
    tru_recorder = TruGraph(
        graph,
        app_name="Data agent",
        app_version="v1",
        feedbacks=RAG_TRIAD,
        # OTel tracing 模式只允许 WITH_APP_THREAD(后台线程算 feedback), 结束前要等它算完
    )

    banner("③", "录制两次运行 (检索 span 由 @instrument 埋点提供)")
    with tru_recorder as recording:
        run_query(graph, "What are our top 3 client deals? Chart the deal value for each.")
    with tru_recorder as recording:
        run_query(graph, "Is there a common theme across our meeting notes?")

    banner("④", "等待后台 feedback 计算完成并查看结果")
    import time

    feedback_names = ["Groundedness", "Answer Relevance", "Context Relevance"]
    records = None
    for _ in range(120):  # 最多等 10 分钟
        records, _cols = session.get_records_and_feedback()
        have = [c for c in feedback_names if c in records.columns]
        if have and records[have].notna().all().all() and len(have) == len(feedback_names):
            break
        time.sleep(5)
    cols = [c for c in ["input"] + feedback_names if c in records.columns]
    with __import__("pandas").option_context("display.max_colwidth", 48, "display.width", 140):
        print(records[cols].to_string(index=False))

    banner("⑤", "Dashboard (可选)")
    print("""  cd L4 && ../.venv/bin/python -c "
from trulens.core.session import TruSession; from trulens.dashboard import run_dashboard
run_dashboard(TruSession())"    # 浏览器打开 http://localhost:8501""")


if __name__ == "__main__":
    main()
