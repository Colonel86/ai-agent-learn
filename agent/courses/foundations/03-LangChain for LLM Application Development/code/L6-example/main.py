"""
LangChain Lesson 6: Agents
演示 Agent 使用内置工具 + 自定义工具
"""

import os
import warnings
from datetime import date
from dotenv import load_dotenv, find_dotenv
from langchain_openai import ChatOpenAI
from langchain.agents import load_tools, initialize_agent, AgentType, tool

warnings.filterwarnings("ignore")
load_dotenv(find_dotenv())
LLM_MODEL = "gpt-3.5-turbo"


# ── 1. 内置工具：llm-math + wikipedia ────────────────────────────────────────

def demo_builtin_tools():
    print("=" * 60)
    print("1. 内置工具：llm-math + Wikipedia")
    print("=" * 60)

    llm = ChatOpenAI(temperature=0, model=LLM_MODEL)
    tools = load_tools(["llm-math", "wikipedia"], llm=llm)

    agent = initialize_agent(
        tools=tools,
        llm=llm,
        agent=AgentType.CHAT_ZERO_SHOT_REACT_DESCRIPTION,
        handle_parsing_errors=True,
        verbose=True,
    )

    # 数学计算
    print("\n[数学问题]")
    result = agent.invoke({"input": "What is 25% of 300?"})
    print(f"答案: {result['output']}")

    # Wikipedia 查询
    print("\n[Wikipedia 查询]")
    result = agent.invoke({
        "input": "Tom M. Mitchell is an American computer scientist. What book did he write?"
    })
    print(f"答案: {result['output']}")


# ── 2. 自定义工具 ─────────────────────────────────────────────────────────────

@tool
def get_today_date(text: str) -> str:
    """Returns today's date. Use this for any questions about today's date.
    The input should always be an empty string, and this function will always
    return today's date. Any date math should occur outside this function."""
    return str(date.today())


@tool
def word_count(text: str) -> str:
    """Counts the number of words in a given text string.
    Input should be the text you want to count words in."""
    count = len(text.split())
    return f"The text contains {count} words."


def demo_custom_tools():
    print("\n" + "=" * 60)
    print("2. 自定义工具（@tool 装饰器）")
    print("=" * 60)

    llm = ChatOpenAI(temperature=0, model=LLM_MODEL)
    base_tools = load_tools(["llm-math"], llm=llm)

    agent = initialize_agent(
        tools=base_tools + [get_today_date, word_count],
        llm=llm,
        agent=AgentType.CHAT_ZERO_SHOT_REACT_DESCRIPTION,
        handle_parsing_errors=True,
        verbose=True,
    )

    # 使用自定义 date 工具
    print("\n[今天日期]")
    try:
        result = agent.invoke({"input": "What is today's date?"})
        print(f"答案: {result['output']}")
    except Exception as e:
        print(f"执行异常（Agent 有时不稳定）: {e}")

    # 使用自定义 word_count 工具
    print("\n[字数统计]")
    try:
        result = agent.invoke({
            "input": "How many words are in this sentence: The quick brown fox jumps over the lazy dog"
        })
        print(f"答案: {result['output']}")
    except Exception as e:
        print(f"执行异常: {e}")


# ── 3. ReAct 推理过程说明 ─────────────────────────────────────────────────────

def explain_react():
    print("\n" + "=" * 60)
    print("3. ReAct 推理框架说明")
    print("=" * 60)

    explanation = """
    Agent 的工作方式（ReAct 循环）:

    Thought:  我需要查今天的日期
    Action:   get_today_date("")
    Observation: 2024-01-15
    Thought:  已经得到答案
    Final Answer: Today is 2024-01-15

    关键点:
    - LLM 作为推理引擎，决定下一步行动
    - Tool 的 docstring 是路由决策的依据，必须写清楚
    - handle_parsing_errors=True 处理 LLM 输出格式不规范的情况
    - Agent 具有非确定性，同一问题可能走不同路径
    """
    print(explanation)


# ── 主入口 ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    demo_builtin_tools()
    demo_custom_tools()
    explain_react()
