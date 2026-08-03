"""本地化适配层 —— 把课程原版的 OpenAI 云端栈换成本地可跑的等价栈。

原课程假设你有 OpenAI key,用 gpt-3.5-turbo / gpt-4 做生成、text-embedding-ada-002
做检索。这里保持**同样的库和同样的写法**(llama-index / giskard),只把两个接入点换掉:

  - 生成:任意 OpenAI 兼容 API。默认 DeepSeek,读 .env 的 OPENAI_API_KEY /
          OPENAI_BASE_URL / MODEL。想换回真 OpenAI 只改 .env,代码一行不动。
  - 检索:DeepSeek 没有 embedding API → 用 fastembed 在本地跑
          BAAI/bge-small-en-v1.5(384 维 ONNX,纯 CPU,不碰 MPS)。

本模块还负责几个"不设就会踩"的环境补丁,见 _patch_env()。所有补丁必须在
import fastembed / transformers 之前生效,所以这个模块要最先被 import。
"""

from __future__ import annotations

import os
from pathlib import Path

CODE_ROOT = Path(__file__).resolve().parent.parent

# 检索用的本地 embedding 模型(384 维)。课程原版是 OpenAI 的 1536 维 ada-002,
# 换模型后维度对不上,所以随课程附带的向量库必须重建,见 knowledge_base.py。
EMBED_MODEL = "BAAI/bge-small-en-v1.5"


def _patch_env() -> None:
    """四个环境补丁。每一条都对应一个实际会让程序挂掉/刷屏的坑。"""

    # 1. fastembed 首次下载模型走 HuggingFace,国内直连易卡死 → 走镜像。
    os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

    # 2. giskard 会连带装 transformers + opentelemetry。transformers 在 import 时
    #    无条件注册一个指向 localhost:4318 的 OTLP exporter,没起 collector 就会
    #    狂刷 "Transient error ... 4318" 警告,把演示输出淹掉。
    os.environ.setdefault("OTEL_SDK_DISABLED", "true")

    # 3. httpx 会经 urllib.getproxies() 自动读 macOS 系统代理(shell 里看不到代理
    #    变量也会中招),代理不稳时会 503 掐掉所有请求。api.deepseek.com 是国内
    #    服务,直连即可。
    no_proxy = os.environ.get("NO_PROXY", "")
    if "api.deepseek.com" not in no_proxy:
        merged = ",".join(filter(None, [no_proxy, "api.deepseek.com,localhost,127.0.0.1"]))
        os.environ["NO_PROXY"] = merged
        os.environ["no_proxy"] = merged

    # 4. tokenizers 在 fork 后并行会刷警告。
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")


_patch_env()

from dotenv import load_dotenv  # noqa: E402

load_dotenv(CODE_ROOT / ".env")


def fastembed_cache_dir() -> str:
    """fastembed 模型缓存目录。

    不显式指定时 fastembed 会落到临时目录,看不见 ~/.cache/fastembed 里已下好的
    模型,断网或被代理拦时就会重下失败。
    """
    return os.getenv("FASTEMBED_CACHE_PATH", os.path.expanduser("~/.cache/fastembed"))


def model_name() -> str:
    return os.getenv("MODEL", "deepseek-v4-flash")


def api_base() -> str:
    return os.getenv("OPENAI_BASE_URL", "https://api.deepseek.com/v1")


def api_key() -> str:
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        raise RuntimeError(
            "没找到 OPENAI_API_KEY。请把 code/.env.example 复制成 code/.env 并填入 key。"
        )
    return key


def extra_body() -> dict:
    """DeepSeek 专属请求体补丁。

    deepseek-v4-flash 默认开 thinking 模式,而 thinking 模式不支持强制 tool_choice
    (报 "Thinking mode does not support this tool_choice"),L5 的函数调用会直接挂。
    非 DeepSeek 后端不需要这个参数,所以按 base_url 判断后再加。
    """
    if "deepseek" not in api_base():
        return {}
    return {"thinking": {"type": "disabled"}}


