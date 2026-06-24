"""
迭代第 3 版：指定目标受众
改进：说明描述面向家具零售商，应聚焦材料和技术细节
观察：输出内容从"消费者导向"转变为"技术导向"

对应 Notebook 章节：Issue 2 - Text focuses on the wrong details
"""
from config import get_completion, print_section
from fact_sheet import FACT_SHEET_CHAIR


def run():
    print_section("V3 - 指定目标受众（Issue 2: Wrong Details → 面向家具零售商）")

    prompt = f"""
Your task is to help a marketing team create a
description for a retail website of a product based
on a technical fact sheet.

Write a product description based on the information
provided in the technical specifications delimited by
triple backticks.

The description is intended for furniture retailers,
so should be technical in nature and focus on the
materials the product is constructed from.

Use at most 50 words.

Technical specifications: ```{FACT_SHEET_CHAIR}```
"""
    response = get_completion(prompt)
    word_count = len(response.split())

    print(f"[Response]\n{response}")
    print(f"\n[字数统计] {word_count} words")
    print("\n💡 对比 V2：是否出现了 'aluminum'、'nylon'、'HD36 foam' 等材料词汇？")

    return response


if __name__ == "__main__":
    run()
