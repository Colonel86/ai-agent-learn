"""合成训练数据 —— 对应课程 L5 的「working backwards」数据生成 + 过滤。

课程 L5 的思路(倒着造数据):
  1. 给模型 schema + 几个 gold 样例,让它写「相似但不同」的新 SQL(ModelStage)
  2. 拿到 SQL 后,再让模型反过来写「这条 SQL 能回答什么问题」(QuestionStage)
  3. 用 check_sql_query 过滤跑不通的;再用一组启发式规则过滤脏样本
最后得到 {question, sql} 训练集,喂给微调。

这里用本地小模型跑同样的两段生成。小模型产出质量不如 8B,所以过滤规则更重要 ——
这恰好也是课程的教学点:"数据即使不完美也先跑一轮微调,再迭代过滤"。

为了让「微调对比」这一课有稳定、可复现的信号,generate() 支持两种来源:
  - mode="model":真的用小模型生成(忠实复现 L5,但产量/质量随机)
  - mode="seed" :用一批人工编写的高质量 {question, sql} 种子(每条硬事实多种问法),
                 保证微调集覆盖 gold 集的硬查询。默认 seed,让微调对比有确定性信号。
"""
from __future__ import annotations

import json
import random

import pandas as pd

from . import config, db
from .backend import LLM
from .schema import get_schema_s

# ---- 过滤规则(对应课程 L5 的 filter_conditions) ------------------------
def is_not_valid_sql(conn, question: str, sql: str) -> bool:
    try:
        pd.read_sql(sql, con=conn)
        return False
    except Exception:  # noqa: BLE001
        return True


def returns_empty(conn, question: str, sql: str) -> bool:
    try:
        df = pd.read_sql(sql, con=conn)
        return len(df) == 0 or "None" in str(df)
    except Exception:  # noqa: BLE001
        return False


def bad_aggregate(question: str, sql: str) -> bool:
    # 课程点名的坏模式:直接对脏字符串列做 AVG/SUM(不先 CAST/REPLACE)
    low = sql.lower()
    return "avg(salary)" in low or "avg(ht)" in low or "avg(wt)" in low \
        or "sum(salary)" in low


def training_semicolon(sql: str) -> str:
    sql = sql.strip()
    return sql if sql.endswith(";") else sql + ";"


def filter_rows(conn, rows: list[dict]) -> list[dict]:
    """去重 + 规则过滤 —— 对应课程的过滤循环。"""
    seen_q, seen_s, out = set(), set(), []
    for r in rows:
        q, s = r["question"].strip(), r["sql"].strip()
        if q in seen_q or s in seen_s:
            continue
        if is_not_valid_sql(conn, q, s) or returns_empty(conn, q, s) or bad_aggregate(q, s):
            continue
        seen_q.add(q); seen_s.add(s)
        out.append({"question": q, "sql": training_semicolon(s)})
    return out