def get_llm(temperature: float = 0.1, model: str | None = None, **kwargs):
    """构造 llama-index 的 LLM。

    用 OpenAILike 而不是 OpenAI:后者会按模型名查内置的 context window / 能力表,
    deepseek-v4-flash 不在表里会直接报错。OpenAILike 把这些信息交给我们显式声明。
    """
    from llama_index.llms.openai_like import OpenAILike

    additional_kwargs = {}
    body = extra_body()
    if body:
        additional_kwargs["extra_body"] = body

    return OpenAILike(
        model=model or model_name(),
        api_base=api_base(),
        api_key=api_key(),
        temperature=temperature,
        is_chat_model=True,
        is_function_calling_model=True,
        context_window=64_000,
        additional_kwargs=additional_kwargs,
        **kwargs,
    )


def get_openai_client():
    """裸 openai SDK 客户端 —— L2/L4 里课程直接用 openai.chat.completions 的地方。"""
    from openai import OpenAI

    return OpenAI(api_key=api_key(), base_url=api_base())


def chat_completion(client, messages, **kwargs) -> str:
    """对 client.chat.completions.create 的薄封装,统一注入 thinking 补丁。"""
    body = extra_body()
    if body:
        kwargs.setdefault("extra_body", body)
    resp = client.chat.completions.create(
        model=kwargs.pop("model", model_name()), messages=messages, **kwargs
    )
    return resp.choices[0].message.content


_embed_model = None


def get_embed_model():
    """llama-index 的 embedding 模型(进程内单例,避免重复加载 ONNX)。"""
    global _embed_model
    if _embed_model is None:
        from llama_index.embeddings.fastembed import FastEmbedEmbedding

        _embed_model = FastEmbedEmbedding(
            model_name=EMBED_MODEL, cache_dir=fastembed_cache_dir()
        )
    return _embed_model


def configure_giskard() -> None:
    """把 giskard 的 LLM 扫描接到 DeepSeek + 本地 embedding 上。

    giskard 2.x 走 litellm 调模型,模型名要写成 "<provider>/<model>" 并从环境变量
    取 key。embedding 那边 giskard 自带 fastembed 支持,但默认会下一个多语言模型;
    我们显式换成课程检索用的同一个 bge-small,避免多下一份模型。
    """
    import giskard.llm as gl
    from fastembed import TextEmbedding
    from giskard.llm.embeddings.fastembed import FastEmbedEmbedding

    os.environ.setdefault("DEEPSEEK_API_KEY", api_key())

    litellm_model = f"deepseek/{model_name()}" if "deepseek" in api_base() else model_name()

    # disable_structured_output:DeepSeek 不支持 response_format=json_schema,
    # giskard 默认会用它来约束扫描器的输出格式,不关掉会 400。
    gl.set_llm_model(litellm_model, disable_structured_output=True)

    # 注意这里必须用 set_default_embedding(注入 embedding 对象),不能用
    # set_embedding_model(只收 litellm 模型名字符串)。giskard 看到环境里有
    # OPENAI_API_KEY 就会默认走 openai/text-embedding-3-small——而我们这个 key 是
    # DeepSeek 的,没有 embedding 接口,真走过去就是 404。
    # set_default_embedding 虽然标了 deprecated,但它是目前唯一能塞进自定义
    # embedding 的入口,且优先级高于名字推断。调用顺序不能反:set_embedding_model
    # 会把注入的对象重置成 None。
    gl.set_default_embedding(
        FastEmbedEmbedding(
            text_embedding=TextEmbedding(EMBED_MODEL, cache_dir=fastembed_cache_dir())
        )
    )

    quiet_logs()  # giskard/litellm 在 import 时会重配 root logging,得再压一次


def quiet_logs() -> None:
    """把第三方库的日志压到 WARNING 以上。

    需要显式点名而不是只调 root logger:llama-index 的 condense_question 会用
    INFO 把**每一条改写后的查询全文**打出来,giskard 扫描时几十条越狱 prompt 会
    直接把演示输出淹掉。另外 giskard/litellm 在 import 时会重配 root logging,
    所以这个函数在 import helpers 时和 configure_giskard() 之后各调一次。
    """
    import logging

    for name in (
        "llama_index",
        "llama_index.core",
        "httpx",
        "httpcore",
        "openai",
        "giskard",
        "LiteLLM",
        "litellm",
    ):
        logging.getLogger(name).setLevel(logging.WARNING)


def banner(title: str) -> None:
    """演示脚本的分节横幅。"""
    print("\n" + "=" * 72)
    print(title)
    print("=" * 72)
