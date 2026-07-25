# L1 · 第一张图:episode 进,实体/边出

## 本课目标

1. **体感"图 vs 条目"的区别**:同样两段对话,mem0(12c L1)出来的是 3 条事实字符串;Graphiti 出来的是**实体节点 + 关系边**——"ming—居住于→杭州"、"ming—任职于→网易";
2. **认识边上的四个时间戳**:`valid_at`/`invalid_at`(事实在现实世界的有效区间)+ `created_at`/`expired_at`(系统何时得知/作废)——**bi-temporal 就是这两对时间轴分离**,面试里能准确说出这四个字段就赢了大多数人;
3. **体感摄入成本**:每个 episode 要抽实体、关系、做时序判断,比 mem0 的 add() 慢好几倍——这是图谱路线的固有代价,不是 bug。

## 运行

```bash
cd "agent/courses/memory/12d-Zep Graphiti Hands-On/code"
source .venv/bin/activate
# 确认 Neo4j 在跑:docker ps | grep graphiti-neo4j
python L1/main.py --reset
```

跑完开 <http://localhost:7474>(neo4j / graphiti123),执行 `MATCH (n) RETURN n` 看图。

## 观察点

| 步骤 | 看什么 | 面试挂钩 |
|---|---|---|
| ① 摄入耗时 | 单个 episode 多少秒?对比 12c 的 add() | "图记忆的代价是什么" |
| ② 实体列表 | "用户/杭州/网易/埃塞俄比亚豆"有没有被认出来?摘要写了什么 | 实体抽取质量 |
| ② 边列表 | 事实是不是"主-谓-宾"式的关系,而非孤立句子 | "存的是关系不是文档" |
| ③ search | 返回的边带 valid_at;invalid_at 此时应全为 None | L2 铺垫 |

## 练习

1. 在 Neo4j Browser 跑 `MATCH (a)-[r:RELATES_TO]->(b) RETURN a.name, r.fact, b.name`,把图读成三元组;
2. 再 add 一段提到"耶加雪菲"的对话,看它是新建实体还是挂到已有实体上(实体去重/归并);
3. 把 `group_id` 换成别人,确认图是隔离的(≈ mem0 的 user_id,Zep 云的 user)。
