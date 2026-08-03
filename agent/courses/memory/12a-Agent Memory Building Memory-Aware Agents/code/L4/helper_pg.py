"""helper_pg.py —— 课程 helper.py（Oracle 版）的 PostgreSQL + pgvector 移植。

本文件由脚本从 helper.py 生成：Oracle 专属部分（连接初始化/DDL/SQL 方言/OracleVS/
IVF 索引）替换为 PG 等价物，其余 DB 无关代码（Toolbox、摘要压实、工具注册、样例
数据等）与课程版逐字节相同。对外符号名与课程版保持一致，main.py 可平移。
"""

import os
import sys
import time
import warnings
import logging
import psycopg
from dotenv import load_dotenv, find_dotenv
from langchain_postgres import PGVector
from langchain_postgres.vectorstores import DistanceStrategy
import json as json_lib
from datetime import datetime
import inspect
import uuid
from typing import Callable, Optional, Union
from pydantic import BaseModel

# Suppress warnings
import warnings
warnings.filterwarnings("ignore")


# these expect to find a .env file at the directory above the lesson.                                                                                                                     # the format for that file is (without the comment)                                                                                                                                       #API_KEYNAME=AStringThatIsTheLongAPIKeyFromSomeService
def load_env():
    _ = load_dotenv(find_dotenv())


def suppress_warnings():
    # HuggingFace / transformers log messages
    logging.getLogger("huggingface_hub").setLevel(logging.ERROR)
    logging.getLogger("transformers").setLevel(logging.ERROR)


def get_openai_api_key():
    load_env()
    openai_api_key = os.getenv("OPENAI_API_KEY")
    return openai_api_key


# =============================================================================
# PG INFRASTRUCTURE（对照 Oracle 版的 setup_oracle_database/connect_to_oracle/
# create_*_table/safe_create_index 区域）
# =============================================================================


def connect_to_postgres(dsn: str):
    """连接 PG 并确保 vector 扩展就绪。

    对应 Oracle 版 setup_oracle_database + connect_to_oracle 两步——PG 不需要
    建表空间/建用户，一条 CREATE EXTENSION 即完成向量能力初始化。
    """
    conn = psycopg.connect(dsn)
    with conn.cursor() as cur:
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
    conn.commit()
    return conn


def table_exists(conn, table_name):
    """Check if a table exists (PG: to_regclass)."""
    with conn.cursor() as cur:
        cur.execute("SELECT to_regclass(%s)", (table_name.lower(),))
        return cur.fetchone()[0] is not None


def create_conversational_history_table(conn, table_name: str = "CONVERSATIONAL_MEMORY"):
    """创建对话历史表（先删后建，与课程版行为一致）。

    方言对照：VARCHAR2→varchar, CLOB→text, SYS_GUID()→gen_random_uuid()。
    """
    with conn.cursor() as cur:
        cur.execute(f"DROP TABLE IF EXISTS {table_name}")
        cur.execute(f"""
            CREATE TABLE {table_name} (
                id varchar(100) DEFAULT gen_random_uuid() PRIMARY KEY,
                thread_id varchar(100) NOT NULL,
                role varchar(50) NOT NULL,
                content text NOT NULL,
                timestamp timestamptz DEFAULT CURRENT_TIMESTAMP,
                metadata text,
                created_at timestamptz DEFAULT CURRENT_TIMESTAMP,
                summary_id varchar(100) DEFAULT NULL
            )
        """)
        cur.execute(f"CREATE INDEX idx_{table_name.lower()}_thread_id ON {table_name}(thread_id)")
        cur.execute(f"CREATE INDEX idx_{table_name.lower()}_timestamp ON {table_name}(timestamp)")
    conn.commit()
    print(f"Table {table_name} created successfully with indexes")
    return table_name


