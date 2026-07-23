"""L6 · 可选变体:用**真·Guardrails Hub 的 RestrictToTopic 校验器**(对照本地自建版)。

默认 main.py 用课程自己写的 ConstrainTopic(zero-shot bart,guardrails 0.5.3,本地 venv);
本文件用 hub 上的 RestrictToTopic(`from tryolabs_grhub_restricttotopic import RestrictToTopic`,
guardrails 0.10.2,跑在独立 code/.venv-hub)。

hub 版比自建版更完整:同时支持 valid_topics(白名单)和 invalid_topics(黑名单)。

前置见 code/HUB.md。运行:
  ../.venv-hub/bin/python main_hub.py
"""

import os
import warnings

warnings.filterwarnings("ignore")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
os.environ.setdefault("OTEL_SDK_DISABLED", "true")  # 关掉 guardrails 0.10.x 的 OTLP 遥测噪音

from guardrails import Guard
from tryolabs_grhub_restricttotopic import RestrictToTopic


def main() -> None:
    print("构建真 hub RestrictToTopic guard(首次加载模型,较慢)...")
    # disable_llm=True:只用本地 zero-shot 分类器,不调 LLM(无需额外凭证,纯离线,
    # 对应自建版的模式)。若想开 LLM 兜底,去掉它并给 llm_callable 配好 DeepSeek。
    guard = Guard().use(
        RestrictToTopic(
            valid_topics=["pizza", "food", "restaurant"],
            invalid_topics=["politics", "automobiles"],
            disable_llm=True,
            on_fail="exception",
        )
    )
    samples = [
        "What pizzas do you have on the menu?",
        "What's the difference between a Ford F-150 and a Ford Ranger?",
    ]
    for s in samples:
        print(f"\n文本:{s}")
        try:
            guard.validate(s)
            print("  → ✅ 通过(在允许话题内)")
        except Exception as e:
            print(f"  → 🛡️ 抛异常:{str(e)[:150]}")

    print("\n" + "=" * 60)
    print("这是真·hub RestrictToTopic(0.10.2),对照默认 main.py 的本地自建 zero-shot 版。")
    print("hub 版同时支持 valid/invalid 话题双清单;自建版只查 banned,但逻辑透明、可离线。")


if __name__ == "__main__":
    main()
