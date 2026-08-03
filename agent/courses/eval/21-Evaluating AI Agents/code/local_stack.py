"""本地化适配层：DeepSeek 兼容 API + 本地 Phoenix server。

课程原版用 OpenAI gpt-4o-mini + DeepLearning.AI 托管的 Phoenix。
本地化后:
- Chat/评审模型: DeepSeek (OPENAI 兼容 API), 见 code/.env
- Phoenix: 本地 `phoenix serve` (http://localhost:6006)
- DeepSeek 不支持 json_schema response_format → 结构化输出走 json_object + pydantic 校验
- deepseek-v4-flash 默认开 thinking, 不支持强制 tool_choice → 所有调用注入 thinking disabled
"""

import os
import sys
from pathlib import Path

os.environ.setdefault("MPLBACKEND", "Agg")  # 无头运行, 图表落盘为 png

from dotenv import load_dotenv

_CODE_DIR = Path(__file__).resolve().parent
load_dotenv(_CODE_DIR / ".env")

from openai import OpenAI  # noqa: E402

MODEL = os.getenv("MODEL", "deepseek-v4-flash")
EVAL_MODEL = os.getenv("EVAL_MODEL", MODEL)
DEEPSEEK_API_KEY = os.environ["DEEPSEEK_API_KEY"]
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
PHOENIX_ENDPOINT = os.getenv("PHOENIX_COLLECTOR_ENDPOINT", "http://localhost:6006/")

# deepseek-v4-flash 默认 thinking 模式不支持强制 tool_choice, 统一关闭
DS_EXTRA_BODY = {"thinking": {"type": "disabled"}}

client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)


def ds_chat(**kwargs):
    """client.chat.completions.create 的 DeepSeek 封装: thinking disabled + temperature=0。

    网络偶发 Connection error, 带 3 次指数退避重试。
    """
    import time

    from openai import APIConnectionError, APITimeoutError

    kwargs.setdefault("model", MODEL)
    kwargs.setdefault("temperature", 0)
    kwargs.setdefault("extra_body", DS_EXTRA_BODY)
    for attempt in range(3):
        try:
            return client.chat.completions.create(**kwargs)
        except (APIConnectionError, APITimeoutError):
            if attempt == 2:
                raise
            time.sleep(2**attempt)


def clip(text: str, max_chars: int = 40_000) -> str:
    """截断超长工具输出, 防止 messages 累积过大被网关 413 拒收。"""
    text = str(text)
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + f"\n... [truncated, total {len(text)} chars]"


def make_eval_llm():
    """phoenix.evals 3.x 的 LLM 封装, 指向 DeepSeek。

    evals 的 AUTO 模式会先试 json_schema(DeepSeek 400), 再自动降级到强制 tool calling;
    强制 tool_choice 需要 thinking disabled, 由 EVAL_KWARGS 透传。
    """
    from phoenix.evals import LLM

    conn = {"base_url": DEEPSEEK_BASE_URL, "api_key": DEEPSEEK_API_KEY}
    return LLM(
        provider="openai",
        model=EVAL_MODEL,
        client="openai",
        sync_client_kwargs=dict(conn),
        async_client_kwargs=dict(conn),
    )


# 传给 ClassificationEvaluator(**EVAL_KWARGS), 逐调用透传到 DeepSeek
EVAL_KWARGS = {"temperature": 0, "extra_body": DS_EXTRA_BODY}


def ensure_phoenix():
    """确认本地 Phoenix server 可达, 不可达时给出启动提示。"""
    import httpx

    try:
        httpx.get(PHOENIX_ENDPOINT, timeout=3, trust_env=False).raise_for_status()
    except Exception:
        sys.exit(
            f"[!] Phoenix server 不可达: {PHOENIX_ENDPOINT}\n"
            f"    先在另一个终端启动: cd code && .venv/bin/python -m phoenix.server.main serve"
        )


def phoenix_client():
    from phoenix.client import Client

    return Client(base_url=PHOENIX_ENDPOINT)


def banner(step: str, title: str):
    line = "=" * 64
    print(f"\n{line}\n{step} {title}\n{line}")


def run_chart_code(code: str, save_path: str) -> bool:
    """执行模型生成的画图代码, plt.show() 重定向为落盘 png。"""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    saved = []

    def _show(*args, **kwargs):
        plt.savefig(save_path, dpi=110, bbox_inches="tight")
        saved.append(save_path)
        plt.close("all")

    orig_show = plt.show
    plt.show = _show
    try:
        exec(code, {"__name__": "__chart__"})
        if not saved and plt.get_fignums():
            _show()
        return bool(saved)
    except Exception as e:
        print(f"    [chart 代码执行失败: {type(e).__name__}: {e}]")
        return False
    finally:
        plt.show = orig_show
