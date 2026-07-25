"""L1 第一张图 — Graphiti 摄入对话,看实体/边被抽成什么样。

流程:
  build_indices → add_episode(两段对话) → 打印抽出的节点(实体)和边(事实)
  → search 混合检索 → 注意每条边上的 valid_at(L2 的主角 invalid_at 此时应全空)

用法:
  python main.py           # 需要 ../.env + Neo4j 容器在跑
  python main.py --reset   # 先清空 Neo4j 整库再跑
"""

import argparse
import asyncio
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from common import CosineReranker, FastEmbedEmbedder, make_llm_client, neo4j_conn  # noqa: E402

from graphiti_core import Graphiti  # noqa: E402
from graphiti_core.nodes import EpisodeType  # noqa: E402

GROUP = "ming"  # graphiti 的隔离单位叫 group_id(≈ mem0 的 user_id,Zep 云端的 user)


def banner(title: str) -> None:
    print(f"\n{'=' * 60}\n{title}\n{'=' * 60}")


def show_edge(edge) -> None:
    """边 = 事实。重点看四个时间戳——bi-temporal 的落点。"""
    print(f"  fact       : {edge.fact}")
    print(f"  valid_at   : {edge.valid_at}    (事实何时开始为真)")
    print(f"  invalid_at : {edge.invalid_at}    (何时被后续事实取代,None=仍有效)")
    print(f"  created_at : {edge.created_at}    (系统何时得知)")
    print(f"  expired_at : {edge.expired_at}    (系统何时作废该边)")
    print("  ---")


async def run() -> None:
    uri, user, pwd = neo4j_conn()
    embedder = FastEmbedEmbedder()
    graphiti = Graphiti(
        uri, user, pwd,
        llm_client=make_llm_client(),
        embedder=embedder,
        cross_encoder=CosineReranker(embedder),
        max_coroutines=5,  # 别撞 DeepSeek 并发限流
    )
    try:
        await graphiti.build_indices_and_constraints()

        # -- 1. 摄入两段对话(与 12c L1 同一个叙事,方便两边对照) -------------
        banner("① add_episode:对话进图(比 mem0 慢得多,是预期——在抽实体+关系+时序)")
        episodes = [
            "用户: 帮我推荐点周末喝的,我平时只喝手冲,浅烘的埃塞俄比亚豆最合口味。\n"
            "助手: 好的,浅烘埃塞豆果酸明亮,周末可以试试耶加雪菲的日晒处理。",
            "用户: 对了我住在杭州,在网易做后端开发,最好推荐些公司附近能买到豆子的店。",
        ]
        for i, body in enumerate(episodes):
            t0 = datetime.now(timezone.utc)
            await graphiti.add_episode(
                name=f"对话片段-{i + 1}",
                episode_body=body,
                source=EpisodeType.message,
                source_description="咖啡闲聊",
                reference_time=datetime.now(timezone.utc),
                group_id=GROUP,
            )
            print(f"episode {i + 1} 摄入完成,耗时 {(datetime.now(timezone.utc) - t0).total_seconds():.1f}s")

        # -- 2. 看图里长出了什么:节点(实体)和边(事实) ----------------------
        banner("② 图里长出了什么(也可以开 http://localhost:7474 可视化看)")
        records, _, _ = await graphiti.driver.execute_query(
            "MATCH (n:Entity {group_id: $g}) RETURN n.name AS name, n.summary AS summary",
            g=GROUP,
        )
        print(f"实体节点 × {len(records)}:")
        for r in records:
            print(f"  - {r['name']}: {(r['summary'] or '')[:60]}")

        records, _, _ = await graphiti.driver.execute_query(
            "MATCH (:Entity {group_id: $g})-[r:RELATES_TO]->(:Entity) RETURN r.fact AS fact",
            g=GROUP,
        )
        print(f"\n关系边(事实)× {len(records)}:")
        for r in records:
            print(f"  - {r['fact']}")

        # -- 3. 混合检索:语义 + BM25 + 图遍历,返回的是"边"不是"文档" --------
        banner('③ search("ming 在哪个城市工作?")——注意返回的是带时间戳的边')
        edges = await graphiti.search("用户在哪个城市生活和工作?", group_ids=[GROUP])
        for edge in edges[:5]:
            show_edge(edge)

        banner("完成。下一课 L2:喂矛盾信息,看 invalid_at 如何登场(不删旧边)")
    finally:
        await graphiti.close()


async def reset() -> None:
    # 清库不需要 Graphiti(它的构造会连带初始化 LLM/reranker),直接用 neo4j 驱动
    from neo4j import AsyncGraphDatabase

    uri, user, pwd = neo4j_conn()
    driver = AsyncGraphDatabase.driver(uri, auth=(user, pwd))
    async with driver.session() as session:
        await session.run("MATCH (n) DETACH DELETE n")
    await driver.close()
    print("已清空 Neo4j 整库。")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true", help="清空 Neo4j 后再跑")
    args = parser.parse_args()
    if args.reset:
        asyncio.run(reset())
    asyncio.run(run())
