"""
EP06 自由练习 — 换成你自己的文本跑一遍

步骤：
  1. 修改下面的变量替换成你的文本
  2. python your_turn.py
"""
from pathlib import Path
from config import get_completion, print_section

# ── 在这里替换 ───────────────────────────────────────────────

# 练习 A：翻译（改成任意文本 + 目标语言）
MY_TEXT = "I need to schedule a meeting with the team to discuss the project timeline."
TARGET_LANGUAGE = "Chinese (Simplified)"  # 可改成 Japanese、French、German 等

# 练习 B：语气转换（改成你想转换语气的文本）
MY_CASUAL_TEXT = "Hey, so I checked out that new API and it's pretty dope, let's use it."
TARGET_TONE = "professional business email"  # 可改成 formal academic、friendly blog post 等

# 练习 C：拼写/语法检查（改成你的文本）
MY_DRAFT = """
The team have been working very hard on this project since last month.
Their is still some issues we need to resolve before the deadline.
We need to make sure that each team members are doing they're part.
"""

# ─────────────────────────────────────────────────────────────

# Step A: 翻译
print_section(f"Step A: 翻译 → {TARGET_LANGUAGE}")
prompt_a = f"Translate the following text to {TARGET_LANGUAGE}:\n```{MY_TEXT}```"
print(get_completion(prompt_a))

# Step B: 语气转换
print_section(f"Step B: 语气转换 → {TARGET_TONE}")
prompt_b = f"Rewrite the following text as a {TARGET_TONE}:\n'{MY_CASUAL_TEXT}'"
print(get_completion(prompt_b))

# Step C: 拼写/语法检查
print_section("Step C: 拼写 & 语法检查")
prompt_c = f"""
Proofread and correct the following text, then rewrite the corrected version.
If no errors are found, say "No errors found".
Text: ```{MY_DRAFT}```
"""
corrected = get_completion(prompt_c)
print(corrected)

# Step D: APA 风格改写（bonus）
print_section("Step D: APA 风格改写（bonus）")
prompt_d = f"""
Proofread, correct, and rewrite the following text to be more compelling.
Follow APA style and target an advanced reader. Output in markdown.
Text: ```{MY_DRAFT}```
"""
apa = get_completion(prompt_d)
print(apa)

# 保存 APA 版本
Path(__file__).parent.joinpath("your_turn_apa.md").write_text(apa, encoding="utf-8")
print("\n✅ APA 版本已保存为 your_turn_apa.md")
print("\n完成！尝试修改 MY_TEXT / TARGET_LANGUAGE / MY_DRAFT，观察结果变化。")
