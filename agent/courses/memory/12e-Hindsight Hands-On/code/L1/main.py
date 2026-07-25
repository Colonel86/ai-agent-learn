"""L1 快速上手 — Hindsight embedded 模式,retain / recall / reflect 三操作闭环。

流程:
  进程内拉起 HindsightServer(嵌入式 pg0,零外部服务)
  → retain 三条信息(与 12c/12d 同一个咖啡叙事,方便三方对照)
  → recall 语义查询 + 时序查询(TEMPR 四路检索的第一次体感)
  → reflect 让它"反思"生成带态度的回答(disposition 的入口,L5 展开)

用法:
  python main.py           # 需要 ../.env 里有 DEEPSEEK_API_KEY
  python main.py --bank X  # 换个 bank 名跑(bank 之间完全隔离)
"""

import argparse
import json
import os
from datetime import datetime
from pathlib import Path

# ---- 环境变量必须在 import hindsight 之前全部就位 --------------------------

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

os.environ.setdefault("HINDSIGHT_API_LLM_OUTPUT_LANGUAGE", "Chinese")  # 记忆产物强制中文

# api.deepseek.com 直连即可——加入 NO_PROXY,绕开不稳的系统代理(httpx 读 macOS 系统代理)
for _v in ("NO_PROXY", "no_proxy"):
    _cur = os.environ.get(_v, "")
    if "api.deepseek.com" not in _cur:
        os.environ[_v] = f"{_cur},api.deepseek.com" if _cur else "api.deepseek.com"
os.environ.setdefault("HINDSIGHT_API_LLM_MAX_CONCURRENT", "8")  # 防 DeepSeek 限流

# 本机 HF 直连/镜像都拉不下模型(CDN 被 SSL 阻断) → 两个绕行:
# 1) embedding 用 onnx provider 指向本地模型文件(复用 12c/12d 已下载的 bge-small-zh);
# 2) reranker 用纯 RRF,免去 cross-encoder 模型下载(L3 检索课再讨论代价)。
_MODEL_DIR = Path(__file__).resolve().parent.parent / "models" / "fast-bge-small-zh-v1.5"
os.environ.setdefault("HINDSIGHT_API_EMBEDDINGS_PROVIDER", "onnx")
os.environ.setdefault("HINDSIGHT_API_EMBEDDINGS_ONNX_MODEL_PATH", str(_MODEL_DIR / "model_optimized.onnx"))
os.environ.setdefault("HINDSIGHT_API_EMBEDDINGS_ONNX_TOKENIZER_NAME_OR_PATH", str(_MODEL_DIR))
os.environ.setdefault("HINDSIGHT_API_EMBEDDINGS_ONNX_QUERY_PREFIX", "")  # BGE 系不用 E5 前缀
os.environ.setdefault("HINDSIGHT_API_EMBEDDINGS_ONNX_PASSAGE_PREFIX", "")
os.environ.setdefault("HINDSIGHT_API_EMBEDDINGS_ONNX_POOLING", "cls")  # BGE 用 CLS pooling
os.environ.setdefault("HINDSIGHT_API_RERANKER_PROVIDER", "rrf")

from hindsight import HindsightClient, HindsightServer  # noqa: E402


def banner(title: str) -> None:
    print(f"\n{'=' * 60}\n{title}\n{'=' * 60}")


def show(obj) -> None:
    if hasattr(obj, "model_dump"):
        obj = obj.model_dump()
    print(json.dumps(obj, ensure_ascii=False, indent=2, default=str))


def main(bank: str) -> None:
    banner("启动 embedded server(首次运行会下载 embedding/cross-encoder 模型)")
    # LLM 参数必须显式传构造函数(默认是 groq,不读 HINDSIGHT_API_LLM_* 环境变量);
    # 其余配置(embedding/输出语言/并发)是进程内引擎,环境变量生效。
    # 首启初始化 pg0 + 下载模型远超默认 30s 超时,显式 start(timeout=600)。
    server = HindsightServer(
        llm_provider="deepseek",
        llm_api_key=os.environ["DEEPSEEK_API_KEY"],
        llm_model="deepseek-chat",
    )
    server.start(timeout=600)
    try:
        print(f"server 起在 {server.url}(嵌入式 pg0,无外部依赖)")
        client = HindsightClient(base_url=server.url)

        # -- 1. retain:与 12c/12d 相同叙事,方便三方对照 ----------------------
        banner("① retain × 3(注意耗时:结构化抽取 + 双索引构建)")
        items = [
            ("我平时只喝手冲,浅烘的埃塞俄比亚豆最合口味。", "咖啡偏好闲聊"),
            ("我住在杭州,在网易做后端开发。", "个人情况"),
            ("上周试了朋友推荐的深烘曼特宁,又苦又焦,再也不想喝了。", "咖啡体验"),
        ]
        for content, ctx in items:
            t0 = datetime.now()
            client.retain(bank_id=bank, content=content, context=ctx)
            print(f"  retained({(datetime.now() - t0).total_seconds():.1f}s): {content[:24]}…")

        # -- 2. recall:TEMPR 四路并行检索的出口 -------------------------------
        banner('② recall("这个人对咖啡有什么口味偏好?")')
        results = client.recall(bank_id=bank, query="这个人对咖啡有什么口味偏好?")
        show(results)

        banner('③ recall 时序查询("上周发生了什么?")——时序是四路之一')
        show(client.recall(bank_id=bank, query="上周发生了什么?"))

        # -- 3. reflect:三操作里其它框架没有的那一个 --------------------------
        banner('④ reflect("该给这个人推荐什么咖啡?为什么?")——生成带推理的洞察')
        show(client.reflect(bank_id=bank, query="该给这个人推荐什么咖啡?为什么?"))

        banner("完成。L2 解剖 retain 的抽取产物;L4 看 observations 如何从事实里长出来")
    finally:
        server.stop()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--bank", default="ming-l1", help="memory bank 名(默认 ming-l1)")
    main(parser.parse_args().bank)
