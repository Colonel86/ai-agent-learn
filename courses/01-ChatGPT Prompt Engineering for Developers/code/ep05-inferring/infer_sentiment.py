"""
EP05 Demo 1 — 情感推断
演示：从产品评论中推断情感（positive / negative）
  1a：让模型自由描述情感
  1b：强制输出单个词（positive / negative）
"""
from config import get_completion, print_section
from review_data import lamp_review

# ── Demo 1a：自由描述情感 ─────────────────────────────────────
print_section("Demo 1a: 情感推断（自由描述）")

prompt_verbose = f"""
What is the sentiment of the following product review,
which is delimited with triple backticks?

Review text: '''{lamp_review}'''
"""

response_verbose = get_completion(prompt_verbose)
print(response_verbose)

# ── Demo 1b：强制单词输出 ─────────────────────────────────────
print_section("Demo 1b: 情感推断（单词：positive / negative）")

prompt_single = f"""
What is the sentiment of the following product review,
which is delimited with triple backticks?

Give your answer as a single word, either "positive" \
or "negative".

Review text: '''{lamp_review}'''
"""

response_single = get_completion(prompt_single)
print(response_single)

# ── 说明 ──────────────────────────────────────────────────────
print_section("💡 观察")
print(
    "1a 输出：自然语言描述，适合阅读理解\n"
    "1b 输出：单词，适合程序直接解析\n"
    "\n"
    "→ 当需要把结果送入下游代码时，"
    "始终用约束性 prompt 限制输出格式。"
)
