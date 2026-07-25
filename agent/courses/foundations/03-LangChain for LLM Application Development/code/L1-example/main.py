"""
LangChain Lesson 1: Models, Prompts, and Output Parsers
（LangChain 1.x 版本，使用 with_structured_output 替代 StructuredOutputParser）

演示三个核心模式：
  1. 直接调用 OpenAI（无 LangChain）
  2. ChatPromptTemplate（提示词模板复用）
  3. with_structured_output（结构化输出，生产推荐）
"""

import os
from typing import List

from dotenv import load_dotenv, find_dotenv
from openai import OpenAI
from pydantic import BaseModel, Field

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

load_dotenv(find_dotenv())

# 从 .env 读 MODEL，默认 deepseek-v4-flash（兼容 OpenAI / DeepSeek 后端）
LLM_MODEL = os.getenv("MODEL", "deepseek-v4-flash")


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


# ── 2. LangChain ChatPromptTemplate ─────────────────────────────────────────

def demo_prompt_template():
    print("\n" + "=" * 60)
    print("2. LangChain ChatPromptTemplate")
    print("=" * 60)

    chat = ChatOpenAI(
        temperature=0.0,
        model=LLM_MODEL,
        # deepseek-v4-flash 默认开 thinking 模式,影响结构化输出与确定性,统一关闭
        extra_body={"thinking": {"type": "disabled"}},
    )

    template_string = """Translate the text delimited by triple backticks \
into a style that is {style}.
text: ```{text}```
"""
    prompt_template = ChatPromptTemplate.from_template(template_string)
    print("模板输入变量：", prompt_template.input_variables)

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


# ── 3. with_structured_output（v1 推荐：Pydantic schema + 原生 JSON 模式）────

class ReviewExtraction(BaseModel):
    """从商品评论中抽取的字段。"""

    gift: bool = Field(
        description="商品是否作为礼物购买。是为 True，否或未知为 False。"
    )
    delivery_days: int = Field(
        description="商品送达耗时（天）。如评论里没提，输出 -1。"
    )
    price_value: List[str] = Field(
        description="评论中关于价格或性价比的句子列表。"
    )


def demo_structured_output():
    print("\n" + "=" * 60)
    print("3. with_structured_output - LLM 输出 → Pydantic 对象")
    print("=" * 60)

    chat = ChatOpenAI(
        temperature=0.0,
        model=LLM_MODEL,
        # deepseek-v4-flash 默认开 thinking 模式,影响结构化输出与确定性,统一关闭
        extra_body={"thinking": {"type": "disabled"}},
    )

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

    # 关键一行：把 chat model 包装成「输入 prompt → 输出 Pydantic 对象」的 runnable
    # method="json_mode" 适用于 DeepSeek 等支持 OpenAI 兼容 JSON 模式的后端
    structured_chat = chat.with_structured_output(
        ReviewExtraction,
        method="json_mode",
    )

    review_template = """\
For the following text, extract the following information and respond \
in JSON with keys: gift (bool), delivery_days (int), price_value (list of strings).

gift: Was the item purchased as a gift? True/False.
delivery_days: How many days did delivery take? -1 if unknown.
price_value: Sentences about price/value as a list.

text: {text}
"""
    prompt = ChatPromptTemplate.from_template(review_template)

    # 链式组合：prompt | structured_chat
    chain = prompt | structured_chat
    result: ReviewExtraction = chain.invoke({"text": customer_review})

    print("\n解析后（Pydantic 对象）：")
    print(result)
    print(f"\n类型验证: {type(result).__name__}")
    print(f"gift          = {result.gift}")
    print(f"delivery_days = {result.delivery_days}")
    print(f"price_value   = {result.price_value}")

    print("\n转 dict（便于 JSON 序列化）：")
    print(result.model_dump())


# ── 主入口 ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    demo_direct_api()
    demo_prompt_template()
    demo_structured_output()
