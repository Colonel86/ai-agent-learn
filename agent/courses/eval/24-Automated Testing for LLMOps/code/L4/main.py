"""L4 · 模型评分评估进阶: 幻觉检测 + 数据集回归 + 评估报告工件

运行: cd L4 && ../.venv/bin/python main.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from local_stack import banner, run_pytest

LESSON_DIR = Path(__file__).resolve().parent


def main():
    banner("①", "幻觉检测: judge 对照 quiz bank 判「有没有出处」")
    print("""  课程原版靠 gpt-3.5 对 books 真的幻觉出一份 quiz; DeepSeek 会直接拒答
  (prompt 规则=第一道防线), 故幻觉样本改为固定 fixture 做确定性验证:
  正样本(真实 geography quiz)->Y, 负样本(手工构造的 books quiz)->N""")
    run_pytest(str(LESSON_DIR / "test_hallucinations.py"), "hallucination-eval")

    banner("②", "数据集回归: 多种问法, 故意混入不支持的用例 (Italy)")
    print("  quiz bank 里没有 Italy 主题, 助手按 prompt 规则拒答 -> 断言失败")
    print("  课程用意: 数据集要混入边界用例, 失败暴露的是「支持范围」而非 bug")
    run_pytest(str(LESSON_DIR / "test_with_dataset.py"), "dataset-regression", expect_fail=True)

    banner("③", "评估报告工件: 逐条 判决+解释, 产出 HTML (对应 CI store_artifacts)")
    import save_eval_artifacts

    save_eval_artifacts.main()

    banner("④", "本课结论")
    print("""  幻觉评估的关键: judge 只对照给定事实集, 不判「对错」判「有没有出处」
  数据集里的 Italy 失败正是报告工件的动机: 红绿灯只说挂了,
  逐条 判决+解释 的 HTML 才说清「挂在哪、为什么」""")


if __name__ == "__main__":
    main()
