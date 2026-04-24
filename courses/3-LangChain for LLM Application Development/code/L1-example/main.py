"""
LangChain Lesson 1: Models, Prompts, and Output Parsers
演示三个核心模式：直接调用 → PromptTemplate → StructuredOutputParser
"""

import os
from dotenv import load_dotenv, find_dotenv
from openai import OpenAI
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import ResponseSchema, StructuredOutputParser

load_dotenv(find_dotenv())

LLM_MODEL = "gpt-3.5-turbo"

# ── 1. 直接调用 OpenAI（无 LangChain）────────────────────────────────────────

def get_completion(prompt: str, model: str = LLM_MODEL) -> str:
    client = OpenAI()
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )
    return response.choices[0].message.content


def demo_direct_api():
    print("=" * 60)
    print("1. 直接调用 OpenAI API")
    print("=" * 60)

    customer_email = """
    Arrr, I be fuming that me blender lid flew off and splattered
    me kitchen walls with smoothie! And to make matters worse,
    the warranty don't cover the cost of cleaning up me kitchen.
    I need yer help right now, matey!
    """

    style = "American English in a calm and respectful tone"
    prompt = f"""Translate the text delimited by triple backticks
into a style that is {style}.
text: ```{customer_email}```
"""
    response = get_completion(prompt)
    print("翻译结果：")
    print(response)


# ── 2. LangChain PromptTemplate ───────────────────────────────────────────────

def demo_prompt_template():
    print("\n" + "=" * 60)
    print("2. LangChain PromptTemplate")
    print("=" * 60)

    chat = ChatOpenAI(temperature=0.0, model=LLM_MODEL)

    template_string = """Translate the text delimited by triple backticks \
into a style that is {style}.
text: ```{text}```
"""
    prompt_template = ChatPromptTemplate.from_template(template_string)
    print("模板输入变量：", prompt_template.messages[0].prompt.input_variables)

    # 场景 A：客户投诉邮件（海盗体 → 礼貌美式英语）
    customer_email = """
    Arrr, I be fuming that me blender lid flew off and splattered
    me kitchen walls with smoothie! And to make matters worse,
    the warranty don't cover the cost of cleaning up me kitchen.
    I need yer help right now, matey!
    """
    customer_messages = prompt_template.format_messages(
        style="American English in a calm and respectful tone",
        text=customer_email,
    )
    customer_response = chat.invoke(customer_messages)
    print("\n[客户邮件翻译] 海盗体 → 礼貌英语：")
    print(customer_response.content)

    # 场景 B：客服回复（英文 → 海盗体），复用同一模板
    service_reply = """Hey there customer, the warranty does not cover \
cleaning expenses for your kitchen because it's your fault that \
you misused your blender by forgetting to put the lid on. Tough luck! See ya!
"""
    service_messages = prompt_template.format_messages(
        style="a polite tone that speaks in English Pirate",
        text=service_reply,
    )
    service_response = chat.invoke(service_messages)
    print("\n[客服回复翻译] 英文 → 海盗体：")
    print(service_response.content)


# ── 3. StructuredOutputParser ─────────────────────────────────────────────────

def demo_output_parser():
    print("\n" + "=" * 60)
    print("3. StructuredOutputParser - LLM 输出 → Python dict")
    print("=" * 60)

    chat = ChatOpenAI(temperature=0.0, model=LLM_MODEL)

    customer_review = """\
This leaf blower is pretty amazing. It has four settings: \
candle blower, gentle breeze, windy city, and tornado. \
It arrived in two days, just in time for my wife's anniversary present. \
I think my wife liked it so much she was speechless. \
So far I've been the only one using it every other morning \
to clear the leaves on our lawn. \
It's slightly more expensive than the other leaf blowers out there, \
but I think it's worth it for the extra features.
"""

    # 定义期望输出字段
    response_schemas = [
        ResponseSchema(
            name="gift",
            description="Was the item purchased as a gift for someone else? "
                        "Answer True if yes, False if not or unknown.",
        ),
        ResponseSchema(
            name="delivery_days",
            description="How many days did it take for the product to arrive? "
                        "If this information is not found, output -1.",
        ),
        ResponseSchema(
            name="price_value",
            description="Extract any sentences about the value or price, "
                        "output them as a comma-separated Python list.",
        ),
    ]

    output_parser = StructuredOutputParser.from_response_schemas(response_schemas)
    format_instructions = output_parser.get_format_instructions()

    review_template = """\
For the following text, extract the following information:

gift: Was the item purchased as a gift? Answer True or False.
delivery_days: How many days did delivery take? Output -1 if unknown.
price_value: Extract sentences about value/price as a comma-separated list.

text: {text}

{format_instructions}
"""

    prompt = ChatPromptTemplate.from_template(template=review_template)
    messages = prompt.format_messages(
        text=customer_review,
        format_instructions=format_instructions,
    )

    response = chat.invoke(messages)
    print("\nLLM 原始输出（字符串）：")
    print(response.content)

    output_dict = output_parser.parse(response.content)
    print("\n解析后（Python dict）：")
    print(output_dict)
    print(f"\n类型验证: {type(output_dict)}")
    print(f"gift       = {output_dict.get('gift')}")
    print(f"delivery_days = {output_dict.get('delivery_days')}")
    print(f"price_value   = {output_dict.get('price_value')}")


# ── 主入口 ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    demo_direct_api()
    demo_prompt_template()
    demo_output_parser()
