"""L5 程序性记忆（prompt 自我改写）— python 命令直接运行的课程演示。

对应 lesson_5.ipynb 完整流程：
  1) triage 规则和 agent 指令都放进 store（首跑写入默认值，之后每次从 store 读）
  2) create_multi_prompt_optimizer 把自然语言反馈写回 prompt：
     反馈① "Always sign your emails `John Doe`" → main_agent 指令被改写，回信带签名
     反馈② "Ignore any emails from Alice Jones" → triage-ignore 规则被改写，
       同一封邮件从 RESPOND 翻成 IGNORE

用法（code/ 根目录下）：
  .venv/bin/python L5/main.py
"""

import json
from typing import Literal

from local_stack import make_llm, make_embed, EMBED_DIMS

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
from pydantic import BaseModel, Field
from schemas import Router, State


def banner(title: str) -> None:
    print(f"\n{'=' * 70}\n{title}\n{'=' * 70}")


profile = {
    "name": "John",
    "full_name": "John Doe",
    "user_profile_background": "Senior software engineer leading a team of 5 developers",
}

# 仅作首跑默认值，之后 triage 规则/agent 指令都以 store 里的为准
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
# few-shot 模板（本课样例库为空，仅保持与课程一致的 prompt 结构）
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


def _get_or_seed(namespace, key, default: str) -> str:
    """从 store 读 prompt，不存在则写入默认值（程序性记忆的读路径）。"""
    result = store.get(namespace, key)
    if result is None:
        store.put(namespace, key, {"prompt": default})
        return default
    return result.value["prompt"]


# ---------------------------------------------------------------------------
# triage 路由（规则来自 store）+ 响应 agent（指令来自 store）+ 图
# ---------------------------------------------------------------------------

