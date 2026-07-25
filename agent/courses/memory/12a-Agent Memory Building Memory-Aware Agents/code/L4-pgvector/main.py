"""12a·L4 Memory Operations：抽取、压实与自更新记忆 — pgvector 版本地演示（Oracle 版见 ../L4/main.py）。

课程主题：Compaction ≠ Summarization。摘要是有损压缩；压实是无损卸载——
原文进 DB，上下文里只留 [Summary ID] + 描述，需要时 expand_summary(id) 换回来。
精髓在第 4 步：summary_id 回填到源数据行，归档状态持久化在数据行本身（崩溃可恢复）。

与 Oracle 版的差异只在基础设施段（PG 连接 + 清场 + StoreManager 签名）和
⑤ 步验证 SQL 的占位符方言（:t → %(t)s）；①-④ 的演示逻辑逐字相同。

前提：pgvector 容器在跑（见 L2-pgvector/README.md）。

演示流程（python main.py）：
  ① 灌入 30 条研究对话（helper 自带样例）→ ② 监控 context 用量
  ③ summarize_conversation：LLM 摘要 → 存 SUMMARY_MEMORY → 回填 summary_id
  ④ expand_summary(id)：从摘要引用换回全部原文（无损验证）
  ⑤ SQL 层验证：未归档 0 条 / 已归档 30 条
"""

import os
import time

from dotenv import load_dotenv

load_dotenv()
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

from helper_pg import (
    SAMPLE_RESEARCH_CONVERSATION,
    MemoryManager,
    StoreManager,
    Toolbox,
    connect_to_postgres,
    create_conversational_history_table,
    create_tool_log_table,
    monitor_context_window,
    register_common_tools,
    summarize_conversation,
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

MODEL = os.getenv("MODEL", "deepseek-chat")
PG_DSN = os.getenv("PG_DSN", "postgresql://postgres:postgres@127.0.0.1:5433/postgres")
SQLALCHEMY_URL = PG_DSN.replace("postgresql://", "postgresql+psycopg://")


# ---- LLM client 适配器（helper 写死 gpt-5*，统一改写 + 关 thinking）----


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

# ---- 数据库与存储（clean slate，L4 notebook 用 EUCLIDEAN）----

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
# ① 灌 30 条研究对话
# ---------------------------------------------------------------------------

THREAD_ID = f"test_summary_{int(time.time())}"
print("\n" + "=" * 72)
print(f"① 写入 {len(SAMPLE_RESEARCH_CONVERSATION)} 条对话 → thread {THREAD_ID}")
print("=" * 72)
for role, content in SAMPLE_RESEARCH_CONVERSATION:
    memory_manager.write_conversational_memory(content, role, THREAD_ID)
    time.sleep(0.05)  # 保证时间戳可排序

# ---------------------------------------------------------------------------
# ② 压实前：监控 context 用量
# ---------------------------------------------------------------------------

before = memory_manager.read_conversational_memory(THREAD_ID, limit=100)
usage = monitor_context_window(before)
print("\n② 压实前 context 用量:")
print(f"   tokens={usage['tokens']:,} / {usage['max']:,}  ({usage['percent']}%, {usage['status']})")
print(f"   会话原文长度: {len(before):,} 字符")

# ---------------------------------------------------------------------------
# ③ 压实：摘要 → 入库 → 回填 summary_id
# ---------------------------------------------------------------------------

print("\n" + "=" * 72)
print("③ summarize_conversation（LLM 摘要 + summary_id 回填源数据行）")
print("=" * 72)
result = summarize_conversation(THREAD_ID, memory_manager, client)
print(f"   Summary ID: {result['id']}")
print(f"   描述: {result['description']}")
print("\n   摘要正文:")
print(result["summary"])

# ---------------------------------------------------------------------------
# ④ 展开：从摘要引用换回原文（Compaction 的"无损"验证）
# ---------------------------------------------------------------------------

print("\n" + "=" * 72)
print("④ expand_summary —— 按 Summary ID 取回被压实的原始对话")
print("=" * 72)
expand_fn = toolbox._tools_by_name["expand_summary"]
expanded = expand_fn(result["id"])
print(expanded[:1200] + ("\n...(截断展示)" if len(expanded) > 1200 else ""))

# ---------------------------------------------------------------------------
# ⑤ SQL 层验证归档状态
# ---------------------------------------------------------------------------

print("\n" + "=" * 72)
print("⑤ 验证：summary_id 已回填到源数据行")
print("=" * 72)
with memory_manager.conn.cursor() as cur:
    cur.execute(
        f"SELECT COUNT(*) FROM {memory_manager.conversation_table}"
        f" WHERE thread_id = %(t)s AND summary_id IS NULL", {"t": THREAD_ID})
    unsummarized = cur.fetchone()[0]
    cur.execute(
        f"SELECT COUNT(*) FROM {memory_manager.conversation_table}"
        f" WHERE thread_id = %(t)s AND summary_id IS NOT NULL", {"t": THREAD_ID})
    summarized = cur.fetchone()[0]
print(f"   未归档消息: {unsummarized} 条（应为 0）")
print(f"   已归档消息: {summarized} 条（应为 {len(SAMPLE_RESEARCH_CONVERSATION)}）")

after = memory_manager.read_conversational_memory(THREAD_ID, limit=100)
usage_after = monitor_context_window(after)
print(f"\n   压实后 conversation context: {usage_after['tokens']:,} tokens"
      f"（此前 {usage['tokens']:,}）—— 原文没有被删除，只是搬进了 SUMMARY_MEMORY")
print("\n✅ 演示完成：Summarization 丢信息，Compaction 搬信息。")
