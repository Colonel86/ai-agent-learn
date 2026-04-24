"""
一键运行 EP06 所有演示（或指定某一个）

用法：
  python run_all.py        # 运行全部 5 个演示
  python run_all.py 1      # Demo 1 — 基础翻译
  python run_all.py 2      # Demo 2 — 通用翻译器
  python run_all.py 3      # Demo 3 — 语气转换
  python run_all.py 4      # Demo 4 — 格式转换（生成 output.html）
  python run_all.py 5      # Demo 5 — 拼写语法检查（生成 diff_output.html / apa_output.md）
"""
import sys
import runpy

DEMOS = {
    1: ("translate_basic",     "Demo 1 — 基础翻译"),
    2: ("translate_universal", "Demo 2 — 通用翻译器"),
    3: ("transform_tone",      "Demo 3 — 语气转换"),
    4: ("convert_format",      "Demo 4 — 格式转换"),
    5: ("spellcheck",          "Demo 5 — 拼写语法检查"),
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
