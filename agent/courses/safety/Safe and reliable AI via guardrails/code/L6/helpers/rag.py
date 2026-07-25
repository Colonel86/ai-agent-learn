"""L3 的 RAG 应用侧 —— 与 L1 相同的本地 RAG,但 **client/model 可注入**。

L3 要把同一个 RAG 聊天机器人分别接两种 client:
  1. 普通 DeepSeek client(直连)—— 演示"没有护栏时会泄漏 Project Colosseum"
  2. guarded client(指向 guardrails 服务器)—— LLM 调用被服务器上的 colosseum guard 拦截

注意:RAG 应用本身**不是**护栏;护栏是后面用真 guardrails(config.py + 服务器)实现的。
这里只是把 L1 的 LocalRAG 泛化成能换 client,方便把请求路由到服务器。
"""

import os
from typing import List, Tuple

import numpy as np
from openai import OpenAI

os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")
from fastembed import TextEmbedding  # noqa: E402

EMBED_MODEL = "BAAI/bge-small-en-v1.5"


def chunk_markdown_files(directory: str) -> List[str]:
    chunks: List[str] = []
    for filename in sorted(os.listdir(directory)):
        if not filename.endswith(".md"):
            continue
        with open(os.path.join(directory, filename), encoding="utf-8") as f:
            content = f.read()
        title = os.path.splitext(filename)[0]
        current_h1, current_h2, current_content = "", "", []
        for line in content.split("\n"):
            if line.startswith("# "):
                if current_content:
                    chunks.append(_format_chunk(title, current_h1, current_h2, current_content))
                current_h1, current_h2, current_content = line[2:].strip(), "", []
            elif line.startswith("## "):
                if current_content:
                    chunks.append(_format_chunk(title, current_h1, current_h2, current_content))
                current_h2, current_content = line[3:].strip(), []
            else:
                current_content.append(line)
        if current_content:
            chunks.append(_format_chunk(title, current_h1, current_h2, current_content))
    return chunks


def _format_chunk(title: str, h1: str, h2: str, content: List[str]) -> str:
    section_info = f"{h1}/{h2}" if h2 else h1
    return f"Title: {title}\nSection: {section_info}\n" + "\n".join(content).strip()


class LocalRAG:
    def __init__(self, system_message: str, data_dir: str,
                 client: OpenAI | None = None, model: str | None = None):
        self.system_message = system_message
        self.model = model or os.getenv("MODEL", "deepseek-v4-flash")
        # client 可注入:直连 DeepSeek,或指向 guardrails 服务器的 guarded client
        self._client = client or OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL", "https://api.deepseek.com/v1"),
        )
        self._embedder = TextEmbedding(EMBED_MODEL, cache_dir=os.getenv("FASTEMBED_CACHE_PATH"))
        self.strings = chunk_markdown_files(data_dir)
        self.embeddings = self._embed(self.strings)
        self.reset()

    def _embed(self, texts: List[str]) -> np.ndarray:
        return np.array(list(self._embedder.embed(texts)), dtype=np.float32)

    def query(self, query_string: str, k: int = 3, threshold: float = 0.9) -> List[Tuple[str, float]]:
        if len(self.embeddings) == 0:
            return []
        q = self._embed([query_string])[0]
        emb = self.embeddings
        sims = emb @ q / (np.linalg.norm(emb, axis=1) * np.linalg.norm(q))
        distances = 1 - sims
        results: List[Tuple[str, float]] = []
        for idx in np.argsort(distances):
            if distances[idx] < threshold and len(results) < k:
                results.append((self.strings[idx], float(distances[idx])))
            else:
                break
        results.reverse()
        return results

    def retrieve(self, user_msg: str, k: int = 3, threshold: float = 0.9) -> str:
        ctx = ""
        for idx, (c, _) in enumerate(self.query(user_msg, k=k, threshold=threshold)):
            ctx += f"# Context {idx + 1}:\n{c}\n\n"
        return ctx

    @staticmethod
    def _augment(user_msg: str, retrieval: str) -> str:
        return (
            "\n\nUse this context to help answer the question:\n\n"
            f"{retrieval}\n\nUser message:\n{user_msg}\n"
        )

    def reset(self) -> None:
        self.messages = [{"role": "system", "content": self.system_message}]

    def chat(self, user_msg: str, k: int = 3, threshold: float = 0.9) -> str:
        context = self.retrieve(user_msg, k=k, threshold=threshold)
        augmented = self._augment(user_msg, context)
        query_messages = self.messages + [{"role": "user", "content": augmented}]
        resp = self._client.chat.completions.create(
            model=self.model, messages=query_messages, temperature=0.0,
        )
        bot = resp.choices[0].message.content
        self.messages.append({"role": "user", "content": augmented})
        self.messages.append({"role": "assistant", "content": bot})
        return bot
