"""L8 · 可选变体:用**真·Guardrails Hub 的 CompetitorCheck 校验器**(对照本地自建版)。

默认 main.py 用课程自己写的 CheckCompetitorMentions(NER+相似,guardrails 0.5.3,本地 venv);
本文件用 hub 上的 CompetitorCheck(`from guardrails_grhub_competitor_check import CompetitorCheck`,
guardrails 0.10.2,跑在独立 code/.venv-hub)。

前置见 code/HUB.md(配 token + 建 .venv-hub + 装 guardrails-grhub-competitor-check +
spacy en_core_web_trf)。运行:
  ../.venv-hub/bin/python main_hub.py
"""

import os
import warnings

warnings.filterwarnings("ignore")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
os.environ.setdefault("OTEL_SDK_DISABLED", "true")  # 关掉 guardrails 0.10.x 的 OTLP 遥测噪音

from guardrails import Guard
from guardrails_grhub_competitor_check import CompetitorCheck


def main() -> None:
    print("构建真 hub CompetitorCheck guard(首次加载 spacy en_core_web_trf,较慢)...")
    guard = Guard().use(CompetitorCheck(competitors=["Pizza by Alfredo"], on_fail="exception"))
    samples = [
        "Sure! Pizza by Alfredo offers a great deal on large orders.",
        "We have Margherita, Pepperoni and Veggie Supreme on the menu.",
    ]
    for s in samples:
        print(f"\n文本:{s}")
        try:
            guard.validate(s)
            print("  → ✅ 通过(未提竞品)")
        except Exception as e:
            print(f"  → 🛡️ 抛异常:{str(e)[:150]}")

    print("\n" + "=" * 60)
    print("这是真·hub CompetitorCheck(0.10.2),对照默认 main.py 的本地自建 NER 版。")
    print("hub 版用 spacy en_core_web_trf + 内置匹配逻辑,官方维护;自建版逻辑透明可改、可离线。")


if __name__ == "__main__":
    main()
