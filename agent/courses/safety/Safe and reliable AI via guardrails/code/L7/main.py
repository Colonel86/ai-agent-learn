"""L7 · Ensuring no PII is leaked —— 本地可运行(真 guardrails + Microsoft Presidio)。

对照 DeepLearning.AI《Safe and reliable AI via guardrails》L7。严格按课程逻辑,不做等价替代:
用 **Presidio**(本地开源 PII 引擎,无需任何 key)+ 自定义 `PIIDetector`(真 guardrails Validator)
在输入/输出两侧防 PII 泄漏。

流程(对应课程 Lesson_7):
  1. 复现 L1 的 PII 留存(姓名+电话被存进后端消息历史)
  2. Presidio analyzer(识别 PII)+ anonymizer(打码)
  3. detect_pii + PIIDetector validator
  4. 进程内 pii_guard(EXCEPTION):含 PII 的消息 → 抛异常
  5. 服务器 pii_guard(输入 refrain / 输出 fix):含 PII 的输入被拒,PII 不入库
  6. 输出脱敏(on_fail=FIX):把 LLM 生成里的电话号码实时打码

服务器段用课程自己引入的 Presidio + 自定义 PIIDetector(hub DetectPII 需 Hub key,实测 401;
且 hub DetectPII 本质也是 Presidio 封装),详见 config_l7.py。

Part 5 需先起服务器(见 README)。
"""

import os
import re
import warnings

warnings.filterwarnings("ignore")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
os.environ.setdefault("OTEL_SDK_DISABLED", "true")  # transformers.utils.metrics 会无条件注册 localhost:4318 OTLP exporter,没起 collector 就刷警告

import httpx
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

from guardrails import Guard, OnFailAction

from helpers import LocalRAG, PIIDetector, anonymize_pii, build_pii_guard, detect_pii

DATA_DIR = "shared_data"
SERVER = "http://127.0.0.1:8000"
GUARDED_MODEL = "deepseek/deepseek-v4-flash"

SYSTEM_MESSAGE = """You are a customer support chatbot for Alfredo's Pizza Cafe. \
Your responses should be based solely on the provided information.
- Only answer questions related to Alfredo's Pizza Cafe.
- If a question cannot be answered using the knowledge base, say you don't have that \
information and offer to connect the user with a human representative.
"""

PII_PROMPT = ("can you tell me what orders i've placed in the last 3 months? "
              "my name is hank tate and my phone number is 555-123-4567")


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
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"),
                    base_url=os.getenv("OPENAI_BASE_URL", "https://api.deepseek.com/v1"))
    model = os.getenv("MODEL", "deepseek-v4-flash")

    # 1) 复现 PII 留存
    section("1) 复现 PII 留存 (RAG,直连 DeepSeek):姓名+电话被存进后端历史")
    rag = LocalRAG(system_message=SYSTEM_MESSAGE, data_dir=DATA_DIR)
    rag.chat(PII_PROMPT)
    phone_re = re.compile(r"\b\d{3}-\d{3}-\d{4}\b")
    leaked_roles = [m["role"] for m in rag.messages if phone_re.search(m["content"])]
    print(f"后端 messages 里命中电话号码的消息角色:{leaked_roles or '(无)'}")
    print("→ ⚠️ PII 被原样存进后端(与模型是否复述无关)——这正是要在护栏层拦住的。")

    # 2) Presidio analyzer + anonymizer
    section("2) Microsoft Presidio:analyzer 识别 + anonymizer 打码")
    text = ("can you tell me what orders i've placed in the last 3 months? "
            "my name is Hank Tate and my phone number is 555-123-4567")
    print(f"原文:{text}")
    print(f"识别到的 PII 实体:{detect_pii(text, ('PERSON','PHONE_NUMBER','EMAIL_ADDRESS'))}")
    print(f"打码后:{anonymize_pii(text)}")

    # 3) + 4) PIIDetector validator + 进程内 pii_guard
    section("3/4) PIIDetector validator + 进程内 pii_guard(on_fail=EXCEPTION)")
    guard = build_pii_guard(on_fail=OnFailAction.EXCEPTION)
    print(f"输入:{PII_PROMPT}")
    try:
        guard.validate(PII_PROMPT)
        print("→ (未触发)")
    except Exception as e:
        print(f"→ 🛡️ 抛异常:{str(e)[:160]}")

    # 6) 输出脱敏(先演示不依赖服务器的 FIX)
    section("6) 输出脱敏 (on_fail=FIX):把回答里的 PII 打码后再返回")
    fix_guard = Guard().use(
        PIIDetector(entities=("PHONE_NUMBER", "EMAIL_ADDRESS"), on_fail=OnFailAction.FIX)
    )
    llm_out = ("Sure! You can reach the manager Jamie at 555-987-6543 "
               "or email support@alfredos.example for help.")
    print(f"LLM 原始输出:{llm_out}")
    outcome = fix_guard.validate(llm_out)
    print(f"脱敏后输出:  {outcome.validated_output}")
    print("→ on_fail=FIX 用 Presidio anonymizer 把电话/邮箱替换成 <占位符>,再给用户看。")

    # 5) 服务器 pii_guard
    if not server_up():
        section("⚠️ guardrails 服务器未启动 —— 跳过 Part 5")
        print("请先在另一个终端启动服务器(3.12 venv):")
        print("  ../.venv/bin/guardrails-api start --config config_l7.py --env server.env --port 8000")
        print("然后重跑 python main.py。")
    else:
        section("5) 服务器 pii_guard(输入 refrain / 输出 fix):含 PII 的输入")
        guarded = OpenAI(api_key="sk-not-used",
                         base_url=f"{SERVER}/guards/pii_guard/openai/v1/")
        print(f"[用户] {PII_PROMPT}")
        try:
            resp = guarded.chat.completions.create(
                model=GUARDED_MODEL, temperature=0,
                messages=[{"role": "user", "content": PII_PROMPT}])
            print(f"[机器人] {resp.choices[0].message.content[:250]}")
            print("→ 输入通过(或被 refrain 处理);服务器端不会把带 PII 的原始输入留存。")
        except Exception as e:
            print(f"[被 pii_guard 处理/拦截] {type(e).__name__}: {str(e)[:180]}")
            print("→ 🛡️ 含 PII 的输入在服务器端被 refrain,PII 不进入后续处理/留存。")

    # 小结
    section("小结 (Takeaways)")
    print(
        "PII 泄漏是**架构层**问题(见 L1):模型再听话也拦不住,因为泄漏发生在存储/日志/输出侧。\n"
        "L7 的解法是把 PII 校验放到确定性护栏层,两侧都设防:\n"
        "  · 输入侧(refrain/exception):含 PII 的用户输入不留存、不喂给模型,从源头减少暴露面。\n"
        "  · 输出侧(fix):用 Presidio 把模型可能吐出的 PII 实时打码,再展示给用户。\n"
        "Presidio(本地开源、无需 key)负责识别+打码,自定义 PIIDetector 把它接进 guardrails,\n"
        "进程内与服务器两种部署皆可。这正是 L1 的 PII 失效模式的确定性闭环。"
    )


if __name__ == "__main__":
    main()
