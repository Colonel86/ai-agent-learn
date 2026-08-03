"""L4 · Checking for hallucinations using NLI —— 本地可运行演示(真 guardrails + 真 NLI 模型)。

对照 DeepLearning.AI《Safe and reliable AI via guardrails》L4。**严格按课程示例逻辑**,
不做等价替代:自定义 `HallucinationValidation` validator(真 guardrails Validator)+ 真 NLI
模型 `GuardrailsAI/finetuned_nli_provenance` + SentenceTransformer + nltk 分句。

L4 不需要 guardrails 服务器,全程在进程内本地跑。唯一的本地化是把复现幻觉的 RAG 聊天机器人
从 OpenAI 换成 DeepSeek(仅为演示"幻觉长啥样",与 validator 逻辑无关)。

流程(对应课程 Lesson_4):
  1. 复现 L1 的幻觉例子(向 RAG 要"veggie supreme 的详细做法"——知识库里根本没有)
  2. 起 NLI pipeline,跑课程的两个 sun 例子(蕴含 / 矛盾)
  3. 构建 HallucinationValidation validator,用 sun 例子单测(逐字照抄课程)
  4. [本地额外验证] 把 validator 接到真实 RAG 回答上,用知识库当 sources,逐句判幻觉

首次运行会从 HuggingFace 下载 NLI 模型与 all-MiniLM(约几十~百 MB)。国内可先:
  export HF_ENDPOINT=https://hf-mirror.com

运行:
  cp .env.example .env        # 填 OPENAI_API_KEY(DeepSeek 的 key)
  cd .. && /opt/homebrew/bin/python3.12 -m venv .venv && .venv/bin/pip install -r requirements-unified.txt
  cd L4 && ../.venv/bin/python main.py   # L1-L8 共用 code/.venv(guardrails 0.10.2)
"""

import os
import warnings

warnings.filterwarnings("ignore")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
# 国内下载 HF 模型可改镜像;默认直连(镜像偶发不稳时也能回退)
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")
# transformers.utils.metrics 在 import 时无条件注册指向 localhost:4318 的 OTLP exporter,
# 没起 collector 就会刷 "Transient error ... 4318" 警告;必须在 import transformers 前禁用
os.environ.setdefault("OTEL_SDK_DISABLED", "true")

from dotenv import load_dotenv

load_dotenv()

from helpers import HallucinationValidation, LocalRAG, ensure_punkt, make_nli_pipeline

DATA_DIR = "shared_data"

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


def main() -> None:
    ensure_punkt()

    # ------------------------------------------------------------------
    # 1) 复现 L1 的幻觉:知识库只有 veggie supreme 的配料,没有任何"做法"
    # ------------------------------------------------------------------
    section("1) 复现幻觉 (RAG,直连 DeepSeek):索要知识库里不存在的披萨做法")
    rag = LocalRAG(system_message=SYSTEM_MESSAGE, data_dir=DATA_DIR)
    print(f"知识库:{len(rag.strings)} 个 chunk")
    print(f"\n[用户] {HALLUCINATION_PROMPT}")
    answer = rag.chat(HALLUCINATION_PROMPT)
    print(f"[机器人] {answer[:500]}")

    # ------------------------------------------------------------------
    # 2) NLI pipeline:课程的两个例子(蕴含 vs 矛盾)
    # ------------------------------------------------------------------
    section("2) NLI 模型 (GuardrailsAI/finetuned_nli_provenance):蕴含 vs 矛盾")
    print("加载 NLI pipeline(首次会下载模型)...")
    nli = make_nli_pipeline()
    premise = "The sun rises in the east and sets in the west."
    for hypo in ("The sun rises in the east.", "The sun rises in the west."):
        result = nli({"text": premise, "text_pair": hypo})
        print(f"\n  Premise:    {premise}")
        print(f"  Hypothesis: {hypo}")
        print(f"  Result:     {result}")

    # ------------------------------------------------------------------
    # 3) HallucinationValidation validator:课程的 sun 单测(逐字照抄课程逻辑)
    # ------------------------------------------------------------------
    section("3) HallucinationValidation validator:sun 例子单测")
    print("构建 validator(复用同一 NLI 模型 + all-MiniLM embedding)...")
    hv = HallucinationValidation(
        sources=["The sun rises in the east and sets in the west"]
    )
    for sentence in ("The sun sets in the east", "The sun sets in the west"):
        r = hv.validate(sentence)
        print(f"\n  验证:'{sentence}'")
        print(f"  outcome = {r.outcome}")
        if r.outcome == "fail":
            print(f"  error   = {r.error_message}")

    # ------------------------------------------------------------------
    # 4) [本地额外验证] 把 validator 接到真实 RAG 回答上
    #    用知识库全文当 sources,逐句判断第 1 步那条回答是否有幻觉
    #    (课程把"给 validator 套 guard"留到 L5;这里只是提前验证 validator 对真实回答有效)
    # ------------------------------------------------------------------
    section("4) [本地额外验证] 用知识库当 sources,检测第 1 步 RAG 回答里的幻觉")
    kb_validator = HallucinationValidation(sources=rag.strings)
    r = kb_validator.validate(answer)
    print(f"\n对第 1 步的回答逐句做 NLI 蕴含判定,结果:outcome = {r.outcome}")
    if r.outcome == "fail":
        print("被标记为『无知识库出处』的句子:")
        print(f"  {r.error_message}")
        print(
            "\n↳ 诚实解读:这次 DeepSeek 其实**拒答了**(没编造做法),但 validator 仍把这些句子\n"
            "   全标出来——因为拒答语、寒暄语(『我没有该信息』『要帮你下单吗』)本来就**不在知识库里**,\n"
            "   自然没有蕴含来源。这暴露了 provenance 型护栏的真实取舍:**它会过度标记任何非知识库\n"
            "   出处的句子,包括合理拒答**。工程上要么只对『事实性声明』启用、要么给拒答/寒暄开白名单。\n"
            "   若模型真编了一段做法,同样会被标出来——那才是它要拦的幻觉。判据一致:没出处=标记。")
    else:
        print("↳ 每一句都在知识库里找到了蕴含来源。")

    # ------------------------------------------------------------------
    section("小结 (Takeaways)")
    print(
        "幻觉护栏的做法不是『让模型别编』(软约束),而是**事后逐句核对来源**(确定性校验):\n"
        "  · 把回答拆成句子(nltk)\n"
        "  · 每句找语义最相关的知识库来源(embedding, cos>0.8)\n"
        "  · 用 NLI 模型判断『来源是否蕴含这句』——不蕴含=没出处=幻觉\n"
        "这就是 provenance 型幻觉检测:只认『知识库能证明的话』,模型说得再流畅,没出处也拦。\n"
        "L5 会把这个 validator 套进 Guard,变成能自动拦截/改写的护栏。"
    )


if __name__ == "__main__":
    main()
