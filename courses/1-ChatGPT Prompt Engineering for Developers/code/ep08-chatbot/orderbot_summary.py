"""
EP08 Demo 3 — OrderBot 订单 JSON 摘要
演示：模拟一段完整的点餐对话，然后生成结构化 JSON 订单摘要
（对应课程 notebook 末尾的 JSON summary 代码段）

不需要交互输入，直接运行即可看到完整流程。
"""
import json
from config import get_completion_from_messages, print_section

# ── 模拟一段已完成的对话（来自课程演示场景）─────────────────────
SYSTEM_MESSAGE = """
You are OrderBot, an automated service to collect orders for a pizza restaurant. \
You first greet the customer, then collect the order, \
and then ask if it's a pickup or delivery. \
You wait to collect the entire order, then summarize it and check for a final \
time if the customer wants to add anything else. \
If it's a delivery, you ask for an address. \
Finally you collect the payment. \
Make sure to clarify all options, extras and sizes to uniquely \
identify the item from the menu. \
You respond in a short, very conversational friendly style. \
The menu includes:
pepperoni pizza  $12.95 (large), $10.00 (medium), $7.00 (small)
cheese pizza     $10.95 (large), $9.25 (medium),  $6.50 (small)
eggplant pizza   $11.95 (large), $9.75 (medium),  $6.75 (small)
fries $4.50 (large), $3.50 (small)
greek salad $7.25
Toppings: extra cheese $2.00, mushrooms $1.50, sausage $3.00,
canadian bacon $3.50, AI sauce $1.50, peppers $1.00
Drinks: coke $3.00 (large), $2.00 (medium), $1.00 (small)
sprite $3.00 (large), $2.00 (medium), $1.00 (small)
bottled water $5.00
"""

# 模拟对话：点了一个中号茄子披萨 + 小薯条 + 中杯可乐，自取
simulated_context = [
    {"role": "system",    "content": SYSTEM_MESSAGE},
    {"role": "assistant", "content": "Welcome! What can I get for you today?"},
    {"role": "user",      "content": "Hi, I would like to order a pizza."},
    {"role": "assistant", "content": "Sure! Which pizza would you like? "
                                     "We have pepperoni, cheese, and eggplant. "
                                     "And what size?"},
    {"role": "user",      "content": "A medium eggplant pizza please."},
    {"role": "assistant", "content": "Great choice! Any toppings on that?"},
    {"role": "user",      "content": "No extra toppings thanks."},
    {"role": "assistant", "content": "Got it! Anything else — sides or drinks?"},
    {"role": "user",      "content": "Small fries and a medium coke."},
    {"role": "assistant", "content": "Perfect. To confirm: 1 medium eggplant pizza ($9.75), "
                                     "1 small fries ($3.50), 1 medium coke ($2.00). "
                                     "Is that everything?"},
    {"role": "user",      "content": "Yes that's all. I'll pick it up."},
    {"role": "assistant", "content": "Awesome! Your total is $15.25. "
                                     "Your order will be ready shortly. "
                                     "How would you like to pay?"},
    {"role": "user",      "content": "Credit card."},
    {"role": "assistant", "content": "Perfect, payment processed! See you soon! 🍕"},
]

# ── 打印模拟对话 ──────────────────────────────────────────────
print_section("模拟对话记录")
for msg in simulated_context:
    if msg["role"] == "system":
        continue
    role_label = "顾客" if msg["role"] == "user" else "OrderBot"
    print(f"[{role_label}] {msg['content']}")

# ── 生成 JSON 订单摘要 ────────────────────────────────────────
print_section("生成 JSON 订单摘要")

summary_messages = simulated_context.copy()
summary_messages.append({
    "role": "system",
    "content": (
        "Create a JSON summary of the previous food order. "
        "Itemize the price for each item. "
        "The fields should be: "
        "1) pizza (include size and price) "
        "2) list of toppings (with price) "
        "3) list of drinks (include size and price) "
        "4) list of sides (include size and price) "
        "5) total price"
    )
})

summary_raw = get_completion_from_messages(summary_messages, temperature=0)
print("模型原始输出：")
print(summary_raw)

# 尝试解析 JSON
try:
    # 提取 ```json ... ``` 块（如果有）
    clean = summary_raw.strip()
    if clean.startswith("```"):
        clean = clean.split("```")[1]
        if clean.startswith("json"):
            clean = clean[4:]
    order_data = json.loads(clean.strip())

    print("\n解析后的结构化数据：")
    print(json.dumps(order_data, indent=2, ensure_ascii=False))
    print("\n✅ JSON 解析成功，可直接传给订单系统！")
except json.JSONDecodeError as e:
    print(f"\n⚠️  JSON 解析失败：{e}")
    print("改进建议：在 prompt 中强制要求'只输出纯 JSON，不要任何其他文字'")

print_section("💡 观察")
print(
    "• 系统消息（system message）既可以在对话开始时设定人格，\n"
    "  也可以在对话末尾追加新的'任务指令'\n"
    "\n"
    "• 用 temperature=0 生成订单摘要 → 保证格式稳定可解析\n"
    "\n"
    "• 生产建议：要求模型'只输出 JSON，不包含任何解释文字'\n"
    "  prompt 末尾加一句：Output ONLY valid JSON, no other text."
)
