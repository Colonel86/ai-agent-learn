"""
EP04 Demo 3 — 提取 vs 摘要
演示："extract" 与 "summarize" 的区别：
  - summarize：更完整，但可能混入无关信息
  - extract：更精准，只返回与主题直接相关的内容
"""
from config import get_completion, print_section
from reviews import review_1

# ── Demo 3a：summarize（运输方向） ────────────────────────────
print_section("Demo 3a: summarize（运输方向）")

prompt_summarize = f"""
Your task is to generate a short summary of a product \
review from an ecommerce site to give feedback to the \
Shipping department.

Summarize the review below, delimited by triple backticks, \
in at most 30 words, and focusing on any aspects that \
mention shipping and delivery of the product.

Review: ```{review_1}```
"""

response_summarize = get_completion(prompt_summarize)
print(response_summarize)

# ── Demo 3b：extract（运输方向） ──────────────────────────────
print_section("Demo 3b: extract（运输方向）")

prompt_extract = f"""
Your task is to extract relevant information from \
a product review from an ecommerce site to give \
feedback to the Shipping department.

From the review below, delimited by triple quotes, \
extract the information relevant to shipping and \
delivery. Limit to 30 words.

Review: ```{review_1}```
"""

response_extract = get_completion(prompt_extract)
print(response_extract)

# ── 差异对比 ──────────────────────────────────────────────────
print_section("💡 summarize vs extract 对比")
print("【summarize 结果】")
print(response_summarize)
print()
print("【extract 结果】")
print(response_extract)
print()
print(
    "核心差异：\n"
    "  summarize → 保留更多上下文，适合给人快速浏览整体印象\n"
    "  extract   → 只保留与主题直接相关的片段，适合结构化数据处理\n"
    "\n"
    "选择建议：\n"
    "  • 需要完整背景 → summarize\n"
    "  • 需要精准字段 → extract"
)
