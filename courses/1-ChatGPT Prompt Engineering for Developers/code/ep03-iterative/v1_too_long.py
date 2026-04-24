"""
迭代第 1 版：最原始的 prompt
问题：输出太长，不适合零售网站展示

对应 Notebook 章节：Generate a marketing product description from a product fact sheet
"""
from config import get_completion, print_section
from fact_sheet import FACT_SHEET_CHAIR


def run():
    print_section("V1 - 原始 Prompt（问题：输出太长）")

    prompt = f"""
Your task is to help a marketing team create a
description for a retail website of a product based
on a technical fact sheet.

Write a product description based on the information
provided in the technical specifications delimited by
triple backticks.

Technical specifications: ```{FACT_SHEET_CHAIR}```
"""
    response = get_completion(prompt)
    word_count = len(response.split())

    print(f"[Response]\n{response}")
    print(f"\n[字数统计] {word_count} words")
    print("\n⚠️  问题：输出太长了，下一步需要限制字数。")

    return response


if __name__ == "__main__":
    run()
