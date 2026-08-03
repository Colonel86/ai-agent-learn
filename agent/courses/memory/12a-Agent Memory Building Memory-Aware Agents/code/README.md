# Agent Memory: Building Memory-Aware Agents — 本地化演示版（pgvector）

课程原版（DeepLearning.AI × Oracle）依赖 OpenAI gpt-5 + sentence-transformers + Oracle 26ai。本目录已本地化，并把存储底座**整体替换为 PostgreSQL + pgvector**（Oracle 不再是运行前提）：

- **Chat**：DeepSeek `deepseek-v4-flash`（OpenAI 兼容端点；helper 硬编码的 gpt-5 由 client 适配器统一改写）
- **Embedding**：fastembed 本地跑 `BAAI/bge-small-en-v1.5`（384 维，ONNX 纯 CPU，免装 torch）
- **数据库**：pgvector/pgvector:pg17 容器（~430MB、秒级启动 vs Oracle Free 4.8GB、30-60 秒初始化）
- **依赖**：统一 pin 到最新稳定版，L2–L5 共用一个 venv

课程三层架构（Application / Memory / Infrastructure）的论点在这里被实证：换存储底座只动 Infrastructure 层——各课 `main.py` 的演示流程与 Oracle 版逐字相同，`MemoryManager` 向量方法逐字相同，重写的只有连接、DDL、SQL 方言与向量存储类，全部集中在 `helper_pg.py`（由课程 `helper.py` 程序化生成，1400+ 行 DB 无关代码逐字节保留）。

## 架构

```mermaid
flowchart TB
    MM[MemoryManager<br/>统一读写接口 · 与 Oracle 版同构] --> SQL & VEC
    subgraph SQL["SQL 路径 · 精确检索 (psycopg)"]
        CT[(CONVERSATIONAL_MEMORY<br/>按 thread_id + 时间序)]
        TL[(TOOL_LOG_MEMORY)]
    end
    subgraph VEC["向量路径 · 语义检索 (HNSW 索引)"]
        PGE[(langchain_pg_embedding<br/>共享物理表)]
        KB[SEMANTIC_MEMORY] & WF[WORKFLOW_MEMORY] & TB[TOOLBOX_MEMORY] & EN[ENTITY_MEMORY] & SM[SUMMARY_MEMORY] -.collection 逻辑分区.-> PGE
    end
    E[fastembed<br/>bge-small-en-v1.5 · 384 维] -.embedding.-> VEC
```

## 环境准备（一次性）

**1. venv**：

```bash
cd "agent/courses/memory/12a-Agent Memory Building Memory-Aware Agents/code"
uv venv --python 3.11 .venv
uv pip install -p .venv/bin/python -r requirements.txt
```

**2. PG 容器**（首次创建；之后 `docker start pg-memory-lab` 即可）：

```bash
# Docker Hub 直连不通时走 daocloud 镜像再重打 tag
docker pull docker.m.daocloud.io/pgvector/pgvector:pg17
docker tag docker.m.daocloud.io/pgvector/pgvector:pg17 pgvector/pgvector:pg17
docker run -d --name pg-memory-lab -p 5433:5432 \
    -e POSTGRES_PASSWORD=postgres pgvector/pgvector:pg17
```

（5433 是为避开本机被占用的 5432；连接串走 `.env` 的 `PG_DSN`。）

**3. `code/.env`**（已就位，换 key 时改这里）：

```ini
OPENAI_API_KEY=sk-...                          # DeepSeek key
OPENAI_BASE_URL=https://api.deepseek.com/v1
MODEL=deepseek-v4-flash
PG_DSN=postgresql://postgres:postgres@127.0.0.1:5433/postgres
HF_ENDPOINT=https://hf-mirror.com
FASTEMBED_CACHE_PATH=/Users/ming/.cache/fastembed
HF_HUB_OFFLINE=1                               # 模型已缓存时强制离线，绕开代理干扰
```

## 怎么跑

每课一个 `main.py`，带分节横幅逐步打印课程叙事（在 `code/` 根目录下执行）：

```bash
.venv/bin/python L2/main.py   # Memory Manager：7 类记忆存储 + 两种检索路径（~2 分钟）
.venv/bin/python L3/main.py   # Toolbox：工具定义向量化，语义检索按需取用（~3 分钟）
.venv/bin/python L4/main.py   # 上下文管理：Summarization vs Compaction（~4 分钟）
.venv/bin/python L5/main.py   # 完整 agent loop：检索工具 → 拉论文 → 入库 → 答题（~5 分钟）
```

