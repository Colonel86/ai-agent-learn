"""
EP07 Demo 2 — Temperature 参数演示
核心概念：temperature 控制输出的随机性 / 多样性
  temperature = 0   → 确定性输出，每次相同（可靠、可预测）
  temperature = 0.7 → 多样性输出，每次不同（更有创意）
  temperature = 1.0 → 最大多样性（有时天马行空）

演示：
  2a：temperature=0，连续运行 3 次 → 输出完全相同
  2b：temperature=0.7，连续运行 3 次 → 输出各有不同
"""
from config import get_completion, print_section
from review_data import review_blender, sentiment_blender

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
Sign the email as `AI customer agent`.
Customer review: ```{review_blender}```
Review sentiment: {sentiment_blender}
"""

# ── Demo 2a：temperature=0（确定性）─────────────────────────
print_section("Demo 2a: temperature=0（连续 3 次，观察一致性）")

results_t0 = []
for i in range(1, 4):
    r = get_completion(prompt, temperature=0)
    results_t0.append(r)
    print(f"\n--- 第 {i} 次 ---")
    print(r)

# 检测是否完全相同
all_same = len(set(results_t0)) == 1
print(f"\n3 次输出是否完全相同：{'✅ 是' if all_same else '❌ 否'}")

# ── Demo 2b：temperature=0.7（多样性）───────────────────────
print_section("Demo 2b: temperature=0.7（连续 3 次，观察差异）")

results_t07 = []
for i in range(1, 4):
    r = get_completion(prompt, temperature=0.7)
    results_t07.append(r)
    print(f"\n--- 第 {i} 次 ---")
    print(r)

all_same_07 = len(set(results_t07)) == 1
print(f"\n3 次输出是否完全相同：{'✅ 是（偶然）' if all_same_07 else '❌ 否（符合预期）'}")

# ── 总结 ──────────────────────────────────────────────────────
print_section("💡 Temperature 选择指南")
print(
    "┌─────────────────┬────────────────────────────────────────┐\n"
    "│  temperature    │  适用场景                               │\n"
    "├─────────────────┼────────────────────────────────────────┤\n"
    "│  0              │  需要可预测输出：提取、分类、结构化任务   │\n"
    "│  0.3 ~ 0.7      │  客服邮件、内容改写、适度创意            │\n"
    "│  0.8 ~ 1.0      │  头脑风暴、故事创作、多样化备选方案      │\n"
    "└─────────────────┴────────────────────────────────────────┘\n"
    "\n"
    "本课程全程使用 temperature=0 确保演示结果一致\n"
    "生产环境中，客服机器人建议 0~0.3，创意写作建议 0.7+"
)
