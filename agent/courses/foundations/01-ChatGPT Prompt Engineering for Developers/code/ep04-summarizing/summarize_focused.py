"""
EP04 Demo 2 — 定向摘要
演示：针对特定部门生成聚焦摘要（运输部门 / 定价部门）
"""
from config import get_completion, print_section
from reviews import review_1

# ── Demo 2a：面向运输部门的摘要 ───────────────────────────────
print_section("Demo 2a: 面向运输部门的摘要")

prompt_shipping = f"""
Your task is to generate a short summary of a product \
review from an ecommerce site to give feedback to the \
Shipping department.

Summarize the review below, delimited by triple backticks, \
in at most 30 words, and focusing on any aspects that \
mention shipping and delivery of the product.

Review: ```{review_1}```
"""

response_shipping = get_completion(prompt_shipping)
print(response_shipping)

# ── Demo 2b：面向定价部门的摘要 ───────────────────────────────
print_section("Demo 2b: 面向定价部门的摘要")

prompt_pricing = f"""
Your task is to generate a short summary of a product \
review from an ecommerce site to give feedback to the \
Pricing department, responsible for determining the \
price of the product.

Summarize the review below, delimited by triple backticks, \
in at most 30 words, and focusing on any aspects that \
are relevant to the price and perceived value.

Review: ```{review_1}```
"""

response_pricing = get_completion(prompt_pricing)
print(response_pricing)

# ── 对比说明 ──────────────────────────────────────────────────
print_section("💡 观察")
print(
    "两个摘要都聚焦了各自部门关心的信息，\n"
    "但也可能混入一些无关内容。\n"
    "→ 如果只想要精准信息，见 Demo 3 的 extract 方案。"
)
