"""12a·L5 Memory-Aware Agent — pgvector 版本地演示（Oracle 版见 ../L5/main.py）。

课程主题：把 L2-L4 攒的全部基础设施接成一个完整 agent loop：
  循环外·前（确定性）：五段记忆装配 context + >80% 自动压实 + 语义检索 top-5 工具
  循环内（agent 触发）：LLM 决定调哪个工具；工具全量输出落 TOOL_LOG，只回传截断结果
  循环外·后（确定性）：write_workflow / write_entity / 会话写回 —— 收尾必写

与 Oracle 版的差异只在基础设施段（PG 连接 + 清场 + StoreManager 签名）；
AGENT_SYSTEM_PROMPT、agent loop、5 问序列逐字相同。

前提：pgvector 容器在跑（见 L2-pgvector/README.md）；会联网访问 arxiv.org 拉论文。

演示（python main.py）：同一 thread 连续 5 问 ——
  找 MemGPT 论文 → 存全文 → 问要点（吃 KB 记忆）→ 用工具压实会话 → "我第一个问题是什么"（吃摘要记忆）
"""

import json as json_lib
import os

from dotenv import load_dotenv

load_dotenv()
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

from helper_pg import (
    MemoryManager,
    StoreManager,
    Toolbox,
    calculate_context_usage,
    connect_to_postgres,
    create_conversational_history_table,
    create_tool_log_table,
    offload_to_summary,
    register_common_tools,
    suppress_warnings,
)

suppress_warnings()

from langchain_community.embeddings import FastEmbedEmbeddings
from openai import OpenAI

# arxiv 2.x 起移除了 Search.results()，但 langchain_community 仍在调用；
# 旧版 arxiv 1.4.8 又因 arxiv.org 强制 HTTPS 而 301 全挂 → 用新版 + 兼容 shim
import arxiv as _arxiv

if not hasattr(_arxiv.Search, "results"):
    _arxiv_client = _arxiv.Client(page_size=20, delay_seconds=3.0, num_retries=3)
    _arxiv.Search.results = lambda self, offset=0: _arxiv_client.results(
        self, offset=offset
    )

MODEL = os.getenv("MODEL", "deepseek-v4-flash")
PG_DSN = os.getenv("PG_DSN", "postgresql://postgres:postgres@127.0.0.1:5433/postgres")
SQLALCHEMY_URL = PG_DSN.replace("postgresql://", "postgresql+psycopg://")
SHOW_CONTEXT_CHARS = 1500  # 每轮打印的 context 预览长度


# ---- LLM client 适配器（helper/notebook 写死 gpt-5*，统一改写 + 关 thinking）----


class _CompletionsProxy:
    def __init__(self, real, model):
        self._real, self._model = real, model

    def create(self, **kwargs):
        kwargs["model"] = self._model
        kwargs.setdefault("extra_body", {}).setdefault(
            "thinking", {"type": "disabled"}
        )
        return self._real.chat.completions.create(**kwargs)


class _ChatProxy:
    def __init__(self, real, model):
        self.completions = _CompletionsProxy(real, model)


class ModelRewriteClient:
    def __init__(self, model):
        self._real = OpenAI()
        self.chat = _ChatProxy(self._real, model)


client = ModelRewriteClient(MODEL)

# ---- 数据库与存储（clean slate，L5 notebook 用 EUCLIDEAN）----

try:
    database_connection = connect_to_postgres(PG_DSN)
except Exception as e:
    raise SystemExit(f"PostgreSQL 未就绪（{type(e).__name__}），先启动容器（见 L2-pgvector/README.md）")

embedding_model = FastEmbedEmbeddings(model_name="BAAI/bge-small-en-v1.5")

TABLES = {
    "conversational": "CONVERSATIONAL_MEMORY",
    "knowledge_base": "SEMANTIC_MEMORY",
    "workflow": "WORKFLOW_MEMORY",
    "toolbox": "TOOLBOX_MEMORY",
    "entity": "ENTITY_MEMORY",
    "summary": "SUMMARY_MEMORY",
    "tool_log": "TOOL_LOG_MEMORY",
}

with database_connection.cursor() as cur:
    cur.execute("DROP TABLE IF EXISTS langchain_pg_embedding, langchain_pg_collection CASCADE")
    cur.execute(f"DROP TABLE IF EXISTS {TABLES['tool_log']}")
database_connection.commit()

conversation_history_table = create_conversational_history_table(
    database_connection, TABLES["conversational"]
)
tool_log_history_table = create_tool_log_table(database_connection, TABLES["tool_log"])

