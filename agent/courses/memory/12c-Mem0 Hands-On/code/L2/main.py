"""L2 写路径解剖 — ADD/UPDATE/DELETE/NOOP 消解质量实验。

实验设计:
  - 10 组「矛盾对」:先种入旧事实,再喂矛盾的新信息 → 期望旧记忆被 UPDATE/DELETE,
    失败形态 = 矛盾并存(只 ADD)或漏判(NOOP);
  - 3 组「对照」:重复信息(期望 NOOP)× 2 + 无关新信息(期望 ADD)× 1,
    防止把"见什么都改"误当成消解能力强;
  - 每组用独立 user_id 隔离,消解只看得到本组的种子记忆;
  - 自动判定 + 汇总判对率,结果落盘 results.json。

这就是 框架现状.md §2.7 待验证①:「抽取/消解在你的领域上错得多不多」。

用法:
  python main.py            # 全量 13 组(默认清空本地库)
  python main.py --cases 3  # 只跑前 N 组矛盾对(快速冒烟)
"""

import argparse
import json
import os
import shutil
from datetime import datetime
from pathlib import Path

os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

# 模型已有本地缓存时强制离线加载:fastembed 每次初始化都会联网校验元数据,
# 系统代理不稳时(httpx 会读 macOS 系统代理)直接 ProxyError 崩掉,离线可完全绕开
import tempfile  # noqa: E402

if list((Path(tempfile.gettempdir()) / "fastembed_cache").glob("models--Qdrant--bge-small-zh*")):
    os.environ.setdefault("HF_HUB_OFFLINE", "1")

# api.deepseek.com 直连即可——加入 NO_PROXY,绕开不稳的系统代理(httpx 读 macOS 系统代理)
for _v in ("NO_PROXY", "no_proxy"):
    _cur = os.environ.get(_v, "")
    if "api.deepseek.com" not in _cur:
        os.environ[_v] = f"{_cur},api.deepseek.com" if _cur else "api.deepseek.com"

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from mem0 import Memory  # noqa: E402

HERE = Path(__file__).resolve().parent

CONFIG = {
    "llm": {
        "provider": "deepseek",
        "config": {"model": "deepseek-v4-flash", "temperature": 0},
    },
    "embedder": {
        "provider": "fastembed",
        "config": {"model": "BAAI/bge-small-zh-v1.5"},
    },
    "vector_store": {
        "provider": "chroma",
        "config": {"collection_name": "mem0_l2", "path": str(HERE / "chroma_db")},
    },
    "history_db_path": str(HERE / "history.db"),
}

# ---------------------------------------------------------------------------
# 实验数据:每组 = (种子对话, 矛盾/后续信息, 期望行为)
# 期望 RESOLVE = 旧记忆应被 UPDATE 或 DELETE;NOOP = 不应产生变化;ADD = 应新增且不动旧的
# ---------------------------------------------------------------------------

CONTRADICTIONS = [  # 期望全部 RESOLVE
    ("我住在杭州,周末喜欢逛西湖。", "我上个月搬到上海了,已经在浦东安顿下来。"),
    ("我在网易做后端开发。", "我上周从网易离职,入职字节跳动了。"),
    ("我是素食主义者,不吃任何肉类。", "我最近开始吃肉了,医生建议我补充蛋白质。"),
    ("我只喝手冲咖啡,最爱浅烘埃塞豆。", "我现在改喝深烘意式了,浅烘的酸味喝腻了。"),
    ("我单身,一个人住。", "我上个月结婚了,和爱人搬到了一起。"),
    ("我养了一只叫团子的猫。", "团子上周送给我妹妹了,现在家里没有宠物。"),
    ("我在自学日语,准备考 N2。", "日语我放弃了,改学西班牙语了。"),
    ("我用 iPhone,是十年的苹果老用户。", "我上周把手机换成华为了,iPhone 不用了。"),
    ("我每周跑步三次,正在备战半马。", "我膝盖受伤了,医生说至少半年内禁止跑步。"),
    ("我是一名后端工程师。", "我升职了,现在是技术经理,不写一线代码了。"),
]

