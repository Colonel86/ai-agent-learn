"""L2 Baseline 邮件助理 — 本地可运行演示。

对应 lesson2.ipynb 的完整流程：
  triage_router（结构化输出分类 ignore/notify/respond）
  → response_agent（ReAct agent，带 write_email / schedule_meeting / check_calendar_availability 三个模拟工具）

用法：
  python main.py                 # 跑内置的 3 封演示邮件（spam / 通知 / 需要回复）
  python main.py --email x.json  # 跑自定义邮件（JSON: author/to/subject/email_thread）
"""

import argparse
import json
import os
from typing import Literal

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.tools import tool
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import create_react_agent
from langgraph.types import Command

from prompts import agent_system_prompt, triage_system_prompt, triage_user_prompt
from schemas import Router, State

load_dotenv()

MODEL = os.getenv("MODEL", "deepseek-chat")

# ---------------------------------------------------------------------------
# 用户画像与规则（与课程一致）
# ---------------------------------------------------------------------------

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
# LLM
# ---------------------------------------------------------------------------

llm = init_chat_model(MODEL, model_provider="openai")
# DeepSeek 等兼容 API 不支持 json_schema response_format，用 function calling 实现结构化输出
llm_router = llm.with_structured_output(Router, method="function_calling")

# ---------------------------------------------------------------------------
# 工具（占位实现，真实场景接邮件/日历 API）
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


tools = [write_email, schedule_meeting, check_calendar_availability]

# ---------------------------------------------------------------------------
# response agent（ReAct）
# ---------------------------------------------------------------------------


def create_prompt(state):
    prompt = [
        {
            "role": "system",
            "content": agent_system_prompt.format(
                instructions=prompt_instructions["agent_instructions"], **profile
            ),
        }
    ] + state["messages"]
    print(f"  📝 Agent Prompt: {prompt}")
    return prompt


response_agent = create_react_agent(llm, tools=tools, prompt=create_prompt)

# ---------------------------------------------------------------------------
# triage 节点
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
    print(f"  📝 System Prompt: {system_prompt}")
    user_prompt = triage_user_prompt.format(
        author=email["author"],
        to=email["to"],
        subject=email["subject"],
        email_thread=email["email_thread"],
    )
    print(f"  📨 User Prompt: {user_prompt}")
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
                    {
                        "role": "user",
                        "content": f"Respond to the email {email}",
                    }
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


# ---------------------------------------------------------------------------
# 组装总图
# ---------------------------------------------------------------------------

email_agent = (
    StateGraph(State)
    .add_node(triage_router)
    .add_node("response_agent", response_agent)
    .add_edge(START, "triage_router")
    .compile()
)

# ---------------------------------------------------------------------------
# 演示邮件
# ---------------------------------------------------------------------------

SAMPLE_EMAILS = [
    {
        "author": "Marketing Team <marketing@amazingdeals.com>",
        "to": "John Doe <john.doe@company.com>",
        "subject": "🔥 EXCLUSIVE OFFER: Limited Time Discount on Developer Tools! 🔥",
        "email_thread": """Dear Valued Developer,

Don't miss out on this INCREDIBLE opportunity!

🚀 For a LIMITED TIME ONLY, get 80% OFF on our Premium Developer Suite!

💰 Regular Price: $999/month
🎉 YOUR SPECIAL PRICE: Just $199/month!

Click here to claim your discount: https://amazingdeals.com/special-offer

Best regards,
Marketing Team
""",
    },
    {
        "author": "CI Bot <ci@company.com>",
        "to": "John Doe <john.doe@company.com>",
        "subject": "Nightly build #1024 failed on main",
        "email_thread": """Automated notification:

Nightly build #1024 failed during the integration test stage.
Failed job: test-auth-service (exit code 1)
Logs: https://ci.company.com/builds/1024

-- CI Bot
""",
    },
    {
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
]


def run_email(email: dict) -> None:
    print("=" * 72)
    print(f"From:    {email['author']}")
    print(f"Subject: {email['subject']}")
    print("-" * 72)
    response = email_agent.invoke({"email_input": email})
    for m in response.get("messages", []):
        m.pretty_print()
    print()


def main() -> None:
    parser = argparse.ArgumentParser(description="L2 baseline email assistant demo")
    parser.add_argument(
        "--email",
        help="Path to a JSON file with keys: author, to, subject, email_thread",
    )
    args = parser.parse_args()

    print(f"Model: {MODEL} @ {os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1')}\n")

    if args.email:
        with open(args.email) as f:
            run_email(json.load(f))
    else:
        for email in SAMPLE_EMAILS:
            run_email(email)


if __name__ == "__main__":
    main()
