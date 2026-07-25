"""L5 · 可选变体:用**真·Guardrails Hub 的 ProvenanceLLM 校验器**(对照本地 NLI 自建版)。

默认 main.py 用课程 L4 建的 HallucinationValidation(NLI provenance,guardrails 0.5.3,本地 venv);
本文件用 hub 上的 ProvenanceLLM(`from guardrails_grhub_provenance_llm import ProvenanceLLM`,
guardrails 0.10.2,跑在独立 code/.venv-hub)。

差别:hub ProvenanceLLM 用**一个 LLM 当裁判**判断每句是否被 sources 蕴含(课程原用 gpt-4o-mini);
这里把 llm_callable 指到 **DeepSeek**(litellm 路由),需要 server.env 里的 DEEPSEEK_API_KEY。
自建版 NLI 则用一个本地 NLI 模型判蕴含,无需 LLM。

前置见 code/HUB.md。运行(需 DEEPSEEK_API_KEY):
  DEEPSEEK_API_KEY=<key> ../.venv-hub/bin/python main_hub.py
"""

import os
import warnings

warnings.filterwarnings("ignore")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
os.environ.setdefault("OTEL_SDK_DISABLED", "true")

from dotenv import load_dotenv

load_dotenv()

# 把 .env 里的 OPENAI_API_KEY 兜底喂给 DEEPSEEK_API_KEY(litellm 的 deepseek/ 路由用后者)
if os.getenv("OPENAI_API_KEY") and not os.getenv("DEEPSEEK_API_KEY"):
    os.environ["DEEPSEEK_API_KEY"] = os.environ["OPENAI_API_KEY"]

from guardrails import Guard
from guardrails_grhub_provenance_llm import ProvenanceLLM

# 知识库来源(与默认 main.py 同一套披萨知识库的一部分,作为 provenance 的出处)
SOURCES = [
    "Alfredo's Pizza Cafe pizza types: Margherita (tomato sauce, mozzarella, basil); "
    "Pepperoni (tomato sauce, mozzarella, pepperoni); "
    "Veggie Supreme (tomato sauce, mozzarella, bell peppers, onions, mushrooms, olives).",
    "Delivery: average delivery time is 30-45 minutes; up to 60 minutes during peak hours.",
]


def check(guard, text: str, label: str) -> None:
    print(f"\n[{label}] {text}")
    try:
        guard.validate(text, metadata={"sources": SOURCES})
        print("  → ✅ 通过(每句都能在 sources 里找到出处)")
    except Exception as e:
        print(f"  → 🛡️ 判为幻觉/无出处:{str(e)[:150]}")


def main() -> None:
    print("构建真 hub ProvenanceLLM guard(裁判 LLM = DeepSeek via litellm)...")
    guard = Guard().use(
        ProvenanceLLM(
            validation_method="sentence",
            llm_callable="deepseek/deepseek-v4-flash",
            top_k=3,
            on_fail="exception",
        )
    )
    # 有出处的句子(菜单里就有 Veggie Supreme)
    check(guard, "The Veggie Supreme has bell peppers, onions, mushrooms and olives.", "有出处")
    # 无出处的句子(知识库里没有做法/价格)
    check(guard, "To make it, bake the dough at 900 degrees for exactly 3 minutes.", "编造")

    print("\n" + "=" * 60)
    print("这是真·hub ProvenanceLLM(0.10.2),裁判换成 DeepSeek;对照默认 main.py 的本地 NLI 版。")
    print("hub 版用 LLM 判蕴含(更灵活但费 token/联网);NLI 版用本地小模型判(离线省钱但要维护模型)。")


if __name__ == "__main__":
    main()
