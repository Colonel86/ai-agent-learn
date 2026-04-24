"""
迭代第 5 版（终极版）：HTML 格式 + 产品尺寸表格
改进：
  - 格式化为 HTML，描述放入 <div>
  - 末尾附加 "Product Dimensions" 表格（仅英寸单位）
  - 保留产品 ID

对应 Notebook 章节：Issue 3 - Description needs a table of dimensions

运行后会将 HTML 保存到 output.html，可用浏览器直接打开预览。
"""
import os
from config import get_completion, print_section
from fact_sheet import FACT_SHEET_CHAIR

OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "output.html")


def run():
    print_section("V5 - 终极版（Issue 3: 加尺寸表格 + HTML 格式输出）")

    prompt = f"""
Your task is to help a marketing team create a
description for a retail website of a product based
on a technical fact sheet.

Write a product description based on the information
provided in the technical specifications delimited by
triple backticks.

The description is intended for furniture retailers,
so should be technical in nature and focus on the
materials the product is constructed from.

At the end of the description, include every 7-character
Product ID in the technical specification.

After the description, include a table that gives the
product's dimensions. The table should have two columns.
In the first column include the name of the dimension.
In the second column include the measurements in inches only.

Give the table the title 'Product Dimensions'.

Format everything as HTML that can be used in a website.
Place the description in a <div> element.

Technical specifications: ```{FACT_SHEET_CHAIR}```
"""
    response = get_completion(prompt)

    print(f"[Raw HTML Output]\n{response[:500]}...\n（仅显示前 500 字符）")

    # 保存完整 HTML 到文件
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Product Description - EP03 Demo</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 40px auto; padding: 0 20px; }}
        table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
        th, td {{ border: 1px solid #ddd; padding: 8px 12px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        h2 {{ color: #333; }}
    </style>
</head>
<body>
{response}
</body>
</html>"""

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"\n✅ HTML 已保存到：{OUTPUT_FILE}")
    print("👉 用浏览器打开该文件即可预览渲染效果")

    return response


if __name__ == "__main__":
    run()
