"""L3 语义记忆（工具型）— python 命令直接运行的课程演示。

对应 lesson_3.ipynb 完整流程：
  1) langmem 的 manage_memory / search_memory 工具挂到 ReAct agent 上
  2) 对话中主动存记忆（"Jim is my friend"），下一轮靠 search_memory 回忆
  3) triage_router → response_agent 完整图：回复邮件时把上下文写进记忆，
     追问邮件 "Any update on my previous ask?" 靠记忆检索衔接

用法（code/ 根目录下）：
  .venv/bin/python L3/main.py
"""

from typing import Literal

from local_stack import make_llm, make_embed, EMBED_DIMS

from langchain_core.tools import tool
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import create_react_agent
from langgraph.store.memory import InMemoryStore
from langgraph.types import Command
from langmem import create_manage_memory_tool, create_search_memory_tool

from prompts import triage_system_prompt, triage_user_prompt
from schemas import Router, State


def banner(title: str) -> None:
    print(f"\n{'=' * 70}\n{title}\n{'=' * 70}")


profile = {
    "name": "John",
    "full_name": "John Doe",
    "user_profile_background": "Senior software engineer leading a team of 5 developers",
}

prompt_instructions = {
    "triage_rules": {
        "ignore": "Marketing newsletters, spam emails, mass company announcements",
        "notify": "Team member out sick, build system notifications, project status updates",
        "respond": "Direct questions from team members, meeting requests, critical bug reports",
    },
    "agent_instructions": "Use these tools when appropriate to help manage John's tasks efficiently.",
}

llm = make_llm()
llm_router = llm.with_structured_output(Router)

# 语义记忆存储：fastembed 本地 embedding（原 openai:text-embedding-3-small）
store = InMemoryStore(index={"embed": make_embed(), "dims": EMBED_DIMS})


# ---------------------------------------------------------------------------
# 工具：3 个模拟工具 + langmem 记忆读写工具
# ---------------------------------------------------------------------------

@tool
def write_email(to: str, subject: str, content: str) -> str:
    """Write and send an email."""
    return f"Email sent to {to} with subject '{subject}'"


@tool
def schedule_meeting(
    attendees: list[str], subject: str, duration_minutes: int, preferred_day: str
) -> str:
    """Schedule a calendar meeting."""
    return f"Meeting '{subject}' scheduled for {preferred_day} with {len(attendees)} attendees"


@tool
def check_calendar_availability(day: str) -> str:
    """Check calendar availability for a given day."""
    return f"Available times on {day}: 9:00 AM, 2:00 PM, 4:00 PM"


manage_memory_tool = create_manage_memory_tool(
    namespace=("email_assistant", "{langgraph_user_id}", "collection")
)
search_memory_tool = create_search_memory_tool(
    namespace=("email_assistant", "{langgraph_user_id}", "collection")
)

agent_system_prompt_memory = """
< Role >
You are {full_name}'s executive assistant. You are a top-notch executive assistant who cares about {name} performing as well as possible.
</ Role >

< Tools >
You have access to the following tools to help manage {name}'s communications and schedule:

1. write_email(to, subject, content) - Send emails to specified recipients
2. schedule_meeting(attendees, subject, duration_minutes, preferred_day) - Schedule calendar meetings
3. check_calendar_availability(day) - Check available time slots for a given day
4. manage_memory - Store any relevant information about contacts, actions, discussion, etc. in memory for future reference
5. search_memory - Search for any relevant information that may have been stored in memory
</ Tools >

< Instructions >
{instructions}
</ Instructions >
"""


def create_prompt(state):
    return [
        {
            "role": "system",
            "content": agent_system_prompt_memory.format(
                instructions=prompt_instructions["agent_instructions"], **profile
            ),
        }
    ] + state["messages"]


response_agent = create_react_agent(
    make_llm(),  # 本地化：deepseek-v4-flash（原 anthropic:claude-3-5-sonnet-latest）
    tools=[
        write_email,
        schedule_meeting,
        check_calendar_availability,
        manage_memory_tool,
        search_memory_tool,
    ],
    prompt=create_prompt,
    store=store,  # 确保 store 传进 agent
)


