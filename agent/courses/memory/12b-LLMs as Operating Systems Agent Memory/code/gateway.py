"""本地 LLM 网关 — 给 Letta 当 embedding + chat 后端（监听 127.0.0.1:8003）。

两个职责：
1. /v1/embeddings   DeepSeek 没有 embeddings API，用 fastembed 起 OpenAI 风格
   兼容服务（BAAI/bge-small-en-v1.5，384 维），以 Letta 的 hugging-face
   endpoint 类型接入。
2. /v1/chat/completions   透传到 DeepSeek，但注入 thinking=disabled：
   DeepSeek v4 默认开 thinking，thinking 模式不支持 letta 对 memgpt agent
   固定发的 tool_choice=required/强制函数（400），关掉后两者都合法。

用法：.venv/bin/python gateway.py（run_server.sh 会一起拉起）
"""

import os

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

import httpx
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse
from fastembed import TextEmbedding
from pydantic import BaseModel

MODEL_NAME = "BAAI/bge-small-en-v1.5"
UPSTREAM = os.environ.get("OPENAI_BASE_URL", "https://api.deepseek.com/v1").rstrip("/")
API_KEY = os.environ["OPENAI_API_KEY"]

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


@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    body = await request.json()
    body.setdefault("thinking", {"type": "disabled"})
    headers = {"Authorization": f"Bearer {API_KEY}"}
    url = f"{UPSTREAM}/chat/completions"

    if body.get("stream"):
        async def relay():
            async with httpx.AsyncClient(timeout=600) as c:
                async with c.stream("POST", url, json=body, headers=headers) as r:
                    async for chunk in r.aiter_bytes():
                        yield chunk

        return StreamingResponse(relay(), media_type="text/event-stream")

    async with httpx.AsyncClient(timeout=600) as c:
        r = await c.post(url, json=body, headers=headers)
        return JSONResponse(r.json(), status_code=r.status_code)


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8003, log_level="warning")
