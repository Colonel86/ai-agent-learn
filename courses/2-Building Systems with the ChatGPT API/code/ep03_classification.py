"""
EP03: Evaluate Inputs — Classification
=======================================
将客户查询分类为主类别和子类别，用于路由到不同的处理流程。
"""
from config import get_completion_from_messages


def demo_classification():
    print("=" * 60)
    print("Demo: 客户查询分类")
    print("=" * 60)

    delimiter = "####"
    system_message = f"""
You will be provided with customer service queries. \
The customer service query will be delimited with \
{delimiter} characters.
Classify each query into a primary category \
and a secondary category.
Provide your output in json format with the \
keys: primary and secondary.

Primary categories: Billing, Technical Support, \
Account Management, or General Inquiry.

Billing secondary categories:
Unsubscribe or upgrade
Add a payment method
Explanation for charge
Dispute a charge

Technical Support secondary categories:
General troubleshooting
Device compatibility
Software updates

Account Management secondary categories:
Password reset
Update personal information
Close account
Account security

General Inquiry secondary categories:
Product information
Pricing
Feedback
Speak to a human
"""

    # 测试 1: 删除账号请求
    user_message_1 = "I want you to delete my profile and all of my user data"
    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": f"{delimiter}{user_message_1}{delimiter}"},
    ]
    response = get_completion_from_messages(messages)
    print(f"Q: {user_message_1}")
    print(f"A: {response}\n")

    # 测试 2: 产品咨询
    user_message_2 = "Tell me more about your flat screen tvs"
    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": f"{delimiter}{user_message_2}{delimiter}"},
    ]
    response = get_completion_from_messages(messages)
    print(f"Q: {user_message_2}")
    print(f"A: {response}\n")


if __name__ == "__main__":
    demo_classification()
    print("✅ EP03 完成！")
