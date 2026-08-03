"""L5 · Using hallucination guard in a chatbot —— 本地可运行(真 guardrails)。

对照 DeepLearning.AI《Safe and reliable AI via guardrails》L5。把 L4 的幻觉 validator 真正
用起来,分两部分:

  Part 1(进程内 Guard):用 Guard().use(HallucinationValidation, on_fail=EXCEPTION) 包住
    L4 的校验器,sources 直接传入,跑课程的 sun 例子(蕴含通过 / 不蕴含抛异常)。逐字照课程。

  Part 2(guardrails 服务器):hallucination_guard 跑在真 guardrails 服务器上,guarded client
    指向它,把 veggie 幻觉 prompt 经 RAG 打过去,看护栏拦截。

⚠️ 与课程的唯一偏离(已如实标注):课程 Part 2 用 hub 的 ProvenanceLLM 校验器,但装它需要
   Guardrails Hub 的付费/注册 API key(实测 401)。这里改用**课程自己在 L4 建的
   HallucinationValidation**(真 guardrails Validator)跑在**同一个真服务器**上——服务器/Guard/
   guarded client/on_fail 全是真 guardrails,只把"hub LLM 版 provenance"换成"课程 NLI 版"。
   详见 config_l5.py 顶部说明。

Part 2 需先起服务器(见 README)。首次运行下载 NLI 模型 + all-MiniLM(约百 MB/1.3G)。
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

from guardrails import Guard, OnFailAction

from helpers import HallucinationValidation, LocalRAG, ensure_punkt

DATA_DIR = "shared_data"
SERVER = "http://127.0.0.1:8000"
GUARDED_MODEL = "deepseek/deepseek-v4-flash"

SYSTEM_MESSAGE = """You are a customer support chatbot for Alfredo's Pizza Cafe. \
Your responses should be based solely on the provided information.

### Role and Behavior
- Only answer questions related to Alfredo's Pizza Cafe.
- Do not discuss other pizza chains or restaurants.

### Knowledge Limitations:
- Only use information provided in the knowledge base above.
- If a question cannot be answered using the knowledge base, say you don't have that \
information and offer to connect the user with a human representative.
- Do not make up or infer information not explicitly stated in the knowledge base.
"""

HALLUCINATION_PROMPT = (
    "how do i reproduce your veggie supreme pizza on my own? "
    "can you share detailed instructions?"
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
    ensure_punkt()

    # ==================================================================
    # Part 1:进程内 Guard —— 逐字照课程
    # ==================================================================
    section("Part 1) 进程内 Guard(HallucinationValidation, on_fail=EXCEPTION)")
    print("构建 guard(下载 NLI + all-MiniLM,首次较慢)...")
    guard = Guard().use(
        HallucinationValidation(
            embedding_model="all-MiniLM-L6-v2",
            entailment_model="GuardrailsAI/finetuned_nli_provenance",
            sources=[
                "The sun rises in the east and sets in the west.",
                "The sun is hot.",
            ],
            on_fail=OnFailAction.EXCEPTION,
        )
    )

    # 蕴含的句子:应通过
    guard.validate("The sun rises in the east.")
    print("\n输入:'The sun rises in the east.'")
    print("→ ✅ 校验通过(被来源蕴含)")

    # 不蕴含的句子:应抛异常
    print("\n输入:'The sun is a star.'")
    try:
        guard.validate("The sun is a star.")
        print("→ (未触发,异常)")
    except Exception as e:
        print("→ 🛡️ 校验失败,抛出异常(不被来源蕴含,判为幻觉)")
        print(f"   {str(e)[:180]}")

    # ==================================================================
    # Part 2:guardrails 服务器上的 hallucination_guard
    # ==================================================================
    if not server_up():
        section("⚠️ guardrails 服务器未启动 —— 跳过 Part 2")
        print("请先在另一个终端启动服务器(3.12 venv):")
        print("  ../.venv/bin/guardrails-api start --config config_l5.py --env server.env --port 8000")
        print("(服务器启动时会加载 NLI 模型,约需十几秒到几十秒。)然后重跑 python main.py。")
        return

    section("Part 2) 服务器 hallucination_guard:veggie 幻觉 prompt 经 guarded RAG")
    print("说明:课程此处用 hub 的 ProvenanceLLM(需付费 key,实测 401),这里换成课程 L4 的")
    print("      HallucinationValidation 跑在真服务器上。详见 config_l5.py。\n")
    guarded_client = OpenAI(api_key="sk-not-used",
                            base_url=f"{SERVER}/guards/hallucination_guard/openai/v1/")
    guarded_rag = LocalRAG(system_message=SYSTEM_MESSAGE, data_dir=DATA_DIR,
                           client=guarded_client, model=GUARDED_MODEL)
    print(f"[用户] {HALLUCINATION_PROMPT}")
    try:
        ans = guarded_rag.chat(HALLUCINATION_PROMPT)
        print(f"[机器人] {ans[:400]}")
        print("\n→ ✅ 回答通过了幻觉护栏(每句都能在知识库里找到出处)。")
    except Exception as e:
        print(f"[被 hallucination_guard 拦截] {type(e).__name__}: {str(e)[:220]}")
        print("\n→ 🛡️ 护栏在服务器端拦下了这条回答:回答里存在知识库无法证明出处的句子。")

    # ==================================================================
    section("小结 (Takeaways)")
    print(
        "L4 造了幻觉 validator,L5 把它**用起来**:\n"
        "  · Part 1:Guard().use(validator, on_fail=EXCEPTION) —— 进程内直接校验,不蕴含就抛错。\n"
        "  · Part 2:同一个 validator 挂到 guardrails 服务器,应用把 base_url 指过去即接入,\n"
        "    LLM 的每条回答在返回前都被逐句核对知识库出处,没出处就拦。\n"
        "这就是把'可靠性'落到**独立护栏服务**的完整形态:护栏与业务解耦,可复用、可独立升级。\n"
        "\n提醒(承 L4 结论):provenance 护栏会过度标记非知识库出处的句子(含合理拒答),\n"
        "生产中要只对事实性声明启用 / 给拒答开白名单 / 调阈值,否则假阳性会误伤正常回答。"
    )


if __name__ == "__main__":
    main()
