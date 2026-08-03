"""L3 · 规则评估 + 模型评分评估分层, 以及「让 CI 真的会红」

课程叙事:
- per-commit: 快的规则断言, 每次提交都跑
- pre-release: LLM-as-a-Judge 格式评估, 发版前跑(更贵更慢)
- 故意提交一个必失败用例, 验证门禁不是摆设

运行: cd L3 && ../.venv/bin/python main.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from local_stack import banner, run_pytest

LESSON_DIR = Path(__file__).resolve().parent


def main():
    banner("①", "per-commit 层: 规则评估 (关键词/拒答断言)")
    run_pytest(str(LESSON_DIR / "test_assistant.py"), "run-commit-evals")

    banner("②", "pre-release 层: LLM-as-a-Judge 判定输出是否为合法 quiz 格式")
    run_pytest(
        str(LESSON_DIR / "test_release_evals.py") + "::test_model_graded_eval",
        "run-pre-release-evals",
    )

    banner("③", "验证门禁会红: 喂一句寒暄话断言它是 quiz —— 必须失败")
    run_pytest(
        str(LESSON_DIR / "test_release_evals.py") + "::test_model_graded_eval_should_fail",
        "run-pre-release-evals (bad case)",
        expect_fail=True,
    )

    banner("④", "本课结论")
    print("""  评估分层 = 成本分层: 规则断言(免费,秒级) -> LLM judge(有成本,发版前)
  「必失败用例」是评估体系自身的冒烟测试: 门禁若从不变红, 说明评估没在工作""")


if __name__ == "__main__":
    main()
