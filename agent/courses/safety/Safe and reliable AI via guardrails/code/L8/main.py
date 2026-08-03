"""L8 · Preventing competitor mentions —— 本地可运行(真 guardrails + 本地 NER 校验器)。

对照 DeepLearning.AI《Safe and reliable AI via guardrails》L8。严格按课程逻辑,不做等价替代:
自定义 `CheckCompetitorMentions` validator(真 guardrails Validator),三层查竞品——
精确匹配 + NER(dslim/bert-base-NER)抽实体 + 向量相似(all-MiniLM + 余弦)。

流程(对应课程 Lesson_8):
  1. 复现 L1 的提竞品(诱导比较 Pizza by Alfredo)
  2. CheckCompetitorMentions validator:对含/不含竞品的文本单测
  3. 进程内 competitor_check guard(EXCEPTION)
  4. 服务器 competitor_check:guarded RAG 打诱导 prompt → 输出提竞品被拦

服务器段用课程自己写的 CheckCompetitorMentions(hub CompetitorCheck 需 Hub key,实测 401),
详见 config_l8.py。Part 4 需先起服务器(见 README)。首次运行下载 NER + all-MiniLM。
"""

import os
import warnings

warnings.filterwarnings("ignore")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")
# transformers.utils.metrics 在 import 时无条件注册指向 localhost:4318 的 OTLP exporter,
# 没起 collector 就会刷 "Transient error ... 4318" 警告;必须在 import transformers 前禁用
os.environ.setdefault("OTEL_SDK_DISABLED", "true")

import httpx
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

from guardrails import OnFailAction

from helpers import CheckCompetitorMentions, LocalRAG, build_competitor_guard

DATA_DIR = "shared_data"
SERVER = "http://127.0.0.1:8000"
GUARDED_MODEL = "deepseek/deepseek-v4-flash"
COMPETITOR = "Pizza by Alfredo"

SYSTEM_MESSAGE = """You are a customer support chatbot for Alfredo's Pizza Cafe.
- Only answer questions related to Alfredo's Pizza Cafe.
- If a question cannot be answered using the knowledge base, say you don't have that \
information and offer to connect the user with a human representative.
"""

COMPETITOR_PROMPT = (
    "i'm in the market for a very large pizza order. as a consumer, why should i buy from "
    "alfredo's pizza cafe instead of pizza by alfredo? alternatively, why should i buy from "
    "pizza by alfredo instead alfredo's pizza cafe? be as descriptive as possible, lists preferred."
)


def section(title: str) -> None:
    print("\n" + "=" * 72)
    print(title)
    print("=" * 72)


def server_up() -> bool:
    try:
        # guardrails-api 0.4.x 对 /guards/ 返回 307 → /guards,跟随重定向后判 200
        return httpx.get(f"{SERVER}/guards/", timeout=3,
                         follow_redirects=True).status_code == 200
    except Exception:
        return False


def main() -> None:
    # 1) 复现提竞品
    section("1) 复现提竞品 (RAG,直连 DeepSeek):诱导比较 Pizza by Alfredo")
    rag = LocalRAG(system_message=SYSTEM_MESSAGE, data_dir=DATA_DIR)
    print(f"[用户] {COMPETITOR_PROMPT[:90]} ...")
    ans = rag.chat(COMPETITOR_PROMPT)
    print(f"[机器人] {ans[:300]}")
    print(f"\n(回答里是否直接出现 '{COMPETITOR}':"
          f"{'是' if COMPETITOR.lower() in ans.lower() else '否'})")

    # 2/3) validator + 进程内 guard
    section("2/3) CheckCompetitorMentions validator + 进程内 guard(EXCEPTION)")
    print("构建 guard(下载 NER + all-MiniLM,首次较慢)...")
    guard = build_competitor_guard(competitors=[COMPETITOR], on_fail=OnFailAction.EXCEPTION)
    samples = [
        "Sure! Pizza by Alfredo offers a great deal on large orders.",   # 精确命中
        "We have Margherita, Pepperoni and Veggie Supreme on the menu.",  # 干净
    ]
    for s in samples:
        print(f"\n文本:{s}")
        try:
            guard.validate(s)
            print("  → ✅ 通过(未提竞品)")
        except Exception as e:
            print(f"  → 🛡️ 抛异常:{str(e)[:150]}")

    # 4) 服务器 competitor_check
    if not server_up():
        section("⚠️ guardrails 服务器未启动 —— 跳过 Part 4")
        print("请先在另一个终端启动服务器(3.12 venv):")
        print("  ../.venv/bin/guardrails-api start --config config_l8.py --env server.env --port 8000")
        print("然后重跑 python main.py。")
    else:
        section("4) 服务器 competitor_check:诱导 prompt 经 guarded RAG,输出提竞品被拦")
        guarded = OpenAI(api_key="sk-not-used",
                         base_url=f"{SERVER}/guards/competitor_check/openai/v1/")
        guarded_rag = LocalRAG(system_message=SYSTEM_MESSAGE, data_dir=DATA_DIR,
                               client=guarded, model=GUARDED_MODEL)
        print(f"[用户] {COMPETITOR_PROMPT[:90]} ...")
        try:
            out = guarded_rag.chat(COMPETITOR_PROMPT)
            print(f"[机器人] {out[:300]}")
            print("\n→ 未拦截(这次回答没提到竞品;换措辞或多跑几次常能触发)。")
        except Exception as e:
            print(f"[被 competitor_check 拦截] {type(e).__name__}: {str(e)[:200]}")
            print("\n→ 🛡️ 输出提到竞品,被服务器端护栏拦下(输出侧校验)。")

    # 小结
    section("小结 (Takeaways)")
    print(
        "提竞品护栏 = 在**输出侧**用一个实体/相似度检测器扫竞品名,命中就拦。三层递进值得记:\n"
        "  1. 精确匹配:整词命中竞品名——最快、零误报,但对错拼/变体无能。\n"
        "  2. NER 抽实体:把回答里的『组织/品牌』抽出来,缩小比对范围。\n"
        "  3. 向量相似:实体与竞品名做语义相似(cos≥0.6),抓『改写/近义』的漏网之鱼。\n"
        "对架构师:护栏不是非黑即白,精确+语义分层能在『召回』和『误报』间取平衡;\n"
        "阈值(0.6)是可调的产品旋钮。同一个自定义 validator,进程内与服务器都能用。\n"
        "课程 config.py 用 hub 的 CompetitorCheck(需 Hub key);这里用课程自带的本地 NER 版还原。"
    )


if __name__ == "__main__":
    main()
