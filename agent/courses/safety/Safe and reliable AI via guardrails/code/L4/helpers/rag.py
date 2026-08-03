"""本地可运行的极简 RAG —— 替代原课程 helper.py 里的 SimpleVectorDB + RAGChatWidget。

原版:SentenceTransformer(all-MiniLM) 做 embedding + OpenAI(gpt-3.5) + ipywidgets 交互控件。
本地版:fastembed 本地 embedding(纯 CPU/ONNX,避开 MPS)+ 任意 OpenAI 兼容 API(默认 DeepSeek)
+ 纯脚本 chat()(不依赖 Jupyter/ipywidgets)。检索的距离/阈值语义与原版保持一致。

L1 只演示 RAG 的**失效模式**,还没上 guardrails——所以这里刻意不 import guardrails:
原课程 RAGChatWidget 一旦传了 client 就走纯 OpenAI 分支,Guard 分支是后面几课才用到的。
"""

import os
from typing import List, Tuple

import numpy as np
from openai import OpenAI

# fastembed 首次下载模型走镜像(国内直连 HuggingFace 易卡死)
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")
from fastembed import TextEmbedding  # noqa: E402

EMBED_MODEL = "BAAI/bge-small-en-v1.5"


def chunk_markdown_files(directory: str) -> List[str]:
    """按 #/## 标题把 markdown 切块(与原课程 helper.py 完全一致的切法)。"""
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
    """脚本化的 RAG 客服机器人。chat() 会像原课程一样把(增强后的)对话写进 self.messages,
    这样 PII 演示能直接检查后端留存的消息历史。"""

    def __init__(self, system_message: str, data_dir: str, model: str | None = None):
        self.system_message = system_message
        self.model = model or os.getenv("MODEL", "deepseek-v4-flash")
        self._client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL", "https://api.deepseek.com/v1"),
        )
        # 默认复用 ~/.cache/fastembed(其他课已下载过 bge-small),否则 fastembed 落到临时目录后重新联网下载
        self._embedder = TextEmbedding(
            EMBED_MODEL,
            cache_dir=os.getenv("FASTEMBED_CACHE_PATH", os.path.expanduser("~/.cache/fastembed")),
        )

        self.strings = chunk_markdown_files(data_dir)
        self.embeddings = self._embed(self.strings)

        self.reset()

    # -- embedding / 检索(复刻 SimpleVectorDB 的距离=1-cos、阈值语义)--
    def _embed(self, texts: List[str]) -> np.ndarray:
        return np.array(list(self._embedder.embed(texts)), dtype=np.float32)

    def query(self, query_string: str, k: int = 3, threshold: float = 0.9) -> List[Tuple[str, float]]:
        if len(self.embeddings) == 0:
            return []
        q = self._embed([query_string])[0]
        emb = self.embeddings
        sims = emb @ q / (np.linalg.norm(emb, axis=1) * np.linalg.norm(q))
        distances = 1 - sims  # 与原版一致:距离=1-余弦相似度

        results: List[Tuple[str, float]] = []
        for idx in np.argsort(distances):
            if distances[idx] < threshold and len(results) < k:
                results.append((self.strings[idx], float(distances[idx])))
            else:
                break
        results.reverse()
        return results

    def retrieve(self, user_msg: str, k: int = 3, threshold: float = 0.9) -> str:
        retrieved_ctx = ""
        for idx, (ctx, _) in enumerate(self.query(user_msg, k=k, threshold=threshold)):
            retrieved_ctx += f"# Context {idx + 1}:\n{ctx}\n\n"
        return retrieved_ctx

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

        # 和原课程一样:把(增强后的)用户消息与回复写回历史——PII 演示要检查这里
        self.messages.append({"role": "user", "content": augmented})
        self.messages.append({"role": "assistant", "content": bot})
        return bot
