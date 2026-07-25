"""L2 Baseline 邮件助理 — 本地可运行演示。

对应 lesson2.ipynb 的完整流程：
  triage_router（结构化输出分类 ignore/notify/respond）
  → response_agent（ReAct agent，带 write_email / schedule_meeting / check_calendar_availability 三个模拟工具）

用法：
  python main.py                 # 跑内置的 3 封演示邮件（推销 / 通知 / 需要回复）
  python main.py --verbose       # 额外打印完整 prompt（调试用）
  python main.py --email x.json  # 跑自定义邮件（JSON: author/to/subject/email_thread）
"""

import argparse
import json
import os
import warnings

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.tools import tool

# langchain 内部会把 PendingDeprecationWarning 强制设为 always，
# 这里用局部上下文压掉 langgraph 导入时的序列化器警告
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    from langgraph.graph import StateGraph, START, END
    from langgraph.prebuilt import create_react_agent
    from langgraph.types import Command

from prompts import agent_system_prompt, triage_system_prompt, triage_user_prompt
from schemas import Router, State

from typing import Literal

load_dotenv()

MODEL = os.getenv("MODEL", "deepseek-chat")
VERBOSE = False  # --verbose 时打印完整 prompt

# ---------------------------------------------------------------------------
# 用户画像与规则（与课程一致，内容中文化）
# ---------------------------------------------------------------------------

profile = {
    "name": "张伟",
    "full_name": "张伟",
    "user_profile_background": "高级软件工程师，带一个 5 人的开发团队",
}

prompt_instructions = {
    "triage_rules": {
        "ignore": "营销推广邮件、垃圾邮件、全员群发公告",
        "notify": "团队成员请病假、构建系统通知、项目状态更新",
        "respond": "团队成员的直接提问、会议邀请、严重 bug 报告",
    },
    "agent_instructions": "在合适的时机使用这些工具，帮张伟高效处理事务。",
}

# ---------------------------------------------------------------------------
# LLM
# ---------------------------------------------------------------------------

# thinking disabled: deepseek-v4-flash 默认开 thinking，不支持结构化输出的强制 tool_choice
llm = init_chat_model(
    MODEL,
    model_provider="openai",
    extra_body={"thinking": {"type": "disabled"}},
)
# DeepSeek 等兼容 API 不支持 json_schema response_format，用 function calling 实现结构化输出
llm_router = llm.with_structured_output(Router, method="function_calling")

# ---------------------------------------------------------------------------
# 工具（占位实现，真实场景接邮件/日历 API）
# ---------------------------------------------------------------------------


@tool
def write_email(to: str, subject: str, content: str) -> str:
    """撰写并发送邮件。"""
    return f"已发送邮件给 {to}，主题：'{subject}'"


@tool
def schedule_meeting(
    attendees: list[str], subject: str, duration_minutes: int, preferred_day: str
) -> str:
    """安排日历会议。"""
    return f"会议 '{subject}' 已安排在{preferred_day}，共 {len(attendees)} 人参加"


@tool
def check_calendar_availability(day: str) -> str:
    """查询某天的日历空闲时段。"""
    return f"{day}的空闲时段：上午 9:00、下午 2:00、下午 4:00"


tools = [write_email, schedule_meeting, check_calendar_availability]

# ---------------------------------------------------------------------------
# response agent（ReAct）
# ---------------------------------------------------------------------------


def _print_prompt_messages(prompt) -> None:
    """把发给 LLM 的消息列表渲染成可读格式（--verbose 用）。

    每轮 ReAct 调用前都会打印一次"LLM 本轮看到的完整输入"，
    消息按 [序号|角色] 分块，工具调用的参数逐项展开。
    """
    print(f"\n  📝 ── Agent Prompt（本轮 {len(prompt)} 条消息）" + "─" * 30)
    for i, m in enumerate(prompt, 1):
        if isinstance(m, dict):
            label, content, tool_calls = m["role"], m.get("content", ""), []
        else:
            label = {"human": "user", "ai": "assistant"}.get(m.type, m.type)
            if m.type == "tool":
                label = f"tool:{m.name}"
            content = m.content or ""
            tool_calls = getattr(m, "tool_calls", None) or []
        print(f"  [{i}|{label}]")
        for line in content.splitlines():
            print(f"      {line}")
        for tc in tool_calls:
            print(f"      🛠️ 调用 {tc['name']}:")
            for k, v in tc["args"].items():
                v_str = str(v)
                if "\n" in v_str:
                    print(f"        {k}:")
                    for line in v_str.splitlines():
                        print(f"          {line}")
                else:
                    print(f"        {k}: {v_str}")
    print("  " + "─" * 56)


def create_prompt(state):
    prompt = [
        {
            "role": "system",
            "content": agent_system_prompt.format(
                instructions=prompt_instructions["agent_instructions"], **profile
            ),
        }
    ] + state["messages"]
    if VERBOSE:
        _print_prompt_messages(prompt)
    return prompt


response_agent = create_react_agent(llm, tools=tools, prompt=create_prompt)

# ---------------------------------------------------------------------------
# triage 节点
# ---------------------------------------------------------------------------

