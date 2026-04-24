"""
EP04 自由练习 — 换成你自己的评论跑一遍

步骤：
  1. 把 MY_REVIEWS 替换成你真实想分析的评论（中英文均可）
  2. 按需调整 FOCUS_TOPIC（定向摘要的聚焦方向）
  3. python your_turn.py
"""
from config import get_completion, print_section

# ── 在这里替换成你自己的评论 ─────────────────────────────────
MY_REVIEWS = [
    """
    Bought this wireless keyboard for working from home. The typing feel is
    excellent and the battery lasts about 3 months on a single charge.
    However, the Bluetooth connection sometimes drops when my phone is nearby.
    The build quality feels premium for the price. Delivery was fast, arrived
    in 1 day. Overall a solid purchase if you can live with occasional
    connectivity hiccups.
    """,
    """
    这款咖啡机真的很不错！出咖啡速度很快，大概 30 秒就能出一杯。
    口感醇厚，不输咖啡馆的水平。唯一的缺点是机器噪音有点大，
    早上用的时候怕吵到家人。价格略贵，但品质对得起定价。
    快递很快，下单后第二天就到了，包装也很严实。强烈推荐！
    """,
]

MY_REVIEW_NAMES = ["无线键盘", "咖啡机"]

# 定向摘要的聚焦方向（可以改成 pricing / customer service / product quality 等）
FOCUS_TOPIC = "shipping and delivery"

# ─────────────────────────────────────────────────────────────

# Step 1: 基础摘要（30 词）
print_section("Step 1: 基础摘要（30 词以内）")
for i, review in enumerate(MY_REVIEWS):
    prompt = f"""
    Summarize the following product review in at most 30 words.
    Review: ```{review}```
    """
    result = get_completion(prompt)
    print(f"[{MY_REVIEW_NAMES[i]}] {result}")

# Step 2: 定向摘要
print_section(f"Step 2: 定向摘要（聚焦：{FOCUS_TOPIC}）")
for i, review in enumerate(MY_REVIEWS):
    prompt = f"""
    Your task is to generate a short summary of a product review
    to give feedback to the relevant department.

    Summarize the review below, delimited by triple backticks,
    in at most 30 words, focusing on any aspects related to {FOCUS_TOPIC}.

    Review: ```{review}```
    """
    result = get_completion(prompt)
    print(f"[{MY_REVIEW_NAMES[i]}] {result}")

# Step 3: 信息提取
print_section(f"Step 3: 信息提取（提取：{FOCUS_TOPIC}）")
for i, review in enumerate(MY_REVIEWS):
    prompt = f"""
    Extract only the information relevant to {FOCUS_TOPIC}
    from the product review below, delimited by triple backticks.
    Limit to 30 words. If no relevant information, say "No relevant info found."

    Review: ```{review}```
    """
    result = get_completion(prompt)
    print(f"[{MY_REVIEW_NAMES[i]}] {result}")

# Step 4: 情感判断（bonus — 为 EP05 Inferring 预热）
print_section("Step 4: 情感判断（bonus）")
for i, review in enumerate(MY_REVIEWS):
    prompt = f"""
    What is the overall sentiment of the following product review?
    Answer with a single word: Positive, Negative, or Mixed.

    Review: ```{review}```
    """
    result = get_completion(prompt)
    print(f"[{MY_REVIEW_NAMES[i]}] 情感：{result}")

print()
print("✅ 练习完成！尝试修改 MY_REVIEWS 或 FOCUS_TOPIC，观察结果变化。")
