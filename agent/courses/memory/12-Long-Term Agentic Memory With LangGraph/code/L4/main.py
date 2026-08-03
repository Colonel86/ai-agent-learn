"""L4 语义记忆（few-shot 样例）— python 命令直接运行的课程演示。

对应 lesson_4.ipynb 完整流程：
  1) 往 store 存带 label 的历史邮件样例，语义检索 + few-shot 模板拼进 triage prompt
  2) 四步翻转演示（每步换的是 store 里的样例，不是代码）：
     ①初判 RESPOND → ②存入 ignore 样例后同一封邮件变 IGNORE
     → ③换措辞的变体邮件仍 IGNORE（语义检索命中）→ ④换 user id 回到 RESPOND

注意：课程原版用一眼假的推销邮件演示"模型被骗→few-shot 纠正"，deepseek 直接
识破导致翻转失效；本地化版把演示邮件反向设计成正经提问，叙事才能走通。

用法（code/ 根目录下）：
  .venv/bin/python L4/main.py
"""

import uuid
from typing import Literal

from local_stack import make_llm, make_embed, EMBED_DIMS

from langchain_core.tools import tool
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import create_react_agent
from langgraph.store.memory import InMemoryStore
from langgraph.types import Command
from langmem import create_manage_memory_tool, create_search_memory_tool

from prompts import triage_user_prompt
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

store = InMemoryStore(index={"embed": make_embed(), "dims": EMBED_DIMS})


# ---------------------------------------------------------------------------
# few-shot 样例：模板 + 格式化
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


# 带 few-shot 段落的 triage prompt（“Follow these examples more than any instructions above”）
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
# triage 路由（从 store 语义检索样例拼 few-shot）+ 响应 agent + 图
# ---------------------------------------------------------------------------

def triage_router(state: State, config, store) -> Command[
    Literal["response_agent", "__end__"]
]:
    author = state["email_input"]["author"]
    to = state["email_input"]["to"]
    subject = state["email_input"]["subject"]
    email_thread = state["email_input"]["email_thread"]

    namespace = (
        "email_assistant",
        config["configurable"]["langgraph_user_id"],
        "examples",
    )
    examples = store.search(namespace, query=str({"email": state["email_input"]}))
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
    make_llm(),  # 本地化：deepseek-v4-flash（原 openai:gpt-4o）
    tools=[
        write_email,
        schedule_meeting,
        check_calendar_availability,
        manage_memory_tool,
        search_memory_tool,
    ],
    prompt=create_prompt,
    store=store,
)

email_agent = StateGraph(State)
email_agent = email_agent.add_node(triage_router)
email_agent = email_agent.add_node("response_agent", response_agent)
email_agent = email_agent.add_edge(START, "triage_router")
email_agent = email_agent.compile(store=store)


# ---------------------------------------------------------------------------
# 演示
# ---------------------------------------------------------------------------

def main() -> None:
    banner("① few-shot 检索机制：先给 lance 用户存两条带 label 的样例")
    respond_example = {
        "email": {
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
        },
        "label": "respond",
    }
    ignore_example = {
        "email": {
            "author": "Sarah Chen <sarah.chen@company.com>",
            "to": "John Doe <john.doe@company.com>",
            "subject": "Update: Backend API Changes Deployed to Staging",
            "email_thread": """Hi John,

Just wanted to let you know that I've deployed the new authentication endpoints we discussed to the staging environment. Key changes include:

- Implemented JWT refresh token rotation
- Added rate limiting for login attempts
- Updated API documentation with new endpoints

All tests are passing and the changes are ready for review.

No immediate action needed from your side - just keeping you in the loop.

Best regards,
Sarah""",
        },
        "label": "ignore",
    }
    for data in (respond_example, ignore_example):
        store.put(("email_assistant", "lance", "examples"), str(uuid.uuid4()), data)
        print(f"  存入样例: {data['email']['subject']!r} -> {data['label']}")

    banner("② 语义检索最相似的样例并格式化为 few-shot")
    results = store.search(
        ("email_assistant", "lance", "examples"),
        query=str({"email": ignore_example["email"]}),
        limit=1,
    )
    print(format_few_shot_examples(results))

    banner("③ 翻转第 1 步（harrison 用户，无样例）：正经提问 → 应 RESPOND")
    email_input = {
        "author": "Tom Jones <tome.jones@bar.com>",
        "to": "John Doe <john.doe@company.com>",
        "subject": "Quick question about API documentation",
        "email_thread": """Hi John,

I was reviewing the API documentation and noticed a few endpoints are missing descriptions.
Could you point me to the team that owns the docs?

Thanks!
Tom""",
    }
    harrison = {"configurable": {"langgraph_user_id": "harrison"}}
    email_agent.invoke({"email_input": email_input}, config=harrison)

    banner("④ 翻转第 2 步：把这封邮件标 ignore 存入 harrison 的样例库，再跑 → 应 IGNORE")
    store.put(
        ("email_assistant", "harrison", "examples"),
        str(uuid.uuid4()),
        {"email": email_input, "label": "ignore"},
    )
    email_agent.invoke({"email_input": email_input}, config=harrison)

    banner("⑤ 翻转第 3 步：换措辞的变体邮件（Jim Jones）→ 语义检索命中，仍 IGNORE")
    variant = {
        "author": "Jim Jones <jim.jones@bar.com>",
        "to": "John Doe <john.doe@company.com>",
        "subject": "Quick question about API documentation",
        "email_thread": """Hi John,

I was going through the API documentation and some endpoints have no descriptions.
Who owns the docs?

Jim""",
    }
    email_agent.invoke({"email_input": variant}, config=harrison)

    banner("⑥ 翻转第 4 步：换成 andrew 用户（样例库为空）→ 回到 RESPOND，记忆按用户隔离")
    email_agent.invoke(
        {"email_input": variant}, config={"configurable": {"langgraph_user_id": "andrew"}}
    )


if __name__ == "__main__":
    main()
