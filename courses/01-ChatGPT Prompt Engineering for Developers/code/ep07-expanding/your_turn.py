"""
EP07 自由练习 — 换成你自己的评论和情感跑一遍

步骤：
  1. 替换 MY_REVIEW / MY_SENTIMENT / MY_PRODUCT
  2. 调整 MY_TEMPERATURE 观察输出差异
  3. python your_turn.py
"""
from config import get_completion, print_section

# ── 在这里替换 ───────────────────────────────────────────────
MY_PRODUCT = "无线耳机"

MY_REVIEW = """
这款耳机音质非常好，低音浑厚，高音清晰。续航也很棒，充一次电能用 30 小时。
但配对过程比较麻烦，每次连接新设备都需要手动进入配对模式，不够智能。
客服回复很及时，帮我解决了初始设置的问题。总体来说物有所值，推荐购买。
"""

MY_SENTIMENT = "neutral"   # 可改成 positive / negative / neutral

MY_TEMPERATURE = 0.7       # 可改成 0（确定性）或 0~1 之间的任意值

# 额外要求（可留空）
EXTRA_INSTRUCTION = "Also mention our 30-day return policy."
# ─────────────────────────────────────────────────────────────

prompt = f"""
You are a customer service AI assistant.
Your task is to send an email reply to a valued customer.
Given the customer email delimited by ```, \
Generate a reply to thank the customer for their review.
If the sentiment is positive or neutral, thank them for \
their review.
If the sentiment is negative, apologize and suggest that \
they can reach out to customer service.
Make sure to use specific details from the review.
Write in a concise and professional tone.
{EXTRA_INSTRUCTION}
Sign the email as `AI customer agent`.
Customer review: ```{MY_REVIEW}```
Review sentiment: {MY_SENTIMENT}
"""

print_section(f"自动回复邮件 — {MY_PRODUCT}（情感：{MY_SENTIMENT}，temperature：{MY_TEMPERATURE}）")
response = get_completion(prompt, temperature=MY_TEMPERATURE)
print(response)

# ── 对比：用 temperature=0 再跑一次 ──────────────────────────
if MY_TEMPERATURE != 0:
    print_section("对比：temperature=0（确定性版本）")
    response_t0 = get_completion(prompt, temperature=0)
    print(response_t0)

    print_section("💡 两个版本的差异")
    print(f"temperature={MY_TEMPERATURE} 版本和 temperature=0 版本的表达方式是否有所不同？\n"
          "反复运行 temperature 较高的版本，观察每次输出是否变化。")

print("\n✅ 完成！尝试修改 MY_SENTIMENT 或 MY_TEMPERATURE，观察模型行为。")
