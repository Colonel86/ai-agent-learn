"""步骤 4(L5 核心):真跑微调 —— 标准 fine-tuning 和/或 memory tuning。

用法:
  python scripts/04_finetune.py finetune   # 只跑标准 fine-tuning
  python scripts/04_finetune.py memory      # 只跑 memory tuning
  python scripts/04_finetune.py both        # 两个都跑(默认)

每种训练产出一个 LoRA adapter(adapters/<name>/)和 loss 曲线(train_summary.json)。
留意打印的 loss:memory tuning 会把 loss 逼到接近 0(把事实背进权重),
标准 fine-tuning 的 loss 会停在一个较高的平台(只学到风格,没背事实)。
"""
import _bootstrap  # noqa: F401
import sys

from nba_sql_tuner.finetune import train

if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "both"
    presets = ["finetune", "memory"] if which == "both" else [which]
    for p in presets:
        train(p)
    print("下一步:python scripts/05_compare.py")
