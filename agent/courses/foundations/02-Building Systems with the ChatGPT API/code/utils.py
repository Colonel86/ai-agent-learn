"""
工具函数 — ep08/ep09/ep10 等课程共享
对应原始课程中的 utils.py 模块
"""
import json
from config import get_completion_from_messages, MODEL, client
from products import (
    products, get_product_by_name, get_products_by_category, get_products_and_category,
)


# ──────────────────────────────────────────────
# 解析 LLM 输出
# ──────────────────────────────────────────────

def read_string_to_list(input_string: str | None) -> list | None:
    if input_string is None:
        return None
    try:
        input_string = input_string.replace("'", '"')
        return json.loads(input_string)
    except json.JSONDecodeError:
        print("Error: Invalid JSON string")
        return None


# ──────────────────────────────────────────────
# 根据分类/产品列表生成产品信息文本
# ──────────────────────────────────────────────

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
                category_name = data["category"]
                for product in get_products_by_category(category_name):
                    output_string += json.dumps(product, indent=4) + "\n"
            else:
                print("Error: Invalid object format")
        except Exception as e:
            print(f"Error: {e}")
    return output_string


# ──────────────────────────────────────────────
# 从用户查询中提取产品/分类
# ──────────────────────────────────────────────

def find_category_and_product_only(user_input: str, products_and_category: dict) -> str:
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

    Where the categories and products must be found in the customer service query.
    If a product is mentioned, it must be associated with the correct category \
in the allowed products list below.
    If no products or categories are found, output an empty list.

    Allowed products are provided in JSON format.
    The keys of each item represent the category.
    The values of each item is a list of products that are within that category.
    Allowed products: {products_and_category}
    """

    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": f"{delimiter}{user_input}{delimiter}"},
    ]
    return get_completion_from_messages(messages)


def get_products_from_query(user_msg: str) -> str:
    """ep10 使用的便捷封装"""
    products_and_category = get_products_and_category()
    return find_category_and_product_only(user_msg, products_and_category)


def get_mentioned_product_info(category_and_product_list: list | None) -> str:
    """ep10 使用：根据提取结果获取产品详细信息"""
    return generate_output_string(category_and_product_list)


# ──────────────────────────────────────────────
# 生成最终回复
# ──────────────────────────────────────────────

def answer_user_msg(user_msg: str, product_info: str) -> str:
    """ep10 使用：根据产品信息回答用户问题"""
    system_message = """
    You are a customer service assistant for a large electronic store. \
    Respond in a friendly and helpful tone, with concise answers. \
    Make sure to ask the user relevant follow-up questions.
    """
    delimiter = "```"
    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": f"{delimiter}{user_msg}{delimiter}"},
        {"role": "assistant", "content": f"Relevant product information:\n{product_info}"},
    ]
    return get_completion_from_messages(messages)
