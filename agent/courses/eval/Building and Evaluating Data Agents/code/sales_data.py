"""本地数据层：替代课程的 Snowflake sales_intelligence 数据库。

课程数据在 Snowflake (deals 表 + 销售会议纪要 + Cortex Search 索引), 本地不可得,
此处按课程叙事合成同构小数据集:
- 结构化: sales_deals 表 (sqlite) —— 客户/行业/金额/状态/负责人
- 非结构化: 5 篇销售会议纪要 —— 刻意埋一个共同主题(客户普遍关注数据合规/监管),
  支撑课程的两个演示 query:「pending deals + 监管变化」「会议纪要共同主题」

检索: fastembed 本地 embedding (BAAI/bge-small-en-v1.5, 纯 CPU) + 余弦相似度。
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import numpy as np

_CODE_DIR = Path(__file__).resolve().parent
DB_PATH = _CODE_DIR / "sales_intelligence.sqlite"

DEALS = [
    # (deal_id, customer, industry, deal_value_usd, status, stage, owner, close_quarter)
    ("D001", "Meridian Bank", "Financial Services", 1_250_000, "won", "closed", "Alice", "2025Q4"),
    ("D002", "Northwind Insurance", "Insurance", 860_000, "pending", "negotiation", "Bob", "2026Q1"),
    ("D003", "Helios Energy", "Energy", 2_400_000, "won", "closed", "Alice", "2025Q3"),
    ("D004", "Cascade Health", "Healthcare", 1_780_000, "pending", "proposal", "Carol", "2026Q2"),
    ("D005", "Atlas Retail", "Retail", 430_000, "lost", "closed", "Bob", "2025Q4"),
    ("D006", "Quantum Capital", "Financial Services", 3_100_000, "pending", "negotiation", "Alice", "2026Q1"),
    ("D007", "Polar Logistics", "Logistics", 640_000, "won", "closed", "Carol", "2025Q4"),
    ("D008", "Vertex Pharma", "Healthcare", 1_950_000, "won", "closed", "Bob", "2025Q2"),
]

MEETING_NOTES = {
    "Meridian Bank": (
        "Meeting with Meridian Bank (2025-11-12). Attendees: CTO, Head of Risk. "
        "They are happy with the analytics platform rollout. Main concern raised: upcoming "
        "financial data-residency regulation may require all customer data to stay in-region. "
        "They asked whether our platform supports regional data pinning. Follow-up: send "
        "compliance whitepaper."
    ),
    "Northwind Insurance": (
        "Meeting with Northwind Insurance (2025-12-03). Attendees: VP Claims, IT Director. "
        "Deal is pending legal review. Their compliance team flagged the new insurance "
        "solvency reporting rules; they need audit trails for every automated decision. "
        "They want SOC2 Type II evidence before signing. Positive on product fit."
    ),
    "Cascade Health": (
        "Meeting with Cascade Health (2026-01-08). Attendees: CIO, Compliance Officer. "
        "Proposal under review. Key topic: HIPAA and the new state-level health data privacy "
        "act - they must demonstrate patient data anonymization end to end. Asked for a "
        "de-identification feature demo. Timeline pushed to Q2 due to regulatory audit."
    ),
    "Quantum Capital": (
        "Meeting with Quantum Capital (2026-01-15). Attendees: Managing Partner, Head of Ops. "
        "Largest pending deal. They operate across US/EU; the EU AI Act and SEC algorithmic "
        "trading disclosure rules are top of mind. They require model decision logging and "
        "explainability reports. Negotiating a phased rollout starting with the compliance module."
    ),
    "Helios Energy": (
        "Meeting with Helios Energy (2025-09-20). Attendees: VP Engineering. Post-sale check-in. "
        "Rollout is on track. They mentioned an upcoming grid-emission reporting mandate will expand "
        "their data pipeline needs next year. Opportunity for an upsell on the reporting add-on."
    ),
}


def build_db(db_path: Path = DB_PATH) -> Path:
    """建 (或重建) 本地 sales_deals sqlite 表"""
    conn = sqlite3.connect(db_path)
    conn.execute("DROP TABLE IF EXISTS sales_deals")
    conn.execute(
        """CREATE TABLE sales_deals (
            deal_id TEXT PRIMARY KEY, customer TEXT, industry TEXT,
            deal_value_usd INTEGER, status TEXT, stage TEXT,
            owner TEXT, close_quarter TEXT)"""
    )
    conn.executemany("INSERT INTO sales_deals VALUES (?,?,?,?,?,?,?,?)", DEALS)
    conn.commit()
    conn.close()
    return db_path


def run_sql(sql: str, db_path: Path = DB_PATH):
    """执行 SQL 返回 (列名, 行)"""
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.execute(sql)
        cols = [d[0] for d in cur.description] if cur.description else []
        rows = cur.fetchall()
        return cols, rows
    finally:
        conn.close()


TABLE_SCHEMA = (
    "Table sales_deals(deal_id TEXT, customer TEXT, industry TEXT, "
    "deal_value_usd INTEGER, status TEXT ('won'|'pending'|'lost'), "
    "stage TEXT, owner TEXT, close_quarter TEXT)"
)


class NotesIndex:
    """会议纪要的本地向量检索 (替代 Cortex Search)"""

    def __init__(self):
        from fastembed import TextEmbedding

        import os

        self._model = TextEmbedding(
            "BAAI/bge-small-en-v1.5",
            cache_dir=os.getenv("FASTEMBED_CACHE_PATH"),
        )
        self._ids = list(MEETING_NOTES.keys())
        self._docs = [MEETING_NOTES[k] for k in self._ids]
        self._vecs = np.array(list(self._model.embed(self._docs)))
        self._vecs = self._vecs / np.linalg.norm(self._vecs, axis=1, keepdims=True)

    def search(self, query: str, k: int = 3):
        q = np.array(list(self._model.embed([query])))[0]
        q = q / np.linalg.norm(q)
        sims = self._vecs @ q
        order = np.argsort(-sims)[:k]
        return [
            {"customer": self._ids[i], "note": self._docs[i], "score": float(sims[i])}
            for i in order
        ]
