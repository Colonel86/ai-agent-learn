"""12b·L1 从零实现自编辑记忆（MemGPT 思想）— 本地可运行演示。

课程主题：与其硬编码记忆管理，不如把"编辑记忆"做成工具交给 LLM 自己调
（self-editing memory）。本文件用裸 OpenAI SDK 复现 notebook 全部四步：

演示流程（python main.py）：
  ① 裸 chatbot：没有记忆，答不出"我叫什么"
  ② 记忆拼进 system prompt（只读）：能答，但记忆是人手写死的
  ③ core_memory_save 工具（单步）：LLM 自己发起 tool call 写记忆，但只能
     "存"或"答"二选一
  ④ agentic loop（多步推理）：循环调 LLM——tool call 就执行并继续，
     纯文本就返回用户；一轮输入内既存记忆又回复
  ⑤ 新会话验证：清空聊天历史只留 [MEMORY]，仍能答对 → 跨会话记忆
"""

import json
import os

from dotenv import load_dotenv
from openai import OpenAI

# .env 在 code/ 根目录（全课程共享）
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env"))

MODEL = os.getenv("MODEL", "deepseek-v4-flash")
client = OpenAI()

# DeepSeek v4 系列默认开 thinking，会拖慢演示且与 tool call 交互不稳，显式关掉
EXTRA_BODY = (
    {"thinking": {"type": "disabled"}}
    if "deepseek" in MODEL or "deepseek" in os.getenv("OPENAI_BASE_URL", "")
    else None
)


def chat(messages, tools=None):
    kwargs = {"model": MODEL, "messages": messages}
    if tools:
        kwargs["tools"] = tools
    if EXTRA_BODY:
        kwargs["extra_body"] = EXTRA_BODY
    return client.chat.completions.create(**kwargs).choices[0]


def banner(title):
    print("\n" + "=" * 72)
    print(title)
    print("=" * 72)


# ---------------------------------------------------------------------------
# ① 裸 chatbot：没有记忆
# ---------------------------------------------------------------------------

banner("① 裸 chatbot（无记忆）—— 问：我叫什么名字？")
resp = chat([
    {"role": "system", "content": "You are a chatbot."},
    {"role": "user", "content": "我叫什么名字？"},
])
print(resp.message.content)

# ---------------------------------------------------------------------------
# ② 记忆拼进 context（只读）
# ---------------------------------------------------------------------------

banner("② [MEMORY] 拼进 system prompt（只读记忆）—— 同样的问题")

SYSTEM_PROMPT = (
    "You are a chatbot. "
    "You have a section of your context called [MEMORY] "
    "that contains information relevant to your conversation"
)

agent_memory = {"human": "姓名：张伟"}
resp = chat([
    {"role": "system", "content": SYSTEM_PROMPT + "\n[MEMORY]\n" + json.dumps(agent_memory, ensure_ascii=False)},
    {"role": "user", "content": "我叫什么名字？"},
])
print(resp.message.content)
print("\n(记忆是人手写死的 —— 下一步让 LLM 自己写)")

# ---------------------------------------------------------------------------
# ③ core_memory_save 工具：LLM 自编辑记忆（单步）
# ---------------------------------------------------------------------------

banner("③ core_memory_save 工具（单步）—— 用户自我介绍，LLM 发起 tool call")

agent_memory = {"human": "", "agent": ""}


def core_memory_save(section: str, memory: str):
    agent_memory[section] += "\n" + memory


CORE_MEMORY_SAVE_SCHEMA = {
    "type": "function",
    "function": {
        "name": "core_memory_save",
        "description": "Save important information about you, the agent, or the human you are chatting with.",
        "parameters": {
            "type": "object",
            "properties": {
                "section": {
                    "type": "string",
                    "enum": ["human", "agent"],
                    "description": "Must be either 'human' (to save information about the human) or 'agent' (to save information about yourself)",
                },
                "memory": {
                    "type": "string",
                    "description": "Memory to save in the section",
                },
            },
            "required": ["section", "memory"],
        },
    },
}

resp = chat(
    [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "system", "content": "[MEMORY]\n" + json.dumps(agent_memory, ensure_ascii=False)},
        {"role": "user", "content": "我叫张伟，在带一个 5 人的后端团队。"},
    ],
    tools=[CORE_MEMORY_SAVE_SCHEMA],
)

for tc in resp.message.tool_calls or []:
    args = json.loads(tc.function.arguments)
    print(f"TOOL CALL: core_memory_save({args})")
    core_memory_save(**args)  # OpenAI 不替你执行工具，得自己跑

print("\n更新后的 agent_memory:")
print(json.dumps(agent_memory, ensure_ascii=False, indent=2))
print("\n(单步的局限：这一轮只发了 tool call，没有给用户任何回复)")

# ---------------------------------------------------------------------------
# ④ agentic loop：多步推理，一轮内既存记忆又回复
# ---------------------------------------------------------------------------

banner("④ agentic loop —— tool call 不中断循环，纯文本回复才交还用户")

SYSTEM_PROMPT_OS = (
    SYSTEM_PROMPT
    + "\nYou must either call a tool (core_memory_save) or write a response to the user. "
    + "Do not take the same actions multiple times! "
    + "When you learn new information, make sure to always call the core_memory_save tool."
)

agent_memory = {"human": ""}


def agent_step(user_message, chat_history=None):
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT_OS},
        # 记忆每次都重新拼装，反映最新状态
        {"role": "system", "content": "[MEMORY]\n" + json.dumps(agent_memory, ensure_ascii=False)},
        *(chat_history or []),
        {"role": "user", "content": user_message},
    ]

    while True:
        resp = chat(messages, tools=[CORE_MEMORY_SAVE_SCHEMA])
        messages.append(resp.message)

        # 纯文本回复 → 跳出循环，交还用户
        if not resp.message.tool_calls:
            return resp.message.content

        # tool call → 执行工具，把结果喂回去，继续循环
        for tc in resp.message.tool_calls:
            args = json.loads(tc.function.arguments)
            print(f"  TOOL CALL: core_memory_save({args})")
            core_memory_save(**args)
            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": f"Updated memory: {json.dumps(agent_memory, ensure_ascii=False)}",
            })


print("\n>>> 用户：我叫张伟，在带一个 5 人的后端团队。")
reply = agent_step("我叫张伟，在带一个 5 人的后端团队。")
print(f"<<< 助手：{reply}")

# ---------------------------------------------------------------------------
# ⑤ 新会话验证：聊天历史清零，只靠 [MEMORY] 回答
# ---------------------------------------------------------------------------

banner("⑤ 新会话（chat_history=[]）—— 只靠记忆回答")

print("\n当前 agent_memory:")
print(json.dumps(agent_memory, ensure_ascii=False, indent=2))

print("\n>>> 用户（新会话）：我叫什么名字？我是做什么的？")
reply = agent_step("我叫什么名字？我是做什么的？")
print(f"<<< 助手：{reply}")

print("\n✅ 演示完成：记忆管理本身也是一个工具，谁来调？LLM 自己。")
