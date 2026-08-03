"""12a·L3 Semantic Tool Memory（Toolbox）— pgvector 版本地演示（Oracle 版见 ../L3/main.py）。

课程主题：工具定义也是记忆。工具多了不能全量塞 context（膨胀 + 选择能力退化），
应该把工具定义存进向量 collection（TOOLBOX_MEMORY），按 query 语义检索 top-k 再交给 LLM。
`read_toolbox` 本身也是一个工具——"能找工具的工具"（自举）。

与 Oracle 版的差异只在 ① 基础设施段（PG 连接 + 共享表清场 + StoreManager 签名）；
②③ 的工具注册与语义检索逻辑逐字相同。Toolbox 的去重查询（_tool_exists_in_db）
已在 helper_pg.py 里从 Oracle JSON_VALUE 移植为 JSONB 查询。

前提：pgvector 容器在跑（见 L2-pgvector/README.md）。

演示流程（python main.py）：
  ① 重建记忆存储 → ② 注册 4-5 个工具（LLM 增强 docstring 后向量化入库）
  ③ 用三个不同措辞的自然语言 query 做语义工具检索，验证"问题→工具"的映射
"""

import os

from dotenv import load_dotenv

load_dotenv()
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

from helper_pg import (
    MemoryManager,
    StoreManager,
    Toolbox,
    connect_to_postgres,
    create_conversational_history_table,
    create_tool_log_table,
    suppress_warnings,
)

suppress_warnings()

from langchain_community.embeddings import FastEmbedEmbeddings
from openai import OpenAI

# langchain_community 的 arxiv 封装踩三个版本坑（截至 0.4.2 仍未修）：
# Search.results()（arxiv 2.x 删）、Result.download_pdf()（arxiv 4.x 删）、
# fitz.fitz 子模块（pymupdf 1.24+ 删）；旧版 arxiv 1.4.8 又因 arxiv.org 强制
# HTTPS 而 301 全挂 → 统一用最新版 + 三个兼容 shim（均有 hasattr 守卫）
import urllib.request

import arxiv as _arxiv
import fitz as _fitz

if not hasattr(_arxiv.Search, "results"):
    _arxiv_client = _arxiv.Client(page_size=20, delay_seconds=3.0, num_retries=3)
    _arxiv.Search.results = lambda self, offset=0: _arxiv_client.results(
        self, offset=offset
    )

if not hasattr(_arxiv.Result, "download_pdf"):
    def _download_pdf(self, dirpath=".", filename=None):
        filename = filename or f"{self.get_short_id().replace('/', '_')}.pdf"
        path = os.path.join(dirpath, filename)
        urllib.request.urlretrieve(self.pdf_url, path)
        return path

    _arxiv.Result.download_pdf = _download_pdf

if not hasattr(_fitz, "fitz"):
    _fitz.fitz = _fitz

MODEL = os.getenv("MODEL", "deepseek-v4-flash")
PG_DSN = os.getenv("PG_DSN", "postgresql://postgres:postgres@127.0.0.1:5433/postgres")
SQLALCHEMY_URL = PG_DSN.replace("postgresql://", "postgresql+psycopg://")


# ---------------------------------------------------------------------------
# LLM client 适配器：helper 里写死了 model="gpt-5"，这里统一改写成 .env 的
# MODEL，并关掉 DeepSeek 的 thinking（避免 tool_choice 兼容问题）
# ---------------------------------------------------------------------------


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

# ---------------------------------------------------------------------------
# ① 数据库与存储（同 L2-pgvector，clean slate 重建）
# ---------------------------------------------------------------------------

try:
    database_connection = connect_to_postgres(PG_DSN)
except Exception as e:
    raise SystemExit(f"PostgreSQL 未就绪（{type(e).__name__}），先启动容器（见 L2-pgvector/README.md）")

embedding_model = FastEmbedEmbeddings(model_name="BAAI/bge-small-en-v1.5")

CONVERSATIONAL_TABLE = "CONVERSATIONAL_MEMORY"
KNOWLEDGE_BASE_TABLE = "SEMANTIC_MEMORY"
WORKFLOW_TABLE = "WORKFLOW_MEMORY"
TOOLBOX_TABLE = "TOOLBOX_MEMORY"
ENTITY_TABLE = "ENTITY_MEMORY"
SUMMARY_TABLE = "SUMMARY_MEMORY"
TOOL_LOG_TABLE = "TOOL_LOG_MEMORY"

# 清场重建：向量侧删两张 langchain 共享表即清空全部 collection
with database_connection.cursor() as cur:
    cur.execute("DROP TABLE IF EXISTS langchain_pg_embedding, langchain_pg_collection CASCADE")
    cur.execute(f"DROP TABLE IF EXISTS {TOOL_LOG_TABLE}")
database_connection.commit()

conversation_history_table = create_conversational_history_table(
    database_connection, CONVERSATIONAL_TABLE
)
tool_log_history_table = create_tool_log_table(database_connection, TOOL_LOG_TABLE)

