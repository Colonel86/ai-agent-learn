"""L7 · 可选变体:用**真·Guardrails Hub 的 DetectPII 校验器**(对照本地 Presidio 自建版)。

这是给已经有 Guardrails Hub API key 的人准备的"真 hub"对照实现。与默认 main.py 的区别:
  - main.py     :用课程自己写的 PIIDetector(基于 Presidio),guardrails 0.5.3,本地 venv
  - main_hub.py :用 hub 上的 DetectPII 校验器(`from guardrails_grhub_detect_pii import DetectPII`),
                 guardrails 0.10.2,跑在**独立的 code/.venv-hub** 里

两者底层都是 Presidio,但 hub 版是官方维护、随 hub 升级的"SOTA"版本。

前置(见 code/HUB.md):
  1. 已 `guardrails configure` 配好 Hub token(写入 ~/.guardrailsrc)
  2. 已建 code/.venv-hub(guardrails 0.10.2)并装好 guardrails-grhub-detect-pii + en_core_web_lg

运行:
  ../.venv-hub/bin/python main_hub.py
"""

import os
import logging
import warnings

warnings.filterwarnings("ignore")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
os.environ.setdefault("OTEL_SDK_DISABLED", "true")  # 关掉 guardrails 0.10.x 的 OTLP 遥测噪音
# AnalyzerEngine 初始化会把 es/it/pl 语种 recognizer 从 en-only registry 剔除并逐条刷 WARNING,无害噪音
logging.getLogger("presidio-analyzer").setLevel(logging.ERROR)

from dotenv import load_dotenv

load_dotenv()

from guardrails import Guard

# 真·hub 校验器(0.10.x 里 hub 校验器是独立 pip 包 guardrails_grhub_*)
from guardrails_grhub_detect_pii import DetectPII


def section(title: str) -> None:
    print("\n" + "=" * 72)
    print(title)
    print("=" * 72)


def main() -> None:
    section("真 hub DetectPII —— 输入检测(EXCEPTION)")
    guard_in = Guard().use(DetectPII(pii_entities=["PERSON", "PHONE_NUMBER"], on_fail="exception"))
    text = "my name is Hank Tate and my phone number is 555-123-4567"
    print(f"输入:{text}")
    try:
        guard_in.validate(text)
        print("→ (未触发)")
    except Exception as e:
        print(f"→ 🛡️ 抛异常:{str(e)[:160]}")

    section("真 hub DetectPII —— 输出脱敏(FIX)")
    guard_out = Guard().use(DetectPII(pii_entities=["PERSON", "PHONE_NUMBER", "EMAIL_ADDRESS"],
                                      on_fail="fix"))
    llm_out = ("Sure! You can reach the manager Jamie at 555-987-6543 "
               "or email jamie@example.com for help.")
    print(f"LLM 原始输出:{llm_out}")
    out = guard_out.validate(llm_out)
    print(f"脱敏后输出:  {out.validated_output}")

    section("小结")
    print(
        "这是**真·Guardrails Hub 的 DetectPII**(0.10.2,code/.venv-hub),与默认 main.py 的\n"
        "本地自建 PIIDetector 对照。两者底层都是 Presidio,行为一致(识别 + 打码);差别在:\n"
        "  · hub 版:官方维护、随 hub 升级、可远程推理,但需 Hub token + 独立 0.10.x 环境。\n"
        "  · 自建版:零依赖 hub、可离线、逻辑透明可改,但要自己跟进模型/规则。\n"
        "对架构师:能用 hub 就省维护,但要评估 token/网络/版本耦合;自建则换来可控与离线。"
    )


if __name__ == "__main__":
    main()
