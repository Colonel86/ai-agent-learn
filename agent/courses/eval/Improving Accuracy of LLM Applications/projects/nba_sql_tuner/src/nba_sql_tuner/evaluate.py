"""评估流水线 —— 对应课程 L3 的 QueryStage + ScoreStage + 指标。

课程用 Lamini 的 async GenerationPipeline(GenerationNode)搭两段流水线。这里用纯 Python
重写同样的两段,语义一一对应:

  QueryStage:  question --模型--> 生成SQL --执行--> generated_df, query_succeeded
               同时跑参考 SQL 得到 reference_df
  ScoreStage:  比较 generated_df 与 reference_df 是否「相似」
               课程用 LLM-as-judge;这里默认用确定性的「结果值集合比较」(小模型当裁判不可靠),
               并保留 LLM-judge 作为可选(use_llm_judge=True)以忠实演示 L3 的 judge 思路。

指标(与课程一致):
  Percent Valid SQL Syntax = query_succeeded 的比例
  Percent Correct SQL      = (query_succeeded AND is_matching) 的比例
"""
from __future__ import annotations

import json
from datetime import datetime

import pandas as pd

from . import config, db
from .backend import LLM
from .prompt import sql_agent_system
from .schema import get_updated_schema


# ---- 结果比较 ------------------------------------------------------------
def _value_multiset(df: pd.DataFrame):
    """把 dataframe 拍平成「规范化的值多重集合」,用于顺序/列名无关的比较。
    数值四舍五入到 2 位,字符串小写去空格。"""
    vals = []
    for v in df.to_numpy().flatten():
        if isinstance(v, float):
            vals.append(round(v, 2))
        elif isinstance(v, int):
            vals.append(float(v))
        else:
            vals.append(str(v).strip().lower())
    return sorted(vals, key=repr)


def values_match(df_a: pd.DataFrame | None, df_b: pd.DataFrame) -> bool:
    """确定性判等:两个结果的值多重集合相同就算匹配(容忍列顺序/命名差异)。"""
    if df_a is None:
        return False
    try:
        return _value_multiset(df_a) == _value_multiset(df_b)
    except Exception:  # noqa: BLE001
        return str(df_a).lower() == str(df_b).lower()


def llm_judge_similar(judge: LLM, df: pd.DataFrame | None, ref_df: pd.DataFrame) -> bool:
    """课程 L3 的 ScoreStage:让 LLM 判断两个 dataframe 是否表达同样信息。"""
    system = (
        "Compare the following two dataframes. They are similar if they are almost "
        "identical, or if they convey the same information about the nba_roster dataset. "
        'Respond with valid JSON {"explanation": str, "similar": bool}'
    )
    user = (
        f"========== Dataframe 1 =========\n{str(df).lower()}\n\n"
        f"========== Dataframe 2 =========\n{str(ref_df).lower()}\n\n"
        "Can you tell me if these dataframes are similar?"
    )
    raw = judge.chat(system, user, max_new_tokens=150)
    return '"similar": true' in raw.lower() or "'similar': true" in raw.lower()


# ---- 单条评估 ------------------------------------------------------------
def eval_one(llm: LLM, conn, question: str, reference_sql: str,
             judge: LLM | None = None) -> dict:
    system = sql_agent_system(get_updated_schema())
    generated_sql = llm.sql(system, question)

    # QueryStage: 跑生成的 SQL
    gen_df, query_succeeded = None, False
    try:
        gen_df = pd.read_sql(generated_sql, con=conn)
        query_succeeded = True
    except Exception:  # noqa: BLE001
        pass

    # 参考 SQL(gold)
    ref_df = pd.read_sql(reference_sql, con=conn)

    # ScoreStage: 是否匹配
    is_matching = values_match(gen_df, ref_df)
    if not is_matching and judge is not None and query_succeeded:
        is_matching = llm_judge_similar(judge, gen_df, ref_df)

    return {
        "question": question,
        "generated_sql": generated_sql,
        "reference_sql": reference_sql,
        "query_succeeded": query_succeeded,
        "is_matching": is_matching,
        "is_correct": query_succeeded and is_matching,
        "generated_df": None if gen_df is None else str(gen_df),
        "reference_df": str(ref_df),
    }


def load_gold(path=None) -> list[dict]:
    path = path or config.GOLD_TEST_SET
    if not path.exists():
        from . import gold
        gold.build()
    with open(path) as f:
        return [json.loads(line) for line in f]


def evaluate(llm: LLM, label: str, use_llm_judge: bool = False,
             save: bool = True, verbose: bool = True, gold_path=None) -> dict:
    """跑完整评估集,返回指标 + 逐条结果。label 用于结果目录命名。
    gold_path 可指定评估集(默认 gold-test-set;泛化探针传 gold-seen/gold-unseen)。"""
    conn = db.engine()
    judge = llm if use_llm_judge else None
    gold = load_gold(gold_path)

    rows = []
    for i, g in enumerate(gold, 1):
        r = eval_one(llm, conn, g["question"], g["sql"], judge=judge)
        rows.append(r)
        if verbose:
            mark = "✓" if r["is_correct"] else ("~" if r["query_succeeded"] else "✗")
            print(f"  [{i:2d}/{len(gold)}] {mark} {g['question'][:50]}")
    conn.close()

    n = len(rows)
    valid = sum(r["query_succeeded"] for r in rows)
    correct = sum(r["is_correct"] for r in rows)
    metrics = {
        "label": label,
        "model": llm.name,
        "n": n,
        "valid_sql_pct": round(100 * valid / n, 1),
        "correct_pct": round(100 * correct / n, 1),
    }

    if save:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        outdir = config.RESULTS / f"{label}_{ts}"
        outdir.mkdir(parents=True, exist_ok=True)
        with open(outdir / "metrics.json", "w") as f:
            json.dump(metrics, f, ensure_ascii=False, indent=2)
        with open(outdir / "rows.jsonl", "w") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        metrics["_dir"] = str(outdir)

    if verbose:
        print(f"\n[{label}] Valid SQL: {metrics['valid_sql_pct']}%  "
              f"Correct: {metrics['correct_pct']}%  ({correct}/{n})")
    return {"metrics": metrics, "rows": rows}
