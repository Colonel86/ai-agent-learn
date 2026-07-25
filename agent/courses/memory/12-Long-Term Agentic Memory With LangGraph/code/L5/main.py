"""L5 邮件助理 + Procedural Memory（程序性记忆）— 本地可运行演示。

在 L4 基础上，把 4 段指令 prompt（agent_instructions / triage_ignore /
triage_notify / triage_respond）从硬编码搬进 store（namespace=(user_id,)），
并用 langmem 的 multi-prompt optimizer 根据用户反馈自动改写它们——
agent 的「行为习惯」本身变成了可学习的记忆。

演示脚本（python main.py）四幕：
  第一幕：Alice 提问邮件 → 回复；查看 store 里的当前指令
  第二幕：反馈 "Always sign your emails `John Doe`" → optimizer 改写指令并写回 store
  第三幕：同一封邮件重跑 → 回复末尾按新指令签名 John Doe
  第四幕：Alice Jones 的邮件先 RESPOND；反馈 "Ignore any emails from Alice Jones"
          → triage_ignore 被改写 → 重跑变 IGNORE
"""

import os

from dotenv import load_dotenv

load_dotenv()
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

from typing import Literal

from fastembed import TextEmbedding
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import create_react_agent
from langgraph.store.memory import InMemoryStore
from langgraph.types import Command
from langmem import (
    create_manage_memory_tool,
    create_multi_prompt_optimizer,
    create_search_memory_tool,
)

from prompts import triage_user_prompt
from schemas import Router, State

MODEL = os.getenv("MODEL", "deepseek-chat")
USER_ID = "demo"

profile = {
    "name": "John",
    "full_name": "John Doe",
    "user_profile_background": "Senior software engineer leading a team of 5 developers",
}

# 只作为 store 的初始值，之后以 store 里的版本为准
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


class FunctionCallingChat(ChatOpenAI):
    """DeepSeek 不支持 json_schema response_format。

    langmem 0.0.8 的 PromptMemory 硬编码了 method="json_schema"
    （langmem/prompts/stateless.py），所以这里必须无条件覆盖，
    不能只改默认值。
    """

    def with_structured_output(self, schema, **kwargs):
        kwargs["method"] = "function_calling"
        return super().with_structured_output(schema, **kwargs)


# thinking disabled: deepseek-v4-flash 默认开 thinking，不支持结构化输出的强制 tool_choice
llm = FunctionCallingChat(
    model=MODEL,
    temperature=0,
    extra_body={"thinking": {"type": "disabled"}},
)
llm_router = llm.with_structured_output(Router)

_embedder = TextEmbedding("BAAI/bge-small-en-v1.5")


def embed(texts: list[str]) -> list[list[float]]:
    return [v.tolist() for v in _embedder.embed(texts)]


store = InMemoryStore(index={"embed": embed, "dims": 384})

# ---------------------------------------------------------------------------
# store 中的可进化 prompt：首次访问用默认值初始化
# ---------------------------------------------------------------------------

PROMPT_DEFAULTS = {
    "agent_instructions": prompt_instructions["agent_instructions"],
    "triage_ignore": prompt_instructions["triage_rules"]["ignore"],
    "triage_notify": prompt_instructions["triage_rules"]["notify"],
    "triage_respond": prompt_instructions["triage_rules"]["respond"],
}


def get_prompt(key: str) -> str:
    namespace = (USER_ID,)
    result = store.get(namespace, key)
    if result is None:
        store.put(namespace, key, {"prompt": PROMPT_DEFAULTS[key]})
        return PROMPT_DEFAULTS[key]
    return result.value["prompt"]


# ---------------------------------------------------------------------------
# few-shot（同 L4）
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
# 工具与 response agent：agent_instructions 每次从 store 读
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


def create_prompt(state, config, store):
    return [
        {
            "role": "system",
            "content": agent_system_prompt_memory.format(
                instructions=get_prompt("agent_instructions"), **profile
            ),
        }
    ] + state["messages"]


response_agent = create_react_agent(llm, tools=tools, prompt=create_prompt, store=store)

# ---------------------------------------------------------------------------
# triage 节点：规则从 store 读 + few-shot 检索
# ---------------------------------------------------------------------------


