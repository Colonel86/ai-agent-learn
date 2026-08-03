"""L2 · 持续集成概述: 搭出被测应用 + 第一批 per-commit 评估

课程原版把 test_assistant.py push 到 GitHub 触发 CircleCI;
本地化用 pytest 直接跑同一批测试, 模拟 per-commit 评估 job。

运行: cd L2 && ../.venv/bin/python main.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import assistant_chain
from local_stack import banner, run_pytest

LESSON_DIR = Path(__file__).resolve().parent


def main():
    banner("①", "被测应用: LCEL 管道 prompt | llm | parser (DeepSeek)")
    chain = assistant_chain()
    answer = chain.invoke({"question": "Generate a quiz about science."})
    print(answer)

    banner("②", "第一批 per-commit 评估: 关键词断言 + 拒答断言 (test_assistant.py)")
    print("  规则评估的特点: 快、零 LLM judge 成本、每次 commit 都跑得起")
    ok = run_pytest(str(LESSON_DIR / "test_assistant.py"), "run-commit-evals")

    banner("③", "CI 对应关系")
    print("""  课程原版流程: push app.py + test_assistant.py -> CircleCI 跑 run-commit-evals job
  本地对应:     pytest test_assistant.py  (circle_config.yml 保留作对照, L5 详解)""")
    print(f"\n  本课结论: per-commit 评估{'通过' if ok else '未通过'}")


if __name__ == "__main__":
    main()
