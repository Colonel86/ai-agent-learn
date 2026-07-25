"""12b·L6 多智能体编排 — 本地可运行演示。

课程主题：MemGPT/Letta 的多智能体协作靠两样东西——
① 共享 memory block：一个 block 同时挂到多个 agent 的 core memory，
   任何一个 agent 改它，其他 agent 立即可见（共享大脑）；
② 跨 agent 消息：`send_message_to_agent_and_wait_for_reply` 工具让
   agent 之间点对点通信（显式编排），或者用 group 做 round-robin 轮转。

前提：先在另一个终端跑 ./run_server.sh（本地 embedding 服务 + Letta server）。

演示流程（python main.py）：
  ① 创建共享 company block（独立于任何 agent 的一等对象）
  ② 显式编排：eval_agent 评估简历 → 好候选人经跨 agent 工具发给
     outreach_agent 起草邮件（Tony Stark 应该被通过）
  ③ round-robin group：两个 agent 组队轮流处理同一条消息
     （SpongeBob 的简历……应该被拒）
  ④ 共享记忆：告诉 outreach_agent_v2 “公司改名 Letta” → 连 eval_agent
     （①②里的老 agent）的 company block 也同步变化

注：课程 notebook 里共享记忆是第 3 节、group 是第 4 节；这里对调，
因为本地 deepseek 栈给 outreach_agent 加了 run_first 工具规则（见下），
共享记忆演示改用没有该规则的 outreach_agent_v2 更干净。
"""

import os

# 本机开着系统代理时，httpx 会把 localhost 请求也送进代理，必须绕过
os.environ.setdefault("NO_PROXY", "localhost,127.0.0.1")
os.environ.setdefault("no_proxy", "localhost,127.0.0.1")

from dotenv import load_dotenv

load_dotenv()

from letta_client import Letta

# chat 走 Letta 的 openai 兼容路径指向 DeepSeek（原生 function calling，
# 不用 letta 0.6.50 里那条靠裸 JSON 解析的 deepseek 专用路径——很不稳）
LLM_CONFIG = {
    "model": os.getenv("LETTA_MODEL", "deepseek-v4-flash"),
    "model_endpoint_type": "openai",
    "model_endpoint": os.getenv("OPENAI_BASE_URL", "https://api.deepseek.com/v1"),
    "context_window": 64000,
    "put_inner_thoughts_in_kwargs": True,
    "temperature": 0.0,
}

# embedding 走本地 fastembed 服务（DeepSeek 没有 embeddings API）
EMBEDDING_CONFIG = {
    "embedding_model": "BAAI/bge-small-en-v1.5",
    "embedding_endpoint_type": "hugging-face",
    "embedding_endpoint": "http://localhost:8003/v1",
    "embedding_dim": 384,
    "embedding_chunk_size": 300,
}

GROUP_DESCRIPTION = "This team is responsible for recruiting candidates."


def print_message(message, with_name=False):
    who = f" ({message.name})" if with_name and getattr(message, "name", None) else ""
    if message.message_type == "reasoning_message":
        print(f"🧠 Reasoning{who}: " + message.reasoning)
    elif message.message_type == "assistant_message":
        print(f"🤖 Agent{who}: " + message.content)
    elif message.message_type == "tool_call_message":
        print(f"🔧 Tool Call{who}: " + message.tool_call.name + " " + message.tool_call.arguments)
    elif message.message_type == "tool_return_message":
        print(f"🔧 Tool Return{who}: " + str(message.tool_return)[:300])
    elif message.message_type == "user_message":
        print("👤 User: " + str(message.content)[:120])
    elif message.message_type == "system_message":
        print("⚙️ System: " + str(message.content)[:120])


def banner(title):
    print("\n" + "=" * 72)
    print(title)
    print("=" * 72)


client = Letta(base_url="http://localhost:8283")

# 可重复运行：先删本演示的旧 group / 旧 agent / 旧共享 block
for g in client.groups.list():
    if g.description == GROUP_DESCRIPTION:
        client.groups.delete(group_id=g.id)
