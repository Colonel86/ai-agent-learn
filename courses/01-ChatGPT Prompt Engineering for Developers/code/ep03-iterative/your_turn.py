"""
自由练习：用你自己的产品规格表跑一遍完整迭代流程

操作步骤：
  1. 修改下方 MY_FACT_SHEET（换成任意产品的规格）
  2. 运行：python your_turn.py
  3. 观察各版本输出，思考还需要哪些改进
"""
from config import get_completion, print_section

# ── TODO: 替换成你自己的产品规格 ─────────────────────────────────────────────
MY_FACT_SHEET = """
OVERVIEW
- Wireless noise-cancelling headphones
- Over-ear design with foldable headband
- Available in: Midnight Black, Pearl White, Navy Blue

SPECS
- Driver size: 40mm dynamic driver
- Frequency response: 20Hz - 20kHz
- Battery life: Up to 30 hours (ANC on), 40 hours (ANC off)
- Charging: USB-C, 10 min charge = 3 hours playback
- Bluetooth: 5.2, range up to 10m
- Weight: 250g

FEATURES
- Active Noise Cancellation (ANC) with 3 modes
- Transparency mode
- Built-in microphone array (4 mics)
- Touch controls on ear cup
- Compatible with voice assistants

MATERIALS
- Ear cushions: Memory foam with protein leather
- Headband: Stainless steel slider with soft padding
- Ear cup: ABS plastic with matte finish

PRODUCT ID: WH-3500
"""
# ─────────────────────────────────────────────────────────────────────────────


def iterate(label: str, prompt: str) -> str:
    print_section(label)
    response = get_completion(prompt)
    print(f"[Response]\n{response}")
    print(f"[字数] {len(response.split())} words")
    return response


def main():
    print("\n🎧 自由练习：耳机产品描述迭代\n")

    # 第 1 版：无约束
    iterate("Step 1 - 原始 Prompt", f"""
Write a product description based on the technical specifications
delimited by triple backticks.
```{MY_FACT_SHEET}```
""")

    # 第 2 版：限字数
    iterate("Step 2 - 限制字数（50 words）", f"""
Write a product description based on the technical specifications
delimited by triple backticks.
Use at most 50 words.
```{MY_FACT_SHEET}```
""")

    # 第 3 版：指定受众
    iterate("Step 3 - 面向消费者电子零售商，聚焦技术参数", f"""
Write a product description based on the technical specifications
delimited by triple backticks.
The description is intended for consumer electronics retailers,
so should highlight technical specs and key differentiators.
Use at most 50 words.
```{MY_FACT_SHEET}```
""")

    # 第 4 版：加产品 ID
    iterate("Step 4 - 末尾加产品 ID", f"""
Write a product description based on the technical specifications
delimited by triple backticks.
The description is intended for consumer electronics retailers,
so should highlight technical specs and key differentiators.
At the end, include the Product ID from the specification.
Use at most 50 words.
```{MY_FACT_SHEET}```
""")

    # 第 5 版：HTML + 规格表
    print_section("Step 5 - HTML 格式 + 规格表格")
    prompt_html = f"""
Write a product description based on the technical specifications
delimited by triple backticks.
The description is intended for consumer electronics retailers,
so should highlight technical specs and key differentiators.
At the end, include the Product ID from the specification.
After the description, include a table titled 'Key Specifications'
with two columns: Spec Name and Value.
Format everything as HTML. Place the description in a <div> element.
```{MY_FACT_SHEET}```
"""
    response_html = get_completion(prompt_html)
    print(f"[HTML Output - 前 400 字符]\n{response_html[:400]}...\n")

    with open("your_turn_output.html", "w", encoding="utf-8") as f:
        f.write(f"<!DOCTYPE html><html><head><meta charset='UTF-8'><style>"
                f"body{{font-family:Arial;max-width:800px;margin:40px auto;padding:0 20px}}"
                f"table{{border-collapse:collapse;width:100%}}"
                f"th,td{{border:1px solid #ddd;padding:8px;text-align:left}}"
                f"th{{background:#f2f2f2}}</style></head><body>{response_html}</body></html>")
    print("✅ 已保存到 your_turn_output.html，用浏览器打开预览")


if __name__ == "__main__":
    main()
