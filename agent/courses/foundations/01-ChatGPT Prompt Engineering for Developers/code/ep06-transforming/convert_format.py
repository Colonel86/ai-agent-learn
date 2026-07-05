"""
EP06 Demo 4 — 格式转换
演示：JSON（Python 字典）→ HTML 表格
输出：在终端打印 HTML 源码，并将完整 HTML 页面保存为 output.html
"""
import json
from pathlib import Path
from config import get_completion, print_section
from text_data import data_json

print_section("Demo 4: 格式转换（JSON → HTML 表格）")

print("输入 JSON：")
print(json.dumps(data_json, ensure_ascii=False, indent=2))

prompt = f"""
Translate the following python dictionary from JSON to an HTML \
table with column headers and title: {data_json}
"""

response = get_completion(prompt)

print("\n生成的 HTML：")
print(response)

# ── 保存为完整 HTML 文件（可用浏览器直接打开）────────────────────
html_page = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Restaurant Employees</title>
  <style>
    body {{ font-family: Arial, sans-serif; padding: 2rem; }}
    table {{ border-collapse: collapse; width: 100%; max-width: 600px; }}
    th, td {{ border: 1px solid #ccc; padding: 8px 16px; text-align: left; }}
    th {{ background-color: #4a90d9; color: white; }}
    tr:nth-child(even) {{ background-color: #f2f2f2; }}
  </style>
</head>
<body>
{response}
</body>
</html>"""

output_path = Path(__file__).parent / "output.html"
output_path.write_text(html_page, encoding="utf-8")
print(f"\n✅ 已保存为 output.html，用浏览器打开可直接预览渲染效果。")

print_section("💡 观察")
print(
    "• 在 prompt 中描述输入格式（JSON）和输出格式（HTML table）即可\n"
    "• 同样可以：JSON → Markdown 表格、CSV → HTML、XML → JSON……\n"
    "• 以前需要写一堆正则表达式，现在一个 prompt 搞定"
)
