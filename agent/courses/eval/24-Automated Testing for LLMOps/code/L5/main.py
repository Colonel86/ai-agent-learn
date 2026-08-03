"""L5 · CircleCI 配置文件详解 (本地解析版)

课程原版逐版 push 到 CircleCI 观察; 本地化改为解析 + 讲解 5 个版本的演进,
并给出「云端 job -> 本地 pytest」的映射。不调 LLM。

运行: cd L5 && ../.venv/bin/python main.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import yaml

from local_stack import banner

LESSON_DIR = Path(__file__).resolve().parent

EVOLUTION = {
    "hello_world.yml": "最小配置: 1 个 job, docker 镜像 + 一条 echo, 没有 workflow",
    "circle_config_v1.yml": "接入课程仓库: 定义 eval-mode 参数, workflow 先只挂 hello-world job",
    "circle_config_v2.yml": "hello-world 换成真正的 run-commit-evals job: 装依赖 + pytest test_assistant.py",
    "circle_config_v3.yml": "加 run-pre-release-evals job(模型评分), 两个 job 同 workflow 顺序跑",
    "circle_config_v4.yml": "按 eval-mode 参数用 when equal 拆成三条 workflow(commit/release/full), 新增 run-manual-evals",
    "circle_config_v5.yml": "加 triggers.schedule 定时触发(cron 每日 0 点), nightly 全量评估",
}

LOCAL_MAPPING = """
  云端 (CircleCI)                        本地对应 (本课程各 lab)
  -------------------------------------  --------------------------------
  run-commit-evals job                   pytest test_assistant.py         (L2/L3)
  run-pre-release-evals job              pytest test_release_evals.py     (L3)
  eval-mode 参数 (commit/release/full)   main.py 里选择跑哪些测试文件
  store_artifacts 评估报告               L4 落盘 quiz_eval_report.html
  nightly 定时触发                        cron + python main.py
"""


def describe(config_path: Path):
    cfg = yaml.safe_load(config_path.read_text())
    jobs = list((cfg.get("jobs") or {}).keys())
    workflows = {
        k: v for k, v in (cfg.get("workflows") or {}).items() if isinstance(v, dict)
    }
    params = list((cfg.get("parameters") or {}).keys())
    print(f"  jobs: {jobs}")
    if params:
        print(f"  parameters: {params}")
    for wf_name, wf in workflows.items():
        wf_jobs = wf.get("jobs", [])
        cond = "when 条件" if "when" in wf else ("定时触发" if "triggers" in wf else "无条件")
        print(f"  workflow [{wf_name}]: {len(wf_jobs)} 个 job, {cond}")


def main():
    banner("①", "从 hello world 到评估流水线: 6 个配置版本演进")
    for i, (fname, note) in enumerate(EVOLUTION.items(), 1):
        path = LESSON_DIR / fname
        print(f"\n--- v{i}: {fname}")
        print(f"  演进点: {note}")
        if path.exists():
            describe(path)

    banner("②", "云端 -> 本地映射")
    print(LOCAL_MAPPING)

    banner("③", "本课结论")
    print("""  CI 配置的核心结构只有三层: jobs(做什么) -> workflows(什么时候做) -> parameters(做哪种)
  评估流水线的演进路线 = 成本分层落到调度上:
  每次 commit 跑便宜的 -> 发版跑贵的 -> 夜里跑全量并存档报告""")


if __name__ == "__main__":
    main()