store_manager = StoreManager(
    sqlalchemy_url=SQLALCHEMY_URL,
    embedding_function=embedding_model,
    embedding_length=384,
    table_names={k: v for k, v in TABLES.items() if k not in ("conversational", "tool_log")},
    conversational_table=conversation_history_table,
    tool_log_table=tool_log_history_table,
    distance="euclidean",
)

memory_manager = MemoryManager(
    conn=database_connection,
    conversation_table=store_manager.get_conversational_table(),
    knowledge_base_vs=store_manager.get_knowledge_base_store(),
    workflow_vs=store_manager.get_workflow_store(),
    toolbox_vs=store_manager.get_toolbox_store(),
    entity_vs=store_manager.get_entity_store(),
    summary_vs=store_manager.get_summary_store(),
    tool_log_table=tool_log_history_table,
)

toolbox = Toolbox(memory_manager, client, embedding_model)
common_tools = register_common_tools(toolbox, memory_manager, TABLES["knowledge_base"])

# ---------------------------------------------------------------------------
# Agent（system prompt 与 agent loop 均为课程 notebook 原文）
# ---------------------------------------------------------------------------

AGENT_SYSTEM_PROMPT = """
# Role
You are a memory-aware agentic research assistant with access to tools.

# Context Window Structure (Partitioned Segments)
The user input is a partitioned context window. It contains a `# Question` section followed by memory segments.
Treat each segment as a distinct memory store with a specific purpose:
- `## Conversation Memory`
- `## Knowledge Base Memory`
- `## Workflow Memory`
- `## Entity Memory`
- `## Summary Memory`

# Memory Store Semantics
- Conversation Memory: Recent thread-level dialogue and instructions. Use it for continuity, user preferences, and unresolved requests.
- Knowledge Base Memory: Retrieved documents/passages. Use it to ground factual and technical claims.
- Workflow Memory: Prior execution patterns and step sequences. Use it to plan tool usage; adapt patterns, do not copy blindly.
- Entity Memory: Named people/orgs/systems and descriptors. Use it to disambiguate references and keep naming consistent.
- Summary Memory: Compressed older context represented by summary IDs. When thread-scoped summaries exist, prefer summaries for the active thread_id.

# Summary Expansion Policy
If critical detail is only present in Summary Memory or appears ambiguous, call `expand_summary(summary_id)` before relying on it.

# Operating Rules
1. Start with the provided memory segments before using tools.
2. If segments conflict, prioritize: current `# Question` > latest Conversation Memory > Knowledge Base evidence > older summaries/workflows.
3. Use only the tools provided in this turn and choose the minimum necessary tool calls.
4. If memory is insufficient, state what is missing and then use an appropriate tool.
5. For conversation compaction, use `summarize_and_store` with `thread_id` so source conversation units are marked as summarized.
"""


def execute_tool(tool_name: str, tool_args: dict, current_thread_id: str | None = None) -> str:
    """Execute a tool by looking it up in the toolbox."""
    if tool_name not in toolbox._tools_by_name:
        return f"Error: Tool '{tool_name}' not found"
    args = dict(tool_args or {})
    if tool_name == "summarize_and_store" and "thread_id" not in args and current_thread_id is not None:
        args["thread_id"] = str(current_thread_id)
    return str(toolbox._tools_by_name[tool_name](**args) or "Done")


def call_openai_chat(messages: list, tools: list = None):
    kwargs = {"model": MODEL, "messages": messages}
    if tools:
        kwargs["tools"] = tools
        kwargs["tool_choice"] = "auto"
    return client.chat.completions.create(**kwargs)


