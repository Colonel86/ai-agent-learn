"""ZephyrBank 知识库 —— 复用课程原始语料,但用本地 embedding 重建索引。

课程随包附带了一个 llama-index 0.9 时代持久化的向量库(data/zb_vstore/),里面有
211 篇 ZephyrBank 文档。**文本还能用,向量不能用**:那些向量是 OpenAI
text-embedding-ada-002 生成的 1536 维,而我们换成了 384 维的 bge-small,维度都对不上。

所以这里的做法是:只从 docstore.json 里取出原始文本,用 fastembed 重新算一遍向量,
建成新索引并持久化到 data/zb_index_local/。第一次跑要花几秒算 211 篇文档的向量,
之后直接加载。

保留原始语料很重要——它里面**混着几份本不该进客服知识库的内部文档**(一份含数据库
主机名和口令的部署配置、几份含内部后台地址的员工手册)。L1 的"敏感信息泄露"漏洞
正是靠它们复现的:用户一问数据库主机名,检索器把配置文件捞出来,没设防的 LLM 就
照单念出去。这类"知识库投毒"是真实 RAG 系统最常见的泄露路径之一。
"""

from __future__ import annotations

import json
from pathlib import Path

from . import local_stack

DATA_DIR = Path(__file__).resolve().parent / "data"
ORIGINAL_DOCSTORE = DATA_DIR / "zb_vstore" / "docstore.json"
LOCAL_INDEX_DIR = DATA_DIR / "zb_index_local"


def load_course_documents() -> list[str]:
    """从课程原始 docstore.json 里取出全部文档正文。"""
    raw = json.loads(ORIGINAL_DOCSTORE.read_text())
    nodes = raw["docstore/data"]
    texts = [node["__data__"].get("text", "") for node in nodes.values()]
    return [t for t in texts if t.strip()]


def build_index(force: bool = False):
    """加载(或首次构建)本地向量索引。"""
    from llama_index.core import (
        Document,
        StorageContext,
        VectorStoreIndex,
        load_index_from_storage,
    )

    embed_model = local_stack.get_embed_model()

    if LOCAL_INDEX_DIR.exists() and not force:
        storage_context = StorageContext.from_defaults(persist_dir=str(LOCAL_INDEX_DIR))
        return load_index_from_storage(storage_context, embed_model=embed_model)

    texts = load_course_documents()
    print(f"[知识库] 首次构建索引:用 {local_stack.EMBED_MODEL} 向量化 {len(texts)} 篇文档…")
    index = VectorStoreIndex.from_documents(
        [Document(text=t) for t in texts], embed_model=embed_model
    )
    index.storage_context.persist(persist_dir=str(LOCAL_INDEX_DIR))
    print(f"[知识库] 索引已持久化到 {LOCAL_INDEX_DIR.relative_to(DATA_DIR.parent.parent)}")
    return index
