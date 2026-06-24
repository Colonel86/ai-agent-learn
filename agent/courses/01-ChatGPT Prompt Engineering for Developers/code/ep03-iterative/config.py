"""
API 配置与辅助函数（与 ep02 共用相同结构）
"""
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def get_completion(prompt: str, model: str = "gpt-3.5-turbo", temperature: float = 0) -> str:
    """发送 prompt，返回模型的文本回复。"""
    messages = [{"role": "user", "content": prompt}]
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
    )
    return response.choices[0].message.content


def print_section(title: str) -> None:
    """打印带分隔线的标题。"""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print('=' * 60)
