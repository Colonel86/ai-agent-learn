"""
一键运行 EP07 所有演示（或指定某一个）

用法：
  python run_all.py        # 运行全部 2 个演示
  python run_all.py 1      # Demo 1 — 自动邮件回复（3 种情感）
  python run_all.py 2      # Demo 2 — Temperature 参数演示（各运行 3 次）

注意：Demo 2 共调用 API 6 次，稍慢，请耐心等待。
"""
import sys
import runpy

DEMOS = {
    1: ("email_reply",      "Demo 1 — 自动邮件回复（3 种情感）"),
    2: ("temperature_demo", "Demo 2 — Temperature 参数演示"),
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
