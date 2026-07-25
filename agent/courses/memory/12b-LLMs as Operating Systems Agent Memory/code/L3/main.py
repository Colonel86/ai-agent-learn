"""12b·L3 用 Letta 构建记忆智能体 — 本地可运行演示。

课程主题：L1/L2 手搓的自编辑记忆，在 Letta（MemGPT 开源实现）里是开箱即用的
服务端能力——agent 状态全部持久化在 server 侧，客户端只发消息。

前提：先在另一个终端跑 ./run_server.sh（本地 embedding 服务 + Letta server）。

演示流程（python main.py）：
  ① 创建 agent：human/persona 两个 memory block + DeepSeek + 本地 embedding
  ② 发消息，观察 reasoning/tool/assistant 消息流与 token 用量
  ③ 解剖 agent state：系统提示、自带记忆工具、memory blocks
  ④ core memory 自编辑：告诉它"我其实叫 Sarah"→ 它自己调 core_memory_replace
  ⑤ archival memory：对话触发写入 + 显式插入 + 语义搜索作答
"""

import os

# 本机开着系统代理时，httpx 会把 localhost 请求也送进代理，必须绕过
os.environ.setdefault("NO_PROXY", "localhost,127.0.0.1")
os.environ.setdefault("no_proxy", "localhost,127.0.0.1")

from dotenv import load_dotenv

load_dotenv()

from letta_client import Letta

AGENT_NAME = "simple_agent"

# chat 走 Letta 的 openai 兼容路径指向 DeepSeek（原生 function calling，
# 不用 letta 0.6.50 里那条靠裸 JSON 解析的 deepseek 专用路径——很不稳）
LLM_CONFIG = {
    "model": os.getenv("LETTA_MODEL", "deepseek-v4-flash"),
    "model_endpoint_type": "openai",
    "model_endpoint": os.getenv("OPENAI_BASE_URL", "https://api.deepseek.com/v1"),
    "context_window": 64000,
    "put_inner_thoughts_in_kwargs": True,
}

# embedding 走本地 fastembed 服务（DeepSeek 没有 embeddings API）
EMBEDDING_CONFIG = {
    "embedding_model": "BAAI/bge-small-en-v1.5",
    "embedding_endpoint_type": "hugging-face",
    "embedding_endpoint": "http://localhost:8003/v1",
    "embedding_dim": 384,
    "embedding_chunk_size": 300,
}


def print_message(message):
    if message.message_type == "reasoning_message":
        print("🧠 Reasoning: " + message.reasoning)
    elif message.message_type == "assistant_message":
        print("🤖 Agent: " + message.content)
    elif message.message_type == "tool_call_message":
        print("🔧 Tool Call: " + message.tool_call.name + " " + message.tool_call.arguments)
    elif message.message_type == "tool_return_message":
        print("🔧 Tool Return: " + str(message.tool_return))
    elif message.message_type == "user_message":
        print("👤 User: " + message.content)


def banner(title):
    print("\n" + "=" * 72)
    print(title)
    print("=" * 72)


client = Letta(base_url="http://localhost:8283")

# ---------------------------------------------------------------------------
# ① 创建 agent（可重复运行：先删同名旧 agent）
# ---------------------------------------------------------------------------

banner("① 创建 agent —— memory blocks: human + persona")

for a in client.agents.list():
    if a.name == AGENT_NAME:
        client.agents.delete(agent_id=a.id)

agent_state = client.agents.create(
    name=AGENT_NAME,
    memory_blocks=[
        {"label": "human", "value": "My name is Charles", "limit": 10000},
        {"label": "persona", "value": "You are a helpful assistant and you always use emojis"},
    ],
    llm_config=LLM_CONFIG,
    embedding_config=EMBEDDING_CONFIG,
)
print(f"agent id: {agent_state.id}")
print(f"model: {agent_state.llm_config.model} @ {agent_state.llm_config.model_endpoint}")
print(f"embedding: {agent_state.embedding_config.embedding_model} (dim {agent_state.embedding_config.embedding_dim})")

# ---------------------------------------------------------------------------
# ② 发消息：reasoning / assistant 消息流 + 用量
# ---------------------------------------------------------------------------

banner('② 发消息："hows it going????"')

response = client.agents.messages.create(
    agent_id=agent_state.id,
    messages=[{"role": "user", "content": "hows it going????"}],
)
for message in response.messages:
    print_message(message)
print(f"\nusage: prompt={response.usage.prompt_tokens}, completion={response.usage.completion_tokens}, steps={response.usage.step_count}")

# ---------------------------------------------------------------------------
# ③ 解剖 agent state：系统提示 / 自带工具 / memory blocks
# ---------------------------------------------------------------------------

banner("③ agent state 解剖")

print("系统提示（前 600 字符）:")
print(agent_state.system[:600] + " ...")
print(f"\n自带工具: {[t.name for t in agent_state.tools]}")
print("\nmemory blocks:")
for block in agent_state.memory.blocks:
    print(f"  [{block.label}] {block.value!r} (limit {block.limit})")

# ---------------------------------------------------------------------------
# ④ core memory 自编辑：纠正名字
# ---------------------------------------------------------------------------

banner('④ core memory 自编辑 —— "my name is actually Sarah"')

response = client.agents.messages.create(
    agent_id=agent_state.id,
    messages=[{"role": "user", "content": "my name is actually Sarah"}],
)
for message in response.messages:
    print_message(message)

human_value = client.agents.blocks.retrieve(
    agent_id=agent_state.id, block_label="human"
).value
print(f"\n更新后的 human block: {human_value!r}")

# ---------------------------------------------------------------------------
# ⑤ archival memory：对话触发写入 + 显式插入 + 语义搜索
# ---------------------------------------------------------------------------

banner("⑤ archival memory —— 写入与语义搜索")

print(">>> 对话触发写入: \"Save the information that 'bob loves cats' to archival\"")
response = client.agents.messages.create(
    agent_id=agent_state.id,
    messages=[{"role": "user", "content": "Save the information that 'bob loves cats' to archival"}],
)
for message in response.messages:
    print_message(message)

print("\n>>> 显式插入 passage: \"Bob loves boston terriers\"")
client.agents.passages.create(agent_id=agent_state.id, text="Bob loves boston terriers")

passages = client.agents.passages.list(agent_id=agent_state.id)
print(f"\narchival 现有 {len(passages)} 条 passage:")
for p in passages:
    print(f"  - {p.text}")

print("\n>>> 语义搜索作答: \"What animals does Bob like? Search archival.\"")
response = client.agents.messages.create(
    agent_id=agent_state.id,
    messages=[{"role": "user", "content": "What animals does Bob like? Search archival."}],
)
for message in response.messages:
    print_message(message)

print("\n✅ 演示完成：记忆状态都在 server 侧 —— 重跑 main.py 之外，")
print("   也可以再开一个 python 会话直接取 agent 继续聊，记忆仍在。")
