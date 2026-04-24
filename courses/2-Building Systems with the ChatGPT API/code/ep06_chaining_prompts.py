"""
EP06: Process Inputs — Chaining Prompts
========================================
将复杂任务拆分为多个 Prompt 链式调用：
1. 提取产品/分类 → 2. 查询产品详情 → 3. 生成最终回复
"""
import json
from config import get_completion_from_messages
from products import products, get_product_by_name, get_products_by_category


# ──────────────────────────────────────────────
# Step 1: 提取产品和分类
# ──────────────────────────────────────────────

DELIMITER = "####"

EXTRACTION_SYSTEM_MSG = f"""
You will be provided with customer service queries. \
The customer service query will be delimited with \
{DELIMITER} characters.
Output a python list of objects, where each object has \
the following format:
    'category': <one of Computers and Laptops, \
    Smartphones and Accessories, \
    Televisions and Home Theater Systems, \
    Gaming Consoles and Accessories, \
    Audio Equipment, Cameras and Camcorders>,
OR
    'products': <a list of products that must \
    be found in the allowed products below>

Where the categories and products must be found in \
the customer service query.
If a product is mentioned, it must be associated with \
the correct category in the allowed products list below.
If no products or categories are found, output an \
empty list.

Allowed products:

Computers and Laptops category:
TechPro Ultrabook
BlueWave Gaming Laptop
PowerLite Convertible
TechPro Desktop
BlueWave Chromebook

Smartphones and Accessories category:
SmartX ProPhone
MobiTech PowerCase
SmartX MiniPhone
MobiTech Wireless Charger
SmartX EarBuds

Televisions and Home Theater Systems category:
CineView 4K TV
SoundMax Home Theater
CineView 8K TV
SoundMax Soundbar
CineView OLED TV

Gaming Consoles and Accessories category:
GameSphere X
ProGamer Controller
GameSphere Y
ProGamer Racing Wheel
GameSphere VR Headset

Audio Equipment category:
AudioPhonic Noise-Canceling Headphones
WaveSound Bluetooth Speaker
AudioPhonic True Wireless Earbuds
WaveSound Soundbar
AudioPhonic Turntable

Cameras and Camcorders category:
FotoSnap DSLR Camera
ActionCam 4K
FotoSnap Mirrorless Camera
ZoomMaster Camcorder
FotoSnap Instant Camera

Only output the list of objects, with nothing else.
"""


def read_string_to_list(input_string: str | None) -> list | None:
    if input_string is None:
        return None
    try:
        input_string = input_string.replace("'", '"')
        return json.loads(input_string)
    except json.JSONDecodeError:
        print("Error: Invalid JSON string")
        return None


def generate_output_string(data_list: list | None) -> str:
    output_string = ""
    if data_list is None:
        return output_string
    for data in data_list:
        try:
            if "products" in data:
                for product_name in data["products"]:
                    product = get_product_by_name(product_name)
                    if product:
                        output_string += json.dumps(product, indent=4) + "\n"
                    else:
                        print(f"Error: Product '{product_name}' not found")
            elif "category" in data:
                for product in get_products_by_category(data["category"]):
                    output_string += json.dumps(product, indent=4) + "\n"
            else:
                print("Error: Invalid object format")
        except Exception as e:
            print(f"Error: {e}")
    return output_string


# ──────────────────────────────────────────────
# 演示
# ──────────────────────────────────────────────

def demo_chaining():
    print("=" * 60)
    print("Demo: 链式 Prompt — 从提取到回复的完整流程")
    print("=" * 60)

    user_message = """tell me about the smartx pro phone and \
the fotosnap camera, the dslr one. \
Also tell me about your tvs"""

    # ── Chain Step 1: 提取产品/分类 ──
    print("\n[Step 1] 提取产品和分类...")
    messages = [
        {"role": "system", "content": EXTRACTION_SYSTEM_MSG},
        {"role": "user", "content": f"{DELIMITER}{user_message}{DELIMITER}"},
    ]
    extraction_response = get_completion_from_messages(messages)
    print(extraction_response)

    # ── Chain Step 2: 查询产品详情 ──
    print("\n[Step 2] 查询产品详情...")
    category_and_product_list = read_string_to_list(extraction_response)
    product_info = generate_output_string(category_and_product_list)
    print(f"(已加载 {product_info.count('name')} 个产品信息)")

    # ── Chain Step 3: 生成最终回复 ──
    print("\n[Step 3] 生成最终回复...")
    system_message = """
You are a customer service assistant for a \
large electronic store. \
Respond in a friendly and helpful tone, \
with very concise answers. \
Make sure to ask the user relevant follow up questions.
"""
    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_message},
        {"role": "assistant", "content": f"Relevant product information:\n{product_info}"},
    ]
    final_response = get_completion_from_messages(messages)
    print(final_response)


def demo_no_match():
    print("\n" + "=" * 60)
    print("Demo: 无匹配产品的查询")
    print("=" * 60)

    user_message = "my router isn't working"
    messages = [
        {"role": "system", "content": EXTRACTION_SYSTEM_MSG},
        {"role": "user", "content": f"{DELIMITER}{user_message}{DELIMITER}"},
    ]
    response = get_completion_from_messages(messages)
    print(f"Q: {user_message}")
    print(f"A: {response}\n")


if __name__ == "__main__":
    demo_chaining()
    demo_no_match()
    print("✅ EP06 完成！")
