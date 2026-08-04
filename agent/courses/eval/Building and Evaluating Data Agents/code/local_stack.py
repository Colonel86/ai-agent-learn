"""本地化适配层：DeepSeek 兼容 API + 本地数据替代 Snowflake Cortex。

课程原版依赖 (均为课程方托管, 本地不可用):
- Snowflake Snowpark session + Cortex Agent (Analyst text2sql + Search 检索)
- OpenAI gpt-4o / o3, Tavily 搜索
本地化:
- LLM: DeepSeek (langchain-openai ChatOpenAI + base_url; 注意 trulens 2.10 钉死 openai<2, 本 venv openai==1.109)
- Cortex Agent -> sales_data.py: 合成 deals 表 (sqlite) + 会议纪要 (fastembed 本地向量检索)
- Tavily -> ddgs (DuckDuckGo, 免 key), 失败时回退到离线内置结果
- TruLens: 本地 sqlite (default.sqlite), OTEL tracing 模式
"""

import os
import sys
from pathlib import Path

os.environ.setdefault("MPLBACKEND", "Agg")  # chart agent 无头画图
os.environ.setdefault("TRULENS_OTEL_TRACING", "1")
# fastembed: HF 镜像 + 本地缓存 (见 env-local-llm-stack 坑 2/3c)
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")
os.environ.setdefault("FASTEMBED_CACHE_PATH", os.path.expanduser("~/.cache/fastembed"))

from dotenv import load_dotenv

_CODE_DIR = Path(__file__).resolve().parent
load_dotenv(_CODE_DIR / ".env")

MODEL = os.getenv("MODEL", "deepseek-v4-flash")
DEEPSEEK_API_KEY = os.environ["DEEPSEEK_API_KEY"]
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")

DS_EXTRA_BODY = {"thinking": {"type": "disabled"}}


def make_llm(json_mode: bool = False, temperature: float = 0):
    """DeepSeek 版 ChatOpenAI。

    json_mode=True 对应课程的 reasoning_llm(o3 + json_object):
    planner/executor 需要严格 JSON 输出。
    """
    from langchain_openai import ChatOpenAI

    kwargs = {}
    if json_mode:
        kwargs["model_kwargs"] = {"response_format": {"type": "json_object"}}
    return ChatOpenAI(
        model=MODEL,
        temperature=temperature,
        api_key=DEEPSEEK_API_KEY,
        base_url=DEEPSEEK_BASE_URL,
        extra_body=DS_EXTRA_BODY,
        max_retries=6,  # deepseek 高峰期偶发 503 Service is too busy
        **kwargs,
    )


def make_tru_provider(model: str | None = None):
    """TruLens OpenAI provider 指向 DeepSeek (course: gpt-4o / gpt-4.1)。

    trulens 对未知模型默认尝试 structured output(json_schema), DeepSeek 会返回
    纯文本导致 ValidationError 白烧重试额度 —— 子类直接声明不支持, 走文本解析路径。
    """
    from trulens.providers.openai import OpenAI as TruOpenAI

    class _DeepSeekTruOpenAI(TruOpenAI):
        def _structured_output_supported(self) -> bool:
            return False

        def _is_cfg_available(self) -> bool:
            return False

    p = _DeepSeekTruOpenAI(
        model_engine=model or MODEL,
        base_url=DEEPSEEK_BASE_URL,
        api_key=DEEPSEEK_API_KEY,
    )
    # _create_chat_completion 走的是 capabilities 缓存(按 model 名全局共享),
    # 预置为不支持, 彻底跳过 responses.parse / chat.parse 的试探与重试
    p._set_capabilities(
        {"responses_api": False, "structured_outputs": False, "cfg": False}
    )
    return p


def banner(step: str, title: str):
    line = "=" * 64
    print(f"\n{line}\n{step} {title}\n{line}")