for a in client.agents.list():
    if a.name in {"outreach_agent", "eval_agent", "outreach_agent_v2", "eval_agent_v2"}:
        client.agents.delete(agent_id=a.id)
for b in client.blocks.list():
    if b.label == "company":
        client.blocks.delete(block_id=b.id)

# ---------------------------------------------------------------------------
# ① 共享 memory block：独立创建，稍后挂到多个 agent
# ---------------------------------------------------------------------------

banner("① 创建共享 company block")

company_description = (
    "The company is called AgentOS and is building AI tools "
    "to make it easier to create and deploy LLM agents."
)

company_block = client.blocks.create(
    value=company_description,
    label="company",
    limit=10000,
)
print(f"block id: {company_block.id}")
print(f"value: {company_block.value!r}")

# ---------------------------------------------------------------------------
# ② 显式编排：eval_agent --send_message_to_agent--> outreach_agent
# ---------------------------------------------------------------------------

banner("② 显式编排 —— 评估简历并转交外联")


def draft_candidate_email(content: str):
    """
    Draft an email to reach out to a candidate.

    Args:
        content (str): Content of the email
    """
    return f"Here is a draft email: {content}"


def reject(candidate_name: str):
    """
    Reject a candidate.

    Args:
        candidate_name (str): The name of the candidate
    """
    return


draft_email_tool = client.tools.upsert_from_function(func=draft_candidate_email)
reject_tool = client.tools.upsert_from_function(func=reject)

outreach_persona = (
    "You are responsible for drafting emails "
    "on behalf of a company with the draft_candidate_email tool. "
    "Candidates to email will be messaged to you. "
    "Always draft the email with the tool first (request_heartbeat=true), "
    "then reply with the draft. "
)

# 比课程多加 run_first 工具规则：letta 跨 agent 来信的包装语写着
# "make sure to use the 'send_message'"，deepseek 会逐字服从、寒暄完就
# 结束回合，永远轮不到 draft 工具；run_first 在 API 层面把第一跳锁死
outreach_agent = client.agents.create(
    name="outreach_agent",
    memory_blocks=[{"label": "persona", "value": outreach_persona}],
    llm_config=LLM_CONFIG,
    embedding_config=EMBEDDING_CONFIG,
    tools=[draft_email_tool.name],
    block_ids=[company_block.id],
    tool_rules=[{"type": "run_first", "tool_name": "draft_candidate_email"}],
)

# 预热：deepseek 会把“首次登录”事件和跨 agent 来信混在同一轮里，
# 固定优先寒暄而不干活；先消耗掉登录寒暄，让来信单独成轮
client.agents.messages.create(
    agent_id=outreach_agent.id,
    messages=[{"role": "user", "content": "hi (warm-up, no drafting needed yet)"}],
)

skills = "Front-end (React, Typescript) or software engineering skills"

eval_persona = (
    f"You are responsible for evaluating candidates. "
    f"Ideal candidates have skills: {skills}. "
    "Reject bad candidates with your reject tool. "
    f"Send strong candidates to agent ID {outreach_agent.id}. "
    "You must either reject or send candidates to the other agent. "
    # 比课程 persona 多加一句：deepseek-v4-flash 会识破 Tony Stark 是虚构人名
    # 而当成假简历拒掉，需要声明名字只是测试占位符、只看技能
    "Candidate names are anonymized placeholders from our ATS; "
    "ignore the name entirely and judge strictly on skills. "
    "When you send a candidate to the other agent, include the candidate's "
    "details and explicitly ask it to draft the outreach email right away. "
)

# eval_agent 只有两条出路：reject 或转发给 outreach_agent（转发即退出循环）
eval_agent = client.agents.create(
    name="eval_agent",
    memory_blocks=[{"label": "persona", "value": eval_persona}],
    llm_config=LLM_CONFIG,
    embedding_config=EMBEDDING_CONFIG,
    tool_ids=[reject_tool.id],
    tools=["send_message_to_agent_and_wait_for_reply"],
    include_base_tools=False,
    block_ids=[company_block.id],
    tool_rules=[
        {"type": "exit_loop", "tool_name": "send_message_to_agent_and_wait_for_reply"}
    ],
)
print(f"eval_agent 工具: {[t.name for t in eval_agent.tools]}")
print(f"outreach_agent 工具: {[t.name for t in outreach_agent.tools]}")