store_manager = StoreManager(
    sqlalchemy_url=SQLALCHEMY_URL,
    embedding_function=embedding_model,
    embedding_length=384,
    table_names={
        "knowledge_base": KNOWLEDGE_BASE_TABLE,
        "workflow": WORKFLOW_TABLE,
        "toolbox": TOOLBOX_TABLE,
        "entity": ENTITY_TABLE,
        "summary": SUMMARY_TABLE,
    },
    conversational_table=conversation_history_table,
    tool_log_table=tool_log_history_table,
    distance="cosine",
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
print("✅ MemoryManager and Toolbox initialized")

# ---------------------------------------------------------------------------
# ② 注册工具（augment=True 时 LLM 会读 docstring + 源码生成增强描述再入库）
# ---------------------------------------------------------------------------

print("\n注册工具（含 LLM docstring 增强，每个工具一次 LLM 调用）...")


@toolbox.register_tool(augment=True)
def read_toolbox(query: str, k: int = 3) -> list[str]:
    """
    Search the toolbox for functions that can help solve a problem or complete a task.

    Use this tool when:
    - You encounter an error or unexpected output and need a different approach
    - The currently available tools don't seem sufficient for the task
    - You need to discover what capabilities are available for a specific problem

    Args:
        query: A natural language description of what you're trying to accomplish.
        k: Number of relevant tools to return

    Returns:
        A list of tool definitions that semantically match your query.
    """
    return memory_manager.read_toolbox(query, k=k)


@toolbox.register_tool(augment=True)
def get_current_time(detailed: bool = False) -> str:
    """
    Returns the current time.

    Args:
        detailed: If True, returns detailed format with microseconds

    Returns:
        str: Current time as formatted string
    """
    from datetime import datetime

    if detailed:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


import json
from urllib.parse import urlparse

from langchain_community.retrievers import ArxivRetriever

arxiv_retriever = ArxivRetriever(
    load_max_docs=8, get_full_documents=False, doc_content_chars_max=4000
)


def _arxiv_id_from_entry_id(entry_id: str) -> str:
    if not entry_id:
        return ""
    path = urlparse(entry_id).path
    return path.split("/abs/")[-1].strip("/")


@toolbox.register_tool(augment=False)
def arxiv_search_candidates(query: str, k: int = 5) -> str:
    """
    Search arXiv and return a JSON list of candidate papers with IDs + metadata.
    """
    docs = arxiv_retriever.invoke(query)
    candidates = []
    for d in (docs or [])[:k]:
        meta = d.metadata or {}
        entry_id = meta.get("Entry ID", "")
        candidates.append(
            {
                "arxiv_id": _arxiv_id_from_entry_id(entry_id),
                "title": meta.get("Title", ""),
                "authors": meta.get("Authors", ""),
                "published": str(meta.get("Published", "")),
                "abstract": (d.page_content or "")[:2500],
            }
        )
    return json.dumps(candidates, ensure_ascii=False, indent=2)


from datetime import datetime, timezone

from langchain_community.document_loaders import ArxivLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter


@toolbox.register_tool(augment=True)
def fetch_and_save_paper_to_kb_db(
    arxiv_id: str, chunk_size: int = 1500, chunk_overlap: int = 200
) -> str:
    """
    Fetch full arXiv paper text (PDF -> text) and store it into the pgvector
    knowledge base collection as chunked records.
    """
    loader = ArxivLoader(query=arxiv_id, load_max_docs=1, doc_content_chars_max=None)
    docs = loader.load()
    if not docs:
        return f"No documents found for arXiv id: {arxiv_id}"
    doc = docs[0]
    title = doc.metadata.get("Title") or f"arXiv {arxiv_id}"
    full_text = doc.page_content or ""
    if not full_text.strip():
        return f"Loaded arXiv {arxiv_id} but extracted empty text."
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, chunk_overlap=chunk_overlap
    )
    chunks = splitter.split_text(full_text)
    ts_utc = datetime.now(timezone.utc).isoformat()
    metadatas = [
        {
            "source": "arxiv", "arxiv_id": arxiv_id, "title": title,
            "chunk_id": i, "num_chunks": len(chunks), "ingested_ts_utc": ts_utc,
        }
        for i in range(len(chunks))
    ]
    memory_manager.write_knowledge_base(chunks, metadatas)
    return f"Saved arXiv {arxiv_id} to {KNOWLEDGE_BASE_TABLE}: {len(chunks)} chunks (title: {title})."


# 课程还注册了 search_tavily（联网搜索），需要 TAVILY_API_KEY；没有就跳过
if os.getenv("TAVILY_API_KEY"):
    from tavily import TavilyClient

    tavily_client = TavilyClient()

    @toolbox.register_tool(augment=True)
    def search_tavily(query: str, max_results: int = 5):
        """Use this function to search the web and store the results in the knowledge base."""
        response = tavily_client.search(query=query, max_results=max_results)
        results = response.get("results", [])
        for r in results:
            text = f"Title: {r.get('title', '')}\nContent: {r.get('content', '')}\nURL: {r.get('url', '')}"
            memory_manager.write_knowledge_base(
                text,
                {"title": r.get("title", ""), "url": r.get("url", ""),
                 "source_type": "tavily_search", "query": query,
                 "timestamp": datetime.now().isoformat()},
            )
        return results

    print("  已注册 search_tavily")
else:
    print("  ⏭️  无 TAVILY_API_KEY，跳过 search_tavily")

print(f"✅ 工具注册完成: {list(toolbox._tools_by_name)}")

# ---------------------------------------------------------------------------
# ③ 语义工具检索：自然语言问题 → top-k 工具定义
# ---------------------------------------------------------------------------

QUERIES = [
    ("Get more details on a paper on AI", 1),   # 课程原 query
    ("I need to find recent academic publications about LLM agents", 2),
    ("what time is it right now?", 1),
]

for query, k in QUERIES:
    print("\n" + "=" * 72)
    print(f'read_toolbox(query="{query}", k={k})')
    print("=" * 72)
    for t in memory_manager.read_toolbox(query, k=k):
        fn = t["function"]
        print(f"  🔧 {fn['name']}")
        print(f"     {fn['description'][:220]}...")

print("\n✅ 演示完成：工具没有全量塞进 context，而是按语义按需检索。")
