"""
EP08 Demo 1 — 多轮对话基础
演示：
  1a：莎士比亚风格的聊天机器人（system message 设定人格）
  1b：上下文缺失 → 模型不记得用户名字
  1c：提供上下文 → 模型能正确回忆（⭐ 核心概念：context）
"""
from config import get_completion_from_messages, print_section

# ── Demo 1a：莎士比亚风格 ─────────────────────────────────────
print_section("Demo 1a: 莎士比亚风格聊天机器人")

messages_shakespeare = [
    {"role": "system",    "content": "You are an assistant that speaks like Shakespeare."},
    {"role": "user",      "content": "tell me a joke"},
    {"role": "assistant", "content": "Why did the chicken cross the road"},
    {"role": "user",      "content": "I don't know"},
]

response = get_completion_from_messages(messages_shakespeare, temperature=1)
print(response)

# ── Demo 1b：无上下文 → 忘记名字 ────────────────────────────
print_section("Demo 1b: 无上下文 — 模型不知道用户名字")

# 第一轮：自我介绍
messages_intro = [
    {"role": "system", "content": "You are friendly chatbot."},
    {"role": "user",   "content": "Hi, my name is Isa"},
]
response_intro = get_completion_from_messages(messages_intro, temperature=1)
print(f"用户：Hi, my name is Isa")
print(f"助手：{response_intro}")

# 第二轮：新对话，没有历史上下文
print()
messages_forget = [
    {"role": "system", "content": "You are friendly chatbot."},
    {"role": "user",   "content": "Yes, can you remind me, What is my name?"},
]
response_forget = get_completion_from_messages(messages_forget, temperature=1)
print(f"用户（新对话）：Yes, can you remind me, What is my name?")
print(f"助手：{response_forget}")
print("\n⚠️  模型不知道名字 — 因为第一轮对话没有被传入！")

# ── Demo 1c：有上下文 → 记得名字 ────────────────────────────
print_section("Demo 1c: 有上下文 — 模型能正确回忆（⭐ context 概念）")

messages_with_context = [
    {"role": "system",    "content": "You are friendly chatbot."},
    {"role": "user",      "content": "Hi, my name is Isa"},
    {"role": "assistant", "content": "Hi Isa! It's nice to meet you. "
                                     "Is there anything I can help you with today?"},
    {"role": "user",      "content": "Yes, you can remind me, What is my name?"},
]
response_context = get_completion_from_messages(messages_with_context, temperature=1)
print(f"（对话包含历史上下文）")
print(f"用户：Yes, you can remind me, What is my name?")
print(f"助手：{response_context}")
print("\n✅ 有了历史上下文，模型能正确记得用户名字！")

# ── 说明 ──────────────────────────────────────────────────────
print_section("💡 核心概念")
print(
    "每次调用语言模型都是独立的——没有内置记忆。\n"
    "\n"
    "要让模型'记住'之前的对话，必须把历史消息一并传入 messages 列表。\n"
    "这就是'上下文（context）'。\n"
    "\n"
    "实际 chatbot 的做法：\n"
    "  context = []           # 初始化\n"
    "  context.append(user_msg)    # 追加用户消息\n"
    "  context.append(assistant_msg)  # 追加助手回复\n"
    "  # ... 对话越来越长，context 也越来越大\n"
    "\n"
    "注意：context 越长，每次调用的 token 费用也越高，需要在实际应用中管理长度。"
)
