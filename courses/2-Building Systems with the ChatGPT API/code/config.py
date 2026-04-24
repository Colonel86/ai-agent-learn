"""
共享配置：API 客户端 & 辅助函数
"""
import os
import openai
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

client = openai.OpenAI()
MODEL = os.getenv("MODEL", "gpt-4o-mini")


def get_completion(prompt: str, model: str = MODEL) -> str:
    messages = [{"role": "user", "content": prompt}]
    response = client.chat.completions.create(
        model=model, messages=messages, temperature=0,
    )
    return response.choices[0].message.content


def get_completion_from_messages(
    messages: list[dict],
    model: str = MODEL,
    temperature: float = 0,
    max_tokens: int = 500,
) -> str:
    response = client.chat.completions.create(
        model=model, messages=messages,
        temperature=temperature, max_tokens=max_tokens,
    )
    return response.choices[0].message.content
