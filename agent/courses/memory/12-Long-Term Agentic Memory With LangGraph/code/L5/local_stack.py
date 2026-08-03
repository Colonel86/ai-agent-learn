"""本地演示适配层：DeepSeek OpenAI 兼容 API + fastembed 本地 embedding。

课程原版依赖 OpenAI(gpt-4o/gpt-4o-mini + text-embedding-3-small) 与 Anthropic
(claude-3-5-sonnet)。本模块把三者统一替换为：

- Chat:      DeepSeek `deepseek-v4-flash`（OpenAI 兼容端点，.env 里 MODEL 可覆盖）
- Embedding: fastembed 本地跑 `BAAI/bge-small-en-v1.5`（384 维，ONNX 纯 CPU）

import 本模块即完成 .env 加载与网络补丁，notebook 里只需：
    from local_stack import make_llm, make_embed, EMBED_DIMS
"""

import os
from pathlib import Path

# ---- 环境补丁：必须在 import fastembed / httpx 相关库之前 ----
# HF 直连会卡死，走镜像
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")
# transformers 系 import 时会注册 localhost:4318 的 OTLP exporter，没起 collector 会狂刷警告
os.environ.setdefault("OTEL_SDK_DISABLED", "true")
# api.deepseek.com 是国内服务，macOS 系统代理不稳时会 503 杀掉 httpx 流量，直连即可
for _var in ("NO_PROXY", "no_proxy"):
    _cur = os.environ.get(_var, "")
    if "api.deepseek.com" not in _cur:
        os.environ[_var] = (_cur + "," if _cur else "") + "api.deepseek.com"

from dotenv import load_dotenv

# 先课目录 .env，再上层 code/.env（load_dotenv 不覆盖已有值，前者优先）
load_dotenv()
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

# fastembed 缓存统一到用户级目录，避免落进临时目录后重复下载
_FASTEMBED_CACHE = os.getenv(
    "FASTEMBED_CACHE_PATH", os.path.expanduser("~/.cache/fastembed")
)
# 模型已缓存时强制离线，绕开 fastembed 初始化时的联网元数据校验
if any(Path(_FASTEMBED_CACHE).glob("*bge-small*")):
    os.environ.setdefault("HF_HUB_OFFLINE", "1")

from langchain_openai import ChatOpenAI

EMBED_DIMS = 384


class _DeepSeekChat(ChatOpenAI):
    """DeepSeek 不支持 json_schema response_format；部分第三方库（如 langmem 的
    PromptMemory）硬编码 json_schema，这里无条件改走 function_calling。"""

    def with_structured_output(self, schema=None, **kwargs):
        kwargs["method"] = "function_calling"
        return super().with_structured_output(schema, **kwargs)


def make_llm(temperature: float = 0) -> ChatOpenAI:
    """DeepSeek chat 模型。temperature=0 保证分类类演示可复现。"""
    return _DeepSeekChat(
        model=os.getenv("MODEL", "deepseek-v4-flash"),
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"),
        temperature=temperature,
        # deepseek-v4-flash 默认开 thinking，不支持强制 tool_choice，必须显式关掉
        extra_body={"thinking": {"type": "disabled"}},
    )


_embedder = None


def make_embed():
    """返回 InMemoryStore(index={"embed": fn, "dims": EMBED_DIMS}) 可用的 embed 函数。"""

    def embed(texts: list[str]) -> list[list[float]]:
        global _embedder
        if _embedder is None:
            from fastembed import TextEmbedding

            _embedder = TextEmbedding(
                model_name="BAAI/bge-small-en-v1.5", cache_dir=_FASTEMBED_CACHE
            )
        return [[float(x) for x in v] for v in _embedder.embed(texts)]

    return embed
