"""步骤 5(收尾):baseline vs fine-tuning vs memory tuning 三方对比。

这是整个项目的「payoff」。产出三样东西:
  1. 准确率对比表(有效SQL% / 正确SQL%)—— 评估驱动的阶梯是否真的爬升
  2. 硬事实并排答案 —— 直观看到 memory tuning 在训练过的事实上近乎零幻觉
  3. loss 曲线摘要 —— memory tuning 把 loss 逼到 ~0,标准 FT 停在平台

结果写 data/results/comparison.json + comparison.md(可直接贴进笔记)。
"""
import _bootstrap  # noqa: F401
import json
from pathlib import Path

import pandas as pd

from nba_sql_tuner import config, db
from nba_sql_tuner.backend import LLM
from nba_sql_tuner.evaluate import evaluate, eval_one
from nba_sql_tuner.schema import get_updated_schema
from nba_sql_tuner.prompt import sql_agent_system

HARD_FACTS = [
    ("Who is the highest paid NBA player?",
     "SELECT NAME, SALARY FROM nba_roster WHERE SALARY != '--' "
     "ORDER BY CAST(REPLACE(REPLACE(SALARY,'$',''),',','') AS INTEGER) DESC LIMIT 1;"),
    ("What is the median weight in the NBA?",
     "SELECT CAST(SUBSTR(WT,1,INSTR(WT,' ')) AS INTEGER) AS w FROM nba_roster "
     "ORDER BY w LIMIT 1 OFFSET (SELECT COUNT(*) FROM nba_roster)/2;"),
    ("What is the average age of the Chicago Bulls?",
     "SELECT AVG(AGE) FROM nba_roster WHERE Team = 'Chicago Bulls';"),
]


def load_models():
    models = {"baseline": LLM()}
    for name in ("finetune", "memory"):
        d = config.ADAPTERS / name
        if (d / "adapter_config.json").exists():
            models[name] = LLM(adapter=d)
    return models


def loss_summary(name):
    f = config.ADAPTERS / name / "train_summary.json"
    if not f.exists():
        return None
    s = json.loads(f.read_text())
    return {"final_loss": s["final_loss"],
            "loss_history": s["loss_history"],
            "epochs": s["preset"]["epochs"]}


def main():
    models = load_models()
    conn = db.engine()

    # 1) 准确率阶梯
    print("=" * 70)
    print("准确率对比(gold 评估集)")
    print("=" * 70)
    metrics = {}
    for name, llm in models.items():
        print(f"\n-- {name} ({llm.name}) --")
        res = evaluate(llm, label=f"cmp_{name}", save=True, verbose=True)
        metrics[name] = res["metrics"]

    # 2) 硬事实并排
    print("\n" + "=" * 70)
    print("硬事实并排答案(训练过的事实上,memory tuning 应近乎零幻觉)")
    print("=" * 70)
    system = sql_agent_system(get_updated_schema())
    hard_rows = []
    for q, ref in HARD_FACTS:
        ref_df = pd.read_sql(ref, con=conn)
        print(f"\nQ: {q}\n   参考答案: {str(ref_df).splitlines()[-1].strip()}")
        row = {"question": q, "reference": str(ref_df)}
        for name, llm in models.items():
            r = eval_one(llm, conn, q, ref)
            mark = "✓" if r["is_correct"] else ("~valid" if r["query_succeeded"] else "✗err")
            print(f"   [{name:8s}] {mark}  {r['generated_sql'][:70]}")
            row[name] = {"correct": r["is_correct"], "sql": r["generated_sql"]}
        hard_rows.append(row)

    # 3) loss 曲线
    print("\n" + "=" * 70)
    print("训练 loss(memory tuning 把 loss 逼到 ~0 = 把事实背进权重)")
    print("=" * 70)
    losses = {}
    for name in ("finetune", "memory"):
        ls = loss_summary(name)
        if ls:
            losses[name] = ls
            print(f"  {name:8s}: final loss={ls['final_loss']:.4f}  "
                  f"({ls['epochs']} epochs)  曲线={ls['loss_history']}")

    conn.close()

    # 写文件
    out = {"metrics": metrics, "hard_facts": hard_rows, "losses": losses}
    (config.RESULTS / "comparison.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2))
    _write_md(metrics, losses, hard_rows)
    print(f"\n结果已写入 {config.RESULTS}/comparison.json 和 comparison.md")


def _write_md(metrics, losses, hard_rows):
    lines = ["# fine-tuning vs memory tuning 对比结果\n",
             "## 准确率阶梯\n",
             "| 模型 | 有效SQL% | 正确SQL% |", "|---|---|---|"]
    for name in ("baseline", "finetune", "memory"):
        if name in metrics:
            m = metrics[name]
            lines.append(f"| {name} | {m['valid_sql_pct']} | {m['correct_pct']} |")
    lines.append("\n## 训练 loss\n")
    lines.append("| 训练 | epochs | final loss |")
    lines.append("|---|---|---|")
    for name, ls in losses.items():
        lines.append(f"| {name} | {ls['epochs']} | {ls['final_loss']:.4f} |")
    lines.append("\n## 硬事实并排\n")
    for r in hard_rows:
        lines.append(f"**Q: {r['question']}**\n")
        for name in ("baseline", "finetune", "memory"):
            if name in r:
                mark = "✓" if r[name]["correct"] else "✗"
                lines.append(f"- `{name}` {mark} `{r[name]['sql']}`")
        lines.append("")
    (config.RESULTS / "comparison.md").write_text("\n".join(lines))


if __name__ == "__main__":
    main()
