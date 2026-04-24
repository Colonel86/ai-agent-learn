"""
Tactic 4: Few-shot prompting
策略四：少样本提示

演示：
  A. 原版：孩子/祖父对话，展示风格继承
  B. 变体：换一个主题，验证模型确实在延续风格
"""
from config import get_completion, print_section


def demo_original():
    """原版 few-shot 示例：祖父用比喻回答孩子的问题。"""
    print_section("A. 原版 Few-shot：祖父比喻风格")

    prompt = """
Your task is to answer in a consistent style.

<child>: Teach me about patience.

<grandparent>: The river that carves the deepest \
valley flows from a modest spring; the \
grandest symphony originates from a single note; \
the most intricate tapestry begins with a solitary thread.

<child>: Teach me about resilience.
"""
    response = get_completion(prompt)
    print(f"[Prompt - 示例部分]\n<child>: Teach me about patience.\n<grandparent>: The river that carves...\n")
    print(f"[New Question]\n<child>: Teach me about resilience.\n")
    print(f"[Response]\n{response}")


def demo_your_topic():
    """用同一个 few-shot 框架，换一个主题，验证风格继承。"""
    print_section("B. 变体：换主题 → 验证风格继承")

    # ← 修改 NEW_TOPIC 来实验不同主题
    NEW_TOPIC = "courage"

    prompt = f"""
Your task is to answer in a consistent style.

<child>: Teach me about patience.

<grandparent>: The river that carves the deepest \
valley flows from a modest spring; the \
grandest symphony originates from a single note; \
the most intricate tapestry begins with a solitary thread.

<child>: Teach me about {NEW_TOPIC}.
"""
    response = get_completion(prompt)
    print(f"[New Topic] {NEW_TOPIC}")
    print(f"[Response]\n{response}")


def demo_chinese_style():
    """用中文 few-shot 示例：让模型用"古诗词"风格回答。"""
    print_section("C. 中文 Few-shot：古诗词风格")

    prompt = """
你的任务是以一致的风格回答问题。

<学生>：请教我关于时间的道理。

<老师>：逝者如斯夫，不舍昼夜。时光如流水，一去不复返。\
珍惜每一刻，方能无愧于心。

<学生>：请教我关于坚持的道理。
"""
    response = get_completion(prompt)
    print(f"[Response]\n{response}")


# ── 自由练习区 ───────────────────────────────────────────────────────────────
def your_turn():
    """
    TODO: 自定义一个全新的 few-shot 示例。
    设计思路：
    1. 选一个你想让模型模仿的风格（技术文档、诗意散文、段子手...）
    2. 给出一个"提问 + 该风格的回答"作为示例
    3. 提一个新问题，观察模型是否能维持风格
    """
    print_section("D. 自由练习：设计你自己的 Few-shot")

    prompt = """
你的任务是以一致的风格回答问题。

<用户>：解释什么是递归。
<程序员>：要理解递归，首先你得理解递归。

<用户>：解释什么是云计算。
"""  # ← 修改这里
    response = get_completion(prompt)
    print(f"[Response]\n{response}")


if __name__ == "__main__":
    demo_original()
    demo_your_topic()
    demo_chinese_style()
    # your_turn()
