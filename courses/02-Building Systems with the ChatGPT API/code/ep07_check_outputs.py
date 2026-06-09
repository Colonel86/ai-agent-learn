"""
EP07: Check Outputs
====================
检查 LLM 输出：
1. 用 Moderation API 检查有害内容
2. 用另一个 LLM 调用验证回复是否基于事实
"""
from config import get_completion_from_messages, client


def demo_moderation_check():
    print("=" * 60)
    print("Demo 1: Moderation API 检查输出")
    print("=" * 60)

    final_response_to_customer = """
The SmartX ProPhone has a 6.1-inch display, 128GB storage, \
12MP dual camera, and 5G. The FotoSnap DSLR Camera \
has a 24.2MP sensor, 1080p video, 3-inch LCD, and \
interchangeable lenses. We have a variety of TVs, including \
the CineView 4K TV with a 55-inch display, 4K resolution, \
HDR, and smart TV features. We also have the SoundMax \
Home Theater system with 5.1 channel, 1000W output, wireless \
subwoofer, and Bluetooth. Do you have any specific questions \
about these products or any other products we offer?
"""
    # 优先尝试 OpenAI 原生 Moderation API
    try:
        response = client.moderations.create(input=final_response_to_customer)
        moderation_output = response.results[0]
        print(f"[OpenAI Moderation] flagged: {moderation_output.flagged}\n")
        return
    except Exception as e:
        print(f"[提示] Moderation API 不可用（{type(e).__name__}），")
        print(f"        当前 base_url 可能不支持该端点（如 DeepSeek）。")
        print(f"        改用 chat completion 模拟 moderation。\n")

    # Fallback：用 chat completion 模拟内容审核
    system_message = """\
You are a content moderation classifier. \
Analyze the assistant's response and respond ONLY with valid JSON:
{
  "flagged": true/false,
  "reason": "brief explanation"
}"""
    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": final_response_to_customer},
    ]
    result = get_completion_from_messages(messages, temperature=0, max_tokens=200)
    print(f"[Chat-based Moderation 输出]\n{result}\n")


def demo_factual_check():
    print("=" * 60)
    print("Demo 2: 验证回复是否基于产品信息")
    print("=" * 60)

    system_message = """
You are an assistant that evaluates whether \
customer service agent responses sufficiently \
answer customer questions, and also validates that \
all the facts the assistant cites from the product \
information are correct.
The product information and user and customer \
service agent messages will be delimited by \
3 backticks, i.e. ```.
Respond with a Y or N character, with no punctuation:
Y - if the output sufficiently answers the question \
AND the response correctly uses product information
N - otherwise

Output a single letter only.
"""

    customer_message = """tell me about the smartx pro phone and \
the fotosnap camera, the dslr one. \
Also tell me about your tvs"""

    product_information = """{ "name": "SmartX ProPhone", "category": "Smartphones and Accessories", "brand": "SmartX", "model_number": "SX-PP10", "warranty": "1 year", "rating": 4.6, "features": [ "6.1-inch display", "128GB storage", "12MP dual camera", "5G" ], "description": "A powerful smartphone with advanced camera features.", "price": 899.99 } { "name": "FotoSnap DSLR Camera", "category": "Cameras and Camcorders", "brand": "FotoSnap", "model_number": "FS-DSLR200", "warranty": "1 year", "rating": 4.7, "features": [ "24.2MP sensor", "1080p video", "3-inch LCD", "Interchangeable lenses" ], "description": "Capture stunning photos and videos with this versatile DSLR camera.", "price": 599.99 }"""

    # 测试 1: 正确回复
    good_response = """The SmartX ProPhone has a 6.1-inch display, 128GB storage, \
12MP dual camera, and 5G. The FotoSnap DSLR Camera has a 24.2MP sensor, \
1080p video, 3-inch LCD, and interchangeable lenses."""

    q_a_pair = f"""
Customer message: ```{customer_message}```
Product information: ```{product_information}```
Agent response: ```{good_response}```

Does the response use the retrieved information correctly?
Does the response sufficiently answer the question

Output Y or N
"""
    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": q_a_pair},
    ]
    response = get_completion_from_messages(messages, max_tokens=1)
    print(f"正确回复的评估: {response} (expected Y)")

    # 测试 2: 无关回复
    bad_response = "life is like a box of chocolates"
    q_a_pair = f"""
Customer message: ```{customer_message}```
Product information: ```{product_information}```
Agent response: ```{bad_response}```

Does the response use the retrieved information correctly?
Does the response sufficiently answer the question?

Output Y or N
"""
    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": q_a_pair},
    ]
    response = get_completion_from_messages(messages)
    print(f"无关回复的评估: {response} (expected N)\n")


if __name__ == "__main__":
    demo_moderation_check()
    demo_factual_check()
    print("✅ EP07 完成！")
