"""
EP02: Language Models, the Chat Format and Tokens
==================================================
课程：Building Systems with the ChatGPT API (DeepLearning.AI × OpenAI)
讲师：Andrew Ng & Isa Fulford

本脚本演示：
1. 基本 Prompt 调用
2. Token 与分词器的影响
3. Chat Format（system / user / assistant 消息角色）
4. Token 计数

使用方法：
  1. cp .env.example .env
  2. 在 .env 中填入你的 OPENAI_API_KEY
  3. pip install -r requirements.txt
  4. python ep02_language_models.py
"""

import os
import openai
import tiktoken
from dotenv import load_dotenv, find_dotenv

# ──────────────────────────────────────────────
# 0. 加载 API 密钥
# ──────────────────────────────────────────────
load_dotenv(find_dotenv())

client = openai.OpenAI()  # 自动读取 OPENAI_API_KEY 环境变量

# 默认模型 —— 可根据需要切换为 "gpt-4o" 等
MODEL = os.getenv("MODEL", "gpt-4o-mini")


# ──────────────────────────────────────────────
# 1. 辅助函数
# ──────────────────────────────────────────────

def get_completion(prompt: str, model: str = MODEL) -> str:
    """发送单条 prompt，返回模型回复文本。"""
    messages = [{"role": "user", "content": prompt}]
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0,
    )
    return response.choices[0].message.content


def get_completion_from_messages(
    messages: list[dict],
    model: str = MODEL,
    temperature: float = 0,
    max_tokens: int = 500,
) -> str:
    """发送多角色消息列表，返回模型回复文本。"""
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content


def get_completion_and_token_count(
    messages: list[dict],
    model: str = MODEL,
    temperature: float = 0,
    max_tokens: int = 500,
) -> tuple[str, dict]:
    """发送消息并返回 (回复文本, token 用量字典)。"""
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    content = response.choices[0].message.content
    token_dict = {
        "prompt_tokens": response.usage.prompt_tokens,
        "completion_tokens": response.usage.completion_tokens,
        "total_tokens": response.usage.total_tokens,
    }
    return content, token_dict


# ──────────────────────────────────────────────
# 2. 基本调用
# ──────────────────────────────────────────────

def demo_basic_completion():
    print("=" * 60)
    print("Demo 1: 基本 Prompt 调用")
    print("=" * 60)

    response = get_completion("What is the capital of France?")
    print(f"Q: What is the capital of France?")
    print(f"A: {response}\n")


# ──────────────────────────────────────────────
# 3. Token 与分词器
# ──────────────────────────────────────────────

def demo_tokens():
    print("=" * 60)
    print("Demo 2: Token 与分词器 — Lollipop 问题")
    print("=" * 60)

    # 直接让模型反转字母（可能出错）
    response1 = get_completion("Take the letters in lollipop and reverse them")
    print(f"直接反转: {response1}")
    print(f"正确答案应为: popillol\n")

    # 加分隔符后再试
    response2 = get_completion(
        "Take the letters in l-o-l-l-i-p-o-p and reverse them"
    )
    print(f"加分隔符后反转: {response2}\n")

    # 用 tiktoken 展示分词差异
    # 注意：tiktoken 只内置了 OpenAI 模型的编码表，DeepSeek 等第三方模型
    # 需要回退到通用编码（cl100k_base 是 GPT-4 同款，对其他模型仅作估算）
    try:
        encoding = tiktoken.encoding_for_model(MODEL)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")
        print(f"[提示] tiktoken 不识别模型 {MODEL}，回退到 cl100k_base 编码器")
    tokens_no_dash = encoding.encode("lollipop")
    tokens_with_dash = encoding.encode("l-o-l-l-i-p-o-p")
    print(f'"lollipop" 分词为 {len(tokens_no_dash)} 个 token: {tokens_no_dash}')
    print(f'  → 解码: {[encoding.decode([t]) for t in tokens_no_dash]}')
    print(f'"l-o-l-l-i-p-o-p" 分词为 {len(tokens_with_dash)} 个 token: {tokens_with_dash}')
    print(f'  → 解码: {[encoding.decode([t]) for t in tokens_with_dash]}\n')


# ──────────────────────────────────────────────
# 4. Chat Format（对话格式）
# ──────────────────────────────────────────────

def demo_chat_format():
    print("=" * 60)
    print("Demo 3: Chat Format — System / User 消息角色")
    print("=" * 60)

    # 4a. Dr. Seuss 风格
    messages = [
        {"role": "system",
         "content": "You are an assistant who responds in the style of Dr Seuss."},
        {"role": "user",
         "content": "write me a very short poem about a happy carrot"},
    ]
    response = get_completion_from_messages(messages, temperature=1)
    print("[Dr. Seuss 风格诗歌]")
    print(response)
    print()

    # 4b. 控制长度：一句话
    messages = [
        {"role": "system",
         "content": "All your responses must be one sentence long."},
        {"role": "user",
         "content": "write me a story about a happy carrot"},
    ]
    response = get_completion_from_messages(messages, temperature=1)
    print("[一句话限制]")
    print(response)
    print()

    # 4c. 组合风格 + 长度
    messages = [
        {"role": "system",
         "content": "You are an assistant who responds in the style of Dr Seuss. "
                    "All your responses must be one sentence long."},
        {"role": "user",
         "content": "write me a story about a happy carrot"},
    ]
    response = get_completion_from_messages(messages, temperature=1)
    print("[Dr. Seuss 风格 + 一句话限制]")
    print(response)
    print()


# ──────────────────────────────────────────────
# 5. Token 计数
# ──────────────────────────────────────────────

def demo_token_count():
    print("=" * 60)
    print("Demo 4: Token 计数")
    print("=" * 60)

    messages = [
        {"role": "system",
         "content": "You are an assistant who responds in the style of Dr Seuss."},
        {"role": "user",
         "content": "write me a very short poem about a happy carrot"},
    ]
    response, token_dict = get_completion_and_token_count(messages)
    print(response)
    print()
    print(f"Token 用量: {token_dict}")
    print(f"  - Prompt tokens:     {token_dict['prompt_tokens']}")
    print(f"  - Completion tokens: {token_dict['completion_tokens']}")
    print(f"  - Total tokens:      {token_dict['total_tokens']}\n")


# ──────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────

if __name__ == "__main__":
    print(f"使用模型: {MODEL}\n")

    demo_basic_completion()
    demo_tokens()
    demo_chat_format()
    demo_token_count()

    print("✅ 所有演示运行完毕！")
