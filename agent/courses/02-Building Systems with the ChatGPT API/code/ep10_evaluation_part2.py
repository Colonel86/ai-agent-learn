"""
EP10: Evaluation Part II
=========================
当没有唯一正确答案时的评估方法：
1. Rubric-based evaluation（基于评分标准）
2. 与专家答案对比评估（OpenAI evals 风格）
"""
from config import get_completion_from_messages
from utils import (
    get_products_from_query, read_string_to_list,
    get_mentioned_product_info, answer_user_msg,
)


# ──────────────────────────────────────────────
# 生成待评估的回复
# ──────────────────────────────────────────────

def generate_response_for_evaluation():
    customer_msg = """
tell me about the smartx pro phone and the fotosnap camera, the dslr one.
Also, what TVs or TV related products do you have?"""

    products_by_category = get_products_from_query(customer_msg)
    category_and_product_list = read_string_to_list(products_by_category)
    product_info = get_mentioned_product_info(category_and_product_list)
    assistant_answer = answer_user_msg(user_msg=customer_msg, product_info=product_info)

    return customer_msg, product_info, assistant_answer


# ──────────────────────────────────────────────
# 方法 1: Rubric-based evaluation
# ──────────────────────────────────────────────

def eval_with_rubric(test_set: dict, assistant_answer: str) -> str:
    cust_msg = test_set["customer_msg"]
    context = test_set["context"]
    completion = assistant_answer

    system_message = """\
    You are an assistant that evaluates how well the customer service agent \
    answers a user question by looking at the context that the customer service \
    agent is using to generate its response.
    """

    user_message = f"""\
You are evaluating a submitted answer to a question based on the context \
that the agent uses to answer the question.
Here is the data:
    [BEGIN DATA]
    ************
    [Question]: {cust_msg}
    ************
    [Context]: {context}
    ************
    [Submission]: {completion}
    ************
    [END DATA]

Compare the factual content of the submitted answer with the context. \
Ignore any differences in style, grammar, or punctuation.
Answer the following questions:
    - Is the Assistant response based only on the context provided? (Y or N)
    - Does the answer include information that is not provided in the context? (Y or N)
    - Is there any disagreement between the response and the context? (Y or N)
    - Count how many questions the user asked. (output a number)
    - For each question that the user asked, is there a corresponding answer to it?
      Question 1: (Y or N)
      Question 2: (Y or N)
      ...
      Question N: (Y or N)
    - Of the number of questions asked, how many of these questions were addressed by the answer? (output a number)
"""

    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_message},
    ]
    return get_completion_from_messages(messages)


# ──────────────────────────────────────────────
# 方法 2: 与专家答案对比（OpenAI evals 风格）
# ──────────────────────────────────────────────

TEST_SET_IDEAL = {
    "customer_msg": """\
tell me about the smartx pro phone and the fotosnap camera, the dslr one.
Also, what TVs or TV related products do you have?""",
    "ideal_answer": """\
Of course!  The SmartX ProPhone is a powerful \
smartphone with advanced camera features. \
For instance, it has a 12MP dual camera. \
Other features include 5G wireless and 128GB storage. \
It also has a 6.1-inch display.  The price is $899.99.

The FotoSnap DSLR Camera is great for \
capturing stunning photos and videos. \
Some features include 1080p video, \
3-inch LCD, a 24.2MP sensor, \
and interchangeable lenses. \
The price is 599.99.

For TVs and TV related products, we offer 3 TVs \


All TVs offer HDR and Smart TV.

The CineView 4K TV has vibrant colors and smart features. \
Some of these features include a 55-inch display, \
4K resolution. It's priced at 599.

The CineView 8K TV is a stunning 8K TV. \
Some features include a 65-inch display and \
8K resolution.  It's priced at 2999.99

The CineView OLED TV lets you experience vibrant colors. \
Some features include a 55-inch display and 4K resolution. \
It's priced at 1499.99.

We also offer 2 home theater products, both which include bluetooth.\
The SoundMax Home Theater is a powerful home theater system for \
an immersive audio experience.
Its features include 5.1 channel, 1000W output, and wireless subwoofer.
It's priced at 399.99.

The SoundMax Soundbar is a sleek and powerful soundbar.
Its features include 2.1 channel, 300W output, and wireless subwoofer.
It's priced at 199.99

Are there any questions additional you may have about these products \
that you mentioned here?
Or may do you have other questions I can help you with?
    """,
}


def eval_vs_ideal(test_set: dict, assistant_answer: str) -> str:
    cust_msg = test_set["customer_msg"]
    ideal = test_set["ideal_answer"]
    completion = assistant_answer

    system_message = """\
    You are an assistant that evaluates how well the customer service agent \
    answers a user question by comparing the response to the ideal (expert) response.
    Output a single letter and nothing else.
    """

    user_message = f"""\
You are comparing a submitted answer to an expert answer on a given question. Here is the data:
    [BEGIN DATA]
    ************
    [Question]: {cust_msg}
    ************
    [Expert]: {ideal}
    ************
    [Submission]: {completion}
    ************
    [END DATA]

Compare the factual content of the submitted answer with the expert answer. \
Ignore any differences in style, grammar, or punctuation.
    The submitted answer may either be a subset or superset of the expert answer, \
or it may conflict with it. Determine which case applies. Answer the question by \
selecting one of the following options:
    (A) The submitted answer is a subset of the expert answer and is fully consistent with it.
    (B) The submitted answer is a superset of the expert answer and is fully consistent with it.
    (C) The submitted answer contains all the same details as the expert answer.
    (D) There is a disagreement between the submitted answer and the expert answer.
    (E) The answers differ, but these differences don't matter from the perspective of factuality.
  choice_strings: ABCDE
"""

    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_message},
    ]
    return get_completion_from_messages(messages)


# ──────────────────────────────────────────────
# 主演示
# ──────────────────────────────────────────────

def main():
    print("正在生成待评估的回复...\n")
    customer_msg, product_info, assistant_answer = generate_response_for_evaluation()

    print("=" * 60)
    print("[助手回复]")
    print("=" * 60)
    print(assistant_answer)

    # 方法 1: Rubric-based
    print("\n" + "=" * 60)
    print("评估方法 1: Rubric-based evaluation")
    print("=" * 60)
    cust_prod_info = {"customer_msg": customer_msg, "context": product_info}
    rubric_result = eval_with_rubric(cust_prod_info, assistant_answer)
    print(rubric_result)

    # 方法 2: 与专家答案对比
    print("\n" + "=" * 60)
    print("评估方法 2: 与专家答案对比")
    print("=" * 60)
    eval_result = eval_vs_ideal(TEST_SET_IDEAL, assistant_answer)
    print(f"正确回复评级: {eval_result}")

    # 测试一个明显错误的回复
    bad_answer = "life is like a box of chocolates"
    eval_result_bad = eval_vs_ideal(TEST_SET_IDEAL, bad_answer)
    print(f"错误回复评级: {eval_result_bad} (expected D)")


if __name__ == "__main__":
    main()
    print("\n✅ EP10 完成！")
