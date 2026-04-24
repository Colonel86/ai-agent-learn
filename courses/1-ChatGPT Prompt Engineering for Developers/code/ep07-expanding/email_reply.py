"""
EP07 Demo 1 — 自动邮件回复
演示：根据客户评论 + 情感，生成个性化客服邮件
  1a：负面情感 → 道歉 + 引导联系客服（课程原版示例）
  1b：正面情感 → 感谢 + 正向回应
  1c：中性情感 → 感谢 + 温和回应
核心原则：使用评论中的具体细节，署名 AI customer agent
"""
from config import get_completion, print_section
from review_data import ALL_REVIEWS

# 共用的 prompt 模板
def build_prompt(review: str, sentiment: str) -> str:
    return f"""
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
Sign the email as `AI customer agent`.
Customer review: ```{review}```
Review sentiment: {sentiment}
"""

for name, review, sentiment in ALL_REVIEWS:
    print_section(f"Demo 1 — {name}（情感：{sentiment}）")
    prompt = build_prompt(review, sentiment)
    response = get_completion(prompt, temperature=0)
    print(response)

print_section("💡 观察")
print(
    "• negative → 模型自动生成道歉 + 引导联系客服\n"
    "• positive → 模型自动感谢并正向回应\n"
    "• neutral  → 模型采用平衡、感谢的语气\n"
    "\n"
    "⭐ 关键技巧：\n"
    "  1. 把情感（sentiment）作为额外上下文传入\n"
    "  2. 明确要求'使用评论中的具体细节'\n"
    "  3. 署名 AI customer agent — 保持透明度"
)
