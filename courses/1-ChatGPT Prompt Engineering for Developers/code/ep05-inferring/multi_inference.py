"""
EP05 Demo 4 — 一次推断多个属性
演示：用单个 prompt 同时提取
  - Sentiment（情感：positive / negative）
  - Anger（是否愤怒：true / false）
  - Item（商品名）
  - Brand（品牌名）
核心优势：减少 API 调用次数，降低延迟和成本
"""
import json
from config import get_completion, print_section
from review_data import lamp_review

# ── Demo 4：一次性多属性推断 ──────────────────────────────────
print_section("Demo 4: 一次推断多个属性（JSON 输出）")

prompt_multi = f"""
Identify the following items from the review text:
- Sentiment (positive or negative)
- Is the reviewer expressing anger? (true or false)
- Item purchased by reviewer
- Company that made the item

The review is delimited with triple backticks. \
Format your response as a JSON object with \
"Sentiment", "Anger", "Item" and "Brand" as the keys.
If the information isn't present, use "unknown" \
as the value.
Make your response as short as possible.
Format the Anger value as a boolean.

Review text: '''{lamp_review}'''
"""

response_multi = get_completion(prompt_multi)
print("原始输出：")
print(response_multi)

# 解析 & 展示
try:
    data = json.loads(response_multi)
    print("\n结构化解析：")
    print(f"  情感：   {data.get('Sentiment', 'unknown')}")
    print(f"  愤怒：   {data.get('Anger', 'unknown')}")
    print(f"  商品：   {data.get('Item', 'unknown')}")
    print(f"  品牌：   {data.get('Brand', 'unknown')}")

    # 下游业务逻辑示例
    print()
    if data.get("Anger") is True:
        print("🚨 触发告警：检测到愤怒情绪，建议人工介入！")
    elif data.get("Sentiment") == "negative":
        print("⚠️  负面评论，建议列入跟进队列。")
    else:
        print("✅ 正面评论，无需特殊处理。")

except json.JSONDecodeError:
    print("\n⚠️  JSON 解析失败，请检查模型输出格式。")

# ── 说明 ──────────────────────────────────────────────────────
print_section("💡 观察")
print(
    "对比 Demo 1-3（每次只推断一个维度）：\n"
    "  • 单次调用 → 同时获得 4 个属性\n"
    "  • API 调用次数：4 次 → 1 次\n"
    "  • 延迟和成本大幅降低\n"
    "\n"
    "⭐ 实际生产中的评论分析流水线推荐采用此模式。"
)
