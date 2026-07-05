"""
API 配置与辅助函数

本集新增：get_completion_from_messages()
  — 接受完整消息列表，支持多轮对话
  — 与 get_completion() 的区别：
      get_completion()         → 单 prompt，内部自动包装成 user 消息
      get_completion_from_messages() → 直接传 messages 列表，支持 system/user/assistant 三种角色
"""
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def get_completion(prompt: str, model: str = "gpt-3.5-turbo", temperature: float = 0) -> str:
    """单轮对话（整个课程系列使用的基础函数）"""
    messages = [{"role": "user", "content": prompt}]
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
    )
    return response.choices[0].message.content


def get_completion_from_messages(
    messages: list,
    model: str = "gpt-3.5-turbo",
    temperature: float = 0,
) -> str:
    """多轮对话（本集核心函数）
    messages 格式：
      [
        {"role": "system",    "content": "..."},  # 系统指令（可选）
        {"role": "user",      "content": "..."},  # 用户消息
        {"role": "assistant", "content": "..."},  # 助手消息（历史）
        ...
      ]
    """
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
    )
    return response.choices[0].message.content


def print_section(title: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print('=' * 60)
