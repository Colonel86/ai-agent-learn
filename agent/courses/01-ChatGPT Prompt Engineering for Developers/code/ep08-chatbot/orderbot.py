"""
EP08 Demo 2 — OrderBot（终端交互版）
原版使用 Jupyter panel 构建 UI，本版改为终端交互循环。

运行后进入对话模式：
  - 直接输入文字与 OrderBot 对话
  - 输入 'quit' 或 'exit' 结束对话
  - 输入 'summary' 生成 JSON 订单摘要

OrderBot 系统指令（来自课程原版）：
  - 披萨餐厅点单机器人
  - 流程：问候 → 收集订单 → 确认取餐/外送 → 汇总 → 收款
"""
import json
from config import get_completion_from_messages

# ── 菜单 & 系统消息（来自课程原版）─────────────────────────────
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

Pizzas:
  pepperoni pizza   $12.95 (large), $10.00 (medium), $7.00 (small)
  cheese pizza      $10.95 (large), $9.25 (medium),  $6.50 (small)
  eggplant pizza    $11.95 (large), $9.75 (medium),  $6.75 (small)

Sides:
  fries             $4.50 (large), $3.50 (small)
  greek salad       $7.25

Toppings (add-on):
  extra cheese      $2.00
  mushrooms         $1.50
  sausage           $3.00
  canadian bacon    $3.50
  AI sauce          $1.50
  peppers           $1.00

Drinks:
  coke              $3.00 (large), $2.00 (medium), $1.00 (small)
  sprite            $3.00 (large), $2.00 (medium), $1.00 (small)
  bottled water     $5.00
"""

SUMMARY_INSTRUCTION = """
Create a JSON summary of the previous food order.
Itemize the price for each item.
The fields should be:
  1) pizza (include size and price)
  2) list of toppings (with price)
  3) list of drinks (include size and price)
  4) list of sides (include size and price)
  5) total price
"""


def run_orderbot() -> None:
    context = [{"role": "system", "content": SYSTEM_MESSAGE}]

    print("\n" + "=" * 60)
    print("  🍕 OrderBot — 披萨餐厅点单机器人")
    print("=" * 60)
    print("输入 'summary' 查看 JSON 订单摘要")
    print("输入 'quit' 或 'exit' 退出")
    print("=" * 60 + "\n")

    # 获取开场白
    opening = get_completion_from_messages(context, temperature=0.5)
    print(f"OrderBot: {opening}\n")
    context.append({"role": "assistant", "content": opening})

    while True:
        user_input = input("你: ").strip()

        if not user_input:
            continue

        if user_input.lower() in ("quit", "exit"):
            print("\nOrderBot: 感谢光临，期待再次为您服务！🍕")
            break

        if user_input.lower() == "summary":
            _print_summary(context)
            continue

        # 正常对话轮次
        context.append({"role": "user", "content": user_input})
        response = get_completion_from_messages(context, temperature=0.5)
        context.append({"role": "assistant", "content": response})
        print(f"\nOrderBot: {response}\n")


def _print_summary(context: list) -> None:
    """根据当前对话上下文生成 JSON 订单摘要"""
    print("\n" + "-" * 40)
    print("  📋 生成订单 JSON 摘要...")
    print("-" * 40)

    summary_messages = context.copy()
    summary_messages.append({"role": "system", "content": SUMMARY_INSTRUCTION})

    summary = get_completion_from_messages(summary_messages, temperature=0)
    print(summary)

    # 尝试解析并美化打印
    try:
        data = json.loads(summary)
        print("\n（解析成功，可直接传给订单系统）")
    except json.JSONDecodeError:
        print("\n（注：如需程序化处理，可在 prompt 中强制要求纯 JSON 输出）")

    print("-" * 40 + "\n")


if __name__ == "__main__":
    run_orderbot()
