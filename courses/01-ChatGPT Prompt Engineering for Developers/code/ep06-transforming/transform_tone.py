"""
EP06 Demo 3 — 语气转换
演示：俚语 → 商务信函（slang to business letter）
"""
from config import get_completion, print_section

print_section("Demo 3: 语气转换（俚语 → 商务信函）")

slang_text = "Dude, This is Joe, check out this spec on this standing lamp."

print(f"原文（俚语）：\n{slang_text}\n")

prompt = f"""
Translate the following from slang to a business letter:
'{slang_text}'
"""

response = get_completion(prompt)
print("转换结果（商务信函）：")
print(response)

print_section("💡 观察")
print(
    "用途：\n"
    "  • 帮助非母语写作者提升正式场合的表达\n"
    "  • 将内部沟通语气转化为客户/合作伙伴友好格式\n"
    "  • 反向也可以：正式 → 口语（更易读的内部文档）"
)
