# 12a·L4 Memory Operations（压实与自更新）— pgvector 版

`../L4`（Oracle 版）的 PG 对照移植。容器/环境准备、Oracle→PG 映射表见 **[L2-pgvector/README.md](../L2-pgvector/README.md)**，此处只记 L4 特有内容。

## 运行

```bash
cd L4-pgvector
uv venv --python 3.11 .venv
uv pip install --python .venv/bin/python -r requirements.txt
cp .env.example .env   # 填 DeepSeek key（摘要生成要用 LLM）
.venv/bin/python main.py
```

演示五步：灌 30+ 条研究对话 → 监控 context 用量 → `summarize_conversation`（LLM 摘要 + **summary_id 回填源数据行**）→ `expand_summary` 无损取回原文 → SQL 层验证归档状态（未归档 0 / 已归档全部）。

## L4 特有的移植点

- **距离策略**：L4 notebook 用 EUCLIDEAN（L2/L3 用 COSINE），PG 版通过 `StoreManager(distance="euclidean")` 传入，映射到 `langchain_postgres.DistanceStrategy.EUCLIDEAN`。若建 HNSW 索引，opclass 必须同步换成 `vector_l2_ops`（`create_hnsw_index(conn, distance="euclidean")`）。
- **`summarize_conversation` 的回填 UPDATE 用 `executemany`**：psycopg3 对 `%(name)s` + dict 序列的支持与 oracledb 的 `:name` 语义一致，逐字换占位符即可。
- 压实链路（`summarise_context_window` / `offload_to_summary`）本身完全 DB 无关，零改动。

## 验证结果（2026-07-14 实跑）

32 条消息全部归档回填（未归档 0），会话上下文 2,007 → 141 tokens；`expand_summary` 完整取回原文——"Summarization 丢信息，Compaction 搬信息"在 PG 底座上同样成立。
