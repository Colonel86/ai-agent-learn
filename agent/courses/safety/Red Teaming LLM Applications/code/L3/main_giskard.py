"""L3 · 可选变体:接上**真 giskard**(giskard.scan)对本地 ZephyrApp 做自动化红队。

—— 这是给"想学 giskard 这个工具本身"的人准备的对照实现,**不属于**默认演示路径。
默认 `python main.py` 仍是零重依赖的本地聚合报告;本文件才真正调用 `giskard.scan`。

它证明了两件事:
  1. giskard 不是"不能接 DeepSeek"——新版底层走 litellm,可以指到任意 OpenAI 兼容后端,
     embedding 也能用本地 fastembed(无需 OpenAI embedding 端点)。
  2. 但代价是真实的:giskard[llm] 会拖进 torch / transformers / datasets / mlflow / faiss
     一大坨(~2GB),且**只支持 Python <3.13**——而本机默认是 3.13,所以要单独用 3.12 建 venv。
     这正是默认演示不把它放进主路径的原因。

运行(务必用单独的 3.12 venv,见 requirements-giskard.txt 顶部):
  /opt/homebrew/bin/python3.12 -m venv .venv-giskard
  .venv-giskard/bin/pip install -r requirements-giskard.txt
  .venv-giskard/bin/python main_giskard.py
  # 产出:giskard_scan_report.html(在浏览器打开看完整报告)

对照原课程:原版是 `giskard.scan(model, only="jailbreak")`。当前 giskard 的对应检测器
tag 是 `llm_prompt_injection`(提示注入)。
"""

import os

from dotenv import load_dotenv

load_dotenv()

import pandas as pd

import giskard
from giskard.llm import set_default_embedding, set_llm_model

# fastembed 首次下载模型走镜像(与 main.py 一致)
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")
from fastembed import TextEmbedding  # noqa: E402
from giskard.llm.embeddings.fastembed import FastEmbedEmbedding  # noqa: E402

from helpers import ZephyrApp  # noqa: E402

EMBED_MODEL = "BAAI/bge-small-en-v1.5"


def configure_giskard() -> None:
    """把 giskard 的裁判 LLM 指到 DeepSeek、embedding 指到本地 fastembed。"""
    base_url = os.getenv("OPENAI_BASE_URL", "https://api.deepseek.com/v1")
    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("MODEL", "deepseek-chat")

    # litellm 的 "openai/<model>" 路由 = OpenAI 兼容后端;api_base/api_key 透传给 litellm。
    # disable_structured_output=True:DeepSeek 不保证 json_schema,关掉结构化输出更稳(本项目已知坑)。
    set_llm_model(
        f"openai/{model}",
        disable_structured_output=True,
        api_base=base_url,
        api_key=api_key,
    )

    # 用 giskard 自带的 fastembed 适配器 + 本机同一个 bge 模型(纯 CPU,无需 OpenAI embedding)。
    cache_dir = os.getenv("FASTEMBED_CACHE_PATH")
    embedder = TextEmbedding(EMBED_MODEL, cache_dir=cache_dir)
    set_default_embedding(FastEmbedEmbedding(embedder))


def build_model() -> giskard.Model:
    """把本地 ZephyrApp 包成 giskard 能扫的 text_generation 模型。

    giskard 的预测函数签名:接收一个 DataFrame(每行一个测试输入),返回输出列表。
    这里每条 scan 生成的对抗问题都用一个全新会话(reset)回答,避免上下文串味。
    """
    app = ZephyrApp()

    def predict(df: pd.DataFrame) -> list[str]:
        outs = []
        for question in df["question"]:
            app.reset()
            outs.append(app.chat(str(question)))
        return outs

    return giskard.Model(
        predict,
        model_type="text_generation",
        name="ZephyrBank Customer Support",
        description=(
            "A customer support assistant for ZephyrBank, a fintech company serving "
            "business owners. Answers questions about accounts, cards, loans and onboarding."
        ),
        feature_names=["question"],
    )


def main() -> None:
    print("配置 giskard:裁判 LLM → DeepSeek,embedding → 本地 fastembed ...")
    configure_giskard()

    print("包装本地 ZephyrApp 为 giskard.Model ...")
    model = build_model()

    # 原课程写法就是 only="jailbreak";在当前 giskard 里,tag "jailbreak" 精确命中
    # 提示注入检测器 LLMPromptInjectionDetector(注意:only 匹配的是 tag,不是 detector 名)。
    print("开始 giskard.scan(only=['jailbreak']) —— 会调用多次 LLM,请稍候 ...\n")
    report = giskard.scan(model, only=["jailbreak"])

    out_html = os.path.join(os.path.dirname(__file__), "giskard_scan_report.html")
    report.to_html(out_html)

    print("\n" + "=" * 70)
    print("giskard.scan 完成。")
    issues = list(report.issues)
    print(f"发现 issue 数:{len(issues)}")
    for issue in issues:
        group = getattr(getattr(issue, "group", None), "name", "issue")
        desc = getattr(issue, "description", str(issue))
        print(f"  - [{group}] {desc}")
    print(f"\n完整报告已写入:{out_html}")
    print("在浏览器打开它,即可看到 giskard 原生的扫描报告 UI(和课程里一致)。")
    print("=" * 70)


if __name__ == "__main__":
    main()
