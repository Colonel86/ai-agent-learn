"""本地 embedding 服务 — 给 Letta 当 embedding 后端。

DeepSeek 没有 embeddings API，Letta 的 "hugging-face" endpoint 类型会朝
{base_url}/embeddings 发 OpenAI 风格请求并解析 data[0].embedding，
所以用 fastembed 起一个 20 行的兼容服务即可（BAAI/bge-small-en-v1.5，384 维）。

用法：.venv/bin/python embed_server.py   # 监听 127.0.0.1:8003
"""

import os

from dotenv import load_dotenv

load_dotenv()
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

import uvicorn
from fastapi import FastAPI
from fastembed import TextEmbedding
from pydantic import BaseModel

MODEL_NAME = "BAAI/bge-small-en-v1.5"

app = FastAPI()
model = TextEmbedding(model_name=MODEL_NAME)


class EmbeddingRequest(BaseModel):
    input: str | list[str]
    model: str = MODEL_NAME
    user: str | None = None


@app.post("/v1/embeddings")
def embeddings(req: EmbeddingRequest):
    texts = [req.input] if isinstance(req.input, str) else req.input
    vectors = list(model.embed(texts))
    return {
        "object": "list",
        "model": MODEL_NAME,
        "data": [
            {"object": "embedding", "index": i, "embedding": v.tolist()}
            for i, v in enumerate(vectors)
        ],
    }


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8003, log_level="warning")
