"""
EP06 Demo 2 — 通用翻译器
场景：跨国电商公司 IT 支持，用户用各自母语提交问题
流程：识别语言 → 翻译成英语和韩语 → 打印对照
"""
from config import get_completion, print_section
from text_data import user_messages

print_section("Demo 2: 通用翻译器（5 条多语言 IT 问题）")

for i, issue in enumerate(user_messages, 1):
    # Step 1: 识别语言
    prompt_lang = f"Tell me what language this is: ```{issue}```"
    lang = get_completion(prompt_lang)

    print(f"\n[{i}] 原始消息（{lang}）：")
    print(f"    {issue}")

    # Step 2: 翻译为英语和韩语
    prompt_translate = f"""
    Translate the following text to English \
    and Korean: ```{issue}```
    """
    translation = get_completion(prompt_translate)
    print(translation)

print_section("💡 应用场景")
print(
    "• 跨国客服系统：统一翻译成运营团队语言\n"
    "• 无需为每种语言单独训练 NLP 模型\n"
    "• 改进建议：让语言识别只返回一个词（JSON 格式），\n"
    "  避免'This is French'这种整句输出"
)
