"""12b·L5 Agentic RAG 与外部记忆 — 本地可运行演示。

课程主题：agent 的记忆不止 server 里那点 blocks——
① Data Source：把整份 PDF 上传、切块、嵌入，挂到 agent 的 archival memory，
   agent 用 archival_memory_search 自主检索（Agentic RAG：检索时机由 agent 决定，
   而不是传统 RAG 那样每轮硬塞 top-k）；
② 自定义工具连接外部数据库：检索逻辑完全绕开 Letta 存储，工具直查外部系统。

前提：先在另一个终端跑 ./run_server.sh（本地 embedding 服务 + Letta server）。

演示流程（python main.py）：
  ① 创建 source → 上传 handbook.pdf → 轮询解析/嵌入 job → 看切出的 passages
  ② 挂 source 到 agent → agent 检索 archival 回答“公司休假政策”
  ③ query_birthday_db 自定义工具 → agent 查外部“数据库”答生日
"""

import os
import time

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
}

# embedding 走本地 fastembed 服务（DeepSeek 没有 embeddings API）
# source 的 embedding_config 必须与要挂载的 agent 完全一致，否则 attach 会被拒
EMBEDDING_CONFIG = {
    "embedding_model": "BAAI/bge-small-en-v1.5",
    "embedding_endpoint_type": "hugging-face",
    "embedding_endpoint": "http://localhost:8003/v1",
    "embedding_dim": 384,
    "embedding_chunk_size": 300,
}

SOURCE_NAME = "employee_handbook"


def print_message(message):
    if message.message_type == "reasoning_message":
        print("🧠 Reasoning: " + message.reasoning)
    elif message.message_type == "assistant_message":
        print("🤖 Agent: " + message.content)
    elif message.message_type == "tool_call_message":
        print("🔧 Tool Call: " + message.tool_call.name + " " + message.tool_call.arguments)
    elif message.message_type == "tool_return_message":
        print("🔧 Tool Return: " + str(message.tool_return)[:300])
    elif message.message_type == "user_message":
        print("👤 User: " + message.content)


def banner(title):
    print("\n" + "=" * 72)
    print(title)
    print("=" * 72)


client = Letta(base_url="http://localhost:8283")

# 可重复运行：先删同名旧 agent 和旧 source
for a in client.agents.list():
    if a.name in {"rag_agent", "birthday_agent"}:
        client.agents.delete(agent_id=a.id)
for s in client.sources.list():
    if s.name == SOURCE_NAME:
        client.sources.delete(source_id=s.id)

# ---------------------------------------------------------------------------
# ① Data Source：上传 PDF → 解析/切块/嵌入 job → passages
# ---------------------------------------------------------------------------

banner("① 创建 data source 并上传 handbook.pdf")

source = client.sources.create(
    name=SOURCE_NAME,
    embedding_config=EMBEDDING_CONFIG,
)
print(f"source id: {source.id}")
print(f"embedding: {source.embedding_config.embedding_model} (dim {source.embedding_config.embedding_dim})")

job = client.sources.files.upload(
    source_id=source.id,
    file=open("handbook.pdf", "rb"),
)
print(f"\n上传后立即返回 job: {job.status}")

while job.status != "completed":
    job = client.jobs.retrieve(job_id=job.id)
    print(f"  job status: {job.status}")
    time.sleep(1)

print(f"\njob metadata（解析出多少 passage）: {job.metadata}")

passages = client.sources.passages.list(source_id=source.id)
print(f"\nsource 切出 {len(passages)} 个 passage，第一个片段：")
print("  " + passages[0].text[:160].replace("\n", " ") + " ...")

# ---------------------------------------------------------------------------
# ② 挂 source 到 agent：archival memory + agent 自主检索（Agentic RAG）
# ---------------------------------------------------------------------------

banner("② 挂载 source → Agentic RAG 检索休假政策")

agent_state = client.agents.create(
    name="rag_agent",
    memory_blocks=[
        {"label": "human", "value": "My name is Sarah"},
        {"label": "persona", "value": "You are a helpful assistant"},
    ],
    llm_config=LLM_CONFIG,
    embedding_config=EMBEDDING_CONFIG,
)

client.agents.sources.attach(agent_id=agent_state.id, source_id=source.id)

attached = client.agents.sources.list(agent_id=agent_state.id)
print(f"agent 已挂载 sources: {[s.name for s in attached]}")

agent_passages = client.agents.passages.list(agent_id=agent_state.id)
print(f"agent 的 archival memory 现在有 {len(agent_passages)} 个 passage（即 source 的全部切块）")

print('\n>>> "Search archival for our company\'s vacation policies"')
response = client.agents.messages.create(
    agent_id=agent_state.id,
    messages=[
        {"role": "user", "content": "Search archival for our company's vacation policies"}
    ],
)
for message in response.messages:
    print_message(message)

# ---------------------------------------------------------------------------
# ③ 自定义工具连接外部数据：birthday_db
# ---------------------------------------------------------------------------

banner("③ 自定义工具连接外部数据库 —— query_birthday_db")


def query_birthday_db(name: str):
    """
    This tool queries an external database to
    lookup the birthday of someone given their name.

    Args:
        name (str): The name to look up

    Returns:
        birthday (str): The birthday in mm-dd-yyyy format

    """
    my_fake_data = {
        "bob": "03-06-1997",
        "sarah": "07-06-1993",
    }
    name = name.lower()
    if name not in my_fake_data:
        return None
    else:
        return my_fake_data[name]


birthday_tool = client.tools.upsert_from_function(func=query_birthday_db)
print(f"已注册工具: {birthday_tool.name} (id={birthday_tool.id})")

birthday_agent = client.agents.create(
    name="birthday_agent",
    memory_blocks=[
        {"label": "human", "value": "My name is Sarah"},
        {
            "label": "persona",
            "value": "You are a agent with access to a birthday_db "
            "that you use to lookup information about users' birthdays.",
        },
    ],
    llm_config=LLM_CONFIG,
    embedding_config=EMBEDDING_CONFIG,
    tool_ids=[birthday_tool.id],
    # 真实场景下外部库的密钥这样注入工具沙箱：
    # tool_exec_environment_variables={"DB_KEY": "my_key"},
)

print('\n>>> "whens my bday????"（human block 里只有名字，生日在外部库）')
response = client.agents.messages.create(
    agent_id=birthday_agent.id,
    messages=[{"role": "user", "content": "whens my bday????"}],
)
for message in response.messages:
    print_message(message)

print("\n✅ 演示完成：archival memory 可以由文档批量灌入（source→attach），")
print("   也可以完全绕开 Letta 存储、用自定义工具直连外部系统 —— 两种外部记忆接法。")