CORRECTIONS = [  # 纠正型:旧信息是错的,毫无保留价值 → 消解的试金石,期望 RESOLVE
    ("我住在杭州。", "纠正一下,我刚才说错了,我住的是苏州,不是杭州。"),
    ("我的猫叫团子。", "打错字了,猫的名字是丸子,不是团子。"),
]

CONTROLS = [
    ("我住在杭州,周末喜欢逛西湖。", "对了我说过,我住在杭州。", "NOOP"),
    ("我只喝手冲咖啡,最爱浅烘埃塞豆。", "再说一次,我平时只喝手冲咖啡。", "NOOP"),
    ("我在网易做后端开发。", "我养了一只叫花卷的柯基。", "ADD"),
]


def snapshot(memory: Memory, user: str) -> dict[str, str]:
    res = memory.get_all(filters={"user_id": user})
    items = res["results"] if isinstance(res, dict) else res
    return {m["id"]: m["memory"] for m in items}


def run_case(memory: Memory, idx: int, seed: str, followup: str, expected: str) -> dict:
    user = f"case-{idx:02d}"
    memory.add([{"role": "user", "content": seed}], user_id=user)
    before = snapshot(memory, user)

    result = memory.add([{"role": "user", "content": followup}], user_id=user)
    events = [
        {"event": r.get("event"), "memory": r.get("memory")}
        for r in result.get("results", [])
    ]
    after = snapshot(memory, user)

    # 判定:种子记忆是否被动过(文本变化=UPDATE / id 消失=DELETE)
    seed_untouched = all(before[mid] == after.get(mid) for mid in before)
    event_types = {e["event"] for e in events}
    only_added = event_types <= {"ADD"} and len(after) > len(before)

    if expected == "RESOLVE":
        # 成功 = 旧记忆被改写或删除;失败 = 矛盾并存(旧的原封不动 + 新增)或 NOOP
        passed = not seed_untouched
        outcome = "RESOLVED" if passed else ("COEXIST" if only_added else "NOOP")
    elif expected == "NOOP":
        passed = seed_untouched and not only_added
        outcome = "NOOP" if not events else "/".join(sorted(event_types))
    else:  # ADD
        passed = seed_untouched and only_added
        outcome = "/".join(sorted(event_types)) if events else "NOOP"

    return {
        "case": idx, "seed": seed, "followup": followup, "expected": expected,
        "events": events, "outcome": outcome, "passed": passed,
        "memories_after": list(after.values()),
    }


def main(n_cases: int) -> None:
    shutil.rmtree(HERE / "chroma_db", ignore_errors=True)
    (HERE / "history.db").unlink(missing_ok=True)
    memory = Memory.from_config(CONFIG)

    cases = [(s, f, "RESOLVE") for s, f in CONTRADICTIONS[:n_cases]]
    if n_cases >= len(CONTRADICTIONS):
        cases += [(s, f, "RESOLVE") for s, f in CORRECTIONS] + CONTROLS

    results = []
    for i, (seed, followup, expected) in enumerate(cases, 1):
        t0 = datetime.now()
        r = run_case(memory, i, seed, followup, expected)
        dt = (datetime.now() - t0).total_seconds()
        flag = "✅" if r["passed"] else "❌"
        print(f"{flag} case-{i:02d} [{expected:>7}] → {r['outcome']:<10} "
              f"({dt:.0f}s)  {seed[:18]}… / {followup[:18]}…")
        results.append(r)

    resolve = [r for r in results if r["expected"] == "RESOLVE"]
    ctrl = [r for r in results if r["expected"] != "RESOLVE"]
    print("\n" + "=" * 62)
    print(f"矛盾消解判对率: {sum(r['passed'] for r in resolve)}/{len(resolve)}")
    if ctrl:
        print(f"对照组(防误改)判对率: {sum(r['passed'] for r in ctrl)}/{len(ctrl)}")
    for r in resolve:
        if not r["passed"]:
            print(f"  失败样本 case-{r['case']:02d}({r['outcome']}): "
                  f"库内现存 {len(r['memories_after'])} 条 → {r['memories_after']}")
    out = HERE / "results.json"
    out.write_text(json.dumps(results, ensure_ascii=False, indent=2))
    print(f"\n明细已写入 {out}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", type=int, default=len(CONTRADICTIONS),
                        help="跑前 N 组矛盾对(默认全部,并附带对照组)")
    main(parser.parse_args().cases)