resume = open("resumes/tony_stark.txt", "r").read()
print("\n>>> 把 Tony Stark 的简历发给 eval_agent")
response = client.agents.messages.create(
    agent_id=eval_agent.id,
    messages=[{"role": "user", "content": f"Evaluate: {resume}"}],
)
for message in response.messages:
    print_message(message)

print("\n>>> outreach_agent 侧发生了什么（收到了转发的候选人详情）：")
for message in client.agents.messages.list(agent_id=outreach_agent.id)[1:]:
    print_message(message)

# letta 0.6.50 的坑：跨 agent 投递路径不传 step_count，run_first 规则
# 不会生效；deepseek 又逐字服从来信包装语里的 "use send_message"，
# 所以起草不会发生在转发那一轮。直连消息则会强制先调 draft 工具。
print("\n>>> 直连 outreach_agent 触发强制起草（run_first 规则生效）：")
response = client.agents.messages.create(
    agent_id=outreach_agent.id,
    messages=[
        {
            "role": "user",
            "content": "Now draft the outreach email for the candidate you just received.",
        }
    ],
)
for message in response.messages:
    print_message(message)

# ---------------------------------------------------------------------------
# ③ round-robin group：不写编排逻辑，轮流处理同一条消息
# ---------------------------------------------------------------------------

banner("③ round-robin group —— SpongeBob 的简历")

# 重建两个普通 agent（都带默认 base tools，编排交给 group 而不是 tool_rules）
outreach_agent_v2 = client.agents.create(
    name="outreach_agent_v2",
    memory_blocks=[{"label": "persona", "value": outreach_persona}],
    llm_config=LLM_CONFIG,
    embedding_config=EMBEDDING_CONFIG,
    tool_ids=[draft_email_tool.id],
    block_ids=[company_block.id],
)
eval_agent_v2 = client.agents.create(
    name="eval_agent_v2",
    memory_blocks=[{"label": "persona", "value": eval_persona}],
    llm_config=LLM_CONFIG,
    embedding_config=EMBEDDING_CONFIG,
    tool_ids=[reject_tool.id],
    block_ids=[company_block.id],
)

round_robin_group = client.groups.create(
    description=GROUP_DESCRIPTION,
    agent_ids=[eval_agent_v2.id, outreach_agent_v2.id],
)
print(f"group id: {round_robin_group.id}（默认 round-robin：按顺序轮流发言）")

resume = open("resumes/spongebob_squarepants.txt", "r").read()
print("\n>>> 把 SpongeBob 的简历发给 group")
response = client.groups.messages.create(
    group_id=round_robin_group.id,
    messages=[{"role": "user", "content": f"Evaluate: {resume}"}],
)
for message in response.messages:
    print_message(message, with_name=True)

# ---------------------------------------------------------------------------
# ④ 共享记忆：改 outreach_agent_v2 的 company block，其他 agent 同步可见
# ---------------------------------------------------------------------------

banner('④ 共享记忆 —— 告诉 outreach_agent_v2 "The company has rebranded to Letta"')

response = client.agents.messages.create(
    agent_id=outreach_agent_v2.id,
    # 比课程原话多点名 company block：deepseek 有时会把改名写进 persona block
    messages=[
        {
            "role": "user",
            "content": "The company has rebranded to Letta. "
            "Update the company memory block to reflect this.",
        }
    ],
)
for message in response.messages:
    print_message(message)

print("\n共享 block 的传播（连 ①② 里的老 agent 也看到了新值）：")
for name, agent_id in [
    ("outreach_agent_v2", outreach_agent_v2.id),
    ("eval_agent_v2", eval_agent_v2.id),
    ("eval_agent (老)", eval_agent.id),
]:
    value = client.agents.blocks.retrieve(agent_id=agent_id, block_label="company").value
    print(f"  {name}: {value!r}")

print("\n✅ 演示完成：共享 block 是多 agent 的公共大脑；")
print("   编排既可以显式（跨 agent 工具 + tool_rules），也可以交给 group 轮转。")
