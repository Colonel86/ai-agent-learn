"""L3 邮件助理 + Semantic Memory（语义记忆）— 本地可运行演示。

在 L2 baseline 上新增：
  - InMemoryStore + 本地 embedding（fastembed / bge-small-en-v1.5，纯 CPU）
  - langmem 的 manage_memory / search_memory 两个工具，agent 自主决定何时读写记忆
  - 记忆按 ("email_assistant", user_id, "collection") 命名空间隔离

演示脚本（python main.py）分两幕：
  第一幕：直接对话 — 先告诉 agent "Jim is my friend"，再问 "who is jim?"，
          看它先 manage_memory 存、后 search_memory 取
  第二幕：邮件流程 — Alice 的提问邮件（respond + 存记忆），
          再来一封 "Any update on my previous ask?" 追问，看它靠记忆接上下文
"""

import os

from dotenv import load_dotenv

load_dotenv()
# fastembed 首次下载模型走 HuggingFace，国内直连易卡死，默认走镜像
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

from typing import Literal

from fastembed import TextEmbedding
from langchain.chat_models import init_chat_model
from langchain_core.tools import tool
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import create_react_agent
from langgraph.store.memory import InMemoryStore
from langgraph.types import Command
from langmem import create_manage_memory_tool, create_search_memory_tool

from prompts import triage_system_prompt, triage_user_prompt
from schemas import Router, State

MODEL = os.getenv("MODEL", "deepseek-chat")
USER_ID = "demo"

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

# ---------------------------------------------------------------------------
# LLM 与本地 embedding
# ---------------------------------------------------------------------------

# temperature=0：演示场景要求分类结果可复现
# thinking disabled: deepseek-v4-flash 默认开 thinking，不支持结构化输出的强制 tool_choice
llm = init_chat_model(
    MODEL,
    model_provider="openai",
    temperature=0,
    extra_body={"thinking": {"type": "disabled"}},
)
# DeepSeek 不支持 json_schema response_format，用 function calling 实现结构化输出
llm_router = llm.with_structured_output(Router, method="function_calling")

_embedder = TextEmbedding("BAAI/bge-small-en-v1.5")


def embed(texts: list[str]) -> list[list[float]]:
    return [v.tolist() for v in _embedder.embed(texts)]


# 课程用 openai:text-embedding-3-small，本地化改用 fastembed（384 维）
store = InMemoryStore(index={"embed": embed, "dims": 384})

# ---------------------------------------------------------------------------
# 工具：3 个业务占位工具 + 2 个 langmem 记忆工具
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
    return (
        f"Meeting '{subject}' scheduled for {preferred_day} "
        f"with {len(attendees)} attendees"
    )


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

tools = [
    write_email,
    schedule_meeting,
    check_calendar_availability,
    manage_memory_tool,
    search_memory_tool,
]

# ---------------------------------------------------------------------------
# response agent（system prompt 多了记忆工具的说明，与 notebook 一致）
# ---------------------------------------------------------------------------

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


# store 传给 agent，langmem 工具运行时从上下文里拿到它
response_agent = create_react_agent(llm, tools=tools, prompt=create_prompt, store=store)

# ---------------------------------------------------------------------------
# triage 节点（与 L2 相同，尚未接记忆）
# ---------------------------------------------------------------------------


def triage_router(state: State) -> Command[Literal["response_agent", "__end__"]]:
    email = state["email_input"]

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
        author=email["author"],
        to=email["to"],
        subject=email["subject"],
        email_thread=email["email_thread"],
    )
    result = llm_router.invoke(
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
    )
    print(f"  🧠 Reasoning: {result.reasoning}")

    if result.classification == "respond":
        print("  📧 Classification: RESPOND - This email requires a response")
        return Command(
            goto="response_agent",
            update={
                "messages": [
                    {"role": "user", "content": f"Respond to the email {email}"}
                ]
            },
        )
    if result.classification == "ignore":
        print("  🚫 Classification: IGNORE - This email can be safely ignored")
        return Command(goto=END)
    if result.classification == "notify":
        print("  🔔 Classification: NOTIFY - This email contains important information")
        return Command(goto=END)
    raise ValueError(f"Invalid classification: {result.classification}")


email_agent = (
    StateGraph(State)
    .add_node(triage_router)
    .add_node("response_agent", response_agent)
    .add_edge(START, "triage_router")
    .compile(store=store)
)

# ---------------------------------------------------------------------------
# 演示
# ---------------------------------------------------------------------------

config = {"configurable": {"langgraph_user_id": USER_ID}}


def banner(title: str) -> None:
    print()
    print("=" * 72)
    print(title)
    print("=" * 72)


def dump_store() -> None:
    print("\n  🗄️  当前记忆库内容:")
    items = store.search(("email_assistant", USER_ID, "collection"))
    if not items:
        print("    (空)")
    for it in items:
        print(f"    - {it.value.get('content', it.value)}")


def chat(content: str) -> None:
    print(f"\n>>> User: {content}")
    response = response_agent.invoke(
        {"messages": [{"role": "user", "content": content}]}, config=config
    )
    for m in response["messages"]:
        m.pretty_print()


def run_email(email: dict) -> None:
    print(f"\nFrom:    {email['author']}")
    print(f"Subject: {email['subject']}")
    print("-" * 72)
    response = email_agent.invoke({"email_input": email}, config=config)
    for m in response.get("messages", []):
        m.pretty_print()


ALICE_EMAIL = {
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

FOLLOW_UP_EMAIL = {
    "author": "Alice Smith <alice.smith@company.com>",
    "to": "John Doe <john.doe@company.com>",
    "subject": "Follow up",
    "email_thread": """Hi John,

Any update on my previous ask?""",
}


def main() -> None:
    print(f"Model: {MODEL} @ {os.getenv('OPENAI_BASE_URL')}")
    print("Embedding: fastembed / BAAI/bge-small-en-v1.5 (local CPU)")

    banner("第一幕 · 记忆写入与读取：agent 自主调用 manage_memory / search_memory")
    chat("Jim is my friend")
    chat("who is jim?")
    dump_store()

    banner("第二幕 · 邮件流程：Alice 提问 → 回复并记住；追问邮件靠记忆接上下文")
    run_email(ALICE_EMAIL)
    dump_store()
    run_email(FOLLOW_UP_EMAIL)
    dump_store()


if __name__ == "__main__":
    main()
