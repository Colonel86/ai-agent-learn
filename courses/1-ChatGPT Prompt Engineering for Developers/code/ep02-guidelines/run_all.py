"""
一键运行所有 Tactic 演示
用法：python run_all.py [tactic编号]

示例：
  python run_all.py        # 运行全部
  python run_all.py 1      # 只运行 Tactic 1
  python run_all.py 6      # 只运行 Tactic 6（最重要的对比实验）
"""
import sys

from tactic1_delimiters       import demo_normal, demo_injection_without_delimiter, demo_injection_with_delimiter
from tactic2_structured_output import demo_json, demo_html
from tactic3_check_conditions  import demo_text_with_steps, demo_text_without_steps
from tactic4_few_shot          import demo_original, demo_your_topic, demo_chinese_style
from tactic5_specify_steps     import demo_without_format, demo_with_format
from tactic6_work_out_solution import demo_wrong_approach, demo_correct_approach

TACTICS = {
    1: {
        "title": "Tactic 1 - Delimiters（分隔符）",
        "demos": [demo_normal, demo_injection_without_delimiter, demo_injection_with_delimiter],
    },
    2: {
        "title": "Tactic 2 - Structured Output（结构化输出）",
        "demos": [demo_json, demo_html],
    },
    3: {
        "title": "Tactic 3 - Check Conditions（条件检查）",
        "demos": [demo_text_with_steps, demo_text_without_steps],
    },
    4: {
        "title": "Tactic 4 - Few-shot Prompting（少样本提示）",
        "demos": [demo_original, demo_your_topic, demo_chinese_style],
    },
    5: {
        "title": "Tactic 5 - Specify Steps（指定步骤）",
        "demos": [demo_without_format, demo_with_format],
    },
    6: {
        "title": "Tactic 6 - Work Out Solution First（先自行推理）⭐",
        "demos": [demo_wrong_approach, demo_correct_approach],
    },
}


def run_tactic(n: int):
    t = TACTICS[n]
    print(f"\n{'#' * 60}")
    print(f"#  {t['title']}")
    print(f"{'#' * 60}")
    for demo_fn in t["demos"]:
        demo_fn()


def main():
    if len(sys.argv) > 1:
        try:
            n = int(sys.argv[1])
            if n not in TACTICS:
                print(f"无效编号，请输入 1~6")
                sys.exit(1)
            run_tactic(n)
        except ValueError:
            print("请传入数字，例如：python run_all.py 6")
            sys.exit(1)
    else:
        for n in TACTICS:
            run_tactic(n)


if __name__ == "__main__":
    main()
