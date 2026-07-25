"""L3 读路径解剖 — search 打分公式 / threshold / metadata 过滤 / TTL / rerank。

关键技巧:全程 `infer=False` 入库——跳过 LLM 抽取,记忆内容完全受控,
让实验只测"读路径",不被写路径的非确定性污染(L2 的教训)。

实验:
  ① 受控语料入库(带 metadata 分类 + 自定义 timestamp)
  ② explain=True:打分公式的现场分解(semantic/bm25/entity 三信号)
  ③ 问法敏感度 + 中英跨语言损耗定量
  ④ threshold:语义分闸门(在混合打分之前生效)
  ⑤ metadata 过滤:filters 里直接写自定义字段
  ⑥ TTL:expiration_date 过期记忆的隐身与显影(show_expired)
  ⑦ rerank=True:LLM 重排的顺序变化与延迟代价

用法:  python main.py
"""

import os
from datetime import datetime, timedelta
from pathlib import Path

os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

import tempfile  # noqa: E402

if list((Path(tempfile.gettempdir()) / "fastembed_cache").glob("models--Qdrant--bge-small-zh*")):
    os.environ.setdefault("HF_HUB_OFFLINE", "1")

# api.deepseek.com 直连即可——加入 NO_PROXY,绕开不稳的系统代理(httpx 读 macOS 系统代理)
for _v in ("NO_PROXY", "no_proxy"):
    _cur = os.environ.get(_v, "")
    if "api.deepseek.com" not in _cur:
        os.environ[_v] = f"{_cur},api.deepseek.com" if _cur else "api.deepseek.com"

from dotenv import load_dotenv  # noqa: E402

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

import shutil  # noqa: E402

from mem0 import Memory  # noqa: E402

HERE = Path(__file__).resolve().parent
USER = "l3"

BASE_CONFIG = {
    "llm": {"provider": "deepseek", "config": {"model": "deepseek-chat", "temperature": 0}},
    "embedder": {"provider": "fastembed", "config": {"model": "BAAI/bge-small-zh-v1.5"}},
    "vector_store": {
        "provider": "chroma",
        "config": {"collection_name": "mem0_l3", "path": str(HERE / "chroma_db")},
    },
    "history_db_path": str(HERE / "history.db"),
}

# 受控语料:内容/分类人工指定(infer=False 原样入库)。
# ⚠️ 原计划给每条带自定义 timestamp 制造时近性差异——实测撞 feature wall:
# add(timestamp=...) 在 OSS 版直接 raise "Temporal reasoning requires a Mem0 API key",
# 文档注释写明 "Platform-only temporal parameter. Not supported in OSS."
NOW = datetime.now()
CORPUS = [
    ("User only drinks pour-over coffee and loves light-roasted Ethiopian beans.", "preference"),
    ("User dislikes dark-roasted Mandheling, finds it bitter and burnt.", "preference"),
    ("用户只喝手冲咖啡,最爱浅烘的埃塞俄比亚豆。", "preference-zh"),
    ("User works as a backend engineer at NetEase in Hangzhou.", "profile"),
    ("User runs three times a week, training for a half marathon.", "habit"),
    ("User injured the knee; doctor forbids running for six months.", "habit"),
    ("User is reading 'Designing Data-Intensive Applications'.", "habit"),
]


def banner(t: str) -> None:
    print(f"\n{'=' * 62}\n{t}\n{'=' * 62}")


def hits(res, k=5):
    items = res["results"] if isinstance(res, dict) else res
    return items[:k]


def show_scores(res, k=5) -> None:
    for m in hits(res, k):
        print(f"  {m['score']:.4f}  {m['memory'][:52]}")


