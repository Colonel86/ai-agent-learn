"""
EP04 Demo 1 — 基础摘要
演示：用字数限制生成简短摘要
"""
from config import get_completion, print_section
from reviews import review_1

# ── Demo 1a：30 词以内的基础摘要 ──────────────────────────────
print_section("Demo 1a: 基础摘要（30 词以内）")

prompt = f"""
Your task is to generate a short summary of a product \
review from an ecommerce site.

Summarize the review below, delimited by triple backticks, \
in at most 30 words.

Review: ```{review_1}```
"""

response = get_completion(prompt)
print(response)

# ── Demo 1b：控制句子数 ────────────────────────────────────────
print_section("Demo 1b: 基础摘要（最多 2 句）")

prompt_sentences = f"""
Your task is to generate a short summary of a product \
review from an ecommerce site.

Summarize the review below, delimited by triple backticks, \
in at most 2 sentences.

Review: ```{review_1}```
"""

response_sentences = get_completion(prompt_sentences)
print(response_sentences)

# ── Demo 1c：控制字符数 ────────────────────────────────────────
print_section("Demo 1c: 基础摘要（最多 100 字符）")

prompt_chars = f"""
Your task is to generate a short summary of a product \
review from an ecommerce site.

Summarize the review below, delimited by triple backticks, \
in at most 100 characters.

Review: ```{review_1}```
"""

response_chars = get_completion(prompt_chars)
print(response_chars)
print(f"（字符数：{len(response_chars)}）")
