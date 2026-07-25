# 12a·L3 Semantic Tool Memory — pgvector 版

`../L3`（Oracle 版）的 PG 对照移植。容器/环境准备、Oracle→PG 映射表和取舍分析见 **[L2-pgvector/README.md](../L2-pgvector/README.md)**，此处只记 L3 特有内容。

## 运行

```bash
# 前提：pg-memory-lab 容器在跑（见 L2-pgvector/README.md 第 1 步）
cd L3-pgvector
uv venv --python 3.11 .venv
uv pip install --python .venv/bin/python -r requirements.txt
cp .env.example .env   # 填 DeepSeek key（工具 docstring 增强要用 LLM）
.venv/bin/python main.py
```

演示：注册 4 个工具（`augment=True` 的走 LLM docstring 增强）→ 三个不同措辞的自然语言 query 语义检索工具，验证"问题→工具"映射（论文详情→fetch 工具、找文献→arxiv 搜索、问时间→get_current_time）。

## L3 特有的移植点

- **`Toolbox._tool_exists_in_db` 是 helper 里除 DDL 外唯一藏 Oracle SQL 的方法**：`JSON_VALUE(metadata, '$.name')` → JSONB `cmetadata->>'name'` + 按 collection JOIN（langchain_postgres 共享物理表，需 JOIN `langchain_pg_collection` 限定）。
- **psycopg 事务语义坑**：该方法在表还不存在时查询会抛错，Oracle 版直接 `except: return False` 就行；PG 上出错后连接进入 aborted 状态，后续所有语句都会失败——except 分支里必须 `conn.rollback()`。这是两库移植时最容易踩的行为差异。
- 依赖锁版本：`pymupdf==1.23.26`（langchain_community 引用 `fitz.fitz`，1.24+ 移除）、`arxiv==2.1.3`（配合 main.py 里的 shim；4.x 接口又变了）。

## 验证结果（2026-07-14 实跑）

三个 query 全部命中正确工具；LLM 增强（DeepSeek）正常，增强后的 docstring 明显更厚（含 step-by-step 与调用时机）。
