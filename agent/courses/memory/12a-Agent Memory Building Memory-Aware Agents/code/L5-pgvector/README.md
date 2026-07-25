# 12a·L5 Memory-Aware Agent（完整 agent loop）— pgvector 版

`../L5`（Oracle 版）的 PG 对照移植——课程终局：五种记忆 + agent loop 全部跑在 PostgreSQL + pgvector 上。容器/环境准备、Oracle→PG 映射表见 **[L2-pgvector/README.md](../L2-pgvector/README.md)**。

## 运行

```bash
cd L5-pgvector
uv venv --python 3.11 .venv
uv pip install --python .venv/bin/python -r requirements.txt
cp .env.example .env   # 填 DeepSeek key
.venv/bin/python main.py   # 会联网访问 arxiv.org 拉 MemGPT 论文
```

演示：同一 thread 连续 5 问——找 MemGPT 论文 → 存全文 → 问要点（吃 KB 记忆）→ 用工具压实会话 → "我第一个问题是什么"（吃摘要记忆）。

## L5 特有的移植点

- **AGENT_SYSTEM_PROMPT 和 agent loop 逐字未动**——这是整个对照实验的终局验证：Application 层（loop + prompt）和 Memory 层（MemoryManager 接口）完全不感知底座从 Oracle 换成了 PG。
- **JSONB metadata filter 全部兼容**：`read_workflow` 的 `{"num_steps": {"$gt": 0}}`、summary 的多键等值 filter，langchain_postgres 原生支持同一套 `$gt`/`$eq` 语法，零改动。
- 工具日志链路（全量输出落 `TOOL_LOG_MEMORY`、LLM 只拿 3000 字符截断版）走 helper_pg 里移植好的 SQL 方法。

## 验证结果（2026-07-14 实跑）

- 第 1 问：`arxiv_search_candidates` → `fetch_and_save_paper_to_kb_db`，MemGPT 论文 71 chunks 入 SEMANTIC_MEMORY
- 第 2/3 问：**0 次工具调用**——直接从 Knowledge Base Memory 段落回答（记忆感知生效）
- 第 4 问：`summarize_and_store` 压实会话；第 5 问：`expand_summary` 取回原文，准确答出第一问是 *"Can you get me the paper MemGPT"*
- 结束态：SEMANTIC 71 / TOOLBOX 5 / WORKFLOW 3 / ENTITY 20 / SUMMARY 1，会话表 10 行、工具日志 4 行，全程无异常
