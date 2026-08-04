"""L3 · 建立可量化的评估体系 (本地化: DeepSeek + 纯 Python 评估管线)

课程原版用 lamini 的 GenerationPipeline(异步 QueryStage+ScoreStage);
本地化为普通循环, 指标一致:
- 有效 SQL %  (能执行)
- 正确 SQL %  (结果与 gold 一致: 精确匹配 或 LLM judge 判相似)

运行: cd L3 && ../.venv/bin/python main.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from local_stack import banner, ds_generate, ds_json, run_sql

LESSON_DIR = Path(__file__).resolve().parent
DB = LESSON_DIR / "nba_roster.db"
GOLD = LESSON_DIR / "data/gold-test-set.jsonl"

SCHEMA = """\
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

SYSTEM = (
    "You are an NBA analyst with 15 years of experience writing complex SQL queries.\n"
    "Consider the nba_roster table with the following schema:\n"
    f"{SCHEMA}\n"
    "Write a sqlite query to answer the following question. "
    'Reply with a JSON object: {"sqlite_query": "..."}'
)


def gen_sql(question: str) -> str:
    return ds_json(question, SYSTEM)["sqlite_query"]


def judge_similar(df_str: str, ref_str: str) -> bool:
    system = (
        "Compare the following two dataframes. They are similar if they are almost identical, "
        "or if they convey the same information about the nba_roster dataset. "
        'Respond with valid JSON {"explanation": str, "similar": true/false}'
    )
    user = (
        f"========== Dataframe 1 =========\n{df_str.lower()}\n\n"
        f"========== Dataframe 2 =========\n{ref_str.lower()}\n"
        "Can you tell me if these dataframes are similar?"
    )
    try:
        return bool(ds_json(user, system)["similar"])
    except Exception:
        return False


def main():
    banner("①", "单点诊断: median weight")
    question = "What is the median weight in the NBA?"
    sql = gen_sql(question)
    print(f"  生成: {sql}")
    try:
        print(run_sql(DB, sql).to_string())
    except Exception as e:
        print(f"  执行失败: {e}")
    correct_sql = (
        "select CAST(SUBSTR(WT, 1, INSTR(WT,' ')) as INTEGER) as percentile "
        "from nba_roster order by percentile limit 1 offset (select count(*) from nba_roster)/2-1"
    )
    print(f"\n  标准答案: {correct_sql}")
    print(run_sql(DB, correct_sql).to_string())

    banner("②", f"批量评估: gold-test-set 20 条, 双指标")
    gold = [json.loads(l) for l in GOLD.read_text().splitlines() if l.strip()]
    valid = correct = 0
    failures = []
    for i, dp in enumerate(gold):
        q = dp["question"]
        try:
            sql = gen_sql(q)
            df = run_sql(DB, sql)
            valid += 1
        except Exception as e:
            failures.append((q, f"执行失败: {str(e)[:60]}"))
            print(f"  [{i+1:2d}] ✗(invalid) {q[:50]}")
            continue
        try:
            ref_df = run_sql(DB, dp["sql"])
        except Exception:
            ref_df = None
        exact = ref_df is not None and str(df).lower() == str(ref_df).lower()
        ok = exact or (ref_df is not None and judge_similar(str(df), str(ref_df)))
        if ok:
            correct += 1
            print(f"  [{i+1:2d}] ✓{'(exact)' if exact else '(judge)'} {q[:50]}")
        else:
            failures.append((q, f"错误结果: {str(df.head(1)).strip()[:60]}"))
            print(f"  [{i+1:2d}] ✗(wrong)  {q[:50]}")

    banner("③", "评估汇总")
    n = len(gold)
    print(f"  有效 SQL: {valid}/{n} ({valid/n:.0%})   正确 SQL: {correct}/{n} ({correct/n:.0%})")
    if failures:
        print("\n  失败样本 (这就是 L5 数据生成要瞄准的靶子):")
        for q, why in failures[:5]:
            print(f"  - {q[:56]}\n      {why}")

    banner("④", "本课结论")
    print("""  评估体系三件套: gold set(带参考 SQL 与答案) + 可执行性指标 + 结果等价判定。
  「正确率」必须落在能自动重跑的数字上, 后面每级优化(prompt/微调)才能对比。
  失败样本清单 = 改进的靶子, L5 的数据生成就从这里 working backwards""")


if __name__ == "__main__":
    main()
