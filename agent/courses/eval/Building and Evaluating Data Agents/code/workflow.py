"""多 Agent 工作流 (课程 helper.py 的本地化版)。

结构与课程一致: planner -> executor -> {web_researcher | cortex_researcher |
chart_generator -> chart_summarizer | synthesizer}, executor 可触发 replan。

本地化替换:
- reasoning LLM: o3 -> DeepSeek json_object 模式
- Cortex Agent (Snowflake Analyst+Search) -> data_agent: 本地 sqlite text2sql + fastembed 笔记检索
- Tavily -> ddgs (免 key), 网络失败回退内置结果
- PythonREPL (langchain_experimental) -> 本地 exec 实现
"""

from __future__ import annotations

import io
import json
import re
import sys
from contextlib import redirect_stdout
from pathlib import Path
from typing import Annotated, Any, Dict, Literal

sys.path.insert(0, str(Path(__file__).resolve().parent))

from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import create_react_agent
from langgraph.types import Command
from trulens.core.otel.instrument import instrument
from trulens.otel.semconv.trace import SpanAttributes

import prompts
import sales_data
from local_stack import banner, make_llm
from prompts import MAX_REPLANS, State, agent_system_prompt, executor_prompt

llm = make_llm()
reasoning_llm = make_llm(json_mode=True)


def _plan_prompt(state):
    """经 prompts 模块间接取 plan_prompt, 让 L6 的 monkeypatch 生效"""
    return prompts.plan_prompt(state)


def _parse_json(content) -> Dict[str, Any]:
    text = content if isinstance(content, str) else str(content)
    return json.loads(text)


# ---------------------------------------------------------------- planner / executor

def planner_node(state: State) -> "Command[Literal['executor']]":
    llm_reply = reasoning_llm.invoke([_plan_prompt(state)])
    try:
        updated_plan = _parse_json(llm_reply.content)
    except json.JSONDecodeError:
        raise ValueError(f"Planner returned invalid JSON:\n{llm_reply.content}")

    replan = state.get("replan_flag", False)
    return Command(
        update={
            "plan": updated_plan,
            "messages": [
                HumanMessage(content=llm_reply.content, name="replan" if replan else "initial_plan")
            ],
            "user_query": state.get("user_query", state["messages"][0].content),
            "current_step": 1 if not replan else state["current_step"],
            "replan_flag": state.get("replan_flag", False),
            "last_reason": "",
            "enabled_agents": state.get("enabled_agents"),
        },
        goto="executor",
    )


def executor_node(
    state: State,
) -> Command[
    Literal["web_researcher", "cortex_researcher", "chart_generator", "synthesizer", "planner"]
]:
    plan: Dict[str, Any] = state.get("plan", {})
    step: int = state.get("current_step", 1)

    if state.get("replan_flag"):
        planned_agent = plan.get(str(step), {}).get("agent")
        return Command(
            update={"replan_flag": False, "current_step": step + 1},
            goto=planned_agent,
        )

    llm_reply = reasoning_llm.invoke([executor_prompt(state)])
    try:
        parsed = _parse_json(llm_reply.content)
        replan: bool = parsed["replan"]
        goto: str = parsed["goto"]
        reason: str = parsed["reason"]
        query: str = parsed["query"]
    except Exception as exc:
        raise ValueError(f"Invalid executor JSON:\n{llm_reply.content}") from exc

    updates: Dict[str, Any] = {
        "messages": [HumanMessage(content=llm_reply.content, name="executor")],
        "last_reason": reason,
        "agent_query": query,
    }

    replans: Dict[int, int] = state.get("replan_attempts", {}) or {}
    step_replans = replans.get(step, 0)

    if replan:
        if step_replans < MAX_REPLANS:
            replans[step] = step_replans + 1
            updates.update(
                {"replan_attempts": replans, "replan_flag": True, "current_step": step}
            )
            return Command(update=updates, goto="planner")
        else:
            next_agent = plan.get(str(step + 1), {}).get("agent", "synthesizer")
            updates["current_step"] = step + 1
            return Command(update=updates, goto=next_agent)

    planned_agent = plan.get(str(step), {}).get("agent")
    updates["current_step"] = step + 1 if goto == planned_agent else step
    updates["replan_flag"] = False
    return Command(update=updates, goto=goto)


# ---------------------------------------------------------------- data agent (Cortex 替代)

@tool
def query_deals_sql(question: Annotated[str, "关于 deals/销售指标的自然语言问题"]) -> str:
    """Answer questions about CRM deal data (customers, deal values, status, owners)
    by generating and executing SQL against the sales_deals table."""
    sql_reply = llm.invoke(
        [
            HumanMessage(
                content=(
                    "Generate a single SQLite SQL query answering the question. "
                    "Reply with ONLY the SQL, no markdown.\n"
                    f"Schema: {sales_data.TABLE_SCHEMA}\nQuestion: {question}"
                )
            )
        ]
    )
    sql = str(sql_reply.content).strip().replace("```sql", "").replace("```", "").strip()
    try:
        cols, rows = sales_data.run_sql(sql)
        table = "\n".join([" | ".join(cols)] + [" | ".join(map(str, r)) for r in rows])
        return f"SQL: {sql}\nResults:\n{table}"
    except Exception as e:
        return f"SQL: {sql}\nSQL execution error: {e}"


