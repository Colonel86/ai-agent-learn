"""
EP06 Demo 5 — 拼写与语法检查
演示：
  5a：批量校对含错误的句子列表
  5b：校对熊猫评论 + redlines 差异对比
  5c：校对 + APA 格式改写（更有说服力，面向高水平读者）
"""
from pathlib import Path
from config import get_completion, print_section
from text_data import grammar_texts, panda_review

# ── Demo 5a：批量校对句子 ─────────────────────────────────────
print_section("Demo 5a: 批量校对（7 个含错句子）")

for i, t in enumerate(grammar_texts, 1):
    prompt = f"""Proofread and correct the following text
    and rewrite the corrected version. If you don't find
    any errors, just say "No errors found". Don't use
    any punctuation around the text:
    ```{t}```"""
    response = get_completion(prompt)
    print(f"[{i}] 原文：{t}")
    print(f"    修正：{response}")
    print()

# ── Demo 5b：校对评论 + redlines 差异对比 ─────────────────────
print_section("Demo 5b: 评论校对 + redlines 差异对比")

prompt_proofread = f"proofread and correct this review: ```{panda_review}```"
corrected = get_completion(prompt_proofread)

print("【校对后版本】")
print(corrected)

# 用 redlines 展示差异
try:
    from redlines import Redlines
    diff = Redlines(panda_review.strip(), corrected.strip())
    print("\n【差异标注（Markdown 格式）】")
    print(diff.output_markdown)

    # 保存为 HTML 可视化
    html_diff = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Review Diff</title>
  <style>
    body {{ font-family: Arial, sans-serif; padding: 2rem; max-width: 800px; }}
    del {{ color: red; background: #ffe0e0; }}
    ins {{ color: green; background: #e0ffe0; }}
  </style>
</head>
<body>
<h2>原始评论 vs 校对后版本（差异标注）</h2>
<p>{diff.output_markdown}</p>
</body>
</html>"""
    diff_path = Path(__file__).parent / "diff_output.html"
    diff_path.write_text(html_diff, encoding="utf-8")
    print("\n✅ 差异已保存为 diff_output.html")

except ImportError:
    print("\n⚠️  未安装 redlines，跳过差异对比。")
    print("    安装方式：pip install redlines --break-system-packages")

# ── Demo 5c：校对 + APA 格式改写 ──────────────────────────────
print_section("Demo 5c: 校对 + APA 格式改写（面向高水平读者）")

prompt_apa = f"""
proofread and correct this review. Make it more compelling.
Ensure it follows APA style guide and targets an advanced reader.
Output in markdown format.
Text: ```{panda_review}```
"""
apa_response = get_completion(prompt_apa)
print(apa_response)

# 保存为 Markdown 文件
apa_path = Path(__file__).parent / "apa_output.md"
apa_path.write_text(apa_response, encoding="utf-8")
print("\n✅ APA 版本已保存为 apa_output.md")

print_section("💡 观察")
print(
    "5a → 批量处理：for 循环 + f-string 动态 prompt\n"
    "5b → redlines：可视化展示模型做了哪些修改\n"
    "5c → 多重指令叠加：校对 + 语气提升 + 格式规范 + 受众指定\n"
    "\n"
    "⭐ 实际写作场景推荐用 5c 的多重指令模式"
)
