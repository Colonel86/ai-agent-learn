"""重建课程的 nba_roster 数据库。

课程平台预置了 nba_roster.db,但它不随 markdown 发布。这里确定性地合成一个
结构/格式完全一致的 roster:
  - SALARY 存成 "$9,945,830"(带 $ 和逗号,null="--")
  - WT   存成 "232 lbs"
  - HT   存成 `6' 7"`
  - Jersey null="NA",COLLEGE null="--"
这些「脏字符串」格式是课程幻觉演示的根源(模型不 REPLACE 掉 $/逗号直接 CAST 就出错),
必须原样保留,否则 L2/L3 的教学点就没了。

gold-test-set 的参考 SQL 直接在这个库上跑得出答案 —— 自洽,不依赖任何外部真值。
"""
from __future__ import annotations

import random
import sqlite3
from pathlib import Path

from . import config

TEAMS = [
    "Atlanta Hawks", "Boston Celtics", "Brooklyn Nets", "Charlotte Hornets",
    "Chicago Bulls", "Cleveland Cavaliers", "Dallas Mavericks", "Denver Nuggets",
    "Detroit Pistons", "Golden State Warriors", "Houston Rockets", "Indiana Pacers",
    "LA Clippers", "Los Angeles Lakers", "Memphis Grizzlies", "Miami Heat",
    "Milwaukee Bucks", "Minnesota Timberwolves", "New Orleans Pelicans",
    "New York Knicks", "Oklahoma City Thunder", "Orlando Magic", "Philadelphia 76ers",
    "Phoenix Suns", "Portland Trail Blazers", "Sacramento Kings", "San Antonio Spurs",
    "Toronto Raptors", "Utah Jazz", "Washington Wizards",
]
POSITIONS = ["PG", "SG", "SF", "PF", "C"]
COLLEGES = [
    "Duke", "Kentucky", "Michigan", "Kansas", "North Carolina", "UCLA", "Gonzaga",
    "Villanova", "Arizona", "Texas", "Florida", "Michigan State", "Connecticut",
    "Memphis", "Washington", "USC", "Alabama", "Baylor", "Auburn", "LSU",
]
FIRST = [
    "James", "Otto", "Chris", "Kevin", "Jaylen", "Marcus", "Tyler", "Devin",
    "Jordan", "Malik", "Cameron", "Anthony", "Trey", "Derrick", "Isaiah",
    "Brandon", "Jalen", "Kyle", "Damian", "Zion", "Luka", "Nikola", "Jimmy",
    "Bradley", "Fred", "Gary", "Terrence", "Josh", "Mike", "Aaron",
]
LAST = [
    "Porter Jr.", "Johnson", "Williams", "Brown", "Davis", "Green", "Smith",
    "Jones", "Miller", "Wilson", "Moore", "Taylor", "Anderson", "Thomas",
    "Jackson", "White", "Harris", "Martin", "Thompson", "Young", "Walker",
    "Allen", "King", "Wright", "Scott", "Hill", "Adams", "Baker", "Nelson",
    "Carter",
]


def _height() -> str:
    feet = random.choice([5, 6, 6, 6, 6, 7])
    inches = random.randint(0, 11)
    return f"{feet}' {inches}\""


def _salary(rng: random.Random) -> str:
    # ~12% 球员薪资缺失,存成 "--"(复现 null 处理)
    if rng.random() < 0.12:
        return "--"
    val = rng.randint(1_000_000, 52_000_000)
    return "$" + f"{val:,}"


def build(seed: int = 42, out_db: Path | None = None) -> Path:
    """确定性生成 roster,写入 sqlite。返回 db 路径。"""
    out_db = out_db or config.DB_PATH
    rng = random.Random(seed)

    rows = []
    for team in TEAMS:
        n = rng.randint(4, 6)  # 每队 4~6 人,总计 ~150
        for _ in range(n):
            name = f"{rng.choice(FIRST)} {rng.choice(LAST)}"
            jersey = "NA" if rng.random() < 0.05 else str(rng.randint(0, 55))
            pos = rng.choice(POSITIONS)
            age = rng.randint(19, 39)
            # 用 rng 保证确定性(_height 用全局 random,这里改用 rng)
            feet = rng.choice([5, 6, 6, 6, 6, 7])
            inches = rng.randint(0, 11)
            ht = f"{feet}' {inches}\""
            wt = f"{rng.randint(170, 290)} lbs"
            college = "--" if rng.random() < 0.15 else rng.choice(COLLEGES)
            salary = _salary(rng)
            rows.append((team, name, jersey, pos, age, ht, wt, college, salary))

    out_db.parent.mkdir(parents=True, exist_ok=True)
    if out_db.exists():
        out_db.unlink()
    conn = sqlite3.connect(out_db)
    cur = conn.cursor()
    cur.execute(
        """CREATE TABLE nba_roster (
            Team TEXT, NAME TEXT, Jersey TEXT, POS TEXT, AGE INT,
            HT TEXT, WT TEXT, COLLEGE TEXT, SALARY TEXT
        )"""
    )
    cur.executemany(
        "INSERT INTO nba_roster VALUES (?,?,?,?,?,?,?,?,?)", rows
    )
    conn.commit()

    # 顺带导出 CSV,方便非 LLM 地检查数据(对应 climate_analyzer 的做法)
    import csv

    with open(config.ROSTER_CSV, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(
            ["Team", "NAME", "Jersey", "POS", "AGE", "HT", "WT", "COLLEGE", "SALARY"]
        )
        w.writerows(rows)

    count = cur.execute("SELECT COUNT(*) FROM nba_roster").fetchone()[0]
    conn.close()
    print(f"[db] 写入 {count} 行 -> {out_db}")
    print(f"[db] CSV 导出 -> {config.ROSTER_CSV}")
    return out_db


def engine() -> sqlite3.Connection:
    """返回 sqlite 连接(课程里叫 engine)。库不存在则先构建。"""
    if not config.DB_PATH.exists():
        build()
    return sqlite3.connect(config.DB_PATH)


if __name__ == "__main__":
    build()
