"""步骤 1(L1+L2):SQL Agent 跑起来 + 现场诊断幻觉。

对应课程 L1(prompt 格式)、L2(SQL Agent + 结构化输出 + 诊断幻觉)。
本地退回 base 小模型后,用 few-shot 纯文本补全让它出 SQL(见 prompt.plain_fewshot_prompt)。
few-shot 只示范简单查询,所以模型在「薪资 / 体重」这类脏字符串列上仍会幻觉 ——
这正是课程 L2 要讲的:生成的 SQL 看着合理,却因为不懂 "$9,945,830" / "232 lbs" 的
字符串格式而算错。
"""
import _bootstrap  # noqa: F401
import pandas as pd

from nba_sql_tuner import db
from nba_sql_tuner.backend import LLM
from nba_sql_tuner.prompt import plain_fewshot_prompt

# (问题, 参考正确 SQL, 幻觉点说明)
CASES = [
    ("Who is the highest paid NBA player?",
     "SELECT NAME, SALARY FROM nba_roster WHERE SALARY != '--' "
     "ORDER BY CAST(REPLACE(REPLACE(SALARY,'$',''),',','') AS INTEGER) DESC LIMIT 1;",
     "薪资是 '$9,945,830' 字符串:必须 REPLACE 掉 $ 和逗号再 CAST,否则按字典序排序会错"),
    ("What is the median weight in the NBA?",
     "SELECT CAST(SUBSTR(WT,1,INSTR(WT,' ')) AS INTEGER) AS w FROM nba_roster "
     "ORDER BY w LIMIT 1 OFFSET (SELECT COUNT(*) FROM nba_roster)/2;",
     "体重是 '232 lbs' 字符串:直接 AVG(WT) 得不到数字,要先 SUBSTR 取数字部分"),
    ("How many players went to Duke?",
     "SELECT COUNT(*) FROM nba_roster WHERE COLLEGE = 'Duke';",
     "简单计数,模型通常能答对"),
]


if __name__ == "__main__":
    llm = LLM()
    conn = db.engine()
    print(f"模型:{llm.name}  (is_base={llm.is_base()})\n")

    print("=" * 72)
    print("模型看到的 few-shot prompt(以第 1 题为例):")
    print("=" * 72)
    print(plain_fewshot_prompt(CASES[0][0]))
    print("\n" + "=" * 72)
    print("逐题:生成 SQL → 执行 → 和参考答案比对(诊断幻觉)")
    print("=" * 72)

    for q, ref_sql, note in CASES:
        gen = llm.sql("", q)
        print(f"\nQ: {q}")
        print(f"  提示:{note}")
        print(f"  生成 SQL: {gen}")
        # 参考答案
        ref_df = pd.read_sql(ref_sql, con=conn)
        ref_val = ref_df.to_string(index=False).replace("\n", " | ")
        try:
            gen_df = pd.read_sql(gen, con=conn)
            gen_val = gen_df.to_string(index=False).replace("\n", " | ")
            print(f"  生成结果: {gen_val}")
            print(f"  参考答案: {ref_val}")
            print(f"  判定: {'✓ 一致' if gen_val.lower()==ref_val.lower() else '✗ 幻觉(结果不符)'}")
        except Exception as e:  # noqa: BLE001
            print(f"  ✗ 执行失败(幻觉):{str(e).splitlines()[0][:80]}")
            print(f"  参考答案: {ref_val}")

    conn.close()
    print("\n下一步:python scripts/02_baseline_eval.py")
