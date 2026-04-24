"""
一键运行全部迭代版本，直观对比每次改进的效果

用法：
  python run_all.py        # 运行全部 5 个版本
  python run_all.py 3      # 只运行第 3 版
  python run_all.py 5      # 只运行终极版（生成 output.html）
"""
import sys

import v1_too_long
import v2_word_limit
import v3_target_audience
import v4_add_product_ids
import v5_html_with_table

VERSIONS = {
    1: ("V1 - 原始 Prompt（太长）",          v1_too_long.run),
    2: ("V2 - 加字数限制（50 words）",        v2_word_limit.run),
    3: ("V3 - 指定目标受众（零售商/技术细节）", v3_target_audience.run),
    4: ("V4 - 加入产品 ID",                  v4_add_product_ids.run),
    5: ("V5 - 终极版（HTML + 尺寸表格）",     v5_html_with_table.run),
}


def main():
    if len(sys.argv) > 1:
        try:
            n = int(sys.argv[1])
            if n not in VERSIONS:
                print(f"无效版本号，请输入 1~5")
                sys.exit(1)
            title, fn = VERSIONS[n]
            print(f"\n▶  运行：{title}")
            fn()
        except ValueError:
            print("请传入数字，例如：python run_all.py 5")
            sys.exit(1)
    else:
        print("\n📋 迭代对比：从 V1 到 V5，观察每次改进带来的变化\n")
        for n, (title, fn) in VERSIONS.items():
            print(f"\n{'▶ ' * 20}")
            print(f"▶  [{n}/5] {title}")
            print(f"{'▶ ' * 20}")
            fn()

        print("\n\n" + "=" * 60)
        print("  ✅ 全部版本运行完毕")
        print("  迭代路径：太长 → 限字数 → 定受众 → 加ID → HTML表格")
        print("  V5 生成了 output.html，用浏览器打开可预览最终效果")
        print("=" * 60)


if __name__ == "__main__":
    main()