_notes_index = None


@tool
def search_meeting_notes(query: Annotated[str, "要在销售会议纪要中检索的内容"]) -> str:
    """Semantic search over sales meeting notes (unstructured customer conversations)."""
    global _notes_index
    if _notes_index is None:
        _notes_index = sales_data.NotesIndex()
    hits = _notes_index.search(query, k=3)
    out = []
    for h in hits:
        out.append(f"[customer={h['customer']} score={h['score']:.3f}]\n{h['note']}")
    return "\n\n".join(out)


data_agent = create_react_agent(
    llm,
    tools=[query_deals_sql, search_meeting_notes],
    prompt=agent_system_prompt(
        """
        You are the Researcher. You can answer questions
        using customer deal data along with meeting notes.
        Do not take any further action.
    """
    ),
)


@instrument(
    span_type=SpanAttributes.SpanType.RETRIEVAL,
    attributes=lambda ret, exception, *args, **kwargs: {
        SpanAttributes.RETRIEVAL.QUERY_TEXT: args[0].get("agent_query")
        if args[0].get("agent_query")
        else None,
        SpanAttributes.RETRIEVAL.RETRIEVED_CONTEXTS: [ret.update["messages"][-1].content]
        if hasattr(ret, "update")
        else "No tool call",
    },
)
def cortex_agents_research_node(state: State) -> Command[Literal["executor"]]:
    query = state.get("agent_query", state.get("user_query", ""))
    agent_response = data_agent.invoke({"messages": query})
    new_message = HumanMessage(
        content=agent_response["messages"][-1].content, name="cortex_researcher"
    )
    return Command(update={"messages": [new_message]}, goto="executor")


# ---------------------------------------------------------------- web research (ddgs 替代 Tavily)

OFFLINE_SEARCH_FALLBACK = (
    "[offline fallback] Recent US financial services regulatory changes (2025-2026): "
    "1) Finalized data-residency rules require in-region storage of customer financial data. "
    "2) SEC expanded algorithmic trading disclosure requirements, mandating model decision logs. "
    "3) State-level health data privacy acts extend HIPAA-like duties to insurers. "
    "4) Insurance solvency reporting now requires auditable trails for automated decisions."
)


@tool
def web_search(query: Annotated[str, "web search query"]) -> str:
    """Search the public web for current information (news, market data, regulations)."""
    try:
        from ddgs import DDGS

        results = list(DDGS().text(query, max_results=5))
        if not results:
            return OFFLINE_SEARCH_FALLBACK
        return "\n\n".join(
            f"[{r.get('title', '')}] {r.get('body', '')} (source: {r.get('href', '')})"
            for r in results
        )
    except Exception:
        return OFFLINE_SEARCH_FALLBACK


web_search_agent = create_react_agent(
    llm,
    tools=[web_search],
    prompt=agent_system_prompt(
        """
        You are the Researcher. You can ONLY perform research by using the provided search tool (web_search).
        When you have found the necessary information, end your output.
        Do NOT attempt to take further actions.
    """
    ),
)


@instrument(
    span_type=SpanAttributes.SpanType.RETRIEVAL,
    attributes=lambda ret, exception, *args, **kwargs: {
        SpanAttributes.RETRIEVAL.QUERY_TEXT: args[0].get("agent_query", ""),
        SpanAttributes.RETRIEVAL.RETRIEVED_CONTEXTS: [ret.update["messages"][-1].content]
        if hasattr(ret, "update")
        else "No tool call",
    },
)
def web_research_node(state: State) -> Command[Literal["executor"]]:
    agent_query = state.get("agent_query")
    result = web_search_agent.invoke({"messages": agent_query})
    result["messages"][-1] = HumanMessage(
        content=result["messages"][-1].content, name="web_researcher"
    )
    return Command(update={"messages": result["messages"]}, goto="executor")


# ---------------------------------------------------------------- chart agent

@tool
def python_repl_tool(
    code: Annotated[str, "The python code to execute to generate your chart."],
):
    """Use this to execute python code that generates charts. Save the chart to a file
    in the current working directory. This is visible to the user."""
    buf = io.StringIO()
    try:
        with redirect_stdout(buf):
            exec(code, {"__name__": "__chart__"})
        result = buf.getvalue()
    except BaseException as e:
        return f"Failed to execute. Error: {repr(e)}"
    return (
        f"Successfully executed:\n```python\n{code}\n```\nStdout: {result}"
        "\n\nIf you have completed all tasks, respond with FINAL ANSWER."
    )


