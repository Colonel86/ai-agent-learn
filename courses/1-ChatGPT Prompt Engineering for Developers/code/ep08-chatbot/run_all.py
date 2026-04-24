"""
一键运行 EP08 演示（或指定某一个）

用法：
  python run_all.py        # 运行 Demo 1 + Demo 3（非交互式）
  python run_all.py 1      # Demo 1 — 多轮对话基础（context / 莎士比亚 / 记名字）
  python run_all.py 2      # Demo 2 — OrderBot 交互对话（需要键盘输入）
  python run_all.py 3      # Demo 3 — OrderBot JSON 订单摘要（非交互式）

注意：
  Demo 2 是交互式程序，run_all.py 不会自动运行它。
  请单独运行：python orderbot.py
"""
import sys
import runpy

DEMOS = {
    1: ("chat_basics",      "Demo 1 — 多轮对话基础"),
    2: None,                # 交互式，需单独运行
    3: ("orderbot_summary", "Demo 3 — OrderBot JSON 订单摘要"),
}

AUTO_DEMOS = [1, 3]   # run_all 默认执行的 demo


def run(demo_num: int) -> None:
    if demo_num == 2:
        print("\n⚠️  Demo 2 是交互式程序，请单独运行：")
        print("    python orderbot.py")
        return
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
        print("（Demo 2 需要交互输入，已跳过。运行 'python orderbot.py' 体验完整点单。）")
        for num in AUTO_DEMOS:
            run(num)
