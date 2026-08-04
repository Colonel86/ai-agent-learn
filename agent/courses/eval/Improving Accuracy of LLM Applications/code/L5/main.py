"""L5 · 生成训练数据与微调迭代闭环 (本地化: DeepSeek 数据生成 + 本地 LoRA 衔接)

课程流程 "working backwards":
① 从 gold (question, sql) 出发, 让模型生成"相似但不同"的新 SQL
② 反向为新 SQL 生成 question
③ 可执行性过滤 -> 训练数据 jsonl
④ llm.train() 派发 Lamini 服务端微调 -> 本地化: 衔接 ../projects/nba_sql_tuner
   (本地 LoRA 真跑 finetune vs memory tuning, CPU ~10 分钟)

运行: cd L5 && ../.venv/bin/python main.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from local_stack import banner, ds_json, run_sql

LESSON_DIR = Path(__file__).resolve().parent
DB = LESSON_DIR / "nba_roster.db"
GOLD = LESSON_DIR / "data/gold-test-set.jsonl"
OUT = LESSON_DIR / "data/training_data/generated_queries_local.jsonl"

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

GEN_SYSTEM = (
    "You are an NBA analyst with 15 years of experience writing complex SQL queries.\n"
    "Consider a table called nba_roster with the following schema:\n"
    f"{SCHEMA}\n"
    "Consider the following questions, and queries used to answer them:"
)


def check_sql_query(query: str) -> bool:
    try:
        df = run_sql(DB, query)
        return len(df) > 0
    except Exception:
        return False


def gen_similar_queries(question: str, sql: str) -> list[str]:
    system = GEN_SYSTEM + f"\nQuestion: {question}\nQuery: {sql}\n"
    user = (
        "Write two queries that are similar but different to those above.\n"
        'Format the queries as a JSON object, i.e.\n{ "explanation": str, "sql_query_1": str, "sql_query_2": str }.\n'
        "First write an explanation of why you decided to write these new queries in about "
        "3-5 sentences, then write the queries. The queries must be valid sqlite and use "
        "the same string-cleaning idioms (REPLACE/CAST/SUBSTR) where numeric columns are dirty strings."
    )
    result = ds_json(user, system, max_tokens=900)
    return [result.get("sql_query_1", ""), result.get("sql_query_2", "")]


def gen_question_for_query(sql: str) -> str:
    system = GEN_SYSTEM
    user = (
        "Now consider the following query.\n"
        f"Query: {sql}\n"
        "Write a question that this query could be used to answer.\n"
        'Format your response as a JSON object, i.e.\n{ "explanation": str, "question": str }.\n'
    )
    return ds_json(user, system, max_tokens=500).get("question", "")


def main():
    banner("①", "working backwards 单步演示: 从一条 gold 生出两条相似 SQL")
    gold = [json.loads(l) for l in GOLD.read_text().splitlines() if l.strip()]
    seed = gold[3]  # median weight
    print(f"  seed 问题: {seed['question']}")
    new_sqls = gen_similar_queries(seed["question"], seed["sql"])
    for i, s in enumerate(new_sqls, 1):
        print(f"\n  新 SQL {i} (可执行={check_sql_query(s)}):\n  {s[:160]}")

    banner("②", "反向生成 question")
    q = gen_question_for_query(new_sqls[0])
    print(f"  为新 SQL 1 生成的问题: {q}")

    banner("③", "管线化: 前 6 条 gold -> 生成 -> 可执行过滤 -> 训练数据")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    kept, dropped = [], 0
    for dp in gold[:6]:
        for s in gen_similar_queries(dp["question"], dp["sql"]):
            if not s or not check_sql_query(s):
                dropped += 1
                continue
            kept.append({"question": gen_question_for_query(s), "sql": s})
            print(f"  + {kept[-1]['question'][:60]}")
    with OUT.open("w") as f:
        for row in kept:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"\n  保留 {len(kept)} 条 / 过滤 {dropped} 条 -> {OUT.relative_to(LESSON_DIR)}")

    banner("④", "微调环节: 衔接本地 LoRA 实验台 (替代 llm.train 派发 Lamini)")
    print("""  课程在这里调用 llm.train(dataset) 派发到 Lamini 服务端微调 Llama-3-8B。
  本地等价物是仓库里的 ../projects/nba_sql_tuner —— 已实现:
    - finetune 预设: 标准 LoRA 微调
    - memory / memory_light 预设: memory tuning (高 epoch 过拟合事实)
    - CPU 真跑 (~10 分钟), 训完 backend.LLM(adapter=...) 加载对比
  运行: cd ../../projects/nba_sql_tuner && bash scripts/run_all.sh
  本课生成的 jsonl 与其 data/ 格式一致, 可直接作为训练集喂入""")

    banner("⑤", "本课结论")
    print("""  迭代闭环 = 评估找靶子(L3) -> working backwards 造数据(本课) ->
  可执行过滤保质量 -> 微调改分布 -> 回到评估看指标 —— 每一圈正确率上台阶。
  数据质量三原则: 从已验证的 gold 出发 / 生成后必须机器可校验 / 靶向失败样本""")


if __name__ == "__main__":
    main()
