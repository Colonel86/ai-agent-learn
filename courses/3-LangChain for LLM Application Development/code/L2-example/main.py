"""
LangChain Lesson 2: Memory
演示四种对话记忆类型
"""

import os
from dotenv import load_dotenv, find_dotenv
from langchain_openai import ChatOpenAI
from langchain.chains import ConversationChain
from langchain.memory import (
    ConversationBufferMemory,
    ConversationBufferWindowMemory,
    ConversationTokenBufferMemory,
    ConversationSummaryBufferMemory,
)

load_dotenv(find_dotenv())
LLM_MODEL = "gpt-3.5-turbo"


# ── 1. ConversationBufferMemory ───────────────────────────────────────────────

def demo_buffer_memory():
    print("=" * 60)
    print("1. ConversationBufferMemory（全量缓冲）")
    print("=" * 60)

    llm = ChatOpenAI(temperature=0.0, model=LLM_MODEL)
    memory = ConversationBufferMemory()
    conversation = ConversationChain(llm=llm, memory=memory, verbose=False)

    r1 = conversation.predict(input="Hi, my name is Andrew")
    print(f"Turn 1: {r1}")

    r2 = conversation.predict(input="What is 1+1?")
    print(f"Turn 2: {r2}")

    r3 = conversation.predict(input="What is my name?")
    print(f"Turn 3: {r3}")

    print("\n[Memory buffer]:")
    print(memory.buffer)

    # 手动添加记录
    print("\n[手动 save_context]:")
    memory2 = ConversationBufferMemory()
    memory2.save_context({"input": "Hi"}, {"output": "What's up"})
    memory2.save_context({"input": "Not much, just hanging"}, {"output": "Cool"})
    print(memory2.load_memory_variables({}))


# ── 2. ConversationBufferWindowMemory ─────────────────────────────────────────

def demo_window_memory():
    print("\n" + "=" * 60)
    print("2. ConversationBufferWindowMemory（滑动窗口，k=1）")
    print("=" * 60)

    llm = ChatOpenAI(temperature=0.0, model=LLM_MODEL)
    memory = ConversationBufferWindowMemory(k=1)
    conversation = ConversationChain(llm=llm, memory=memory, verbose=False)

    r1 = conversation.predict(input="Hi, my name is Andrew")
    print(f"Turn 1: {r1}")

    r2 = conversation.predict(input="What is 1+1?")
    print(f"Turn 2: {r2}")

    r3 = conversation.predict(input="What is my name?")
    print(f"Turn 3 (k=1，已忘记介绍): {r3}")


# ── 3. ConversationTokenBufferMemory ──────────────────────────────────────────

def demo_token_memory():
    print("\n" + "=" * 60)
    print("3. ConversationTokenBufferMemory（Token 限制）")
    print("=" * 60)

    llm = ChatOpenAI(temperature=0.0, model=LLM_MODEL)
    memory = ConversationTokenBufferMemory(llm=llm, max_token_limit=50)

    memory.save_context({"input": "AI is what?!"}, {"output": "Amazing!"})
    memory.save_context({"input": "Backpropagation is what?"}, {"output": "Beautiful!"})
    memory.save_context({"input": "Chatbots are what?"}, {"output": "Charming!"})

    print("max_token_limit=50 时保留的内容:")
    print(memory.load_memory_variables({}))


# ── 4. ConversationSummaryBufferMemory ────────────────────────────────────────

def demo_summary_memory():
    print("\n" + "=" * 60)
    print("4. ConversationSummaryBufferMemory（摘要缓冲）")
    print("=" * 60)

    llm = ChatOpenAI(temperature=0.0, model=LLM_MODEL)

    schedule = (
        "There is a meeting at 8am with your product team. "
        "You will need your PowerPoint presentation prepared. "
        "9am-12pm have time to work on your LangChain project. "
        "At Noon, lunch at the Italian restaurant with a customer "
        "who wants to understand the latest in AI. "
        "Be sure to bring your laptop to show the latest LLM demo."
    )

    memory = ConversationSummaryBufferMemory(llm=llm, max_token_limit=100)
    memory.save_context({"input": "Hello"}, {"output": "What's up"})
    memory.save_context({"input": "Not much, just hanging"}, {"output": "Cool"})
    memory.save_context(
        {"input": "What is on the schedule today?"},
        {"output": schedule}
    )

    print("[Token 超限后自动生成的摘要]:")
    print(memory.load_memory_variables({}))

    conversation = ConversationChain(llm=llm, memory=memory, verbose=True)
    response = conversation.predict(input="What would be a good demo to show?")
    print(f"\nAgent 回复: {response}")


# ── 主入口 ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    demo_buffer_memory()
    demo_window_memory()
    demo_token_memory()
    demo_summary_memory()
