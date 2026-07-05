"""
EP09: Evaluation Part I
========================
当存在"标准答案"时，评估 LLM 的分类/提取准确性。
包含 v1 和 v2 两个版本的 prompt，以及自动化测试集评估。
"""
import json
from config import get_completion_from_messages
from products import get_products_and_category


products_and_category = get_products_and_category()


# ──────────────────────────────────────────────
# v1: 初始版本
# ──────────────────────────────────────────────

def find_category_and_product_v1(user_input: str, products_and_category: dict) -> str:
    delimiter = "####"
    system_message = f"""
    You will be provided with customer service queries. \
    The customer service query will be delimited with {delimiter} characters.
    Output a python list of json objects, where each object has the following format:
        'category': <one of Computers and Laptops, Smartphones and Accessories, \
Televisions and Home Theater Systems, Gaming Consoles and Accessories, \
Audio Equipment, Cameras and Camcorders>,
    AND
        'products': <a list of products that must be found in the allowed products below>

    Where the categories and products must be found in the customer service query.
    If a product is mentioned, it must be associated with the correct category \
in the allowed products list below.
    If no products or categories are found, output an empty list.

    List out all products that are relevant to the customer service query based \
on how closely it relates to the product name and product category.
    Do not assume, from the name of the product, any features or attributes \
such as relative quality or price.

    The allowed products are provided in JSON format.
    The keys of each item represent the category.
    The values of each item is a list of products that are within that category.
    Allowed products: {products_and_category}
    """

    few_shot_user_1 = """I want the most expensive computer."""
    few_shot_assistant_1 = """
    [{'category': 'Computers and Laptops', \
'products': ['TechPro Ultrabook', 'BlueWave Gaming Laptop', 'PowerLite Convertible', 'TechPro Desktop', 'BlueWave Chromebook']}]
    """

    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": f"{delimiter}{few_shot_user_1}{delimiter}"},
        {"role": "assistant", "content": few_shot_assistant_1},
        {"role": "user", "content": f"{delimiter}{user_input}{delimiter}"},
    ]
    return get_completion_from_messages(messages)


# ──────────────────────────────────────────────
# v2: 改进版（处理 hard cases）
# ──────────────────────────────────────────────

def find_category_and_product_v2(user_input: str, products_and_category: dict) -> str:
    delimiter = "####"
    system_message = f"""
    You will be provided with customer service queries. \
    The customer service query will be delimited with {delimiter} characters.
    Output a python list of json objects, where each object has the following format:
        'category': <one of Computers and Laptops, Smartphones and Accessories, \
Televisions and Home Theater Systems, Gaming Consoles and Accessories, \
Audio Equipment, Cameras and Camcorders>,
    AND
        'products': <a list of products that must be found in the allowed products below>
    Do not output any additional text that is not in JSON format.
    Do not write any explanatory text after outputting the requested JSON.

    Where the categories and products must be found in the customer service query.
    If a product is mentioned, it must be associated with the correct category \
in the allowed products list below.
    If no products or categories are found, output an empty list.

    List out all products that are relevant to the customer service query based \
on how closely it relates to the product name and product category.
    Do not assume, from the name of the product, any features or attributes \
such as relative quality or price.

    The allowed products are provided in JSON format.
    The keys of each item represent the category.
    The values of each item is a list of products that are within that category.
    Allowed products: {products_and_category}
    """

    few_shot_user_1 = """I want the most expensive computer. What do you recommend?"""
    few_shot_assistant_1 = """
    [{'category': 'Computers and Laptops', \
'products': ['TechPro Ultrabook', 'BlueWave Gaming Laptop', 'PowerLite Convertible', 'TechPro Desktop', 'BlueWave Chromebook']}]
    """

    few_shot_user_2 = """I want the most cheapest computer. What do you recommend?"""
    few_shot_assistant_2 = """
    [{'category': 'Computers and Laptops', \
'products': ['TechPro Ultrabook', 'BlueWave Gaming Laptop', 'PowerLite Convertible', 'TechPro Desktop', 'BlueWave Chromebook']}]
    """

    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": f"{delimiter}{few_shot_user_1}{delimiter}"},
        {"role": "assistant", "content": few_shot_assistant_1},
        {"role": "user", "content": f"{delimiter}{few_shot_user_2}{delimiter}"},
        {"role": "assistant", "content": few_shot_assistant_2},
        {"role": "user", "content": f"{delimiter}{user_input}{delimiter}"},
    ]
    return get_completion_from_messages(messages)


# ──────────────────────────────────────────────
# 评估函数
# ──────────────────────────────────────────────

def eval_response_with_ideal(response: str, ideal, debug: bool = False) -> float:
    if debug:
        print("response:", response)

    json_like_str = response.replace("'", '"')
    l_of_d = json.loads(json_like_str)

    if l_of_d == [] and ideal == []:
        return 1.0
    elif l_of_d == [] or ideal == []:
        return 0.0

    correct = 0
    for d in l_of_d:
        cat = d.get("category")
        prod_l = d.get("products")
        if cat and prod_l:
            prod_set = set(prod_l)
            ideal_cat = ideal.get(cat)
            if ideal_cat:
                prod_set_ideal = set(ideal_cat)
                if prod_set == prod_set_ideal:
                    correct += 1
                else:
                    print(f"incorrect — got: {prod_set}, expected: {prod_set_ideal}")
                    if prod_set <= prod_set_ideal:
                        print("  (response is a subset of ideal)")
                    elif prod_set >= prod_set_ideal:
                        print("  (response is a superset of ideal)")
            else:
                if debug:
                    print(f"did not find category {cat} in ideal: {ideal}")

    return correct / len(l_of_d)