CLASSIFICATION_LABELS = {
    "ignore": "🚫 IGNORE —— 直接忽略，不打扰用户",
    "notify": "🔔 NOTIFY —— 通知用户，无需回复",
    "respond": "📧 RESPOND —— 需要回复，转给响应 agent",
}


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
    if VERBOSE:
        print(f"  📝 System Prompt: {system_prompt}")
        print(f"  📨 User Prompt: {user_prompt}")

    result = llm_router.invoke(
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
    )
    print(f"🧠 分类理由: {result.reasoning}")
    print(f"➡️  {CLASSIFICATION_LABELS[result.classification]}")

    if result.classification == "respond":
        return Command(
            goto="response_agent",
            update={
                "messages": [
                    {"role": "user", "content": f"请回复这封邮件 {email}"}
                ]
            },
        )
    if result.classification in ("ignore", "notify"):
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
        "author": "市场部 <marketing@amazingdeals.com>",
        "to": "张伟 <zhangwei@company.com>",
        "subject": "🔥 独家优惠：开发者工具限时折扣！🔥",
        "email_thread": """尊敬的开发者：

千万不要错过这个绝佳机会！

🚀 仅限本周，我们的高级开发者套件全场 2 折！

💰 原价：¥6999/月
🎉 您的专属价：仅需 ¥1399/月！

点击这里领取折扣：https://amazingdeals.com/special-offer

市场部 敬上
""",
    },
    {
        "author": "CI 机器人 <ci@company.com>",
        "to": "张伟 <zhangwei@company.com>",
        "subject": "main 分支夜间构建 #1024 失败",
        "email_thread": """自动通知：

夜间构建 #1024 在集成测试阶段失败。
失败任务：test-auth-service（退出码 1）
日志：https://ci.company.com/builds/1024

-- CI 机器人
""",
    },
    {
        "author": "李娜 <lina@company.com>",
        "to": "张伟 <zhangwei@company.com>",
        "subject": "关于 API 文档的一个小问题",
        "email_thread": """张伟你好，

我在核对新认证服务的 API 文档时，发现有几个接口似乎没写进规范。想跟你确认一下：是有意省略，还是文档需要补？

具体是这两个：
- /auth/refresh
- /auth/validate

谢谢！
李娜""",
    },
]

# ---------------------------------------------------------------------------
# 人类友好的输出渲染
# ---------------------------------------------------------------------------


def _box(text: str, indent: str = "      ") -> None:
    """把邮件正文框起来打印。"""
    print(f"{indent}┌{'─' * 60}")
    for line in (text or "").splitlines():
        print(f"{indent}│ {line}")
    print(f"{indent}└{'─' * 60}")


def _one_line(text: str, limit: int = 90) -> str:
    flat = " ".join((text or "").split())
    return flat[:limit] + ("…" if len(flat) > limit else "")


def render_agent_trace(messages) -> None:
    """把 ReAct 轨迹渲染成可读的步骤列表（代替 pretty_print 的全量 dump）。"""
    step = 0
    final_answer = None
    for m in messages:
        if m.type == "ai":
            tool_calls = getattr(m, "tool_calls", None) or []
            if tool_calls:
                if m.content:
                    print(f"   💭 {_one_line(m.content)}")
                for tc in tool_calls:
                    step += 1
                    name, args = tc["name"], tc["args"]
                    if name == "write_email":
                        print(f"   [{step}] 🛠️  write_email → {args.get('to')}")
                        print(f"       主题: {args.get('subject')}")
                        _box(args.get("content", ""), indent="       ")
                    else:
                        brief = ", ".join(f"{k}={v}" for k, v in args.items())
                        print(f"   [{step}] 🛠️  {name}({brief})")
            elif m.content:
                final_answer = m.content
        elif m.type == "tool":
            print(f"       ↳ {_one_line(m.content)}")
    if final_answer:
        print("   💬 处理总结:")
        for line in final_answer.splitlines():
            print(f"      {line}")


def run_email(email: dict, index: str = "") -> None:
    print()
    print(f"═══ 邮件{index} ".ljust(72, "═"))
    print(f"发件人: {email['author']}")
    print(f"主题:   {email['subject']}")
    print("─" * 72)
    response = email_agent.invoke({"email_input": email})
    messages = response.get("messages", [])
    if messages:
        print("🤖 响应 agent 执行轨迹:")
        render_agent_trace(messages)


def main() -> None:
    global VERBOSE
    parser = argparse.ArgumentParser(description="L2 baseline 邮件助理演示")
    parser.add_argument("--email", help="自定义邮件 JSON 文件路径")
    parser.add_argument("--verbose", action="store_true", help="打印完整 prompt（调试）")
    args = parser.parse_args()
    VERBOSE = args.verbose

    print(f"模型: {MODEL} @ {os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1')}")

    if args.email:
        with open(args.email) as f:
            run_email(json.load(f))
    else:
        for i, email in enumerate(SAMPLE_EMAILS, 1):
            run_email(email, f" {i}/{len(SAMPLE_EMAILS)}")


if __name__ == "__main__":
    main()
