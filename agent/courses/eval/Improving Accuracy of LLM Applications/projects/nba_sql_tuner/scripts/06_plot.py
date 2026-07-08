"""步骤 6(可选):把 loss 曲线和准确率阶梯画成纯 ASCII 图,贴进终端/笔记。

不依赖 matplotlib —— 直接在终端画,零依赖、可截图。
读 adapters/*/train_summary.json 和 data/results/comparison.json。
"""
import _bootstrap  # noqa: F401
import json

from nba_sql_tuner import config


def sparkline(values):
    blocks = "▁▂▃▄▅▆▇█"
    lo, hi = min(values), max(values)
    span = (hi - lo) or 1
    return "".join(blocks[min(7, int((v - lo) / span * 7))] for v in values)


def bar(pct, width=40):
    n = int(round(pct / 100 * width))
    return "█" * n + "·" * (width - n)


def main():
    print("=" * 60)
    print("训练 loss 曲线(每 epoch 平均)")
    print("=" * 60)
    for name in ("finetune", "memory"):
        f = config.ADAPTERS / name / "train_summary.json"
        if not f.exists():
            continue
        s = json.loads(f.read_text())
        h = s["loss_history"]
        print(f"\n{name:8s}  {h[0]:.2f} {sparkline(h)} {h[-1]:.3f}  "
              f"({len(h)} epochs, final={h[-1]:.4f})")

    cmp = config.RESULTS / "comparison.json"
    if cmp.exists():
        m = json.loads(cmp.read_text())["metrics"]
        print("\n" + "=" * 60)
        print("准确率阶梯(正确SQL%)")
        print("=" * 60)
        for name in ("baseline", "finetune", "memory"):
            if name in m:
                p = m[name]["correct_pct"]
                print(f"{name:8s} {bar(p)} {p:5.1f}%")


if __name__ == "__main__":
    main()
