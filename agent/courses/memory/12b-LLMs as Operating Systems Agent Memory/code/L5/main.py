"""12b·L5 Agentic RAG 与外部记忆 — 本地可运行演示。

课程主题：agent 的记忆不止 server 里那点 blocks——
① Data Source：把整份 PDF 上传、切块、嵌入，挂到 agent 的 archival memory，
   agent 用 archival_memory_search 自主检索（Agentic RAG：检索时机由 agent 决定，
   而不是传统 RAG 那样每轮硬塞 top-k）；
② 自定义工具连接外部数据库：检索逻辑完全绕开 Letta 存储，工具直查外部系统。

前提：先在另一个终端跑 ./run_server.sh（本地 embedding 服务 + Letta server）。

演示流程（python main.py）：
  ① 创建 folder（0.6 时代叫 source）→ 上传 handbook.pdf → 轮询解析/嵌入状态
  ② 挂 folder 到 agent → file block 进上下文 + 自动挂文件工具 →
     agent 用 semantic_search_files 检索回答“公司休假政策”
  ③ query_birthday_db 自定义工具 → agent 查外部“数据库”答生日
"""

import inspect
import os
import time

# 本机开着系统代理时，httpx 会把 localhost 请求也送进代理，必须绕过
os.environ.setdefault("NO_PROXY", "localhost,127.0.0.1")
os.environ.setdefault("no_proxy", "localhost,127.0.0.1")

from dotenv import load_dotenv

# .env 在 code/ 根目录（全课程共享）
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env"))

from letta_client import Letta

# letta 0.16 默认建 letta_v1_agent，不带课程要讲的 MemGPT 记忆工具循环，
# 必须显式选经典 memgpt_agent
AGENT_TYPE = "memgpt_agent"

# chat 走 openai 兼容路径指向本地网关（gateway.py :8003），由网关转发 DeepSeek
# 并注入 thinking=disabled：letta 对 memgpt agent 固定发 tool_choice=required，
# DeepSeek v4 的 thinking 模式不支持（400），关 thinking 后合法
LLM_CONFIG = {
    "model": os.getenv("LETTA_MODEL", "deepseek-v4-flash"),
    "model_endpoint_type": "openai",
    "model_endpoint": "http://localhost:8003/v1",
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

# 可重复运行：先删同名旧 agent 和旧 folder（sources 在 letta 0.16 里改叫 folders）
for a in client.agents.list():
    if a.name in {"rag_agent", "birthday_agent"}:
        client.agents.delete(agent_id=a.id)
for f in client.folders.list():
    if f.name == SOURCE_NAME:
        client.folders.delete(folder_id=f.id)

# ---------------------------------------------------------------------------
# ① Data folder：上传 PDF → 解析/切块/嵌入 → 轮询处理状态
# ---------------------------------------------------------------------------

banner("① 创建 data folder 并上传 handbook.pdf")

folder = client.folders.create(
    name=SOURCE_NAME,
    embedding_config=EMBEDDING_CONFIG,
)
print(f"folder id: {folder.id}")
print(f"embedding: {folder.embedding_config.embedding_model} (dim {folder.embedding_config.embedding_dim})")

# 0.6 时代上传返回 job、用 jobs.retrieve 轮询；0.16 直接轮询文件的 processing_status
uploaded = client.folders.files.upload(
    folder_id=folder.id,
    file=open("handbook.pdf", "rb"),
)
print(f"\n上传后立即返回: {uploaded.processing_status}")

file_meta = uploaded
while file_meta.processing_status != "completed":
    file_meta = client.folders.files.retrieve(file_meta.id, folder_id=folder.id)
    print(f"  processing_status: {file_meta.processing_status}")
    time.sleep(1)

print(f"\n解析/嵌入完成: {file_meta.total_chunks} chunks（已嵌入 {file_meta.chunks_embedded}）")

# ---------------------------------------------------------------------------
# ② 挂 source 到 agent：archival memory + agent 自主检索（Agentic RAG）
# ---------------------------------------------------------------------------

banner("② 挂载 folder → Agentic RAG 检索休假政策")

agent_state = client.agents.create(
    name="rag_agent",
    agent_type=AGENT_TYPE,
    memory_blocks=[
        {"label": "human", "value": "My name is Sarah"},
        {"label": "persona", "value": "You are a helpful assistant"},
    ],
    llm_config=LLM_CONFIG,
    embedding_config=EMBEDDING_CONFIG,
)

client.agents.folders.attach(agent_id=agent_state.id, folder_id=folder.id)

attached = list(client.agents.folders.list(agent_id=agent_state.id))
print(f"agent 已挂载 folders: {[f.name for f in attached]}")

# 与课程（letta 0.6：source 切块灌进 agent 的 archival passages，用
# archival_memory_search 检索）的关键差异：0.16 里 folder 附件不再进
# archival，而是走「文件」新通道——文件以 file block 出现在 agent 上下文，
# 同时自动挂上 open_files/grep_files/semantic_search_files 三个文件工具，
# semantic_search_files 用的就是 ① 里生成的那批 embedding
ag = client.agents.retrieve(agent_id=agent_state.id, include_relationships=["tools", "memory"])
print(f"挂载后自动出现的文件工具: {sorted(t.name for t in ag.tools if 'file' in t.name)}")
print(f"上下文里的 file blocks: {[b.label for b in ag.memory.file_blocks]}")

# 比课程原话多点名工具：deepseek 会先 open_files 且猜错文件名后就放弃，
# 点名 semantic_search_files 才稳定走语义检索
print('\n>>> "Use semantic_search_files to find our company\'s vacation policies"')
response = client.agents.messages.create(
    agent_id=agent_state.id,
    messages=[
        {
            "role": "user",
            "content": "Use the semantic_search_files tool to find our company's "
            "vacation policies in the employee handbook, then summarize them.",
        }
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


# letta-client 1.x 移除了 upsert_from_function，改为直接上传函数源码
birthday_tool = client.tools.upsert(source_code=inspect.getsource(query_birthday_db))
print(f"已注册工具: {birthday_tool.name} (id={birthday_tool.id})")

birthday_agent = client.agents.create(
    name="birthday_agent",
    agent_type=AGENT_TYPE,
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

print("\n✅ 演示完成：外部文档可以整份灌给 agent（folder→attach→文件工具检索），")
print("   也可以完全绕开 Letta 存储、用自定义工具直连外部系统 —— 两种外部记忆接法。")
