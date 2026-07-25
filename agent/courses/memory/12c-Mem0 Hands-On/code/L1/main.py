"""L1 快速上手 — mem0 开源版最小闭环。

一次跑完记忆的完整生命周期:
  add(对话) → LLM 抽取成事实 → get_all 看存了什么
  → search 语义检索 → 再 add 矛盾信息观察消解 → history 看单条记忆的演化
  → update/delete 手动干预

用法:
  python main.py           # 完整跑一遍(需要 ../.env 里有 DEEPSEEK_API_KEY)
  python main.py --reset   # 先清空本地库再跑(chroma_db/ + history.db)
"""

import argparse
import json
import os
import shutil
from pathlib import Path

# 坑 2:HF 镜像必须在 import fastembed/mem0 之前设置
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

# 模型已有本地缓存时强制离线,绕开 fastembed 初始化时的联网校验(系统代理不稳会 ProxyError)
import tempfile  # noqa: E402
from pathlib import Path as _Path  # noqa: E402

if list((_Path(tempfile.gettempdir()) / "fastembed_cache").glob("models--Qdrant--bge-small-zh*")):
    os.environ.setdefault("HF_HUB_OFFLINE", "1")

# api.deepseek.com 是国内服务直连即可——加入 NO_PROXY,绕开不稳的系统代理
# (httpx 会自动读 macOS 系统代理,代理 503 会杀掉所有 LLM 调用)
for _v in ("NO_PROXY", "no_proxy"):
    _cur = os.environ.get(_v, "")
    if "api.deepseek.com" not in _cur:
        os.environ[_v] = f"{_cur},api.deepseek.com" if _cur else "api.deepseek.com"

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from mem0 import Memory  # noqa: E402  (必须晚于 HF_ENDPOINT 设置)

HERE = Path(__file__).resolve().parent

# ---------------------------------------------------------------------------
# 配置:三个可插拔组件各自指定 provider —— 这就是"底座全可插拔"的含义
# ---------------------------------------------------------------------------

CONFIG = {
    "llm": {  # 抽取 + 消解用的 LLM(每次 add 烧 1–2 次调用的就是它)
        "provider": "deepseek",
        "config": {
            "model": "deepseek-v4-flash",
            "temperature": 0,  # 消解决策要可复现
        },
    },
    "embedder": {  # DeepSeek 无 embedding API → fastembed 本地跑,中文语料用 zh 模型
        "provider": "fastembed",
        "config": {"model": "BAAI/bge-small-zh-v1.5"},
    },
    "vector_store": {  # 嵌入式 Chroma,零服务;L6 会换成 pgvector 验证可插拔
        "provider": "chroma",
        "config": {
            "collection_name": "mem0_l1",
            "path": str(HERE / "chroma_db"),
        },
    },
    "history_db_path": str(HERE / "history.db"),  # 记忆演化事件流(SQLite)
}


def banner(title: str) -> None:
    print(f"\n{'=' * 60}\n{title}\n{'=' * 60}")


def show(obj) -> None:
    print(json.dumps(obj, ensure_ascii=False, indent=2, default=str))


def main() -> None:
    memory = Memory.from_config(CONFIG)
    user = "ming"

    # -- 1. add:喂一段带偏好的对话,观察 LLM 抽取出哪些事实 -----------------
    banner("① add():对话进去,事实出来")
    conversation = [
        {"role": "user", "content": "帮我推荐点周末喝的,我平时只喝手冲,浅烘的埃塞俄比亚豆最合口味。"},
        {"role": "assistant", "content": "好的,浅烘埃塞豆果酸明亮,周末可以试试耶加雪菲的日晒处理。"},
        {"role": "user", "content": "对了我住在杭州,最好推荐些本地能买到豆子的店。"},
    ]
    result = memory.add(conversation, user_id=user)
    print("add() 返回的事件(注意 event 字段——首次全是 ADD):")
    show(result)

    # -- 2. get_all:看存储里实际躺着什么 ------------------------------------
    # 注意:mem0 2.x 起读取 API 只收 filters={...},顶层 user_id 已废弃
    banner("② get_all():存储里实际是什么样")
    all_memories = memory.get_all(filters={"user_id": user})
    show(all_memories)

    # -- 3. search:换个问法做语义检索,注意 score ---------------------------
    banner('③ search("这位用户对咖啡有什么讲究?")')
    hits = memory.search("这位用户对咖啡有什么讲究?", filters={"user_id": user})
    show(hits)

    # -- 4. 矛盾信息进来:观察两阶段消解(L2 的主角,这里先见一面) -----------
    banner("④ 再 add 矛盾信息:『我搬到上海了』→ 期望 UPDATE 而非并存")
    result2 = memory.add(
        [{"role": "user", "content": "跟你说下,我上个月搬到上海了,以后推荐上海的店吧。"}],
        user_id=user,
    )
    print("注意 event 字段——理想情况『住在杭州』被 UPDATE/DELETE,而不是新增一条矛盾记忆:")
    show(result2)
    print("\n消解后的全量记忆:")
    show(memory.get_all(filters={"user_id": user}))

    # -- 5. history:单条记忆的演化事件流(写路径的显微镜) --------------------
    banner("⑤ history():挑一条记忆看它的一生")
    memories = memory.get_all(filters={"user_id": user})
    items = memories["results"] if isinstance(memories, dict) else memories
    if items:
        target = items[0]
        print(f"目标记忆: {target['memory']!r} (id={target['id']})")
        show(memory.history(memory_id=target["id"]))

    # -- 6. update / delete:绕过 LLM 的确定性手动干预 -----------------------
    banner("⑥ update()/delete():手动干预(确定性写入的原型)")
    if items:
        target = items[0]
        memory.update(memory_id=target["id"], text=target["memory"] + "(已人工核实)")
        print("update 后:")
        show(memory.get(target["id"]))
        memory.delete(memory_id=target["id"])
        print(f"delete 后再查: {memory.get(target['id'])}")

    banner("完成。下一课 L2:系统性解剖 ADD/UPDATE/DELETE/NOOP 消解")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true", help="清空本地 chroma_db/ 和 history.db 后再跑")
    args = parser.parse_args()
    if args.reset:
        shutil.rmtree(HERE / "chroma_db", ignore_errors=True)
        (HERE / "history.db").unlink(missing_ok=True)
        print("已清空本地存储。")
    main()