# ──────────────────────────────────────────────
# 测试集
# ──────────────────────────────────────────────

MSG_IDEAL_PAIRS = [
    {
        "customer_msg": "Which TV can I buy if I'm on a budget?",
        "ideal_answer": {
            "Televisions and Home Theater Systems": {
                "CineView 4K TV", "SoundMax Home Theater", "CineView 8K TV",
                "SoundMax Soundbar", "CineView OLED TV",
            }
        },
    },
    {
        "customer_msg": "I need a charger for my smartphone",
        "ideal_answer": {
            "Smartphones and Accessories": {
                "MobiTech PowerCase", "MobiTech Wireless Charger", "SmartX EarBuds",
            }
        },
    },
    {
        "customer_msg": "What computers do you have?",
        "ideal_answer": {
            "Computers and Laptops": {
                "TechPro Ultrabook", "BlueWave Gaming Laptop", "PowerLite Convertible",
                "TechPro Desktop", "BlueWave Chromebook",
            }
        },
    },
    {
        "customer_msg": "tell me about the smartx pro phone and the fotosnap camera, the dslr one. Also, what TVs do you have?",
        "ideal_answer": {
            "Smartphones and Accessories": {"SmartX ProPhone"},
            "Cameras and Camcorders": {"FotoSnap DSLR Camera"},
            "Televisions and Home Theater Systems": {
                "CineView 4K TV", "SoundMax Home Theater", "CineView 8K TV",
                "SoundMax Soundbar", "CineView OLED TV",
            },
        },
    },
    {
        "customer_msg": "tell me about the CineView TV, the 8K one, Gamesphere console, the X one.\nI'm on a budget, what computers do you have?",
        "ideal_answer": {
            "Televisions and Home Theater Systems": {"CineView 8K TV"},
            "Gaming Consoles and Accessories": {"GameSphere X"},
            "Computers and Laptops": {
                "TechPro Ultrabook", "BlueWave Gaming Laptop", "PowerLite Convertible",
                "TechPro Desktop", "BlueWave Chromebook",
            },
        },
    },
    {
        "customer_msg": "What smartphones do you have?",
        "ideal_answer": {
            "Smartphones and Accessories": {
                "SmartX ProPhone", "MobiTech PowerCase", "SmartX MiniPhone",
                "MobiTech Wireless Charger", "SmartX EarBuds",
            }
        },
    },
    {
        "customer_msg": "I'm on a budget. Can you recommend some smartphones to me?",
        "ideal_answer": {
            "Smartphones and Accessories": {
                "SmartX EarBuds", "SmartX MiniPhone", "MobiTech PowerCase",
                "SmartX ProPhone", "MobiTech Wireless Charger",
            }
        },
    },
    {
        "customer_msg": "What Gaming consoles would be good for my friend who is into racing games?",
        "ideal_answer": {
            "Gaming Consoles and Accessories": {
                "GameSphere X", "ProGamer Controller", "GameSphere Y",
                "ProGamer Racing Wheel", "GameSphere VR Headset",
            }
        },
    },
    {
        "customer_msg": "What could be a good present for my videographer friend?",
        "ideal_answer": {
            "Cameras and Camcorders": {
                "FotoSnap DSLR Camera", "ActionCam 4K", "FotoSnap Mirrorless Camera",
                "ZoomMaster Camcorder", "FotoSnap Instant Camera",
            }
        },
    },
    {
        "customer_msg": "I would like a hot tub time machine.",
        "ideal_answer": [],
    },
]


# ──────────────────────────────────────────────
# 主演示
# ──────────────────────────────────────────────

def demo_evaluate_v1():
    print("=" * 60)
    print("Demo 1: v1 Prompt — 单个测试")
    print("=" * 60)
    msg = "Which TV can I buy if I'm on a budget?"
    result = find_category_and_product_v1(msg, products_and_category)
    print(f"Q: {msg}")
    print(f"A: {result}\n")


def demo_evaluate_v2():
    print("=" * 60)
    print("Demo 2: v2 Prompt — Hard test case")
    print("=" * 60)
    msg = "tell me about the CineView TV, the 8K one, Gamesphere console, the X one.\nI'm on a budget, what computers do you have?"
    result = find_category_and_product_v2(msg, products_and_category)
    print(f"Q: {msg}")
    print(f"A: {result}\n")


def demo_run_all_tests():
    print("=" * 60)
    print("Demo 3: 自动化测试集评估 (v2)")
    print("=" * 60)

    score_accum = 0
    for i, pair in enumerate(MSG_IDEAL_PAIRS):
        customer_msg = pair["customer_msg"]
        ideal = pair["ideal_answer"]

        response = find_category_and_product_v2(customer_msg, products_and_category)

        try:
            score = eval_response_with_ideal(response, ideal)
        except Exception as e:
            print(f"example {i}: Error — {e}")
            score = 0

        print(f"example {i}: score = {score}")
        score_accum += score

    n_examples = len(MSG_IDEAL_PAIRS)
    fraction_correct = score_accum / n_examples
    print(f"\nFraction correct: {fraction_correct:.2f} ({int(score_accum)}/{n_examples})")


if __name__ == "__main__":
    import sys

    if "--full" in sys.argv:
        demo_run_all_tests()
    else:
        demo_evaluate_v1()
        demo_evaluate_v2()
        print("提示: 运行 python ep09_evaluation_part1.py --full 运行完整测试集")

    print("✅ EP09 完成！")