def call_agent(query: str, thread_id: str = "1", max_iterations: int = 10) -> str:
    """Agent loop with context window monitoring and summarization."""
    thread_id = str(thread_id)
    steps = []
    summaries = []

    # 1. 确定性装配：五段记忆
    print("\n" + "=" * 50)
    print("🧠 BUILDING CONTEXT...")
    memory_context = ""
    memory_context += memory_manager.read_conversational_memory(thread_id) + "\n\n"
    memory_context += memory_manager.read_knowledge_base(query) + "\n\n"
    memory_context += memory_manager.read_workflow(query) + "\n\n"
    memory_context += memory_manager.read_entity(query) + "\n\n"
    memory_context += memory_manager.read_summary_context(query, thread_id=thread_id) + "\n\n"

    # 2. 确定性压实：>80% 触发
    usage = calculate_context_usage(memory_context)
    print(f"📊 Context: {usage['percent']}% ({usage['tokens']}/{usage['max']} tokens)")
    if usage["percent"] > 80:
        print("⚠️ Context >80% - offloading conversation context to summary memory...")
        memory_context, summaries = offload_to_summary(
            memory_context, memory_manager, client, thread_id=thread_id
        )
        if summaries:
            print(f"🧾 Created {len(summaries)} summary reference(s)")
        usage = calculate_context_usage(memory_context)
        print(f"📊 After offload: {usage['percent']}%")

    context = f"# Question\n{query}\n\n{memory_context}"
    print(f"==== CONTEXT WINDOW (前 {SHOW_CONTEXT_CHARS} 字符) ====")
    print(context[:SHOW_CONTEXT_CHARS] + ("\n...(截断)" if len(context) > SHOW_CONTEXT_CHARS else ""))

    # 3. 确定性检索工具 top-5
    dynamic_tools = memory_manager.read_toolbox(query, k=5)
    print(f"🔧 Tools: {[t['function']['name'] for t in dynamic_tools]}")

    # 4. 收前写入（确定性）
    memory_manager.write_conversational_memory(query, "user", thread_id)
    try:
        memory_manager.write_entity("", "", "", llm_client=client, text=query)
    except Exception:
        pass

    # 5. Agent loop（工具调用由 LLM 决定）
    messages = [
        {"role": "system", "content": AGENT_SYSTEM_PROMPT},
        {"role": "user", "content": context},
    ]
    final_answer = ""
    print("\n🤖 AGENT LOOP")
    for iteration in range(max_iterations):
        print(f"\n--- Iteration {iteration + 1} ---")
        response = call_openai_chat(messages, tools=dynamic_tools)
        msg = response.choices[0].message

        if msg.tool_calls:
            messages.append({
                "role": "assistant", "content": msg.content or "",
                "tool_calls": [
                    {"id": tc.id, "type": "function",
                     "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                    for tc in msg.tool_calls
                ],
            })
            for tc in msg.tool_calls:
                tool_name = tc.function.name
                tool_args = json_lib.loads(tc.function.arguments)
                args_display = {
                    k: (v[:50] + "..." if isinstance(v, str) and len(v) > 50 else v)
                    for k, v in tool_args.items()
                }
                print(f"🛠️ {tool_name}({args_display})")
                try:
                    result = execute_tool(tool_name, tool_args, current_thread_id=thread_id)
                    status, error_message = "success", None
                    steps.append(f"{tool_name}({args_display}) → success")
                except Exception as e:
                    result = f"Error: {e}"
                    status, error_message = "failed", str(e)
                    steps.append(f"{tool_name}({args_display}) → failed")

                # 全量输出落 TOOL_LOG_MEMORY，LLM 只拿截断版（上下文控制）
                log_id = memory_manager.write_tool_log(
                    thread_id=thread_id, tool_call_id=tc.id, tool_name=tool_name,
                    tool_args=tool_args, result=result, status=status,
                    error_message=error_message, metadata={"iteration": iteration + 1},
                )
                if len(result) > 3000:
                    result_for_llm = (
                        result[:3000]
                        + f"\n\n[Truncated for context. Full output saved in TOOL_LOG_MEMORY as log_id: {log_id}]"
                    )
                else:
                    result_for_llm = result
                print(f"   → {result_for_llm[:200]}{'...' if len(result_for_llm) > 200 else ''}")
                messages.append({"role": "tool", "tool_call_id": tc.id, "content": result_for_llm})
        else:
            final_answer = msg.content or ""
            print(f"\n✅ DONE ({len(steps)} tool calls)")
            break
    else:
        print(f"\n⚠️ WARNING: Max iterations ({max_iterations}) reached")
        final_answer = "I was unable to complete the request within the allowed iterations."

    # 6. 收尾必写（确定性）：workflow + entity + 会话
    if steps:
        memory_manager.write_workflow(query, steps, final_answer)
    try:
        memory_manager.write_entity("", "", "", llm_client=client, text=final_answer)
    except Exception:
        pass
    memory_manager.write_conversational_memory(final_answer, "assistant", thread_id)

    print("\n" + "=" * 50 + f"\n💬 ANSWER:\n{final_answer}\n" + "=" * 50)
    return final_answer


# ---------------------------------------------------------------------------
# 演示：同一 thread 连续 5 问（课程原 query 序列）
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    THREAD = "50000"
    for i, q in enumerate([
        "Can you get me the paper MemGPT",
        "Can you save the content of the paper",
        "What are the main key takeaways from the paper",
        "Summarize the conversation so far using your tool",
        "What was my first question?",
    ], 1):
        print("\n" + "#" * 72)
        print(f"# 第 {i} 问: {q}")
        print("#" * 72)
        call_agent(q, thread_id=THREAD)
