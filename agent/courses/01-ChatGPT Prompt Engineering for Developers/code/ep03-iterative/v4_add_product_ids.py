"""
迭代第 4 版：在描述末尾加入产品 ID
改进：At the end of the description, include every 7-character Product ID
观察：模型能从规格表中识别并附加 SWC-100、SWC-110

对应 Notebook 章节：Issue 2 续 - 加入 Product ID
"""
from config import get_completion, print_section
from fact_sheet import FACT_SHEET_CHAIR


def run():
    print_section("V4 - 加入产品 ID（在 V3 基础上追加 Product ID 要求）")

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

At the end of the description, include every 7-character
Product ID in the technical specification.

Use at most 50 words.

Technical specifications: ```{FACT_SHEET_CHAIR}```
"""
    response = get_completion(prompt)
    word_count = len(response.split())

    print(f"[Response]\n{response}")
    print(f"\n[字数统计] {word_count} words")

    # 验证产品 ID 是否出现
    for pid in ["SWC-100", "SWC-110"]:
        if pid in response:
            print(f"✅ 产品 ID {pid} 已包含")
        else:
            print(f"⚠️  产品 ID {pid} 未找到")

    return response


if __name__ == "__main__":
    run()
