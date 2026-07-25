"""12a·L2 Memory Manager — 本地可运行演示。

课程主题：不同记忆类型需要不同的数据模型与检索策略，由统一的 MemoryManager 编排。
  - Conversational（会话）→ SQL 表，按 thread_id 精确取（不是相似度！）
  - Knowledge Base / Workflow / Toolbox / Entity / Summary → 5 个向量表，语义检索
  - 全部落在 Oracle 26ai/23ai 的同一个库里（SQL 表 + VECTOR 列 + IVF 索引）

本地化前提（见 README）：
  docker run -d --name oracle-memory-lab -p 1521:1521 \
      -e ORACLE_PASSWORD=YourPassword123 gvenzl/oracle-free:23-slim-faststart

演示流程（python main.py）：
  ① 管理员建 VECTOR 用户 → ② 建 7 张记忆表 + 5 个 IVF 向量索引
  ③ MemoryManager 灌 arXiv 论文进 knowledge base（HF 拉不到就用内置样例）
  ④ 语义检索 knowledge base；⑤ 会话记忆写入/按 thread_id 读回 —— 对比两种检索路径
"""

import os

from dotenv import load_dotenv

load_dotenv()
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

from helper import (
    MemoryManager,
    StoreManager,
    connect_to_oracle,
    create_conversational_history_table,
    create_tool_log_table,
    safe_create_index,
    setup_oracle_database,
    suppress_warnings,
)

suppress_warnings()

from langchain_community.embeddings import FastEmbedEmbeddings
from langchain_community.vectorstores.utils import DistanceStrategy

# ---------------------------------------------------------------------------
# ① 数据库：管理员一次性建 VECTOR 用户，然后以 VECTOR 连接
# ---------------------------------------------------------------------------

DSN = os.getenv("ORACLE_DSN", "127.0.0.1:1521/FREEPDB1")

if not setup_oracle_database(dsn=DSN):
    raise SystemExit(
        "Oracle 未就绪。先启动容器并等它初始化完成（docker logs -f oracle-memory-lab，"
        "看到 DATABASE IS READY TO USE! 再跑）"
    )

database_connection = connect_to_oracle(
    user="VECTOR",
    password="VectorPwd_2025",
    dsn=DSN,
    program="local.memory_lab.L2",
)
print("Using user:", database_connection.username)

# ---------------------------------------------------------------------------
# ② 七张记忆表 + 向量索引
# ---------------------------------------------------------------------------

# 课程用 HuggingFaceEmbeddings(paraphrase-mpnet-base-v2, 768 维, torch)；
# 本地化用 fastembed(bge-small-en-v1.5, 384 维, ONNX 纯 CPU)，接口一致
embedding_model = FastEmbedEmbeddings(model_name="BAAI/bge-small-en-v1.5")

CONVERSATIONAL_TABLE = "CONVERSATIONAL_MEMORY"  # Episodic
KNOWLEDGE_BASE_TABLE = "SEMANTIC_MEMORY"        # Semantic
WORKFLOW_TABLE = "WORKFLOW_MEMORY"              # Procedural
TOOLBOX_TABLE = "TOOLBOX_MEMORY"                # Procedural
ENTITY_TABLE = "ENTITY_MEMORY"                  # Semantic
SUMMARY_TABLE = "SUMMARY_MEMORY"                # Semantic
TOOL_LOG_TABLE = "TOOL_LOG_MEMORY"

conversation_history_table = create_conversational_history_table(
    database_connection, CONVERSATIONAL_TABLE
)
tool_log_history_table = create_tool_log_table(database_connection, TOOL_LOG_TABLE)

store_manager = StoreManager(
    client=database_connection,
    embedding_function=embedding_model,
    table_names={
        "knowledge_base": KNOWLEDGE_BASE_TABLE,
        "workflow": WORKFLOW_TABLE,
        "toolbox": TOOLBOX_TABLE,
        "entity": ENTITY_TABLE,
        "summary": SUMMARY_TABLE,
    },
    distance_strategy=DistanceStrategy.COSINE,
    conversational_table=conversation_history_table,
    tool_log_table=tool_log_history_table,
)

knowledge_base_vs = store_manager.get_knowledge_base_store()
workflow_vs = store_manager.get_workflow_store()
toolbox_vs = store_manager.get_toolbox_store()
entity_vs = store_manager.get_entity_store()
summary_vs = store_manager.get_summary_store()

print("\nCreating vector indexes...")
safe_create_index(database_connection, knowledge_base_vs, "knowledge_base_vs_ivf")
safe_create_index(database_connection, workflow_vs, "workflow_vs_ivf")
safe_create_index(database_connection, toolbox_vs, "toolbox_vs_ivf")
safe_create_index(database_connection, entity_vs, "entity_vs_ivf")
safe_create_index(database_connection, summary_vs, "summary_vs_ivf")

memory_manager = MemoryManager(
    conn=database_connection,
    conversation_table=conversation_history_table,
    knowledge_base_vs=knowledge_base_vs,
    workflow_vs=workflow_vs,
    toolbox_vs=toolbox_vs,
    entity_vs=entity_vs,
    summary_vs=summary_vs,
    tool_log_table=tool_log_history_table,
)

# ---------------------------------------------------------------------------
# ③ 灌 knowledge base：优先 HF 流式拉 arXiv 数据集，失败退回内置样例
# ---------------------------------------------------------------------------