各课 notebook 与 `helper.py` 为课程 Oracle 原版，仅作对照不作演示入口（要跑它们需另起 Oracle 容器并装 oracledb/langchain-oracledb）。

## 每课演示看点

```mermaid
graph LR
    L2["L2 Memory Manager<br/>7 类记忆·SQL/向量双路径"] --> L3["L3 Toolbox<br/>工具即记忆·语义检索"]
    L3 --> L4["L4 上下文管理<br/>摘要 vs 压实"]
    L4 --> L5["L5 完整 agent loop<br/>记忆驱动的研究助理"]
```

| 课 | 演示叙事 |
| --- | --- |
| **L2** | 不同记忆类型不同数据模型：会话记忆走 SQL 表按 `thread_id` 精确取，知识库等 5 类记忆走向量 collection 语义检索——同一个 PG 库里 SQL + 向量并存 |
| **L3** | 工具定义也是记忆：LLM 增强 docstring 后向量化入 TOOLBOX_MEMORY，用自然语言 query 语义检索 top-k 工具；`read_toolbox` 本身也是工具（自举） |
| **L4** | Summarization 丢信息、Compaction 搬信息：32 条消息压实后 context 从 ~2000 tokens 降到 ~140，原文完整搬进 SUMMARY_MEMORY，可按 Summary ID 展开 |
| **L5** | 全部组件拼成 agent loop：语义检索工具 → arXiv 搜索 → 拉全文入知识库 → 基于知识库答题，全程记忆读写落 PG |

## Oracle → PG 移植的取舍（架构师视角）

- **"同一个库 SQL + 向量"的核心卖点两边等价**：精确/时序走 SQL、语义走向量，PG 一个连接搞定，不需要独立向量库。
- **物理布局差异是真实的取舍**：Oracle 版一种记忆一张表；`langchain_postgres` 把所有 collection 塞进 `langchain_pg_embedding` 共享表按 `collection_id` 分区。要严格每表隔离（独立索引参数/扩缩容）得绕开 LangChain 集成手写 pgvector 表。
- **PGVector 必须传 `embedding_length`**，否则 embedding 列无维度、HNSW 索引建不起来。
- **psycopg 事务坑**：SQL 出错后必须 `rollback()`，否则连接卡死在 aborted 状态（Oracle 驱动无此行为）。
- 课程 Oracle 的 hybrid search 只留了接口没真用；PG 侧可用 `tsvector` + 向量 RRF 自拼实现同等能力。

## 本地化改了什么

课程 `helper.py` 零改动（留作对照）；演示走 `helper_pg.py` + 各课 `main.py`：

1. **client 适配器**：helper 多处硬编码 `model="gpt-5"` → 包一层 `chat.completions.create`，统一改写为 `.env` 的 MODEL 并注入 `thinking: disabled`
2. **embedding 换 fastembed**：LangChain Embeddings 接口通用，直接喂 PGVector
3. **arxiv 生态三连坑 shim**（langchain-community 0.4.2 仍未修，均带 hasattr 守卫）：`Search.results()`（arxiv 2.x 删）→ Client.results 补回；`Result.download_pdf()`（arxiv 4.x 删）→ `pdf_url` + urllib 重实现；`fitz.fitz`（pymupdf 1.24+ 删）→ 别名兜底。arxiv.org 连跑几轮会 429 限流，封禁窗口可达 15 分钟+，等够再跑

## 依赖版本

课程原 requirements 未 pin 版本；本地化统一 pin 最新稳定版（2026-07）：

| 包 | 版本 | 说明 |
| --- | --- | --- |
| psycopg[binary] / langchain-postgres | 3.3.4 / 0.0.17 | 替代 oracledb / langchain-oracledb |
| langchain / langchain-community / langchain-openai | 1.3.14 / 0.4.2 / 1.4.1 | |
| openai | 2.49.0 | 走 DeepSeek 兼容端点 |
| fastembed | 0.8.0 | 替代 sentence-transformers（课程原用，拉 torch ~2GB，不装） |
| datasets | 5.0.0 | L2 拉 arXiv 样例数据集（失败自动用内置样例） |
| arxiv / pymupdf | 4.0.0 / 1.28.0 | 配合 main.py 里的三个兼容 shim |
