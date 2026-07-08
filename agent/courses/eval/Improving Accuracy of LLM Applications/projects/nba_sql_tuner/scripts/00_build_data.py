"""步骤 0:重建课程数据资产(nba_roster.db + gold-test-set.jsonl)。

对应课程里平台预置、但不随 markdown 发布的 data/ 目录。确定性合成,可重复运行。
"""
import _bootstrap  # noqa: F401
from nba_sql_tuner import db, gold

if __name__ == "__main__":
    db.build()
    gold.build()
    print("\n数据就绪。下一步:python scripts/01_agent_demo.py")
