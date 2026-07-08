"""重建 gold-test-set.jsonl —— 对应课程 data/gold-test-set.jsonl。

课程的 gold 集是 {question, sql} 对,sql 是「正确答案」的参考查询。这里自己写一套,
覆盖课程反复用到的几类硬查询:
  - 薪资:必须 REPLACE 掉 $ 和逗号再 CAST,否则字典序排序会出错(L2 幻觉现场)
  - 体重/身高:存成 "232 lbs" / `6' 7"`,要 SUBSTR/CAST 才能算数(L3 median weight)
  - 分组计数、按队聚合等常规查询

因为库是我们自己生成的,参考 SQL 直接在库上跑得出答案,自洽。
build() 会逐条执行校验,任何跑不通的会报错,保证 gold 集全部有效。
"""
from __future__ import annotations

import json

import pandas as pd

from . import config, db

# (question, reference_sql) —— 参考 SQL 是「正确写法」
GOLD: list[tuple[str, str]] = [
    (
        "Who is the highest paid NBA player?",
        "SELECT NAME, SALARY FROM nba_roster WHERE SALARY != '--' "
        "ORDER BY CAST(REPLACE(REPLACE(SALARY, '$', ''), ',', '') AS INTEGER) DESC "
        "LIMIT 1;",
    ),
    (
        "What is the median weight in the NBA?",
        "SELECT CAST(SUBSTR(WT, 1, INSTR(WT, ' ')) AS INTEGER) AS w FROM nba_roster "
        "ORDER BY w LIMIT 1 OFFSET (SELECT COUNT(*) FROM nba_roster) / 2;",
    ),
    (
        "What is the average age of all players in the NBA?",
        "SELECT AVG(AGE) FROM nba_roster;",
    ),
    (
        "What is the median age of the Chicago Bulls?",
        "SELECT AGE FROM nba_roster WHERE Team = 'Chicago Bulls' ORDER BY AGE "
        "LIMIT 1 OFFSET (SELECT COUNT(*) FROM nba_roster WHERE Team = 'Chicago Bulls') / 2;",
    ),
    (
        "Which college has produced the most NBA players?",
        "SELECT COLLEGE, COUNT(*) AS c FROM nba_roster WHERE COLLEGE != '--' "
        "GROUP BY COLLEGE ORDER BY c DESC LIMIT 1;",
    ),
    (
        "How many players in the NBA went to Duke?",
        "SELECT COUNT(*) FROM nba_roster WHERE COLLEGE = 'Duke';",
    ),
    (
        "What is the average salary of the Los Angeles Lakers?",
        "SELECT AVG(CAST(REPLACE(REPLACE(SALARY, '$', ''), ',', '') AS INTEGER)) "
        "FROM nba_roster WHERE Team = 'Los Angeles Lakers' AND SALARY != '--';",
    ),
    (
        "How many players are on the Boston Celtics roster?",
        "SELECT COUNT(*) FROM nba_roster WHERE Team = 'Boston Celtics';",
    ),
    (
        "Which team has the highest average salary?",
        "SELECT Team, AVG(CAST(REPLACE(REPLACE(SALARY, '$', ''), ',', '') AS INTEGER)) AS avg_sal "
        "FROM nba_roster WHERE SALARY != '--' GROUP BY Team ORDER BY avg_sal DESC LIMIT 1;",
    ),
    (
        "What is the average age of the Golden State Warriors?",
        "SELECT AVG(AGE) FROM nba_roster WHERE Team = 'Golden State Warriors';",
    ),
    (
        "How many centers (POS = 'C') are there in the NBA?",
        "SELECT COUNT(*) FROM nba_roster WHERE POS = 'C';",
    ),
    (
        "What is the average weight of players in the NBA?",
        "SELECT AVG(CAST(SUBSTR(WT, 1, INSTR(WT, ' ')) AS INTEGER)) FROM nba_roster;",
    ),
    (
        "Who is the oldest player in the NBA?",
        "SELECT NAME, AGE FROM nba_roster ORDER BY AGE DESC LIMIT 1;",
    ),
    (
        "What is the 75th percentile salary in the NBA?",
        "SELECT CAST(REPLACE(REPLACE(SALARY, '$', ''), ',', '') AS INTEGER) AS s "
        "FROM nba_roster WHERE SALARY != '--' ORDER BY s "
        "LIMIT 1 OFFSET (SELECT COUNT(*) FROM nba_roster WHERE SALARY != '--') * 3 / 4;",
    ),
    (
        "How many players have a salary above 20 million dollars?",
        "SELECT COUNT(*) FROM nba_roster WHERE SALARY != '--' "
        "AND CAST(REPLACE(REPLACE(SALARY, '$', ''), ',', '') AS INTEGER) > 20000000;",
    ),
]


def build() -> None:
    conn = db.engine()
    n_ok = 0
    with open(config.GOLD_TEST_SET, "w") as f:
        for question, sql in GOLD:
            # 逐条校验:参考 SQL 必须能在库上跑通,否则 gold 集就是坏的
            try:
                res = pd.read_sql(sql, con=conn)
            except Exception as e:  # noqa: BLE001
                raise SystemExit(f"[gold] 参考 SQL 跑不通!\n  Q: {question}\n  SQL: {sql}\n  {e}")
            f.write(json.dumps({"question": question, "sql": sql}) + "\n")
            n_ok += 1
    conn.close()
    print(f"[gold] {n_ok} 条参考查询全部校验通过 -> {config.GOLD_TEST_SET}")


if __name__ == "__main__":
    build()
