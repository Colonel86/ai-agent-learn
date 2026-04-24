"""
EP08: Build an End-to-End System
=================================
将整个课程的 Prompt 链串联成完整的客服系统：
  输入审核 → 提取产品 → 查询详情 → 生成回复 → 输出审核 → 质量评估
支持命令行交互式对话。
"""
from config import get_completion_from_messages, client
from products import get_products_and_category
from utils import (
    find_category_and_product_only, read_string_to_list,
    generate_output_string,
)


def process_user_message(user_input: str, all_messages: list, debug: bool = True):
    """完整的 7 步处理流程"""
    delimiter = "```"

    # Step 1: Moderation 检查输入
    response = client.moderations.create(input=user_input)
    if response.results[0].flagged:
        if debug:
            print("Step 1: Input flagged by Moderation API.")
        return "Sorry, we cannot process this request.", all_messages
    if debug:
        print("Step 1: Input passed moderation check.")

    # Step 2: 提取产品/分类
    products_and_category = get_products_and_category()
    category_and_product_response = find_category_and_product_only(
        user_input, products_and_category
    )
    category_and_product_list = read_string_to_list(category_and_product_response)
    if debug:
        print("Step 2: Extracted list of products.")

    # Step 3: 查询产品详情
    product_information = generate_output_string(category_and_product_list)
    if debug:
        print("Step 3: Looked up product information.")

    # Step 4: 生成回复
    system_message = """
    You are a customer service assistant for a large electronic store. \
    Respond in a friendly and helpful tone, with concise answers. \
    Make sure to ask the user relevant follow-up questions.
    """
    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": f"{delimiter}{user_input}{delimiter}"},
        {"role": "assistant", "content": f"Relevant product information:\n{product_information}"},
    ]
    final_response = get_completion_from_messages(all_messages + messages)
    if debug:
        print("Step 4: Generated response to user question.")
    all_messages = all_messages + messages[1:]

    # Step 5: Moderation 检查输出
    response = client.moderations.create(input=final_response)
    if response.results[0].flagged:
        if debug:
            print("Step 5: Response flagged by Moderation API.")
        return "Sorry, we cannot provide this information.", all_messages
    if debug:
        print("Step 5: Response passed moderation check.")

    # Step 6: 质量评估
    eval_message = f"""
    Customer message: {delimiter}{user_input}{delimiter}
    Agent response: {delimiter}{final_response}{delimiter}

    Does the response sufficiently answer the question?
    """
    eval_messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": eval_message},
    ]
    evaluation_response = get_completion_from_messages(eval_messages)
    if debug:
        print("Step 6: Model evaluated the response.")

    # Step 7: 决定是否使用该回复
    if "Y" in evaluation_response:
        if debug:
            print("Step 7: Model approved the response.")
        return final_response, all_messages
    else:
        if debug:
            print("Step 7: Model disapproved the response.")
        neg_str = "I'm unable to provide the information you're looking for. I'll connect you with a human representative for further assistance."
        return neg_str, all_messages


def demo_single_query():
    print("=" * 60)
    print("Demo: 单次查询的端到端处理")
    print("=" * 60)

    user_input = "tell me about the smartx pro phone and the fotosnap camera, the dslr one. Also what tell me about your tvs"
    response, _ = process_user_message(user_input, [])
    print(f"\n[最终回复]\n{response}\n")


def interactive_chat():
    print("=" * 60)
    print("交互式客服对话（输入 quit 退出）")
    print("=" * 60)

    context = [{"role": "system", "content": "You are Service Assistant"}]

    while True:
        user_input = input("\nYou: ").strip()
        if not user_input or user_input.lower() in ("quit", "exit", "q"):
            print("再见！")
            break

        response, context = process_user_message(user_input, context, debug=False)
        context.append({"role": "assistant", "content": response})
        print(f"\nAssistant: {response}")


if __name__ == "__main__":
    import sys

    if "--chat" in sys.argv:
        interactive_chat()
    else:
        demo_single_query()
        print("提示: 运行 python ep08_end_to_end.py --chat 进入交互式对话模式")
    print("✅ EP08 完成！")
