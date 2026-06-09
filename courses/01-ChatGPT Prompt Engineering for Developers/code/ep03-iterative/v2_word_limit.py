"""
迭代第 2 版：加上字数限制
改进：Use at most 50 words
观察：LLM 字数控制"大致准确"但不精确（常在 50~60 词之间）

对应 Notebook 章节：Issue 1 - The text is too long
"""
from config import get_completion, print_section
from fact_sheet import FACT_SHEET_CHAIR


def run():
    print_section("V2 - 加字数限制（Issue 1: Too Long → 加 'Use at most 50 words'）")

    prompt = f"""
Your task is to help a marketing team create a
description for a retail website of a product based
on a technical fact sheet.

Write a product description based on the information
provided in the technical specifications delimited by
triple backticks.

Use at most 50 words.

Technical specifications: ```{FACT_SHEET_CHAIR}```
"""
    response = get_completion(prompt)
    word_count = len(response.split())

    print(f"[Response]\n{response}")
    print(f"\n[字数统计] {word_count} words")

    if word_count <= 55:
        print("✅ 基本符合要求（LLM 字数控制有 ±5 词的误差，属正常）")
    else:
        print(f"⚠️  超出较多（{word_count} words），可以尝试更严格的表达，如 'Use at most 3 sentences'")

    # 实验：换一种表达方式限制长度
    print_section("V2b - 换用句数限制（Use at most 3 sentences）")
    prompt_sentences = prompt.replace("Use at most 50 words.", "Use at most 3 sentences.")
    response_sentences = get_completion(prompt_sentences)
    print(f"[Response]\n{response_sentences}")
    print(f"[字数统计] {len(response_sentences.split())} words")

    return response


if __name__ == "__main__":
    run()
