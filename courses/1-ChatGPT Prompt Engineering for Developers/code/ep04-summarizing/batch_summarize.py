"""
EP04 Demo 4 — 批量摘要
演示：遍历多条评论，自动生成 20 词以内的简短摘要
真实场景：电商仪表盘，快速消化大量用户评论
"""
from config import get_completion, print_section
from reviews import REVIEWS, REVIEW_NAMES

print_section("Demo 4: 批量摘要（4 条评论 × 20 词）")

summaries = []

for i, review in enumerate(REVIEWS):
    prompt = f"""
    Your task is to generate a short summary of a product \
    review from an ecommerce site.

    Summarize the review below, delimited by triple backticks, \
    in at most 20 words.

    Review: ```{review}```
    """
    response = get_completion(prompt)
    summaries.append(response)
    print(f"[{i + 1}] {REVIEW_NAMES[i]}")
    print(f"    {response}")
    print()

# ── 汇总展示（模拟仪表盘） ────────────────────────────────────
print_section("仪表盘视图（汇总）")
print(f"{'#':<4} {'商品':<12} {'摘要'}")
print("-" * 70)
for i, (name, summary) in enumerate(zip(REVIEW_NAMES, summaries)):
    print(f"{i + 1:<4} {name:<12} {summary}")

print()
print(
    "💡 提示：\n"
    "  这个批量流程可扩展到数百条评论，\n"
    "  结合分页或数据库写回，即可构建实时评论摘要仪表盘。"
)
