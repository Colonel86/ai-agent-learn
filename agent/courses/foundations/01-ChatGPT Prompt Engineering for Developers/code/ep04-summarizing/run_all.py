"""
一键运行 EP04 所有演示（或指定某一个）

用法：
  python run_all.py        # 运行全部 4 个演示
  python run_all.py 1      # 只运行 Demo 1（基础摘要）
  python run_all.py 2      # 只运行 Demo 2（定向摘要）
  python run_all.py 3      # 只运行 Demo 3（提取 vs 摘要）
  python run_all.py 4      # 只运行 Demo 4（批量摘要）
"""
import sys
import runpy

DEMOS = {
    1: ("summarize_basic",     "Demo 1 — 基础摘要"),
    2: ("summarize_focused",   "Demo 2 — 定向摘要"),
    3: ("extract_vs_summarize","Demo 3 — 提取 vs 摘要"),
    4: ("batch_summarize",     "Demo 4 — 批量摘要"),
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
