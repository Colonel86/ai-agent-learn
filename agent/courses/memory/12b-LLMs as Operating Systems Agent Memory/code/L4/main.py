"""12b·L4 编程定制 Agent 记忆 — 本地可运行演示。

课程主题：MemGPT 的记忆不是黑盒——memory block 是可编程的一等对象，
工具函数能拿到 agent_state 自省，甚至可以扔掉自带记忆工具、
用自定义系统提示 + 自定义工具实现完全另一套记忆管理（task queue）。

前提：先在另一个终端跑 ./run_server.sh（本地 embedding 服务 + Letta server）。

演示流程（python main.py）：
  ① memory blocks 解剖：blocks.list / 按 block_id 取 / 按 label 取 / prompt_template
  ② 工具访问 AgentState：get_agent_id 工具在运行时拿到自己的 agent id
  ③ 自定义 task queue 记忆：去掉全部自带记忆工具，换上自定义系统提示 +
     task_queue_push/pop 工具 —— 记忆管理策略完全由你编程
"""

import json
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
    "model": os.getenv("LETTA_MODEL", "deepseek-chat"),
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

# 可重复运行：先删本演示会创建的同名旧 agent
DEMO_AGENTS = {"blocks_agent", "state_tool_agent", "task_agent"}
for a in client.agents.list():
    if a.name in DEMO_AGENTS:
        client.agents.delete(agent_id=a.id)

# ---------------------------------------------------------------------------
# ① memory blocks 是一等对象：list / 按 id 取 / 按 label 取 / prompt template
# ---------------------------------------------------------------------------

banner("① memory blocks 解剖")

agent_state = client.agents.create(
    name="blocks_agent",
    memory_blocks=[
        {"label": "human", "value": "The human's name is Bob the Builder."},
        {"label": "persona", "value": "My name is Sam, the all-knowing sentient AI."},
    ],
    llm_config=LLM_CONFIG,
    embedding_config=EMBEDDING_CONFIG,
)
print(f"agent id: {agent_state.id}")

blocks = client.agents.blocks.list(agent_id=agent_state.id)
print("\nblocks.list —— 每个 block 都有独立 id，可脱离 agent 单独读写：")
for block in blocks:
    print(f"  [{block.label}] id={block.id} value={block.value!r}")

block_id = blocks[0].id
by_id = client.blocks.retrieve(block_id)
print(f"\n按 block_id 全局取（client.blocks.retrieve）: [{by_id.label}] {by_id.value!r}")

human_block = client.agents.blocks.retrieve(agent_id=agent_state.id, block_label="human")
print(f"按 label 在 agent 下取（client.agents.blocks.retrieve）: {human_block.value!r}")

prompt_template = client.agents.core_memory.retrieve(agent_id=agent_state.id).prompt_template
print(f"\ncore memory 的 prompt template（blocks 如何被编译进上下文）:\n  {prompt_template!r}")

# ---------------------------------------------------------------------------
# ② 工具访问 AgentState：工具函数签名带 agent_state 参数即可自省
# ---------------------------------------------------------------------------

banner("② 工具访问 AgentState —— get_agent_id")


def get_agent_id(agent_state: "AgentState"):
    """
    Query your agent ID field
    """
    return agent_state.id


get_id_tool = client.tools.upsert_from_function(func=get_agent_id)
print(f"已注册工具: {get_id_tool.name} (id={get_id_tool.id})")

state_tool_agent = client.agents.create(
    name="state_tool_agent",
    memory_blocks=[],
    llm_config=LLM_CONFIG,
    embedding_config=EMBEDDING_CONFIG,
    tool_ids=[get_id_tool.id],
)

print(f'\n>>> 问它: "What is your agent id?"（真实 id: {state_tool_agent.id}）')
response = client.agents.messages.create(
    agent_id=state_tool_agent.id,
    messages=[{"role": "user", "content": "What is your agent id?"}],
)
for message in response.messages:
    print_message(message)

# ---------------------------------------------------------------------------
# ③ 自定义 task queue 记忆：换系统提示 + 自定义工具，不用自带记忆工具
# ---------------------------------------------------------------------------

banner("③ 自定义 task queue 记忆管理")


def task_queue_push(agent_state: "AgentState", task_description: str):
    """
    Push to a task queue stored in core memory.

    Args:
        task_description (str): A description of the next task you must accomplish.

    Returns:
        Optional[str]: None is always returned as this function
        does not produce a response.
    """
    import json

    from letta_client import Letta

    client = Letta(base_url="http://localhost:8283")

    block = client.agents.blocks.retrieve(agent_id=agent_state.id, block_label="tasks")
    tasks = json.loads(block.value)
    tasks.append(task_description)

    client.agents.blocks.modify(
        agent_id=agent_state.id,
        block_label="tasks",
        value=json.dumps(tasks),
    )
    return None


def task_queue_pop(agent_state: "AgentState"):
    """
    Get the next task from the task queue

    Returns:
        Optional[str]: Remaining tasks in the queue
    """
    import json

    from letta_client import Letta

    client = Letta(base_url="http://localhost:8283")

    block = client.agents.blocks.retrieve(agent_id=agent_state.id, block_label="tasks")
    tasks = json.loads(block.value)
    if len(tasks) == 0:
        return None
    task = tasks[0]

    remaining_tasks = json.dumps(tasks[1:])
    client.agents.blocks.modify(
        agent_id=agent_state.id,
        block_label="tasks",
        value=remaining_tasks,
    )
    return f"Remaining tasks {remaining_tasks}"


task_queue_push_tool = client.tools.upsert_from_function(func=task_queue_push)
task_queue_pop_tool = client.tools.upsert_from_function(func=task_queue_pop)

task_agent = client.agents.create(
    name="task_agent",
    system=open("task_queue_system_prompt.txt", "r").read(),
    memory_blocks=[{"label": "tasks", "value": json.dumps([])}],
    llm_config=LLM_CONFIG,
    embedding_config=EMBEDDING_CONFIG,
    tool_ids=[task_queue_pop_tool.id, task_queue_push_tool.id],
    include_base_tools=False,
    tools=["send_message"],
)
print(f"task_agent 的全部工具（自带记忆工具已剔除）: {[t.name for t in task_agent.tools]}")
print(f"tasks block 初始值: {client.agents.blocks.retrieve(agent_id=task_agent.id, block_label='tasks').value}")

print("\n>>> 布置两个任务")
response = client.agents.messages.create(
    agent_id=task_agent.id,
    messages=[
        {
            "role": "user",
            "content": "Add 'start calling me Charles' and "
            "'tell me a haiku about my name' as two seperate tasks.",
        }
    ],
)
for message in response.messages:
    print_message(message)

print(f"\ntasks block 现值: {client.agents.blocks.retrieve(agent_id=task_agent.id, block_label='tasks').value}")

print('\n>>> "Complete your tasks" —— 观察它循环 pop 直到队列为空才 send_message')
response = client.agents.messages.create(
    agent_id=task_agent.id,
    messages=[{"role": "user", "content": "Complete your tasks"}],
)
for message in response.messages:
    print_message(message)

print(f"\ntasks block 最终值: {client.agents.blocks.retrieve(agent_id=task_agent.id, block_label='tasks').value}")

print("\n✅ 演示完成：memory block 可编程读写、工具能自省 agent_state、")
print("   记忆管理策略（这里是 task queue）完全可以自定义替换。")
