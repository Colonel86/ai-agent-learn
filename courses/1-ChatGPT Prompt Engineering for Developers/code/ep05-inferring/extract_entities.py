"""
EP05 Demo 3 — 实体提取
演示：从评论中提取产品名称和品牌名称，输出为 JSON
"""
import json
from config import get_completion, print_section
from review_data import lamp_review

# ── Demo 3：提取商品名 & 品牌名 ───────────────────────────────
print_section("Demo 3: 实体提取（商品名 + 品牌名 → JSON）")

prompt_entities = f"""
Identify the following items from the review text:
- Item purchased by reviewer
- Company that made the item

The review is delimited with triple backticks. \
Format your response as a JSON object with \
"Item" and "Brand" as the keys.
If the information isn't present, use "unknown" \
as the value.
Make your response as short as possible.

Review text: '''{lamp_review}'''
"""

response_entities = get_completion(prompt_entities)
print("原始输出：")
print(response_entities)

# 解析 JSON 并结构化展示
try:
    data = json.loads(response_entities)
    print("\n解析结果：")
    print(f"  商品：{data.get('Item', 'unknown')}")
    print(f"  品牌：{data.get('Brand', 'unknown')}")
except json.JSONDecodeError:
    print("\n⚠️  JSON 解析失败，请检查模型输出格式。")

# ── 说明 ──────────────────────────────────────────────────────
print_section("💡 观察")
print(
    "通过在 prompt 中指定 JSON 格式和 key 名称，\n"
    "可以让模型直接输出可被程序消费的结构化数据。\n"
    "\n"
    "常见用途：\n"
    "  • 从非结构化评论中自动标记商品 / 品牌\n"
    "  • 构建知识图谱或数据库记录"
)
