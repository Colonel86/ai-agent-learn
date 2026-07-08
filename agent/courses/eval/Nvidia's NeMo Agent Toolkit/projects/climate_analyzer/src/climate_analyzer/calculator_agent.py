"""Standalone LangGraph calculator agent (course L5).

一个完整的、与 NAT 毫无关联的 LangGraph agent:自带数学工具、自己的推理循环。
它只要求调用方给一个 LangChain 兼容的 LLM——这正是"LLM Lifting"的接口前提。
"""
import numexpr
from langchain.agents import create_agent
from langchain_core.tools import tool


@tool
def evaluate_expression(expression: str) -> str:
    """Evaluate a plain math expression, e.g. '1200 * (1 - 0.025) ** 5'.
    Supports +,-,*,/,**,(), and functions like sqrt, log, exp, sin."""
    # numexpr 是独立的数值表达式解析器,不执行 Python 语义:
    # 没有属性访问、没有函数定义、没有 import——LLM 生成的字符串在这里只能是算式
    try:
        return str(numexpr.evaluate(expression.strip()).item())
    except Exception as e:  # 把错误交回给 agent 让它自我纠正
        return f"error: {e}"


@tool
def percentage_change(old_value: float, new_value: float) -> str:
    """Percentage change from old_value to new_value."""
    return f"{(new_value - old_value) / old_value * 100:.4f}%"


@tool
def compound_growth_rate(start_value: float, end_value: float, periods: float) -> str:
    """Compound growth rate per period (CAGR) given start value, end value and number of periods."""
    rate = (end_value / start_value) ** (1 / periods) - 1
    return f"{rate * 100:.4f}% per period"


@tool
def linear_projection(current_value: float, rate_per_period: float, periods: float) -> str:
    """Project a value forward linearly: current_value + rate_per_period * periods."""
    return str(current_value + rate_per_period * periods)


MATH_TOOLS = [evaluate_expression, percentage_change, compound_growth_rate, linear_projection]

SYSTEM_PROMPT = (
    "You are a precise calculator agent. Break complex problems into steps, "
    "use the math tools for every numeric computation (never compute in your head), "
    "and end with a short explanation of the result showing the steps."
)


def create_calculator_agent(llm):
    """Build the LangGraph agent from any LangChain-compatible LLM."""
    return create_agent(llm, MATH_TOOLS, system_prompt=SYSTEM_PROMPT)


async def calculate_with_agent(question: str, agent) -> str:
    """Run one question through the agent, return the final answer text."""
    result = await agent.ainvoke({"messages": [("user", question)]})
    return result["messages"][-1].content
