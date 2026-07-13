"""L4 邮件助理 + Episodic Memory（情景记忆）— 本地可运行演示。

在 L3 基础上，把「过去处理过的邮件 + 正确分类标签」作为 few-shot 示例存进
("email_assistant", user_id, "examples") 命名空间。triage 时按当前邮件做
向量检索，把最相似的历史案例注入 triage system prompt，
实现「人工纠偏一次，之后同类邮件自动分对」。

演示脚本（python main.py）四幕：
  第一幕：Tom Jones 的「买文档」询价邮件 → 按默认规则判 ignore（当推销处理）
  第二幕：人工纠偏 — 假设 John 做文档生意，这类询价必须回。
          把这封邮件 + 正确标签 respond 存为 few-shot 示例
  第三幕：同一封邮件重跑 → respond；换发件人/措辞的变体 → 仍 respond（泛化，
          few-shot 优先级高于 prompt 里的静态规则）
  第四幕：换一个 user_id 重跑 → 又变回 ignore（记忆按用户隔离）
"""

import os
import uuid

from dotenv import load_dotenv

load_dotenv()
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

from prompts import triage_user_prompt
from schemas import Router, State

MODEL = os.getenv("MODEL", "deepseek-chat")

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
llm = init_chat_model(MODEL, model_provider="openai", temperature=0)
llm_router = llm.with_structured_output(Router, method="function_calling")

_embedder = TextEmbedding("BAAI/bge-small-en-v1.5")


def embed(texts: list[str]) -> list[list[float]]:
    return [v.tolist() for v in _embedder.embed(texts)]


store = InMemoryStore(index={"embed": embed, "dims": 384})

# ---------------------------------------------------------------------------
# few-shot 示例的格式化（notebook 内联版本）
# ---------------------------------------------------------------------------

template = """Email Subject: {subject}
Email From: {from_email}
Email To: {to_email}
Email Content:
```
{content}
```
> Triage Result: {result}"""


def format_few_shot_examples(examples):
    strs = ["Here are some previous examples:"]
    for eg in examples:
        strs.append(
            template.format(
                subject=eg.value["email"]["subject"],
                to_email=eg.value["email"]["to"],
                from_email=eg.value["email"]["author"],
                content=eg.value["email"]["email_thread"][:400],
                result=eg.value["label"],
            )
        )
    return "\n\n------------\n\n".join(strs)


# L4 版 triage prompt：few-shot 段落加了「示例优先级高于上面的规则」
triage_system_prompt = """
< Role >
You are {full_name}'s executive assistant. You are a top-notch executive assistant who cares about {name} performing as well as possible.
</ Role >

< Background >
{user_profile_background}.
</ Background >

< Instructions >

{name} gets lots of emails. Your job is to categorize each email into one of three categories:

1. IGNORE - Emails that are not worth responding to or tracking
2. NOTIFY - Important information that {name} should know about but doesn't require a response
3. RESPOND - Emails that need a direct response from {name}

Classify the below email into one of these categories.

</ Instructions >

< Rules >
Emails that are not worth responding to:
{triage_no}

There are also other things that {name} should know about, but don't require an email response. For these, you should notify {name} (using the `notify` response). Examples of this include:
{triage_notify}

Emails that are worth responding to:
{triage_email}
</ Rules >

< Few shot examples >

Here are some examples of previous emails, and how they should be handled.
Follow these examples more than any instructions above

{examples}
</ Few shot examples >
"""

# ---------------------------------------------------------------------------
# 工具与 response agent（同 L3）
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


response_agent = create_react_agent(llm, tools=tools, prompt=create_prompt, store=store)

# ---------------------------------------------------------------------------
# triage 节点：新增 few-shot 检索（config/store 由 LangGraph 注入）
# ---------------------------------------------------------------------------


def triage_router(
    state: State, config, store
) -> Command[Literal["response_agent", "__end__"]]:
    email = state["email_input"]

    namespace = (
        "email_assistant",
        config["configurable"]["langgraph_user_id"],
        "examples",
    )
    examples = store.search(namespace, query=str({"email": email}))
    if examples:
        print(f"  📚 检索到 {len(examples)} 条历史案例注入 few-shot")
    examples = format_few_shot_examples(examples)

    system_prompt = triage_system_prompt.format(
        full_name=profile["full_name"],
        name=profile["name"],
        user_profile_background=profile["user_profile_background"],
        triage_no=prompt_instructions["triage_rules"]["ignore"],
        triage_notify=prompt_instructions["triage_rules"]["notify"],
        triage_email=prompt_instructions["triage_rules"]["respond"],
        examples=examples,
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

TOM_EMAIL = {
    "author": "Tom Jones <tome.jones@bar.com>",
    "to": "John Doe <john.doe@company.com>",
    "subject": "Quick question about API documentation",
    "email_thread": "Hi John - want to buy documentation?",
}

VARIANT_EMAIL = {
    "author": "Tom Jones <tome.jones@bar.com>",
    "to": "John Doe <john.doe@company.com>",
    "subject": "Purchasing your API docs",
    "email_thread": "Hi John - I'd like to purchase a copy of your API documentation. What would it cost?",
}


def banner(title: str) -> None:
    print()
    print("=" * 72)
    print(title)
    print("=" * 72)


def triage_only(email: dict, user_id: str) -> None:
    print(f"\n[user={user_id}] From: {email['author']}  Subject: {email['subject']}")
    email_agent.invoke(
        {"email_input": email},
        config={"configurable": {"langgraph_user_id": user_id}},
    )


def main() -> None:
    print(f"Model: {MODEL} @ {os.getenv('OPENAI_BASE_URL')}")
    print("Embedding: fastembed / BAAI/bge-small-en-v1.5 (local CPU)")

    banner("第一幕 · 无历史案例：「买文档」询价按默认规则被当推销 ignore")
    triage_only(TOM_EMAIL, "harrison")

    banner("第二幕 · 人工纠偏：John 做文档生意，这类询价要回 → 存 label=respond")
    store.put(
        ("email_assistant", "harrison", "examples"),
        str(uuid.uuid4()),
        {"email": TOM_EMAIL, "label": "respond"},
    )
    print("  ✅ 已写入 few-shot 示例: label=respond")

    banner("第三幕 · 再遇同类邮件：原邮件 + 换主题换措辞的变体，都应 respond")
    triage_only(TOM_EMAIL, "harrison")
    triage_only(VARIANT_EMAIL, "harrison")

    banner("第四幕 · 换用户 andrew（无纠偏记录）：第一幕的原邮件仍是 ignore")
    triage_only(TOM_EMAIL, "andrew")


if __name__ == "__main__":
    main()