def triage_router(
    state: State, config, store
) -> Command[Literal["response_agent", "__end__"]]:
    email = state["email_input"]

    examples = store.search(
        ("email_assistant", config["configurable"]["langgraph_user_id"], "examples"),
        query=str({"email": email}),
    )
    examples = format_few_shot_examples(examples)

    system_prompt = triage_system_prompt.format(
        full_name=profile["full_name"],
        name=profile["name"],
        user_profile_background=profile["user_profile_background"],
        triage_no=get_prompt("triage_ignore"),
        triage_notify=get_prompt("triage_notify"),
        triage_email=get_prompt("triage_respond"),
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
# 反馈 → optimizer 改写 prompt → 写回 store
# ---------------------------------------------------------------------------

optimizer = create_multi_prompt_optimizer(llm, kind="prompt_memory")

# optimizer 里的 prompt 名 → store key
PROMPT_STORE_KEYS = {
    "main_agent": "agent_instructions",
    "triage-ignore": "triage_ignore",
    "triage-notify": "triage_notify",
    "triage-respond": "triage_respond",
}


def apply_feedback(messages, feedback: str) -> None:
    print(f'\n  💬 用户反馈: "{feedback}"')
    prompts = [
        {
            "name": "main_agent",
            "prompt": get_prompt("agent_instructions"),
            "update_instructions": "keep the instructions short and to the point",
            "when_to_update": "Update this prompt whenever there is feedback on how the agent should write emails or schedule events",
        },
        {
            "name": "triage-ignore",
            "prompt": get_prompt("triage_ignore"),
            "update_instructions": "keep the instructions short and to the point",
            "when_to_update": "Update this prompt whenever there is feedback on which emails should be ignored",
        },
        {
            "name": "triage-notify",
            "prompt": get_prompt("triage_notify"),
            "update_instructions": "keep the instructions short and to the point",
            "when_to_update": "Update this prompt whenever there is feedback on which emails the user should be notified of",
        },
        {
            "name": "triage-respond",
            "prompt": get_prompt("triage_respond"),
            "update_instructions": "keep the instructions short and to the point",
            "when_to_update": "Update this prompt whenever there is feedback on which emails should be responded to",
        },
    ]
    updated = optimizer.invoke(
        {"trajectories": [(messages, feedback)], "prompts": prompts}
    )
    # notebook 只回写了 main_agent、其余留作练习；这里补全全部 4 个
    for old, new in zip(prompts, updated):
        if new["prompt"] != old["prompt"]:
            key = PROMPT_STORE_KEYS[old["name"]]
            store.put((USER_ID,), key, {"prompt": new["prompt"]})
            print(f"  ✏️  {old['name']} 已更新 → store[{key}]:")
            print(f"      {new['prompt']}")


# ---------------------------------------------------------------------------
# 演示
# ---------------------------------------------------------------------------

config = {"configurable": {"langgraph_user_id": USER_ID}}

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

ALICE_JONES_EMAIL = {
    "author": "Alice Jones <alice.jones@bar.com>",
    "to": "John Doe <john.doe@company.com>",
    "subject": "Quick question about API documentation",
    "email_thread": """Hi John,

Urgent issue - your service is down. Is there a reason why""",
}


def banner(title: str) -> None:
    print()
    print("=" * 72)
    print(title)
    print("=" * 72)


def run_email(email: dict):
    print(f"\nFrom:    {email['author']}  Subject: {email['subject']}")
    response = email_agent.invoke({"email_input": email}, config=config)
    for m in response.get("messages", []):
        m.pretty_print()
    return response


def show_instructions() -> None:
    print("\n  🗄️  store 中当前指令:")
    for key in PROMPT_DEFAULTS:
        print(f"    - {key}: {get_prompt(key)}")


def main() -> None:
    print(f"Model: {MODEL} @ {os.getenv('OPENAI_BASE_URL')}")
    print("Embedding: fastembed / BAAI/bge-small-en-v1.5 (local CPU)")

    banner("第一幕 · 基线：Alice 提问邮件 → 回复（注意签名方式）")
    response = run_email(ALICE_EMAIL)
    show_instructions()

    banner('第二幕 · 反馈进化：\"Always sign your emails `John Doe`\"')
    apply_feedback(response["messages"], "Always sign your emails `John Doe`")
    show_instructions()

    banner("第三幕 · 同一封邮件重跑：回复应按新指令签名 John Doe")
    run_email(ALICE_EMAIL)

    banner("第四幕 · 改 triage 行为：先看 Alice Jones 邮件的默认分类")
    response = run_email(ALICE_JONES_EMAIL)
    apply_feedback(response["messages"], "Ignore any emails from Alice Jones")
    show_instructions()
    print("\n  重跑 Alice Jones 邮件:")
    run_email(ALICE_JONES_EMAIL)


if __name__ == "__main__":
    main()
