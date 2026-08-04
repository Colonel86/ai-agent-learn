"""L2 · 搭 SQL Agent 并诊断幻觉 (本地化: DeepSeek + 本地 nba_roster.db)

核心现场: nba_roster 的数值列全是脏字符串 (SALARY="$4,556,983", WT="232 lbs")。
- 贫乏 schema(只有列名类型) -> 模型按"分布上最顺"的方式直接 ORDER BY SALARY,
  字符串排序给出**看起来对、实际错**的答案 (silently wrong, 最危险的幻觉)
- 富 schema(带示例值) -> 模型知道要 REPLACE+CAST, 才有机会写对

运行: cd L2 && ../.venv/bin/python main.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from local_stack import banner, ds_generate, run_sql

LESSON_DIR = Path(__file__).resolve().parent
DB = LESSON_DIR / "nba_roster.db"

POOR_SCHEMA = """\
0|Team|TEXT
1|NAME|TEXT
2|Jersey|TEXT
3|POS|TEXT
4|AGE|INT
5|HT|TEXT
6|WT|TEXT
7|COLLEGE|TEXT
8|SALARY|TEXT
"""

RICH_SCHEMA = """\
0|Team|TEXT eg. "Toronto Raptors"
1|NAME|TEXT eg. "Otto Porter Jr."
2|Jersey|TEXT eg. "0" and when null has a value "NA"
3|POS|TEXT eg. "PF"
4|AGE|INT eg. "22" in years
5|HT|TEXT eg. `6' 7"` or `6' 10"`
6|WT|TEXT eg. "232 lbs"
7|COLLEGE|TEXT eg. "Michigan" and when null has a value "--"
8|SALARY|TEXT eg. "$9,945,830" and when null has a value "--"
"""

QUESTION = "Who is the highest paid NBA player?"


def make_system(schema: str) -> str:
    return (
        "You are an NBA analyst with 15 years of experience writing complex SQL queries.\n"
        "Consider the nba_roster table with the following schema:\n"
        f"{schema}\n"
        "Write a sqlite query to answer the following question. "
        "Reply with ONLY the SQL, no markdown, no explanation."
    )


def gen_and_run(schema: str, label: str):
    sql = ds_generate(QUESTION, make_system(schema), max_tokens=300)
    sql = sql.strip().replace("```sql", "").replace("```", "").strip()
    print(f"\n  [{label}] 生成的 SQL:\n  {sql}")
    try:
        df = run_sql(DB, sql)
        print(f"  执行结果:\n{df.head(3).to_string()}")
        return df
    except Exception as e:
        print(f"  执行失败: {e}")
        return None


def main():
    banner("①", "看数据: 数值列全是脏字符串 (幻觉现场的根源)")
    print(run_sql(DB, "SELECT NAME, WT, SALARY FROM nba_roster LIMIT 4").to_string())

    banner("②", "贫乏 schema: 只有列名和类型")
    gen_and_run(POOR_SCHEMA, "poor schema")
    print("""
  ⚠ 细看生成的 SQL: 实测 deepseek 常只 REPLACE 掉 $ 忘了逗号 ——
  CAST("51,915,615") 在逗号处截断得到 51, 等于按"百万位"排序。
  这题碰巧对(Curry 的百万位最大), 换成 percentile 类问题立刻错 ——
  比课程原版(字符串排序)更隐蔽的 silently wrong""")

    banner("③", "富 schema: 带示例值 (模型才知道 SALARY 长什么样)")
    gen_and_run(RICH_SCHEMA, "rich schema")

    banner("④", "标准答案对照 (REPLACE 去 $ 和逗号后 CAST)")
    correct = (
        "SELECT NAME, SALARY FROM nba_roster WHERE SALARY != '--' "
        "ORDER BY CAST(REPLACE(REPLACE(SALARY,'$',''),',','') AS INTEGER) DESC LIMIT 1"
    )
    print(f"  {correct}")
    print(run_sql(DB, correct).to_string())

    banner("⑤", "本课结论")
    print("""  最危险的幻觉不是报错, 是 silently wrong: 残缺的 CAST 也能"碰巧答对"。
  第一级(最便宜的)准确率手段: 把领域知识写进 prompt —— schema 带示例值。
  但 prompt 装不下所有事实, 这就是后面评估(L3)和微调(L5)的出场理由""")


if __name__ == "__main__":
    main()
