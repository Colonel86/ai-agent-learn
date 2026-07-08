"""步骤 2(L3):对 baseline 模型跑评估流水线,得到准确率基线。

对应课程 L3。产出 Percent Valid SQL / Percent Correct SQL 两个指标,写入 data/results/。
这是「准确率提升阶梯」的第 0 级 —— 后面每一步都跟它比。
"""
import _bootstrap  # noqa: F401
from nba_sql_tuner.backend import LLM
from nba_sql_tuner.evaluate import evaluate

if __name__ == "__main__":
    llm = LLM()
    print(f"评估 baseline 模型:{llm.name}\n")
    evaluate(llm, label="baseline")
    print("\n下一步:python scripts/03_generate_data.py")
