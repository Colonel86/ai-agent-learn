"""12d 共享适配层:把 Graphiti 的三个可插拔组件接到本地标准栈上。

- LLM      → DeepSeek(OpenAIGenericClient + json_object 模式)
- Embedder → fastembed 本地跑 bge-small-zh-v1.5(与 12c 同款,512 维)
- Reranker → fastembed 余弦相似度极简实现(默认 OpenAIRerankerClient 依赖
             OpenAI 专属 logit_bias token ID,DeepSeek 接不了)
"""

import logging
import os
import tempfile
from pathlib import Path

# HF 镜像必须在 import fastembed 之前(12 系列坑 2)
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

# 模型已有本地缓存时强制离线加载:fastembed 每次初始化都联网校验元数据,
# httpx 会读 macOS 系统代理,代理不稳时直接 ProxyError 崩掉(12c 同款补丁)
if list((Path(tempfile.gettempdir()) / "fastembed_cache").glob("models--Qdrant--bge-small-zh*")):
    os.environ.setdefault("HF_HUB_OFFLINE", "1")


def _bypass_proxy_for(host: str) -> None:
    """api.deepseek.com 是国内服务,直连即可——加入 NO_PROXY,
    避免 httpx 把它路由进不稳的系统代理(nat 模式 503 会杀掉所有 LLM 调用)。"""
    for var in ("NO_PROXY", "no_proxy"):
        cur = os.environ.get(var, "")
        if host not in cur:
            os.environ[var] = f"{cur},{host}" if cur else host


_bypass_proxy_for("api.deepseek.com")

# graphiti 的检索 Cypher 会引用尚不存在的 e.episodes 属性,neo4j 驱动对此发
# GqlStatusObject 警告刷屏,无害,静音掉
logging.getLogger("neo4j.notifications").setLevel(logging.ERROR)

import numpy as np
from fastembed import TextEmbedding

from graphiti_core.cross_encoder.client import CrossEncoderClient
from graphiti_core.embedder.client import EmbedderClient
from graphiti_core.llm_client.config import LLMConfig
from graphiti_core.llm_client.openai_generic_client import OpenAIGenericClient

EMBED_MODEL = "BAAI/bge-small-zh-v1.5"  # 512 维,ONNX 纯 CPU


class FastEmbedEmbedder(EmbedderClient):
    """graphiti 没有 fastembed 集成;EmbedderClient 接口只有两个方法,自己包。"""

    def __init__(self, model_name: str = EMBED_MODEL):
        self._model = TextEmbedding(model_name=model_name)

    async def create(self, input_data) -> list[float]:
        text = input_data if isinstance(input_data, str) else str(input_data[0])
        return list(next(iter(self._model.embed([text]))))

    async def create_batch(self, input_data_list: list[str]) -> list[list[float]]:
        return [list(v) for v in self._model.embed(input_data_list)]


class CosineReranker(CrossEncoderClient):
    """极简本地 reranker:query 与 passage 的 embedding 余弦相似度排序。

    够 L1/L2 用;L3 检索专题再对比正经 cross-encoder(BGE reranker)。
    """

    def __init__(self, embedder: FastEmbedEmbedder):
        self._embedder = embedder

    async def rank(self, query: str, passages: list[str]) -> list[tuple[str, float]]:
        if not passages:
            return []
        vecs = await self._embedder.create_batch([query, *passages])
        q, ps = np.array(vecs[0]), np.array(vecs[1:])
        q = q / np.linalg.norm(q)
        ps = ps / np.linalg.norm(ps, axis=1, keepdims=True)
        scores = ps @ q
        ranked = sorted(zip(passages, scores.tolist()), key=lambda x: -x[1])
        return [(p, float(s)) for p, s in ranked]


def make_llm_client() -> OpenAIGenericClient:
    """DeepSeek 经 OpenAI 兼容端点接入。

    structured_output_mode="json_object":DeepSeek 不支持 json_schema
    response_format(12 系列坑 1),graphiti 原生提供 json_object 降级,无需 hack。
    """
    return OpenAIGenericClient(
        config=LLMConfig(
            api_key=os.environ["DEEPSEEK_API_KEY"],
            base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"),
            model="deepseek-chat",
            small_model="deepseek-chat",  # graphiti 的简单任务走 small_model,一并指到 deepseek
            temperature=0,
        ),
        structured_output_mode="json_object",
    )


def neo4j_conn() -> tuple[str, str, str]:
    return (
        os.getenv("NEO4J_URI", "bolt://localhost:7687"),
        os.getenv("NEO4J_USER", "neo4j"),
        os.getenv("NEO4J_PASSWORD", "graphiti123"),
    )