SAMPLE_PAPERS = [
    {"arxiv_id": "1706.03762", "title": "Attention Is All You Need",
     "subjects": "cs.CL cs.LG",
     "abstract": "We propose the Transformer, a model architecture relying entirely on attention mechanisms, dispensing with recurrence and convolutions."},
    {"arxiv_id": "2005.11401", "title": "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks",
     "subjects": "cs.CL",
     "abstract": "RAG models combine parametric and non-parametric memory: a seq2seq generator conditioned on documents retrieved from a dense vector index of Wikipedia."},
    {"arxiv_id": "2210.03629", "title": "ReAct: Synergizing Reasoning and Acting in Language Models",
     "subjects": "cs.CL cs.AI",
     "abstract": "ReAct interleaves reasoning traces and task-specific actions, allowing language models to interface with external tools and environments."},
    {"arxiv_id": "2310.08560", "title": "MemGPT: Towards LLMs as Operating Systems",
     "subjects": "cs.AI",
     "abstract": "MemGPT manages different memory tiers to provide extended context within a limited window, using interrupts and self-directed memory paging."},
    {"arxiv_id": "2201.11903", "title": "Chain-of-Thought Prompting Elicits Reasoning in Large Language Models",
     "subjects": "cs.CL",
     "abstract": "Generating a chain of thought — a series of intermediate reasoning steps — significantly improves complex reasoning ability of large language models."},
    {"arxiv_id": "2106.09685", "title": "LoRA: Low-Rank Adaptation of Large Language Models",
     "subjects": "cs.CL cs.LG",
     "abstract": "LoRA freezes pretrained weights and injects trainable rank decomposition matrices, greatly reducing trainable parameters for downstream tasks."},
    {"arxiv_id": "2304.03442", "title": "Generative Agents: Interactive Simulacra of Human Behavior",
     "subjects": "cs.HC cs.AI",
     "abstract": "Generative agents remember, reflect and plan: an architecture with a memory stream, retrieval, reflection and planning simulates believable human behavior."},
    {"arxiv_id": "n/a", "title": "Autonomous Navigation and Path Planning for Planetary Rovers",
     "subjects": "cs.RO astro-ph.IM",
     "abstract": "Survey of onboard autonomy for Mars and lunar surface exploration rovers: terrain assessment, hazard avoidance, and long-range path planning under communication delay."},
    {"arxiv_id": "n/a", "title": "Trajectory Design for Deep Space Exploration Missions",
     "subjects": "astro-ph.IM math.OC",
     "abstract": "Low-thrust trajectory optimization and gravity-assist sequencing for interplanetary spacecraft, with case studies on outer solar system exploration."},
    {"arxiv_id": "n/a", "title": "In-Situ Resource Utilization for Sustained Human Space Exploration",
     "subjects": "astro-ph.IM",
     "abstract": "Producing propellant, water and oxygen from lunar and Martian resources to reduce launch mass and enable sustained crewed space exploration."},
]


def ingest_from_huggingface(limit: int = 100) -> int:
    from itertools import islice

    from datasets import load_dataset

    ds = load_dataset("nick007x/arxiv-papers", split="train", streaming=True)
    count = 0
    for paper in islice(ds, limit):
        title = (paper.get("title") or "").strip()
        abstract = (paper.get("abstract") or "").strip()
        subjects = (paper.get("subjects") or paper.get("primary_subject") or "").strip()
        submission_date = (paper.get("submission_date") or "").strip()
        if not (title or abstract or subjects):
            continue
        text = "\n".join(p for p in (title, subjects, abstract) if p)
        memory_manager.write_knowledge_base(
            text=text,
            metadata={
                "arxiv_id": paper.get("arxiv_id"),
                "title": title,
                "subjects": subjects,
                "abstract": abstract,
                "submission_date": submission_date,
            },
        )
        count += 1
    return count


def ingest_samples() -> int:
    for p in SAMPLE_PAPERS:
        text = "\n".join((p["title"], p["subjects"], p["abstract"]))
        memory_manager.write_knowledge_base(text=text, metadata=dict(p))
    return len(SAMPLE_PAPERS)


print("\n" + "=" * 72)
print("③ 灌 knowledge base（arXiv 论文）")
print("=" * 72)
try:
    n = ingest_from_huggingface(100)
    print(f"  从 HuggingFace 流式写入 {n} 篇论文")
except Exception as e:
    print(f"  HF 数据集不可达（{type(e).__name__}），改用内置样例")
    n = ingest_samples()
    print(f"  写入内置样例 {n} 篇")

# ---------------------------------------------------------------------------
# ④ 语义检索（向量路径）
# ---------------------------------------------------------------------------

print("\n" + "=" * 72)
print('④ 语义检索: read_knowledge_base(query="space exploration")')
print("=" * 72)
print(memory_manager.read_knowledge_base(query="space exploration"))

print("\n" + "=" * 72)
print('   再来一个: query="agent long-term memory"')
print("=" * 72)
print(memory_manager.read_knowledge_base(query="agent long-term memory"))

# ---------------------------------------------------------------------------
# ⑤ 会话记忆（SQL 路径）：按 thread_id 精确检索，与向量路径对比
# ---------------------------------------------------------------------------

print("\n" + "=" * 72)
print("⑤ 会话记忆: 写 3 轮对话 → 按 thread_id 精确读回（SQL，非相似度）")
print("=" * 72)
THREAD = "demo-thread-001"
memory_manager.write_conversational_memory("帮我调研 agent 记忆方向的论文", "user", THREAD)
memory_manager.write_conversational_memory("好的，已检索到 MemGPT 和 Generative Agents 两篇", "assistant", THREAD)
memory_manager.write_conversational_memory("重点看 MemGPT 的分页机制", "user", THREAD)
print(memory_manager.read_conversational_memory(thread_id=THREAD, limit=10))

print("\n✅ 演示完成。数据持久在 Oracle 容器卷里，重跑脚本会重建表。")
