"""
Tactic 3: Ask the model to check whether conditions are satisfied
策略三：让模型检查前提条件是否满足

演示两段文本：
  A. text_1：包含步骤序列（泡茶）→ 模型提取步骤
  B. text_2：不包含步骤（晴天描述）→ 模型回复 "No steps provided."
"""
from config import get_completion, print_section


TEXT_WITH_STEPS = """
Making a cup of tea is easy! First, you need to get some \
water boiling. While that's happening, \
grab a cup and put a tea bag in it. Once the water is \
hot enough, just pour it over the tea bag. \
Let it sit for a bit so the tea can steep. After a \
few minutes, take out the tea bag. If you \
like, you can add some sugar or milk to taste. \
And that's it! You've got yourself a delicious \
cup of tea to enjoy.
"""

TEXT_WITHOUT_STEPS = """
The sun is shining brightly today, and the birds are \
singing. It's a beautiful day to go for a \
walk in the park. The flowers are blooming, and the \
trees are swaying gently in the breeze. People \
are out and about, enjoying the lovely weather. \
Some are having picnics, while others are playing \
games or simply relaxing on the grass. It's a \
perfect day to spend time outdoors and appreciate the \
beauty of nature.
"""

PROMPT_TEMPLATE = """
You will be provided with text delimited by triple quotes.
If it contains a sequence of instructions, \
re-write those instructions in the following format:

Step 1 - ...
Step 2 - ...
...
Step N - ...

If the text does not contain a sequence of instructions, \
then simply write "No steps provided."

\"\"\"{text}\"\"\"
"""


def demo_text_with_steps():
    print_section("A. 含步骤的文本 → 提取步骤")
    prompt = PROMPT_TEMPLATE.format(text=TEXT_WITH_STEPS)
    response = get_completion(prompt)
    print(f"[Completion]\n{response}")


def demo_text_without_steps():
    print_section("B. 不含步骤的文本 → 输出 No steps provided.")
    prompt = PROMPT_TEMPLATE.format(text=TEXT_WITHOUT_STEPS)
    response = get_completion(prompt)
    print(f"[Completion]\n{response}")


# ── 自由练习区 ───────────────────────────────────────────────────────────────
def your_turn():
    """
    TODO: 把下面的 YOUR_TEXT 替换成一段中文内容，
    测试模型能否在中文文本中正确识别"有步骤 vs 无步骤"。
    也可以修改 PROMPT_TEMPLATE 里的格式（比如改成"第一步 -"）。
    """
    print_section("C. 自由练习：中文步骤检测")

    YOUR_TEXT = """
    今天天气很好，适合出门散步。公园里花开了，很漂亮。
    """  # ← 替换成你的文本

    prompt = f"""
你将收到用三重引号分隔的文本。
如果它包含一系列操作步骤，请按如下格式重写：

第一步 - ...
第二步 - ...
...
第N步 - ...

如果文本不包含操作步骤，直接回复"未提供步骤"。

\"\"\"{YOUR_TEXT}\"\"\"
"""
    response = get_completion(prompt)
    print(f"[Completion]\n{response}")


if __name__ == "__main__":
    demo_text_with_steps()
    demo_text_without_steps()
    # your_turn()
