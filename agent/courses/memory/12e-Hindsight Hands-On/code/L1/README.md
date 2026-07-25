# L1 · 快速上手:retain / recall / reflect 闭环

## 本课目标

1. **体感 client-server 形态**:mem0 是进程内的库、Graphiti 是库+图数据库,Hindsight 是**服务**——embedded 模式把服务塞进进程(pg0 嵌入式 PostgreSQL),但架构上你调的是 HTTP API;
2. **三操作 vs 两操作**:retain/recall 对应 mem0 的 add/search,**reflect 是别家没有的第三操作**——不是检索,是"基于记忆做深度推理并生成洞察",Hindsight.md §2.1 说"把更新提成一等公民"就落在这里;
3. **第一次体感 TEMPR**:recall 背后是四路并行(语义/BM25/图/时序)+ RRF + cross-encoder + token 裁剪——L3 再解剖,本课先看输出长什么样。

## 运行

```bash
cd "agent/courses/memory/12e-Hindsight Hands-On/code"
source .venv/bin/activate
python L1/main.py
```

首启会下载 embedding + cross-encoder 模型(走 hf-mirror)并初始化 pg0,较慢;之后快很多。

## 观察点

| 步骤 | 看什么 | 对照 |
|---|---|---|
| ① retain 耗时 | 单条几秒?和 mem0 add(1–2s)、Graphiti episode(约 7s)排个序 | 三方写入成本梯度 |
| ② recall 结果 | 返回结构里有没有 fact 类型(world/experience)、时间字段、分数?中文有没有保住(OUTPUT_LANGUAGE)? | 四记忆网络入口 + 12c 的中文问题 |
| ③ 时序查询 | "上周"能不能被解析成时间范围并命中曼特宁那条? | TEMPR 的时序路 |
| ④ reflect | 输出是"检索结果拼接"还是真的做了推理(比如把"讨厌深烘"推广成口味画像)? | reflect ≠ recall |

## 练习

1. `--bank another-person` 换个 bank 重跑,确认 bank 间完全隔离(≈ mem0 user_id / graphiti group_id);
2. retain 一条和已有事实矛盾的信息("我现在改喝深烘了"),recall 看两条是否并存——Hindsight 的矛盾处理策略是什么?(L4 的 observations 演化会回答);
3. 对 ② 的查询换五种问法,观察分数波动——为 L3 的检索解剖攒素材。