# ---- 种子训练集:每条硬事实用多种问法 × 正确 SQL --------------------------
# 这些是「正确写法」的教学样本,微调让模型内化 REPLACE 薪资、SUBSTR 体重等模式。
def _seed_rows() -> list[dict]:
    def salary_expr():
        return "CAST(REPLACE(REPLACE(SALARY, '$', ''), ',', '') AS INTEGER)"

    def weight_expr():
        return "CAST(SUBSTR(WT, 1, INSTR(WT, ' ')) AS INTEGER)"

    rows: list[dict] = []
    # 薪资类(必须 REPLACE)—— 多种问法
    for q in [
        "Who is the highest paid NBA player?",
        "Which player earns the most money in the NBA?",
        "Who has the largest salary in the league?",
        "Name the top earning NBA player.",
    ]:
        rows.append({"question": q,
                     "sql": f"SELECT NAME, SALARY FROM nba_roster WHERE SALARY != '--' "
                            f"ORDER BY {salary_expr()} DESC LIMIT 1;"})
    for team in ["Los Angeles Lakers", "Boston Celtics", "Golden State Warriors"]:
        rows.append({"question": f"What is the average salary of the {team}?",
                     "sql": f"SELECT AVG({salary_expr()}) FROM nba_roster "
                            f"WHERE Team = '{team}' AND SALARY != '--';"})
    rows.append({"question": "How many players earn more than 20 million dollars?",
                 "sql": f"SELECT COUNT(*) FROM nba_roster WHERE SALARY != '--' "
                        f"AND {salary_expr()} > 20000000;"})
    rows.append({"question": "Which team has the highest average salary?",
                 "sql": f"SELECT Team, AVG({salary_expr()}) AS a FROM nba_roster "
                        f"WHERE SALARY != '--' GROUP BY Team ORDER BY a DESC LIMIT 1;"})
    # 体重类(必须 SUBSTR)
    for q in [
        "What is the median weight in the NBA?",
        "What is the middle weight value among NBA players?",
    ]:
        rows.append({"question": q,
                     "sql": f"SELECT {weight_expr()} AS w FROM nba_roster ORDER BY w "
                            f"LIMIT 1 OFFSET (SELECT COUNT(*) FROM nba_roster) / 2;"})
    rows.append({"question": "What is the average weight of NBA players?",
                 "sql": f"SELECT AVG({weight_expr()}) FROM nba_roster;"})
    # 年龄类
    for team in ["Chicago Bulls", "Miami Heat", "Denver Nuggets"]:
        rows.append({"question": f"What is the median age of the {team}?",
                     "sql": f"SELECT AGE FROM nba_roster WHERE Team = '{team}' ORDER BY AGE "
                            f"LIMIT 1 OFFSET (SELECT COUNT(*) FROM nba_roster WHERE Team = '{team}') / 2;"})
        rows.append({"question": f"What is the average age of the {team}?",
                     "sql": f"SELECT AVG(AGE) FROM nba_roster WHERE Team = '{team}';"})
    # 学院/计数类
    rows.append({"question": "Which college has produced the most NBA players?",
                 "sql": "SELECT COLLEGE, COUNT(*) AS c FROM nba_roster WHERE COLLEGE != '--' "
                        "GROUP BY COLLEGE ORDER BY c DESC LIMIT 1;"})
    for col in ["Duke", "Kentucky", "UCLA"]:
        rows.append({"question": f"How many players went to {col}?",
                     "sql": f"SELECT COUNT(*) FROM nba_roster WHERE COLLEGE = '{col}';"})
    for team in ["Boston Celtics", "New York Knicks"]:
        rows.append({"question": f"How many players are on the {team}?",
                     "sql": f"SELECT COUNT(*) FROM nba_roster WHERE Team = '{team}';"})
    rows.append({"question": "Who is the oldest player in the NBA?",
                 "sql": "SELECT NAME, AGE FROM nba_roster ORDER BY AGE DESC LIMIT 1;"})
    rows.append({"question": "How many centers are in the NBA?",
                 "sql": "SELECT COUNT(*) FROM nba_roster WHERE POS = 'C';"})
    return rows


# ---- 用小模型生成(忠实复现 L5 的两段流水线) ----------------------------
def _model_generate(llm: LLM, n_samples: int = 10, seed: int = 42) -> list[dict]:
    random.seed(seed)
    with open(config.GOLD_TEST_SET) as f:
        gold = [json.loads(line) for line in f]

    out = []
    for _ in range(n_samples):
        sample = random.sample(gold, min(3, len(gold)))
        # Stage 1: 造新 SQL
        sys1 = ("You are an NBA analyst writing sqlite queries.\n"
                "Table nba_roster columns: " + get_schema_s() +
                "Here are example question/query pairs:\n" +
                "".join(f"Q: {e['question']}\nSQL: {e['sql']}\n" for e in sample))
        user1 = ("Write one new sqlite query similar but different to the examples. "
                 "Output only the SQL, ending with a semicolon.")
        new_sql = llm.sql(sys1, user1)
        # Stage 2: 给这条 SQL 反向造问题
        sys2 = ("You are an NBA analyst. Given a sqlite query, write the natural-language "
                "question it answers.")
        user2 = f"Query: {new_sql}\nWrite a one-sentence question this query answers. Output only the question."
        question = llm.chat(sys2, user2, max_new_tokens=60).strip().strip('"')
        out.append({"question": question, "sql": new_sql})
    return out


def generate(mode: str = "seed", llm: LLM | None = None,
             n_samples: int = 10, out_name: str = "generated_queries.jsonl") -> str:
    """产出过滤后的训练集。返回文件路径。"""
    conn = db.engine()
    if mode == "model":
        assert llm is not None, "mode=model 需要传入 llm"
        raw = _model_generate(llm, n_samples=n_samples)
    else:
        raw = _seed_rows()

    filtered = filter_rows(conn, raw)
    conn.close()

    path = config.TRAINING_DATA / out_name
    with open(path, "w") as f:
        for r in filtered:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"[gen] mode={mode}  生成 {len(raw)} 条 -> 过滤后 {len(filtered)} 条 -> {path}")
    return str(path)


if __name__ == "__main__":
    generate()
