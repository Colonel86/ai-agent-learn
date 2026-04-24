"""
Tactic 5: Specify the steps required to complete a task
策略五：指定完成任务的步骤

演示：
  A. 无格式约束：模型完成步骤但输出格式可能不稳定
  B. 有格式模板：用 Text/Summary/Translation/Names/Output JSON 约束输出，
     结果结构化可预测，方便程序解析
"""
import json
from config import get_completion, print_section


STORY_TEXT = """
In a charming village, siblings Jack and Jill set out on \
a quest to fetch water from a hilltop \
well. As they climbed, singing joyfully, misfortune \
struck—Jack tripped on a stone and tumbled \
down the hill, with Jill following suit. \
Though slightly battered, the pair returned home to \
comforting embraces. Despite the mishap, \
their adventurous spirits remained undimmed, and they \
continued exploring with delight.
"""


def demo_without_format():
    """步骤明确，但不指定输出格式。"""
    print_section("A. 无格式约束（输出可能不稳定）")

    prompt = f"""
Perform the following actions:
1 - Summarize the following text delimited by triple \
backticks with 1 sentence.
2 - Translate the summary into French.
3 - List each name in the French summary.
4 - Output a json object that contains the following \
keys: french_summary, num_names.

Separate your answers with line breaks.

Text:
```{STORY_TEXT}```
"""
    response = get_completion(prompt)
    print(f"[Response]\n{response}")


def demo_with_format():
    """步骤 + 格式模板，输出结构化且可预测。"""
    print_section("B. 有格式模板（输出稳定，可程序解析）")

    prompt = f"""
Your task is to perform the following actions:
1 - Summarize the following text delimited by
  <> with 1 sentence.
2 - Translate the summary into French.
3 - List each name in the French summary.
4 - Output a json object that contains the
  following keys: french_summary, num_names.

Use the following format:
Text: <text to summarize>
Summary: <summary>
Translation: <summary translation>
Names: <list of names in summary>
Output JSON: <json with french_summary and num_names>

Text: <{STORY_TEXT}>
"""
    response = get_completion(prompt)
    print(f"[Response]\n{response}\n")

    # 尝试从格式化输出中提取 JSON 部分并解析
    print("[尝试解析 JSON 部分]")
    for line in response.split("\n"):
        if line.startswith("Output JSON:"):
            json_str = line.replace("Output JSON:", "").strip()
            try:
                data = json.loads(json_str)
                print(f"  french_summary: {data['french_summary']}")
                print(f"  num_names: {data['num_names']}")
            except json.JSONDecodeError:
                print(f"  原始内容: {json_str}（解析失败，可能需要进一步清洗）")
            break


# ── 自由练习区 ───────────────────────────────────────────────────────────────
def your_turn():
    """
    TODO: 换一段中文故事文本，并修改步骤（比如翻译成日语），
    观察格式模板是否依然有效。
    """
    print_section("C. 自由练习")

    YOUR_TEXT = "从前有座山，山里有座庙，庙里有个老和尚，正在给小和尚讲故事..."

    prompt = f"""
执行以下操作：
1 - 用一句话总结尖括号内的文本。
2 - 将摘要翻译成英语。
3 - 列出摘要中出现的人物。
4 - 输出包含 english_summary 和 num_characters 的 JSON。

使用以下格式：
Text: <待总结文本>
Summary: <中文摘要>
Translation: <英语翻译>
Characters: <人物列表>
Output JSON: <json>

Text: <{YOUR_TEXT}>
"""
    response = get_completion(prompt)
    print(f"[Response]\n{response}")


if __name__ == "__main__":
    demo_without_format()
    demo_with_format()
    # your_turn()