# ---------------------------------------------------------------------------
# triage 路由 + 图
# ---------------------------------------------------------------------------

def triage_router(state: State) -> Command[Literal["response_agent", "__end__"]]:
    author = state["email_input"]["author"]
    to = state["email_input"]["to"]
    subject = state["email_input"]["subject"]
    email_thread = state["email_input"]["email_thread"]

    system_prompt = triage_system_prompt.format(
        full_name=profile["full_name"],
        name=profile["name"],
        user_profile_background=profile["user_profile_background"],
        triage_no=prompt_instructions["triage_rules"]["ignore"],
        triage_notify=prompt_instructions["triage_rules"]["notify"],
        triage_email=prompt_instructions["triage_rules"]["respond"],
        examples=None,
    )
    user_prompt = triage_user_prompt.format(
        author=author, to=to, subject=subject, email_thread=email_thread
    )
    result = llm_router.invoke(
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
    )
    if result.classification == "respond":
        print("📧 Classification: RESPOND - This email requires a response")
        goto = "response_agent"
        update = {
            "messages": [
                {
                    "role": "user",
                    "content": f"Respond to the email {state['email_input']}",
                }
            ]
        }
    elif result.classification == "ignore":
        print("🚫 Classification: IGNORE - This email can be safely ignored")
        update = None
        goto = END
    elif result.classification == "notify":
        print("🔔 Classification: NOTIFY - This email contains important information")
        update = None
        goto = END
    else:
        raise ValueError(f"Invalid classification: {result.classification}")
    return Command(goto=goto, update=update)


email_agent = StateGraph(State)
email_agent = email_agent.add_node(triage_router)
email_agent = email_agent.add_node("response_agent", response_agent)
email_agent = email_agent.add_edge(START, "triage_router")
email_agent = email_agent.compile(store=store)


# ---------------------------------------------------------------------------
# 演示
# ---------------------------------------------------------------------------

def main() -> None:
    config = {"configurable": {"langgraph_user_id": "lance"}}

    banner("① 存记忆：告诉 agent 'Jim is my friend'")
    response = response_agent.invoke(
        {"messages": [{"role": "user", "content": "Jim is my friend"}]}, config=config
    )
    for m in response["messages"]:
        m.pretty_print()

    banner("② 取记忆：问 'who is jim?'（应触发 search_memory）")
    response = response_agent.invoke(
        {"messages": [{"role": "user", "content": "who is jim?"}]}, config=config
    )
    for m in response["messages"]:
        m.pretty_print()

    banner("③ store 里实际存了什么")
    print("namespaces:", store.list_namespaces())
    for item in store.search(("email_assistant", "lance", "collection"), query="jim"):
        print(f"  score={item.score:.3f}  {item.value}")

    banner("④ 完整图：同事提问邮件 → RESPOND，回复过程写入记忆")
    email_input = {
        "author": "Alice Smith <alice.smith@company.com>",
        "to": "John Doe <john.doe@company.com>",
        "subject": "Quick question about API documentation",
        "email_thread": """Hi John,

I was reviewing the API documentation for the new authentication service and noticed a few endpoints seem to be missing from the specs. Could you help clarify if this was intentional or if we should update the docs?

Specifically, I'm looking at:
- /auth/refresh
- /auth/validate

Thanks!
Alice""",
    }
    response = email_agent.invoke({"email_input": email_input}, config=config)
    for m in response["messages"]:
        m.pretty_print()

    banner("⑤ 追问邮件 'Any update on my previous ask?' → 靠记忆衔接上下文")
    followup = {
        "author": "Alice Smith <alice.smith@company.com>",
        "to": "John Doe <john.doe@company.com>",
        "subject": "Follow up",
        "email_thread": """Hi John,

Any update on my previous ask?""",
    }
    response = email_agent.invoke({"email_input": followup}, config=config)
    for m in response["messages"]:
        m.pretty_print()


if __name__ == "__main__":
    main()