def create_tool_log_table(conn, table_name: str = "TOOL_LOG_MEMORY"):
    """创建工具执行日志表（幂等：已存在则直接复用，与课程版行为一致）。"""
    if table_exists(conn, table_name):
        print(f"  ⏭️ Table {table_name} already exists (using existing table)")
        return table_name

    with conn.cursor() as cur:
        cur.execute(f"""
            CREATE TABLE {table_name} (
                id varchar(100) DEFAULT gen_random_uuid() PRIMARY KEY,
                thread_id varchar(100) NOT NULL,
                tool_call_id varchar(200),
                tool_name varchar(200) NOT NULL,
                tool_args text,
                result text,
                result_preview varchar(2000),
                status varchar(30) DEFAULT 'success',
                error_message text,
                metadata text,
                timestamp timestamptz DEFAULT CURRENT_TIMESTAMP,
                created_at timestamptz DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cur.execute(f"CREATE INDEX idx_{table_name.lower()}_thread_id ON {table_name}(thread_id)")
        cur.execute(f"CREATE INDEX idx_{table_name.lower()}_tool_name ON {table_name}(tool_name)")
        cur.execute(f"CREATE INDEX idx_{table_name.lower()}_timestamp ON {table_name}(timestamp)")
    conn.commit()
    print(f"  ✅ Table {table_name} created successfully with indexes")
    return table_name


def create_hnsw_index(conn, distance: str = "cosine", idx_name: str = "langchain_pg_embedding_hnsw"):
    """在 langchain_pg_embedding.embedding 上建 HNSW 索引（对照 Oracle 版 safe_create_index）。

    与 Oracle 版的差异：
      1. langchain_postgres 所有 collection 共享一张物理表，只需一个索引（Oracle 5 个 IVF）
      2. pgvector 的 HNSW 无 Oracle Free 的 ORA-00600 问题，不必退回 IVF
    前提：PGVector 传了 embedding_length（列为定长 vector(n)），HNSW 才建得起来。
    opclass 必须与检索用的距离一致：cosine→vector_cosine_ops，euclidean→vector_l2_ops。
    """
    opclass = {"cosine": "vector_cosine_ops", "euclidean": "vector_l2_ops"}[distance]
    with conn.cursor() as cur:
        cur.execute(
            f"CREATE INDEX IF NOT EXISTS {idx_name}"
            f" ON langchain_pg_embedding USING hnsw (embedding {opclass})"
        )
    conn.commit()
    print(f"  ✅ Created index: {idx_name}")


class MemoryManager:
    """
    A simplified memory manager for AI agents using PostgreSQL + pgvector.

    Manages 7 types of memory:
    - Conversational: Chat history per thread (SQL table)
    - Tool Log: Raw tool execution outputs and metadata (SQL table)
    - Knowledge Base: Searchable documents (Vector store)
    - Workflow: Execution patterns (Vector store)
    - Toolbox: Available tools (Vector store)
    - Entity: People, places, systems (Vector store)
    - Summary: Storing compressed context window
    """

    def __init__(
            self,
            conn,
            conversation_table: str,
            knowledge_base_vs,
            workflow_vs,
            toolbox_vs,
            entity_vs,
            summary_vs,
            tool_log_table: str | None = None
    ):
        self.conn = conn
        self.conversation_table = conversation_table
        self.knowledge_base_vs = knowledge_base_vs
        self.workflow_vs = workflow_vs
        self.toolbox_vs = toolbox_vs
        self.entity_vs = entity_vs
        self.summary_vs = summary_vs
        self.tool_log_table = tool_log_table

    # ==================== CONVERSATIONAL MEMORY (SQL) ====================

    def write_conversational_memory(self, content: str, role: str, thread_id: str) -> str:
        """Store a message in conversation history."""
        thread_id = str(thread_id)
        with self.conn.cursor() as cur:
            cur.execute(f"""
                INSERT INTO {self.conversation_table} (thread_id, role, content, metadata, timestamp)
                VALUES (%(thread_id)s, %(role)s, %(content)s, %(metadata)s, CURRENT_TIMESTAMP)
                RETURNING id
            """, {"thread_id": thread_id, "role": role, "content": content, "metadata": "{}"})
            record_id = cur.fetchone()[0]
        self.conn.commit()
        return record_id

    def read_conversational_memory(self, thread_id: str, limit: int = 10) -> str:
        """Read conversation history for a thread (excludes summarized messages)."""
        thread_id = str(thread_id)
        with self.conn.cursor() as cur:
            cur.execute(f"""
                SELECT role, content, timestamp FROM {self.conversation_table}
                WHERE thread_id = %(thread_id)s AND summary_id IS NULL
                ORDER BY timestamp ASC
                LIMIT %(limit)s
            """, {"thread_id": thread_id, "limit": limit})
            results = cur.fetchall()

        messages = [f"[{ts.strftime('%H:%M:%S')}] [{role}] {content}" for role, content, ts in results]
        messages_formatted = '\n'.join(messages)
        if not messages_formatted:
            messages_formatted = "(No unsummarized messages found for this thread.)"
        return f"""## Conversation Memory
### What this memory is
Chronological, unsummarized messages from the current thread. This memory captures user intent, constraints, and commitments made in recent turns.
### How you should leverage it
- Preserve continuity with prior decisions, terminology, and user preferences.
- Resolve references like "that", "previous step", or "the paper above" using earlier turns.
- If older context conflicts with newer user instructions, prioritize the latest user direction.
### Retrieved messages

{messages_formatted}"""

    def mark_as_summarized(self, thread_id: str, summary_id: str):
        """Mark all unsummarized messages in a thread as summarized."""
        thread_id = str(thread_id)
        with self.conn.cursor() as cur:
            cur.execute(f"""
                UPDATE {self.conversation_table}
                SET summary_id = %(summary_id)s
                WHERE thread_id = %(thread_id)s AND summary_id IS NULL
            """, {"summary_id": summary_id, "thread_id": thread_id})
        self.conn.commit()
        print(f"  📦 Marked messages as summarized (summary_id: {summary_id})")

    # ==================== TOOL LOG MEMORY (SQL) ====================

    def write_tool_log(
            self,
            thread_id: str,
            tool_name: str,
            tool_args,
            result: str,
            status: str = "success",
            tool_call_id: str | None = None,
            error_message: str | None = None,
            metadata: dict | None = None,
    ) -> str | None:
        """Persist raw tool execution logs for auditing and just-in-time retrieval."""
        if not self.tool_log_table:
            return None

        thread_id = str(thread_id)

        if isinstance(tool_args, (dict, list)):
            tool_args_str = json_lib.dumps(tool_args, ensure_ascii=False)
        else:
            tool_args_str = "" if tool_args is None else str(tool_args)

        result_str = "" if result is None else str(result)
        # Oracle VARCHAR2(2000) may be byte-limited; truncate preview by UTF-8 bytes.
        preview = result_str.encode("utf-8")[:2000].decode("utf-8", errors="ignore")

        metadata_str = json_lib.dumps(metadata, ensure_ascii=False) if metadata else "{}"

        with self.conn.cursor() as cur:
            cur.execute(f"""
                INSERT INTO {self.tool_log_table}
                    (thread_id, tool_call_id, tool_name, tool_args, result, result_preview, status, error_message, metadata, timestamp)
                VALUES
                    (%(thread_id)s, %(tool_call_id)s, %(tool_name)s, %(tool_args)s, %(result)s, %(result_preview)s, %(status)s, %(error_message)s, %(metadata)s, CURRENT_TIMESTAMP)
                RETURNING id
            """, {
                "thread_id": thread_id,
                "tool_call_id": tool_call_id,
                "tool_name": tool_name,
                "tool_args": tool_args_str,
                "result": result_str,
                "result_preview": preview,
                "status": status,
                "error_message": error_message,
                "metadata": metadata_str,
            })
            log_id = cur.fetchone()[0]

        self.conn.commit()
        return log_id

    def read_tool_logs(self, thread_id: str, limit: int = 20) -> list[dict]:
        """Read recent tool logs for a thread, newest first."""
        if not self.tool_log_table:
            return []

        thread_id = str(thread_id)
        with self.conn.cursor() as cur:
            cur.execute(f"""
                SELECT id, tool_call_id, tool_name, tool_args, result_preview, status, error_message, metadata, timestamp
                FROM {self.tool_log_table}
                WHERE thread_id = %(thread_id)s
                ORDER BY timestamp DESC
                LIMIT %(limit)s
            """, {"thread_id": thread_id, "limit": limit})
            rows = cur.fetchall()

        logs = []
        for log_id, tool_call_id, tool_name, tool_args, result_preview, status, error_message, metadata, ts in rows:
            logs.append({
                "id": log_id,
                "tool_call_id": tool_call_id,
                "tool_name": tool_name,
                "tool_args": tool_args,
                "result_preview": result_preview,
                "status": status,
                "error_message": error_message,
                "metadata": metadata,
                "timestamp": ts.isoformat() if ts else None,
            })
        return logs

    # ==================== KNOWLEDGE BASE (Vector Store) ====================

    def write_knowledge_base(self, text: str | list[str], metadata: dict | list[dict]):
        """
        Store knowledge-base content with metadata.

        Supports:
        - Single record: text=str, metadata=dict
        - Batch insert: text=list[str], metadata=list[dict]
        """
        if isinstance(text, list):
            texts = [str(t) for t in text]
            if isinstance(metadata, list):
                metadatas = metadata
            else:
                metadatas = [metadata for _ in texts]

            if len(texts) != len(metadatas):
                raise ValueError(
                    f"Knowledge-base batch length mismatch: {len(texts)} texts vs {len(metadatas)} metadata rows"
                )
            self.knowledge_base_vs.add_texts(texts, metadatas)
            return

        self.knowledge_base_vs.add_texts([str(text)], [metadata if isinstance(metadata, dict) else {}])

    def read_knowledge_base(self, query: str, k: int = 3) -> str:
        """Search knowledge base for relevant content."""
        results = self.knowledge_base_vs.similarity_search(query, k=k)
        content = "\n".join([doc.page_content for doc in results])
        if not content:
            content = "(No relevant knowledge base passages found.)"
        return f"""## Knowledge Base Memory
### What this memory is
Retrieved background documents and previously ingested reference material relevant to the current query.
### How you should leverage it
- Ground responses in these passages when making factual or technical claims.
- Prefer concrete details from this memory over unsupported assumptions.
- If evidence is missing or ambiguous, state uncertainty and request clarification or additional retrieval.
### Retrieved passages

{content}"""

    # ==================== WORKFLOW (Vector Store) ====================

    def write_workflow(self, query: str, steps: list, final_answer: str, success: bool = True):
        """Store a completed workflow pattern for future reference."""
        # Format steps as text
        steps_text = "\n".join([f"Step {i + 1}: {s}" for i, s in enumerate(steps)])
        text = f"Query: {query}\nSteps:\n{steps_text}\nAnswer: {final_answer[:200]}"

        metadata = {
            "query": query,
            "success": success,
            "num_steps": len(steps),
            "timestamp": datetime.now().isoformat()
        }
        self.workflow_vs.add_texts([text], [metadata])

    def read_workflow(self, query: str, k: int = 3) -> str:
        """Search for similar past workflows with at least 1 step."""
        # Filter to only include workflows that have steps (num_steps > 0)
        results = self.workflow_vs.similarity_search(
            query,
            k=k,
            filter={"num_steps": {"$gt": 0}}
        )
        if not results:
            return """## Workflow Memory
### What this memory is
Past task trajectories that include query context, ordered steps taken, and prior outcomes.
### How you should leverage it
- Use these workflows as reusable execution patterns for planning and tool orchestration.
- Adapt step sequences to the current task rather than copying blindly.
- Reuse successful patterns first, then adjust when task scope or constraints differ.
### Retrieved workflows
(No relevant workflows found.)"""
        content = "\n---\n".join([doc.page_content for doc in results])
        return f"""## Workflow Memory
### What this memory is
Past task trajectories that include query context, ordered steps taken, and prior outcomes.
### How you should leverage it
- Use these workflows as reusable execution patterns for planning and tool orchestration.
- Adapt step sequences to the current task rather than copying blindly.
- Reuse successful patterns first, then adjust when task scope or constraints differ.
### Retrieved workflows

{content}"""

    # ==================== TOOLBOX (Vector Store) ====================

    def write_toolbox(self, text: str, metadata: dict):
        """Store a tool definition in the toolbox."""
        self.toolbox_vs.add_texts([text], [metadata])

    def read_toolbox(self, query: str, k: int = 3) -> list[dict]:
        """Find relevant tools and return OpenAI-compatible schemas."""
        results = self.toolbox_vs.similarity_search(query, k=k)
        tools = []
        seen_tool_names: set[str] = set()
        for doc in results:
            meta = doc.metadata
            tool_name = meta.get("name", "tool")
            if tool_name in seen_tool_names:
                continue
            seen_tool_names.add(tool_name)
            # Extract parameters from metadata and convert to OpenAI format
            stored_params = meta.get("parameters", {})
            properties = {}
            required = []

            for param_name, param_info in stored_params.items():
                # Convert stored param info to OpenAI schema format
                param_type = param_info.get("type", "string")
                # Map Python types to JSON schema types
                type_mapping = {
                    "<class 'str'>": "string",
                    "<class 'int'>": "integer",
                    "<class 'float'>": "number",
                    "<class 'bool'>": "boolean",
                    "str": "string",
                    "int": "integer",
                    "float": "number",
                    "bool": "boolean"
                }
                json_type = type_mapping.get(param_type, "string")
                properties[param_name] = {"type": json_type}

                # If no default, it's required
                if "default" not in param_info:
                    required.append(param_name)

            tools.append({
                "type": "function",
                "function": {
                    "name": tool_name,
                    "description": meta.get("description", ""),
                    "parameters": {"type": "object", "properties": properties, "required": required}
                }
            })
        return tools

    # ==================== ENTITY (Vector Store) ====================

    def extract_entities(self, text: str, llm_client) -> list[dict]:
        """Use LLM to extract entities (people, places, systems) from text."""
        if not text or len(text.strip()) < 5:
            return []

        prompt = f'''Extract entities from: "{text[:500]}"
Return JSON: [{{"name": "X", "type": "PERSON|PLACE|SYSTEM", "description": "brief"}}]
If none: []'''

        try:
            response = llm_client.chat.completions.create(
                model="gpt-5",
                messages=[{"role": "user", "content": prompt}],
                max_completion_tokens=2000
            )
            result = response.choices[0].message.content.strip()

            # Extract JSON array from response
            start, end = result.find("["), result.rfind("]")
            if start == -1 or end == -1:
                return []

            parsed = json_lib.loads(result[start:end + 1])
            return [{"name": e["name"], "type": e.get("type", "UNKNOWN"), "description": e.get("description", "")}
                    for e in parsed if isinstance(e, dict) and e.get("name")]
        except:
            return []

    def write_entity(self, name: str, entity_type: str, description: str, llm_client=None, text: str = None):
        """Store an entity OR extract and store entities from text."""
        if text and llm_client:
            # Extract and store entities from text
            entities = self.extract_entities(text, llm_client)
            for e in entities:
                self.entity_vs.add_texts(
                    [f"{e['name']} ({e['type']}): {e['description']}"],
                    [{"name": e['name'], "type": e['type'], "description": e['description']}]
                )
            return entities
        else:
            # Store single entity directly
            self.entity_vs.add_texts(
                [f"{name} ({entity_type}): {description}"],
                [{"name": name, "type": entity_type, "description": description}]
            )

    def read_entity(self, query: str, k: int = 5) -> str:
        """Search for relevant entities."""
        results = self.entity_vs.similarity_search(query, k=k)
        if not results:
            return """## Entity Memory
### What this memory is
Entity-level context such as people, organizations, systems, tools, and other named items previously identified in conversations or documents.
### How you should leverage it
- Use entities to disambiguate references and maintain consistent naming.
- Preserve important attributes (roles, relationships, descriptions) across turns.
- Personalize and contextualize responses using relevant known entities.
### Retrieved entities
(No entities found.)"""

        entities = [f"• {doc.metadata.get('name', '?')}: {doc.metadata.get('description', '')}"
                    for doc in results if hasattr(doc, 'metadata')]
        entities_formatted = '\n'.join(entities)
        return f"""## Entity Memory
### What this memory is
Entity-level context such as people, organizations, systems, tools, and other named items previously identified in conversations or documents.
### How you should leverage it
- Use entities to disambiguate references and maintain consistent naming.
- Preserve important attributes (roles, relationships, descriptions) across turns.
- Personalize and contextualize responses using relevant known entities.
### Retrieved entities

{entities_formatted}"""

    # ==================== SUMMARY (Vector Store) ====================

    def write_summary(
            self,
            summary_id: str,
            full_content: str,
            summary: str,
            description: str,
            thread_id: str | None = None,
    ):
        """Store a summary with its original content."""
        metadata = {
            "id": summary_id,
            "full_content": full_content,
            "summary": summary,
            "description": description,
        }
        if thread_id is not None:
            metadata["thread_id"] = str(thread_id)
        self.summary_vs.add_texts(
            [f"{summary_id}: {description}"],
            [metadata]
        )
        return summary_id

    def read_summary_memory(self, summary_id: str, thread_id: str | None = None) -> str:
        """Retrieve a specific summary by ID (just-in-time retrieval)."""
        filters = {"id": summary_id}
        if thread_id is not None:
            filters["thread_id"] = str(thread_id)

        results = self.summary_vs.similarity_search(
            summary_id,
            k=5,
            filter=filters
        )
        if not results:
            if thread_id is not None:
                return f"Summary {summary_id} not found for thread {thread_id}."
            return f"Summary {summary_id} not found."
        doc = results[0]
        return doc.metadata.get('summary', 'No summary content.')

    def read_summary_context(self, query: str = "", k: int = 10, thread_id: str | None = None) -> str:
        """Get available summaries for context window (IDs + descriptions only)."""
        filters = None
        if thread_id is not None:
            filters = {"thread_id": str(thread_id)}
        results = self.summary_vs.similarity_search(query or "summary", k=k, filter=filters)
        if not results:
            scope_note = (
                f"(No summaries available for thread {thread_id}.)"
                if thread_id is not None
                else "(No summaries available.)"
            )
            return """## Summary Memory
### What this memory is
Compressed snapshots of older conversation windows preserved to retain long-range context.
### How you should leverage it
- Use summaries to maintain continuity when full historical messages are not in the active context window.
- Call expand_summary(id) before depending on exact quotes, fine-grained details, or step-by-step chronology.
### Available summaries
""" + scope_note

        lines = [
            "## Summary Memory",
            "### What this memory is",
            "Compressed snapshots of older conversation windows preserved to retain long-range context.",
            "### How you should leverage it",
            "- Use summaries to maintain continuity when full historical messages are not in the active context window.",
            "- Call expand_summary(id) before depending on exact quotes, fine-grained details, or step-by-step chronology.",
            "### Available summaries",
            "Use expand_summary(id) to retrieve the detailed underlying conversation."
        ]
        if thread_id is not None:
            lines.append(f"Scope: thread_id = {thread_id}")
        for doc in results:
            sid = doc.metadata.get('id', '?')
            desc = doc.metadata.get('description', 'No description')
            lines.append(f"  • [ID: {sid}] {desc}")
        return "\n".join(lines)

    def read_conversations_by_summary_id(self, summary_id: str) -> str:
        """
        Retrieve all original conversations that were summarized with a given summary_id.
        Returns conversations in order of occurrence with timestamps.

        Args:
            summary_id: The ID of the summary to expand

        Returns:
            Formatted string with original conversations and timestamps
        """
        with self.conn.cursor() as cur:
            cur.execute(f"""
                SELECT id, role, content, timestamp
                FROM {self.conversation_table}
                WHERE summary_id = %(summary_id)s
                ORDER BY timestamp ASC
            """, {"summary_id": summary_id})
            results = cur.fetchall()

        if not results:
            return f"No conversations found for summary_id: {summary_id}"

        # Format conversations with timestamps
        lines = [f"## Expanded Conversations for Summary ID: {summary_id}"]
        lines.append(f"Total messages: {len(results)}\n")

        for msg_id, role, content, timestamp in results:
            ts_str = timestamp.strftime('%Y-%m-%d %H:%M:%S') if timestamp else "Unknown"
            lines.append(f"[{ts_str}] [{role.upper()}]")
            lines.append(f"{content}")
            lines.append("")  # Empty line between messages

        return "\n".join(lines)


class StoreManager:
    """Manages all stores (vector stores and SQL tables) with getter methods for easy access.

    PG 版：5 个 OracleVS（每种记忆一张物理表）→ 5 个 PGVector collection
    （逻辑分区，共享 langchain_pg_embedding 物理表）。
    Oracle 版的 setup_hybrid_search（OracleVectorizerPreference）无 PG 直接等价物，
    需要时可用 tsvector 全文检索 + 向量自拼 RRF，此处不实现。
    """

    def __init__(self, sqlalchemy_url, embedding_function, embedding_length,
                 table_names, conversational_table, tool_log_table: str | None = None,
                 distance: str = "cosine"):
        """
        Initialize all stores.

        Args:
            sqlalchemy_url: SQLAlchemy 连接串（postgresql+psycopg://...）
            embedding_function: Embedding model to use
            embedding_length: 向量维度（必传，否则 embedding 列无维度、HNSW 建不了）
            table_names: Dict with keys: knowledge_base, workflow, toolbox, entity, summary
            conversational_table: Name of the conversational history SQL table
            tool_log_table: Name of the SQL tool log table
            distance: "cosine" 或 "euclidean"（对应课程版 DistanceStrategy）
        """
        strategy = {
            "cosine": DistanceStrategy.COSINE,
            "euclidean": DistanceStrategy.EUCLIDEAN,
        }[distance]
        self.distance = distance
        self._conversational_table = conversational_table
        self._tool_log_table = tool_log_table

        def _vs(collection):
            return PGVector(
                embeddings=embedding_function,
                collection_name=collection,
                connection=sqlalchemy_url,
                embedding_length=embedding_length,
                distance_strategy=strategy,
                use_jsonb=True,
            )

        self._knowledge_base_vs = _vs(table_names['knowledge_base'])
        self._workflow_vs = _vs(table_names['workflow'])
        self._toolbox_vs = _vs(table_names['toolbox'])
        self._entity_vs = _vs(table_names['entity'])
        self._summary_vs = _vs(table_names['summary'])

    def get_conversational_table(self):
        """Return the conversational history table name."""
        return self._conversational_table

    def get_tool_log_table(self):
        """Return the tool log table name."""
        return self._tool_log_table

    def get_knowledge_base_store(self):
        """Return the knowledge base vector store."""
        return self._knowledge_base_vs

    def get_workflow_store(self):
        """Return the workflow vector store."""
        return self._workflow_vs

    def get_toolbox_store(self):
        """Return the toolbox vector store."""
        return self._toolbox_vs

    def get_entity_store(self):
        """Return the entity vector store."""
        return self._entity_vs

    def get_summary_store(self):
        """Return the summary vector store."""
        return self._summary_vs


class ToolMetadata(BaseModel):
    """Metadata for a registered tool."""
    name: str
    description: str
    signature: str
    parameters: dict
    return_type: str


class Toolbox:
    """
    A toolbox for registering, storing, and retrieving tools with LLM-powered augmentation.

    Tools are stored with embeddings for semantic retrieval, allowing the agent to
    find relevant tools based on natural language queries.
    """

    def __init__(self, memory_manager, llm_client, embedding_function, model: str = "gpt-5"):
        """
        Initialize the Toolbox.

        Args:
            memory_manager: MemoryManager instance for storing tools
            llm_client: LLM client for augmentation
            embedding_function: Embedding function/model for creating embeddings
            model: LLM model name
        """
        self.memory_manager = memory_manager
        self.llm_client = llm_client
        self.embedding_function = embedding_function
        self.model = model
        self._tools: dict[str, Callable] = {}
        self._tools_by_name: dict[str, Callable] = {}

    def _get_embedding(self, text: str) -> list[float]:
        """
        Get the embedding for a text using the configured embedding function.
        """
        if hasattr(self.embedding_function, 'embed_query'):
            return self.embedding_function.embed_query(text)
        elif callable(self.embedding_function):
            return self.embedding_function(text)
        else:
            raise ValueError("embedding_function must be callable or have embed_query method")

    def _augment_docstring(
            self, docstring: str, source_code: str = ""
    ) -> str:
        """
        Use LLM to improve and expand a tool's docstring
        by analyzing both the original description and the
        function's source code.
        """
        if not docstring.strip() and not source_code.strip():
            return "No description provided."

        code_section = ""
        if source_code.strip():
            code_section = (
                "\n\nFunction source code:\n"
                f"```python\n{source_code}\n```"
            )

        prompt = (
            "You are a technical writer. "
            "Analyze the function's source code and its "
            "original docstring, then produce a richer, "
            "more detailed description. Include:\n"
            "1. A clear one-line summary\n"
            "2. What the function does step by step\n"
            "3. When an agent should call this function\n"
            "4. Important notes or caveats\n\n"
            f"Original docstring:\n{docstring}"
            f"{code_section}\n\n"
            "Return ONLY the improved docstring, "
            "no other text."
        )

        response = self.llm_client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_completion_tokens=2000,
        )

        return response.choices[0].message.content.strip()

    def _generate_queries(self, docstring: str, num_queries: int = 5) -> list[str]:
        """
        Generate synthetic example queries that would lead to using this tool.
        """
        prompt = f"""Based on the following tool description,
            generate {num_queries} diverse example queries
            that a user might ask when they need this tool. Make them natural and varied.

            Tool description:
            {docstring}

            Return ONLY a JSON array of strings, like: ["query1", "query2", ...]
        """

        response = self.llm_client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_completion_tokens=2000
        )

        try:
            queries = json_lib.loads(response.choices[0].message.content.strip())
            return queries if isinstance(queries, list) else []
        except json_lib.JSONDecodeError:
            # Fallback: extract queries from text
            return [response.choices[0].message.content.strip()]

    def _get_tool_metadata(self, func: Callable) -> ToolMetadata:
        """
        Extract metadata from a function for storage and retrieval.
        """
        sig = inspect.signature(func)

        # Extract parameter info
        parameters = {}
        for name, param in sig.parameters.items():
            param_info = {"name": name}
            if param.annotation != inspect.Parameter.empty:
                param_info["type"] = str(param.annotation)
            if param.default != inspect.Parameter.empty:
                param_info["default"] = str(param.default)
            parameters[name] = param_info

        # Extract return type
        return_type = "Any"
        if sig.return_annotation != inspect.Signature.empty:
            return_type = str(sig.return_annotation)

        return ToolMetadata(
            name=func.__name__,
            description=func.__doc__ or "No description",
            signature=str(sig),
            parameters=parameters,
            return_type=return_type
        )

    def _tool_exists_in_db(self, tool_name: str) -> bool:
        """Check if a tool with the given name already exists in the toolbox store."""
        try:
            collection = self.memory_manager.toolbox_vs.collection_name
            conn = self.memory_manager.conn
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT COUNT(*) FROM langchain_pg_embedding e"
                    " JOIN langchain_pg_collection c ON e.collection_id = c.uuid"
                    " WHERE c.name = %(collection)s"
                    " AND e.cmetadata->>'name' = %(name)s",
                    {"collection": collection, "name": tool_name},
                )
                return cur.fetchone()[0] > 0
        except Exception:
            # psycopg 出错后事务处于 aborted 状态，必须回滚才能继续用这个连接
            self.memory_manager.conn.rollback()
            return False

    def register_tool(
            self, func: Optional[Callable] = None, augment: bool = False
    ) -> Union[str, Callable]:
        """
        Register a function as a tool in the toolbox.

        If a tool with the same name already exists in the database,
        the callable is registered in memory but no duplicate row is
        written to the vector store.
        """

        def decorator(f: Callable) -> str:
            tool_name = f.__name__

            # Deduplication: skip DB write if tool already stored
            if self._tool_exists_in_db(tool_name):
                self._tools_by_name[tool_name] = f
                print(f"  ⏭️  Tool '{tool_name}' already in toolbox (skipping DB write)")
                return tool_name

            docstring = f.__doc__ or ""
            signature = str(inspect.signature(f))
            object_id = uuid.uuid4()
            object_id_str = str(object_id)

            if augment:
                # Use LLM to enhance the tool's discoverability
                try:
                    source_code = inspect.getsource(f)
                except (OSError, TypeError):
                    source_code = ""
                augmented_docstring = self._augment_docstring(
                    docstring, source_code
                )
                queries = self._generate_queries(augmented_docstring)

                # Create rich embedding text combining all information
                embedding_text = f"{f.__name__} {augmented_docstring} {signature} {' '.join(queries)}"
                embedding = self._get_embedding(embedding_text)

                tool_data = self._get_tool_metadata(f)
                tool_data.description = augmented_docstring  # Use augmented description

                tool_dict = {
                    "_id": object_id_str,  # Use string, not UUID object
                    "embedding": embedding,
                    "queries": queries,
                    "augmented": True,
                    **tool_data.model_dump(),
                }
            else:
                # Basic registration without augmentation
                embedding = self._get_embedding(f"{f.__name__} {docstring} {signature}")
                tool_data = self._get_tool_metadata(f)

                tool_dict = {
                    "_id": object_id_str,  # Use string, not UUID object
                    "embedding": embedding,
                    "augmented": False,
                    **tool_data.model_dump(),
                }

            # Store the tool in the toolbox memory for retrieval
            # The embedding enables semantic search to find relevant tools
            self.memory_manager.write_toolbox(
                f"{f.__name__} {docstring} {signature}",
                tool_dict
            )

            # Keep reference to the callable for execution
            self._tools[object_id_str] = f
            self._tools_by_name[f.__name__] = f  # Also store by name for easy lookup
            return object_id_str

        if func is None:
            return decorator
        return decorator(func)


# =============================================================================
# TEST DATA FOR SUMMARIZATION DEMOS
# =============================================================================

# Sample conversation about research paper search (30 messages)
# Includes: technical info, emotional context, entities, action items
SAMPLE_RESEARCH_CONVERSATION = [
    ("user",
     "Hi! I'm working on my PhD thesis about transformer architectures in NLP. I need to find recent papers on attention mechanisms."),
    ("assistant",
     "Great topic! I can help you find relevant papers. Are you looking for foundational papers like 'Attention Is All You Need' by Vaswani et al. (2017), or more recent advances from 2023-2024?"),
    ("user",
     "I've already read the Vaswani paper. I need the latest stuff - especially anything on efficient attention for long sequences."),
    ("assistant",
     "Perfect! Here are some key recent papers: 1) 'FlashAttention-2' by Dao (2023) - optimizes GPU memory for attention, 2) 'Longformer' by Beltagy et al. - uses sliding window attention, 3) 'BigBird' by Zaheer et al. - sparse attention patterns. Should I search for more?"),
    ("user", "FlashAttention sounds interesting! Can you find papers that cite it or build upon it?"),
    ("assistant",
     "Found several citing works: 'Ring Attention' extends FlashAttention for distributed training across GPUs. 'Paged Attention' from vLLM applies similar memory optimization for inference. Also, 'Flash-Decoding' focuses on the decoding phase specifically."),
    ("user",
     "This is exactly what I needed! I'm getting excited about this direction. Who are the main researchers in this space?"),
    ("assistant",
     "Key researchers include: Tri Dao (Stanford, FlashAttention author), Christopher Ré (Stanford, his advisor), Dan Fu (together.ai), and the team at Meta AI working on LLaMA optimizations. Dr. Sarah Chen at MIT is also doing great work on theoretical analysis of efficient attention."),
    ("user",
     "I should reach out to Dr. Chen - her work aligns with my theoretical focus. Can you find her recent publications?"),
    ("assistant",
     "Dr. Sarah Chen's recent papers include: 'Theoretical Bounds on Attention Complexity' (NeurIPS 2023), 'Provably Efficient Sparse Attention' (ICML 2024), and a preprint on arXiv about 'Linear Attention with Guaranteed Expressiveness'. Her email is listed as schen@mit.edu on her lab page."),
    ("user",
     "Amazing! I'm feeling much more confident about my literature review now. What about applications to code generation?"),
    ("assistant",
     "For code generation with efficient attention, check out: 'StarCoder' by BigCode - uses multi-query attention, 'CodeLlama' with grouped-query attention, and 'SantaCoder' which analyzes attention patterns in code. Also relevant: 'Repository-Level Code Generation' by Ding et al. addresses long-context code with retrieval-augmented approaches."),
    ("user",
     "Wait, retrieval-augmented approaches - that's actually closer to what I want to do! Tell me more about that direction."),
    ("assistant",
     "RAG for code is fascinating! Key papers: 'REALM' and 'RAG' by Lewis et al. (foundational), 'Retrieval-Augmented Code Generation' by Parvez et al., 'DocPrompting' which retrieves documentation, and 'ReACC' for repository-level completion. The main insight is reducing attention burden by retrieving relevant context."),
    ("user",
     "I'm now thinking my thesis should combine efficient attention WITH retrieval. Is anyone doing that combination?"),
    ("assistant",
     "Yes! 'RETRO' by DeepMind combines retrieval with transformers efficiently. 'Atlas' by Meta shows retrieval can match larger models. More recently, 'Self-RAG' adds self-reflection, and 'RAPTOR' uses hierarchical retrieval. Prof. Michael Zhang at Berkeley published 'Efficient Retrieval-Augmented Transformers' just last month."),
    ("user", "Prof. Zhang's work sounds perfect! I'm a bit nervous about reaching out to senior researchers though..."),
    ("assistant",
     "That's completely normal to feel! A few tips: 1) Read their papers thoroughly first, 2) Mention specific aspects you found interesting, 3) Share your preliminary ideas briefly, 4) Ask a specific question rather than general advice. Most researchers appreciate genuine interest from PhD students."),
    ("user",
     "Thanks, that's helpful advice. Let me refocus - can you summarize the key technical approaches we've discussed?"),
    ("assistant",
     "Here's a summary of efficient attention approaches: 1) **Sparse Attention**: Longformer, BigBird - O(n) complexity via patterns, 2) **Memory-Efficient**: FlashAttention - same computation, less memory, 3) **Linear Attention**: Performers, Linear Transformers - approximate softmax, 4) **Retrieval-Augmented**: RETRO, RAG - offload context to retrieval. Each has tradeoffs between speed, memory, and quality."),
    ("user", "What are the main evaluation benchmarks for these methods?"),
    ("assistant",
     "Key benchmarks include: 1) **Long Range Arena (LRA)** - synthetic tasks up to 16K tokens, 2) **SCROLLS** - real long-document tasks, 3) **PG-19** - book-level language modeling, 4) **CodeXGLUE** - for code tasks, 5) **Needle in a Haystack** - retrieval over long contexts. Also check perplexity on standard LM benchmarks and wall-clock time comparisons."),
    ("user", "I should probably implement some baselines. What frameworks support these efficient attention methods?"),
    ("assistant",
     "Framework support: 1) **FlashAttention** - native in PyTorch 2.0+, also xformers, 2) **HuggingFace Transformers** - many models supported, 3) **DeepSpeed** - has sparse attention ops, 4) **FairScale** - Meta's library, 5) **Triton** - for custom CUDA kernels. I'd recommend starting with HuggingFace + FlashAttention for easiest setup."),
    ("user", "Perfect! I'm feeling much more organized now. One more thing - any good survey papers I should read?"),
    ("assistant",
     "Essential surveys: 1) 'Efficient Transformers: A Survey' by Tay et al. (2022) - comprehensive overview, 2) 'A Survey on Long Text Modeling with Transformers' by Dong et al., 3) 'Scaling Laws for Neural Language Models' by Kaplan et al. - understanding model scaling, 4) 'Formal Algorithms for Transformers' by Phuong & Hutter - theoretical foundations."),
    ("user",
     "The Tay et al. survey is exactly what I needed as a starting point. Thank you so much for this deep dive!"),
    ("assistant",
     "You're welcome! To summarize your research direction: combining efficient attention (FlashAttention-style) with retrieval augmentation (RETRO-style) for code generation. Key contacts: Dr. Sarah Chen (MIT, theory), Prof. Michael Zhang (Berkeley, efficient RAG), Tri Dao (Stanford, FlashAttention). Your next steps: 1) Read the Tay survey, 2) Implement baselines with HuggingFace, 3) Reach out to researchers."),
    ("user", "One last question - what conferences should I target for submission?"),
    ("assistant",
     "Top venues for this work: 1) **NeurIPS** - broad ML, strong on efficiency, 2) **ICML** - theoretical contributions welcome, 3) **ACL/EMNLP** - if NLP-focused, 4) **ICLR** - representation learning angle, 5) **MLSys** - if systems-focused. Workshop options: EfficientNLP, Efficient Deep Learning. Deadlines typically: NeurIPS (May), ICML (Jan), ACL (Jan), ICLR (Sept)."),
    ("user",
     "I think I'll aim for NeurIPS first. This has been an incredibly productive conversation - I went from confused to having a clear research plan!"),
    ("assistant",
     "That's wonderful to hear! Your enthusiasm is contagious. Remember: thesis writing is a marathon, not a sprint. Take breaks, celebrate small wins, and don't hesitate to reach out to your advisor and the researchers we discussed. Good luck with your PhD journey - efficient attention + retrieval for code is a promising direction with real impact potential!"),
]


# =============================================================================
# COMMON TOOLS - Available across all lessons
# =============================================================================

def register_common_tools(
        toolbox,
        memory_manager,
        knowledge_base_table: str = "SEMANTIC_MEMORY",
        include_summary_tools: bool = True,
):
    """
    Register common tools that should be available across all lessons.

    This function creates and registers tools for:
    - ArXiv paper search
    - ArXiv paper fetch and save to knowledge base
    - Get current time
    - Conversation summarization and summary expansion (optional)

        Args:
        toolbox: The Toolbox instance to register tools with
        memory_manager: The MemoryManager instance for storing data
        knowledge_base_table: Name of the knowledge base table
        include_summary_tools: If True, also registers summary tools

    Returns:
        dict: Dictionary of registered tool names to their functions
    """
    from langchain_community.retrievers import ArxivRetriever
    from langchain_community.document_loaders import ArxivLoader
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from urllib.parse import urlparse
    from datetime import timezone

    # Create the ArXiv retriever
    arxiv_retriever = ArxivRetriever(
        load_max_docs=8,
        get_full_documents=False,
        doc_content_chars_max=4000
    )

    def _arxiv_id_from_entry_id(entry_id: str) -> str:
        """Convert 'http://arxiv.org/abs/2310.08560v2' -> '2310.08560v2'"""
        if not entry_id:
            return ""
        path = urlparse(entry_id).path
        return path.split("/abs/")[-1].strip("/")

    # Define the tools
    def arxiv_search_candidates(query: str, k: int = 5) -> str:
        """
        Search arXiv and return a JSON list of candidate papers with IDs + metadata.

        Output schema (JSON string):
        [
          {
            "arxiv_id": "2310.08560v2",
            "entry_id": "http://arxiv.org/abs/2310.08560v2",
            "title": "...",
            "authors": "...",
            "published": "2024-02-12",
            "abstract": "..."
          },
          ...
        ]
        """
        docs = arxiv_retriever.invoke(query)
        candidates = []
        for d in (docs or [])[:k]:
            meta = d.metadata or {}
            entry_id = meta.get("Entry ID", "")
            candidates.append({
                "arxiv_id": _arxiv_id_from_entry_id(entry_id),
                "entry_id": entry_id,
                "title": meta.get("Title", ""),
                "authors": meta.get("Authors", ""),
                "published": str(meta.get("Published", "")),
                "abstract": (d.page_content or "")[:2500],
            })
        return json_lib.dumps(candidates, ensure_ascii=False, indent=2)

    def fetch_and_save_paper_to_kb_db(
            arxiv_id: str,
            chunk_size: int = 1500,
            chunk_overlap: int = 200,
    ) -> str:
        """
        Fetch full arXiv paper text (PDF -> text) and store it into the OracleVS
        knowledge base table as chunked records.
        """
        loader = ArxivLoader(
            query=arxiv_id,
            load_max_docs=1,
            doc_content_chars_max=None,
        )
        docs = loader.load()
        if not docs:
            return f"No documents found for arXiv id: {arxiv_id}"

        doc = docs[0]
        title = (
                doc.metadata.get("Title")
                or doc.metadata.get("title")
                or f"arXiv {arxiv_id}"
        )

        entry_id = doc.metadata.get("Entry ID") or doc.metadata.get("entry_id") or ""
        published = doc.metadata.get("Published") or doc.metadata.get("published") or ""
        authors = doc.metadata.get("Authors") or doc.metadata.get("authors") or ""

        full_text = doc.page_content or ""
        if not full_text.strip():
            return f"Loaded arXiv {arxiv_id} but extracted empty text (PDF parsing issue)."

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
        chunks = splitter.split_text(full_text)

        ts_utc = datetime.now(timezone.utc).isoformat()
        metadatas = []
        for i in range(len(chunks)):
            metadatas.append({
                "source": "arxiv",
                "arxiv_id": arxiv_id,
                "title": title,
                "entry_id": entry_id,
                "published": str(published),
                "authors": str(authors),
                "chunk_id": i,
                "num_chunks": len(chunks),
                "ingested_ts_utc": ts_utc,
            })

        memory_manager.write_knowledge_base(chunks, metadatas)

        return (
            f"Saved arXiv {arxiv_id} to {knowledge_base_table}: "
            f"{len(chunks)} chunks (title: {title})."
        )

    def get_current_time(detailed: bool = False) -> str:
        """
        Returns the current time.

        Args:
            detailed: If True, returns detailed format with microseconds

        Returns:
            str: Current time as formatted string
        """
        if detailed:
            return datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        else:
            return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Register the tools with the toolbox
    toolbox.register_tool(arxiv_search_candidates, augment=False)
    toolbox.register_tool(fetch_and_save_paper_to_kb_db, augment=True)
    toolbox.register_tool(get_current_time, augment=False)

    # Store references so they can be called directly
    registered_tools = {
        "arxiv_search_candidates": arxiv_search_candidates,
        "fetch_and_save_paper_to_kb_db": fetch_and_save_paper_to_kb_db,
        "get_current_time": get_current_time,
    }

    # Optionally include summary tools in the common toolset
    if include_summary_tools:
        summary_tools = register_summary_tools(
            toolbox=toolbox,
            memory_manager=memory_manager,
            llm_client=toolbox.llm_client,
        )
        registered_tools.update(summary_tools)

    print(f"✅ Registered {len(registered_tools)} common tools: {list(registered_tools.keys())}")

    return registered_tools


# =============================================================================
# Context Window Management and Summarization
# =============================================================================

# Model token limits (for context management)
MODEL_TOKEN_LIMITS = {
    "gpt-5": 256000,
}


def calculate_context_usage(context: str, model: str = "gpt-5") -> dict:
    """Calculate context window usage as percentage."""
    estimated_tokens = len(context) // 4  # ~4 chars per token
    max_tokens = MODEL_TOKEN_LIMITS.get(model, 128000)
    percentage = (estimated_tokens / max_tokens) * 100
    return {"tokens": estimated_tokens, "max": max_tokens, "percent": round(percentage, 1)}


def monitor_context_window(context: str, model: str = "gpt-5") -> dict:
    """
    Monitor the current context window and return capacity utilization.

    Args:
        context: The current context string to measure
        model: The model being used (to determine max tokens)

    Returns:
        dict with tokens, max, percent, and status ('ok', 'warning', 'critical')
    """
    result = calculate_context_usage(context, model)

    if result['percent'] < 50:
        result['status'] = 'ok'
    elif result['percent'] < 80:
        result['status'] = 'warning'
    else:
        result['status'] = 'critical'

    return result


def summarise_context_window(
        content: str,
        memory_manager,
        llm_client,
        model: str = "gpt-5",
        thread_id: str | None = None,
) -> dict:
    """
    Summarise content using LLM and store in summary memory.
    Captures technical details, emotional context, and entity information.
    """
    cleaned = (content or "").strip()
    if not cleaned:
        return {"status": "nothing_to_summarize"}

    def _message_text(resp) -> str:
        msg = resp.choices[0].message
        payload = getattr(msg, "content", None)
        if isinstance(payload, str):
            return payload.strip()
        if isinstance(payload, list):
            parts: list[str] = []
            for item in payload:
                if isinstance(item, dict):
                    txt = item.get("text")
                    if isinstance(txt, str) and txt.strip():
                        parts.append(txt.strip())
            return "\n".join(parts).strip()
        return ""

    def _fallback_description(summary_text: str, source_text: str) -> str:
        """Create a specific, non-generic summary label when model labeling is weak."""
        for raw_line in (summary_text or source_text).splitlines():
            line = raw_line.strip().strip("-•* ").strip()
            if not line or line.startswith("###"):
                continue
            words = [w for w in line.split() if w]
            if len(words) < 4:
                continue
            label = " ".join(words[:12]).strip(" ,.;:")
            if label:
                return label
        return "Recent thread context, decisions, and open actions"

    summary_prompt = f"""You are creating durable memory for an AI research assistant.
Summarize this conversation so it can be resumed accurately later.

Output with exactly these headings:
### Technical Information
### Emotional Context
### Entities & References
### Action Items & Decisions

Rules:
- Keep concrete details (names, dates, APIs, errors, decisions).
- Separate confirmed facts from open questions where relevant.
- Do not invent information.
- Keep it concise and useful for continuation.

Conversation:
{cleaned[:6000]}"""

    response = llm_client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": summary_prompt}],
        max_completion_tokens=4000
    )
    summary = _message_text(response)

    # Retry once with a simpler prompt if the model returns empty content.
    if not summary:
        retry_prompt = f"""Summarize this conversation in <= 180 words using these headings:
### Technical Information
### Emotional Context
### Entities & References
### Action Items & Decisions

Conversation:
{cleaned[:6000]}"""
        retry = llm_client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": retry_prompt}],
            max_completion_tokens=4000
        )
        summary = _message_text(retry)

    if not summary:
        # Deterministic fallback so downstream flow never breaks.
        excerpt = cleaned[:500].replace("\n", " ").strip()
        summary = (
            "### Technical Information\n"
            f"{excerpt or '(No content provided.)'}\n\n"
            "### Emotional Context\n"
            "Not available from model output.\n\n"
            "### Entities & References\n"
            "Not available from model output.\n\n"
            "### Action Items & Decisions\n"
            "Not available from model output."
        )

    desc_prompt = f"""Create a short 8-12 word label for this summary.
Return ONLY the label.

Requirements:
- Be specific about the topic/outcome.
- Include a concrete signal (entity, task, or issue).
- Do not use generic labels like "Conversation summary".

Summary:
{summary}"""

    desc_response = llm_client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": desc_prompt}],
        max_completion_tokens=2000
    )
    description = _message_text(desc_response).strip().strip('"').strip("'")
    if not description or description.lower() in {
        "conversation summary",
        "summary",
        "chat summary",
        "thread summary",
    }:
        description = _fallback_description(summary, cleaned)

    summary_id = str(uuid.uuid4())[:8]
    memory_manager.write_summary(summary_id, cleaned, summary, description, thread_id=thread_id)

    return {"id": summary_id, "description": description, "summary": summary}


def offload_to_summary(context: str, memory_manager, llm_client, thread_id: str | None = None) -> tuple[
    str, list[dict]]:
    """
    Simple context compaction:
    - If thread_id is provided, summarize unsummarized conversation units for that thread.
    - Otherwise, summarize the provided context string.
    - Return a compact context with summary references that can be expanded on demand.
    """
    raw_context = (context or "").strip()

    if thread_id is not None:
        result = summarize_conversation(thread_id, memory_manager, llm_client)
    else:
        result = summarise_context_window(raw_context, memory_manager, llm_client, thread_id=thread_id)

    if result.get("status") == "nothing_to_summarize":
        return raw_context, []

    summary_ref = f"[Summary ID: {result['id']}] {result['description']}"
    conversation_stub = (
        "## Conversation Memory\n"
        "Older conversation content was summarized to reduce context size.\n"
        "Use Summary Memory references + expand_summary(id) for full detail."
    )

    # Replace only the conversation section, keep other memory segments intact.
    compact_context = raw_context
    if "## Conversation Memory" in compact_context:
        lines = compact_context.splitlines()
        rebuilt: list[str] = []
        in_conversation = False
        inserted_stub = False

        for line in lines:
            if line.startswith("## "):
                heading = line.strip()
                if heading == "## Conversation Memory":
                    in_conversation = True
                    if not inserted_stub:
                        if rebuilt and rebuilt[-1].strip():
                            rebuilt.append("")
                        rebuilt.extend(conversation_stub.splitlines())
                        rebuilt.append("")
                        inserted_stub = True
                    continue
                in_conversation = False

            if not in_conversation:
                rebuilt.append(line)

        compact_context = "\n".join(rebuilt).strip()
    else:
        compact_context = f"{conversation_stub}\n\n{compact_context}".strip()

    # Add summary reference(s).
    if "## Summary Memory" in compact_context:
        compact_context = f"{compact_context}\n{summary_ref}".strip()
    else:
        compact_context = (
            f"{compact_context}\n\n"
            "## Summary Memory\n"
            "Use expand_summary(id) to retrieve full underlying content.\n"
            f"{summary_ref}"
        ).strip()

    return compact_context, [result]


def summarize_conversation(thread_id: str, memory_manager, llm_client) -> dict:
    """
    Summarize all unsummarized messages in a thread and mark them.

    This function:
    1. Reads all unsummarized messages from the current thread
    2. Generates a comprehensive summary capturing technical, emotional, and entity info
    3. Stores the summary in the summary memory store
    4. Marks all conversation messages with the summary_id for later retrieval
    5. Returns the summary info that can be used to start a new context window
    """
    thread_id = str(thread_id)
    with memory_manager.conn.cursor() as cur:
        cur.execute(f"""
            SELECT id, role, content, timestamp
            FROM {memory_manager.conversation_table}
            WHERE thread_id = %(thread_id)s AND summary_id IS NULL
            ORDER BY timestamp ASC
        """, {"thread_id": thread_id})
        rows = cur.fetchall()

    if not rows:
        return {"status": "nothing_to_summarize"}

    message_ids: list[str] = []
    transcript_lines: list[str] = []
    for msg_id, role, content, timestamp in rows:
        message_ids.append(msg_id)
        ts_str = timestamp.strftime('%Y-%m-%d %H:%M:%S') if timestamp else "Unknown"
        transcript_lines.append(f"[{ts_str}] [{str(role).upper()}] {content}")

    transcript = "\n".join(transcript_lines).strip()
    if not transcript:
        return {"status": "nothing_to_summarize"}

    result = summarise_context_window(transcript, memory_manager, llm_client, thread_id=thread_id)
    if result.get("status") == "nothing_to_summarize":
        return result

    summary_id = result["id"]
    with memory_manager.conn.cursor() as cur:
        cur.executemany(f"""
            UPDATE {memory_manager.conversation_table}
            SET summary_id = %(summary_id)s
            WHERE id = %(id)s AND summary_id IS NULL
        """, [{"summary_id": summary_id, "id": msg_id} for msg_id in message_ids])
    memory_manager.conn.commit()

    result["num_messages_summarized"] = len(message_ids)

    print(f"✅ Conversation summarized: [Summary ID: {summary_id}]")
    print(f"   Description: {result['description']}")
    print(f"   Messages marked summarized: {len(message_ids)}")

    return result


def register_summary_tools(toolbox, memory_manager, llm_client):
    """
    Register summary-related tools with the toolbox.

    Args:
        toolbox: The Toolbox instance to register tools with
        memory_manager: MemoryManager instance for memory operations
        llm_client: OpenAI client for LLM calls

    Returns:
        dict of registered tool functions
    """

    def expand_summary(summary_id: str, thread_id: str = None) -> str:
        """
        Expand a summary reference to retrieve the original conversations.

        Use when you need more details from a [Summary ID: xxx] reference.
        Returns all original messages that were summarized, in chronological order with timestamps.
        """
        summary_text = memory_manager.read_summary_memory(summary_id, thread_id=thread_id)
        original_conversations = memory_manager.read_conversations_by_summary_id(summary_id)

        return f"""## Summary Context
{summary_text}

{original_conversations}"""

    def summarize_and_store(text: str = "", thread_id: str = None) -> str:
        """
        Summarize content and store it in Summary Memory.

        Preferred usage for agent continuity:
        - Provide `thread_id` to summarize unsummarized conversation units and mark them.

        Alternate usage:
        - Provide `text` to summarize arbitrary content.
        """
        if thread_id:
            result = summarize_conversation(thread_id, memory_manager, llm_client)
            if result.get("status") == "nothing_to_summarize":
                return f"No unsummarized messages found for thread {thread_id}."
            return f"Stored as [Summary ID: {result['id']}] {result['description']}"

        text = (text or "").strip()
        if not text:
            return "Provide `thread_id` (preferred) or non-empty `text` to summarize."

        result = summarise_context_window(text, memory_manager, llm_client)
        if result.get("status") == "nothing_to_summarize":
            return "No content to summarize."
        return f"Stored as [Summary ID: {result['id']}] {result['description']}"

    # Register with toolbox
    toolbox.register_tool(expand_summary, augment=True)
    toolbox.register_tool(summarize_and_store, augment=True)

    registered_tools = {
        "expand_summary": expand_summary,
        "summarize_and_store": summarize_and_store,
    }

    print(f"✅ Registered {len(registered_tools)} summary tools: {list(registered_tools.keys())}")

    return registered_tools