chart_agent = create_react_agent(
    llm,
    [python_repl_tool],
    prompt=agent_system_prompt(
        "You can only generate charts with matplotlib (Agg backend, no plt.show). "
        "You are working with a researcher colleague. Save the chart to a file in the "
        "current working directory and provide the path to the chart_summarizer."
    ),
)


def chart_node(state: State) -> Command[Literal["chart_summarizer"]]:
    result = chart_agent.invoke(state)
    result["messages"][-1] = HumanMessage(
        content=result["messages"][-1].content, name="chart_generator"
    )
    return Command(update={"messages": result["messages"]}, goto="chart_summarizer")


chart_summary_agent = create_react_agent(
    llm,
    tools=[],
    prompt=agent_system_prompt(
        "You can only summarize the chart that was generated by the chart generator to answer the user's question. "
        "Your task is to generate a standalone, concise summary for the provided chart image saved at a local PATH, "
        "where the PATH should be and only be provided by your chart generator colleague. "
        "The summary should be no more than 3 sentences and should not mention the chart itself."
    ),
)


def chart_summary_node(state: State) -> Command:
    result = chart_summary_agent.invoke(state)
    print(f"Chart summarizer answer: {result['messages'][-1].content}")
    result["messages"][-1] = HumanMessage(
        content=result["messages"][-1].content, name="chart_summarizer"
    )
    return Command(
        update={"messages": result["messages"], "final_answer": result["messages"][-1].content},
        goto=END,
    )


# ---------------------------------------------------------------- synthesizer

def synthesizer_node(state: State) -> Command:
    relevant_msgs = [
        m.content
        for m in state.get("messages", [])
        if getattr(m, "name", None)
        in ("web_researcher", "cortex_researcher", "chart_generator", "chart_summarizer")
    ]
    user_question = state.get(
        "user_query", state.get("messages", [{}])[0].content if state.get("messages") else ""
    )
    synthesis_instructions = (
        "You are the Synthesizer. Use the context below to directly answer the user's question. "
        "Perform any lightweight calculations, comparisons, or inferences required. "
        "Do not invent facts not supported by the context. If data is missing, say what's missing and, if helpful, "
        "offer a clearly labeled best-effort estimate with assumptions.\n\n"
        "Produce a concise response that fully answers the question, with the following guidance:\n"
        "- Start with the direct answer (one short paragraph or a tight bullet list).\n"
        "- Include key figures from any 'Results:' tables (e.g., totals, top items).\n"
        "- If any message contains citations, include them as a brief 'Citations: [...]' line.\n"
        "- Keep the output crisp; avoid meta commentary or tool instructions."
    )
    summary_prompt = [
        HumanMessage(
            content=(
                f"User question: {user_question}\n\n{synthesis_instructions}\n\n"
                "Context:\n\n" + "\n\n---\n\n".join(relevant_msgs)
            )
        )
    ]
    llm_reply = llm.invoke(summary_prompt)
    reply_content = llm_reply.content
    answer = (
        "".join(c if isinstance(c, str) else str(c) for c in reply_content)
        if isinstance(reply_content, list)
        else str(reply_content)
    ).strip()
    print(f"Synthesizer answer: {answer}")
    return Command(
        update={"final_answer": answer, "messages": [HumanMessage(content=answer, name="synthesizer")]},
        goto=END,
    )


# ---------------------------------------------------------------- graph builder

def build_graph(web_node=None, data_node=None):
    """构建工作流图 (节点齐全, 用 enabled_agents 控制可用范围)。

    L4/L6 可传入加了额外装饰器(inline_evaluation)的节点覆盖默认实现。
    注: langgraph 1.x 会校验 Command[Literal[...]] 里的目标节点, 因此图必须包含
    executor 声明的所有节点 —— L2 通过 enabled_agents 排除数据 agent, 而非删节点。"""
    sales_data.build_db()
    g = StateGraph(State)
    g.add_node("planner", planner_node)
    g.add_node("executor", executor_node)
    g.add_node("web_researcher", web_node or web_research_node)
    g.add_node("cortex_researcher", data_node or cortex_agents_research_node)
    g.add_node("chart_generator", chart_node)
    g.add_node("chart_summarizer", chart_summary_node)
    g.add_node("synthesizer", synthesizer_node)
    g.add_edge(START, "planner")
    return g.compile()


def run_query(graph, query: str, enabled_agents=None, recursion_limit: int = 40):
    enabled = enabled_agents or [
        "web_researcher",
        "cortex_researcher",
        "chart_generator",
        "chart_summarizer",
        "synthesizer",
    ]
    print(f"\nQuery: {query}")
    state = {
        "messages": [HumanMessage(content=query)],
        "user_query": query,
        "enabled_agents": enabled,
        "current_step": 1,
    }
    result = graph.invoke(state, {"recursion_limit": recursion_limit})
    return result