def triage_router(state: State, config, store) -> Command[
    Literal["response_agent", "__end__"]
]:
    author = state["email_input"]["author"]
    to = state["email_input"]["to"]
    subject = state["email_input"]["subject"]
    email_thread = state["email_input"]["email_thread"]

    user_id = config["configurable"]["langgraph_user_id"]
    examples = store.search(
        ("email_assistant", user_id, "examples"),
        query=str({"email": state["email_input"]}),
    )
    examples = format_few_shot_examples(examples)

    namespace = (user_id,)
    ignore_prompt = _get_or_seed(
        namespace, "triage_ignore", prompt_instructions["triage_rules"]["ignore"]
    )
    notify_prompt = _get_or_seed(
        namespace, "triage_notify", prompt_instructions["triage_rules"]["notify"]
    )
    respond_prompt = _get_or_seed(
        namespace, "triage_respond", prompt_instructions["triage_rules"]["respond"]
    )

    system_prompt = triage_system_prompt.format(
        full_name=profile["full_name"],
        name=profile["name"],
        user_profile_background=profile["user_profile_background"],
        triage_no=ignore_prompt,
        triage_notify=notify_prompt,
        triage_email=respond_prompt,
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


def create_prompt(state, config, store):
    user_id = config["configurable"]["langgraph_user_id"]
    prompt = _get_or_seed(
        (user_id,), "agent_instructions", prompt_instructions["agent_instructions"]
    )
    return [
        {
            "role": "system",
            "content": agent_system_prompt_memory.format(instructions=prompt, **profile),
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

optimizer = create_multi_prompt_optimizer(
    make_llm(),  # 本地化：deepseek-v4-flash（原 anthropic:claude-3-5-sonnet-latest）
    kind="prompt_memory",
)

# optimizer 可改写的 prompt 及其写回 store 的 key
PROMPT_STORE_KEYS = {
    "main_agent": "agent_instructions",
    "triage-ignore": "triage_ignore",
    "triage-notify": "triage_notify",
    "triage-respond": "triage_respond",
}


def current_prompts():
    return [
        {
            "name": "main_agent",
            "prompt": store.get(("lance",), "agent_instructions").value["prompt"],
            "update_instructions": "keep the instructions short and to the point",
            "when_to_update": "Update this prompt whenever there is feedback on how the agent should write emails or schedule events",
        },
        {
            "name": "triage-ignore",
            "prompt": store.get(("lance",), "triage_ignore").value["prompt"],
            "update_instructions": "keep the instructions short and to the point",
            "when_to_update": "Update this prompt whenever there is feedback on which emails should be ignored",
        },
        {
            "name": "triage-notify",
            "prompt": store.get(("lance",), "triage_notify").value["prompt"],
            "update_instructions": "keep the instructions short and to the point",
            "when_to_update": "Update this prompt whenever there is feedback on which emails the user should be notified of",
        },
        {
            "name": "triage-respond",
            "prompt": store.get(("lance",), "triage_respond").value["prompt"],
            "update_instructions": "keep the instructions short and to the point",
            "when_to_update": "Update this prompt whenever there is feedback on which emails should be responded to",
        },
    ]


class FeedbackTarget(BaseModel):
    """Decide which single prompt a piece of user feedback should update."""

    reasoning: str = Field(description="Step-by-step reasoning behind the choice.")
    target: Literal["main_agent", "triage-ignore", "triage-notify", "triage-respond"] = Field(
        description="The one prompt this feedback should update."
    )


def route_feedback(feedback: str, prompts) -> str:
    """第一层：按各 prompt 的 when_to_update 描述，路由反馈该改哪一个 prompt。"""
    descriptions = "\n".join(f"- {p['name']}: {p['when_to_update']}" for p in prompts)
    result = llm.with_structured_output(FeedbackTarget).invoke(
        [
            {
                "role": "system",
                "content": (
                    "You maintain a set of prompts for an email assistant. "
                    "Given a piece of user feedback, decide which ONE prompt should be updated.\n\n"
                    f"Prompts and when to update each:\n{descriptions}"
                ),
            },
            {"role": "user", "content": feedback},
        ]
    )
    print(f"  🎯 路由: 反馈应更新 {result.target}")
    return result.target


def apply_feedback(messages, feedback: str) -> None:
    """程序性记忆更新：路由 → 定向改写 → 完整性校验，三层均与反馈内容无关。

    multi_prompt optimizer 让 LLM 一次性改写全部 prompt 时，偶发把规则写错
    位置、或顺手清空别的 prompt（trajectory 每次运行不同，temperature=0 防不住）。
    先路由出目标 prompt，再只把这一个交给 optimizer，结构上消除错位；
    空串不写回，兜底数据完整性。
    """
    prompts = current_prompts()
    target = route_feedback(feedback, prompts)
    target_prompt = next(p for p in prompts if p["name"] == target)
    # 空输出是结构性无效结果（长 trajectory 下偶发），重试属于契约校验而非语义预设
    for attempt in range(1, 4):
        updated = optimizer.invoke(
            {"trajectories": [(messages, feedback)], "prompts": [target_prompt]}
        )
        new_prompt = (updated[0]["prompt"] or "").strip()
        if new_prompt:
            break
        print(f"  ⚠️ optimizer 返回空 prompt（第 {attempt} 次），重试")
    else:
        print(f"  ❌ optimizer 连续 3 次返回空 prompt，保留原 {target}")
        return
    if new_prompt == target_prompt["prompt"]:
        print(f"  ⏸ {target} 无变化")
        return
    store.put(("lance",), PROMPT_STORE_KEYS[target], {"prompt": new_prompt})
    print(f"  ✏️ updated {target}:")
    print(f"     旧: {target_prompt['prompt'][:120]}")
    print(f"     新: {new_prompt[:120]}")


def main() -> None:
    config = {"configurable": {"langgraph_user_id": "lance"}}
    email_input = {
        "author": "Alice Jones <alice.jones@bar.com>",
        "to": "John Doe <john.doe@company.com>",
        "subject": "Quick question about API documentation",
        "email_thread": """Hi John,

Urgent issue - your service is down. Is there a reason why""",
    }

    banner("① 首跑：prompt 从默认值写入 store，邮件 → RESPOND 并起草回信")
    response = email_agent.invoke({"email_input": email_input}, config=config)
    for m in response["messages"]:
        m.pretty_print()
    print("\n当前 store 里的 agent_instructions:")
    print(" ", store.get(("lance",), "agent_instructions").value["prompt"])

    banner("② 反馈①: 'Always sign your emails `John Doe`' → optimizer 改写 prompt")
    apply_feedback(response["messages"], "Always sign your emails `John Doe`")

    banner("③ 同一封邮件再跑：回信应带 John Doe 签名")
    response = email_agent.invoke({"email_input": email_input}, config=config)
    for m in response["messages"]:
        m.pretty_print()

    banner("④ 反馈②: 'Ignore any emails from Alice Jones' → optimizer 改写 triage 规则")
    apply_feedback(response["messages"], "Ignore any emails from Alice Jones")
    print("\n当前 store 里的 triage_ignore:")
    print(" ", store.get(("lance",), "triage_ignore").value["prompt"])

    banner("⑤ 同一封邮件再跑：应从 RESPOND 翻成 IGNORE")
    email_agent.invoke({"email_input": email_input}, config=config)

    banner("最终 store 里的全部 prompt")
    final = {
        name: store.get(("lance",), key).value["prompt"]
        for name, key in PROMPT_STORE_KEYS.items()
    }
    print(json.dumps(final, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