def main() -> None:
    shutil.rmtree(HERE / "chroma_db", ignore_errors=True)
    (HERE / "history.db").unlink(missing_ok=True)
    memory = Memory.from_config(BASE_CONFIG)

    banner("① 受控语料入库(infer=False:跳过 LLM 抽取,原样存储,零 LLM 调用)")
    for text, cat in CORPUS:
        memory.add(text, user_id=USER, infer=False, metadata={"category": cat})
    print(f"入库 {len(CORPUS)} 条,分类人工指定")
    print("⚠️ feature wall 实锤:add(timestamp=...) OSS 版直接报错要求 Mem0 平台 API key")

    banner("② explain=True:打分公式现场分解")
    print("2.x 实装公式: final = (semantic + bm25 + entity_boost) / max_possible")
    print("(纸面宣传的'重要性/时近性加权'不在评分公式里!)\n")
    res = memory.search("What coffee does the user like?", filters={"user_id": USER},
                        top_k=3, explain=True)
    for m in hits(res, 3):
        d = m.get("score_details", {})
        print(f"  final={d.get('final_score', 0):.4f} = (semantic {d.get('semantic_score', 0):.4f}"
              f" + bm25 {d.get('bm25_score', 0):.4f} + entity {d.get('entity_boost', 0):.4f})"
              f" / {d.get('max_possible_score', 0):.1f}   {m['memory'][:38]}")
    print("\n👉 Chroma 无 BM25、spaCy 未装无实体 boost → 本栈上'混合打分'退化为纯语义分")

    banner("③ 问法敏感度 + 跨语言损耗(同一批记忆,四种问法)")
    for q in ["What coffee does the user like?",
              "这位用户对咖啡有什么口味偏好?",
              "他喝什么咖啡?",
              "用户的饮品习惯是什么?"]:
        res = memory.search(q, filters={"user_id": USER}, top_k=2)
        top = hits(res, 2)
        lang_hit = "中文条目" if top and "手冲" in top[0]["memory"] else "英文条目"
        print(f"  「{q}」→ top1 {top[0]['score']:.4f}({lang_hit}), top2 {top[1]['score']:.4f}")

    banner("④ threshold:语义分闸门(默认 0.1,在混合打分之前生效)")
    for th in [0.1, 0.45, 0.55]:
        res = memory.search("coffee preferences", filters={"user_id": USER}, threshold=th)
        print(f"  threshold={th:<5} → 返回 {len(hits(res, 99))} 条")

    banner('⑤ metadata 过滤:filters={"user_id", "category"}')
    res = memory.search("What does the user do regularly?",
                        filters={"user_id": USER, "category": "habit"})
    show_scores(res)
    print("👉 自定义 metadata 字段可直接进 filters——多租户/分域检索的基础")

    banner("⑥ TTL:expiration_date 让记忆自动过期")
    memory.add("限时优惠:本周店内咖啡豆八折。", user_id=USER, infer=False,
               metadata={"category": "promo"},
               expiration_date=(NOW - timedelta(days=1)).strftime("%Y-%m-%d"))  # 已过期
    res = memory.search("咖啡豆有什么优惠?", filters={"user_id": USER})
    visible = [m["memory"] for m in hits(res, 99) if "八折" in m["memory"]]
    res_exp = memory.search("咖啡豆有什么优惠?", filters={"user_id": USER}, show_expired=True)
    visible_exp = [m["memory"] for m in hits(res_exp, 99) if "八折" in m["memory"]]
    print(f"  默认检索命中过期记忆: {len(visible)} 条(应为 0)")
    print(f"  show_expired=True 命中: {len(visible_exp)} 条(应为 1)")
    print("👉 mem0 有'到点隐身'的 TTL,但这不是 Zep 那种事实失效——过期时间要你写入时就知道")

    banner("⑦ rerank=True:LLM 重排的收益与代价")
    try:
        rerank_config = dict(BASE_CONFIG)
        rerank_config["reranker"] = {
            "provider": "llm_reranker",
            "config": {"provider": "deepseek", "model": "deepseek-chat",
                       "api_key": os.environ["DEEPSEEK_API_KEY"]},
        }
        m2 = Memory.from_config(rerank_config)
        q = "用户还能继续跑步训练吗?"
        t0 = datetime.now()
        base = m2.search(q, filters={"user_id": USER}, top_k=3)
        t1 = datetime.now()
        rr = m2.search(q, filters={"user_id": USER}, top_k=3, rerank=True)
        t2 = datetime.now()
        print(f"  不重排({(t1 - t0).total_seconds():.1f}s):")
        show_scores(base, 3)
        print(f"  LLM 重排({(t2 - t1).total_seconds():.1f}s):")
        show_scores(rr, 3)
        print("👉 语义分只看'像不像',重排器看'答不答得上'——受伤禁跑那条应该被提到最前")
    except Exception as e:
        print(f"  reranker 初始化/调用失败(记录为发现): {type(e).__name__}: {e}")

    banner("完成。对照 12e 的 recall scores{semantic,keyword,reranker,final}——"
           "Hindsight 把这套读路径做成了默认全开")


if __name__ == "__main__":
    main()
