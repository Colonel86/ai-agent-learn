"""
EP08 自由练习 — 自定义聊天机器人

修改下面的配置，创建你自己的聊天机器人：
  - 改 BOT_PERSONA 定义机器人的人格/角色/知识范围
  - 改 BOT_NAME 显示名称
  - 运行后进入交互模式

内置例子：一个专注于 Python 编程的助手
"""
from config import get_completion_from_messages

# ── 在这里自定义你的机器人 ───────────────────────────────────

BOT_NAME = "PyBot"

BOT_PERSONA = """
You are PyBot, a friendly and knowledgeable Python programming assistant.
You help developers with Python questions, code reviews, debugging, and best practices.
You explain concepts clearly with code examples when helpful.
You keep responses concise and practical.
When you don't know something, you say so honestly.
You respond in the same language the user writes in (Chinese or English).
"""

# 可选：预置一些开场问候（留空则模型自动生成）
OPENING_MESSAGE = ""  # 例如："你好！我是 PyBot，有什么 Python 问题我可以帮你？"

# ─────────────────────────────────────────────────────────────

def run_custom_bot() -> None:
    context = [{"role": "system", "content": BOT_PERSONA}]

    print(f"\n{'=' * 60}")
    print(f"  🤖 {BOT_NAME}")
    print(f"{'=' * 60}")
    print("输入 'quit' 退出 | 输入 'history' 查看对话历史")
    print(f"{'=' * 60}\n")

    if OPENING_MESSAGE:
        print(f"{BOT_NAME}: {OPENING_MESSAGE}\n")
        context.append({"role": "assistant", "content": OPENING_MESSAGE})
    else:
        opening = get_completion_from_messages(
            context + [{"role": "user", "content": "Please greet me briefly."}],
            temperature=0.7
        )
        print(f"{BOT_NAME}: {opening}\n")
        context.append({"role": "assistant", "content": opening})

    while True:
        user_input = input("你: ").strip()

        if not user_input:
            continue

        if user_input.lower() == "quit":
            print(f"\n{BOT_NAME}: 再见！有问题随时回来 👋")
            break

        if user_input.lower() == "history":
            print("\n── 对话历史 ──")
            for msg in context:
                if msg["role"] == "system":
                    continue
                role = "你" if msg["role"] == "user" else BOT_NAME
                print(f"[{role}] {msg['content'][:100]}{'...' if len(msg['content']) > 100 else ''}")
            print("── 结束 ──\n")
            continue

        context.append({"role": "user", "content": user_input})
        response = get_completion_from_messages(context, temperature=0.7)
        context.append({"role": "assistant", "content": response})
        print(f"\n{BOT_NAME}: {response}\n")


if __name__ == "__main__":
    run_custom_bot()
