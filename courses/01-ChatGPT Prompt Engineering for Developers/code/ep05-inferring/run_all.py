"""
一键运行 EP05 所有演示（或指定某一个）

用法：
  python run_all.py        # 运行全部 5 个演示
  python run_all.py 1      # Demo 1 — 情感推断
  python run_all.py 2      # Demo 2 — 情绪识别 & 愤怒检测
  python run_all.py 3      # Demo 3 — 实体提取
  python run_all.py 4      # Demo 4 — 一次推断多个属性
  python run_all.py 5      # Demo 5 — 话题推断 & 新闻告警
"""
import sys
import runpy

DEMOS = {
    1: ("infer_sentiment",  "Demo 1 — 情感推断"),
    2: ("infer_emotions",   "Demo 2 — 情绪识别 & 愤怒检测"),
    3: ("extract_entities", "Demo 3 — 实体提取"),
    4: ("multi_inference",  "Demo 4 — 一次推断多个属性"),
    5: ("infer_topics",     "Demo 5 — 话题推断 & 新闻告警"),
}


def run(demo_num: int) -> None:
    module, label = DEMOS[demo_num]
    print(f"\n{'#' * 65}")
    print(f"  运行 {label}")
    print(f"{'#' * 65}\n")
    runpy.run_module(module, run_name="__main__", alter_sys=True)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        try:
            num = int(sys.argv[1])
            if num not in DEMOS:
                raise ValueError
            run(num)
        except ValueError:
            print(f"请传入 1–{len(DEMOS)} 之间的数字")
            sys.exit(1)
    else:
        for num in sorted(DEMOS):
            run(num)
