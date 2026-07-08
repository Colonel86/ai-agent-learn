"""步骤 3(L5 前半):生成 + 过滤微调训练数据。

对应课程 L5「working backwards」的数据生成 + 过滤。默认用 seed 模式(人工高质量种子,
每条硬事实多种问法),保证微调集覆盖 gold 的硬查询、对比信号稳定。
加 --model 改用小模型真生成(忠实复现 L5 两段流水线,但产量/质量随机)。
"""
import _bootstrap  # noqa: F401
import sys

from nba_sql_tuner.generate_data import generate

if __name__ == "__main__":
    if "--model" in sys.argv:
        from nba_sql_tuner.backend import LLM
        path = generate(mode="model", llm=LLM(), n_samples=10)
    else:
        path = generate(mode="seed")
    print(f"\n训练数据就绪:{path}")
    print("下一步:python scripts/04_finetune.py both")
