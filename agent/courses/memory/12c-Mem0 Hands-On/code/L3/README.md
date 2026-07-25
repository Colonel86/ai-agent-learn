# L3 · 读路径解剖:打分公式 / threshold / 过滤 / TTL / rerank

## 方法要点

全程 **`infer=False` 入库**——跳过 LLM 抽取,语料内容完全受控,实验只测读路径(L2 证明写路径非确定,不能让它污染检索实验)。零 LLM 成本、秒级完成。

```bash
source ../.venv/bin/activate && python main.py
```

## 实测结果(2026-07,mem0ai 2.0.12 + bge-small-zh + Chroma)

### ① 打分公式:纸面与实装不一致 ⭐

- **实装公式**(源码 `mem0/utils/scoring.py`):`final = (semantic + bm25 + entity_boost) / max_possible`,threshold 在混合**之前**闸语义分;
- **纸面宣传的"相关性/重要性/时近性(recency)加权"里,重要性和时近性都不在 2.x 评分公式里**;
- 本栈实测(`explain=True` 逐项分解):Chroma 无 BM25、spaCy 未装无实体 boost → **三信号退化为纯语义单信号**,`final ≡ semantic`。要吃满混合打分需要 qdrant/pgvector + `pip install mem0ai[nlp]`(L6 验证)。

### ② feature wall 实锤 ⭐

`add(timestamp=...)` 在 OSS 版**直接 raise**:"Temporal reasoning requires a Mem0 API key"——文档注释明写 "Platform-only. Not supported in OSS"。时序推理是付费闸门,这是亲手撞上的第一堵墙(此前只在 Hindsight 的对比材料里见过纸面说法)。`expiration_date` TTL 则是 OSS 可用的。

### ③ 问法敏感度 + 跨语言(同一批记忆,四种问法)

| 问法 | top1 分数 | 命中 |
|---|---|---|
| What coffee does the user like? | 0.631 | 英文条目 |
| 这位用户对咖啡有什么口味偏好? | 0.613 | 中文条目 |
| 他喝什么咖啡? | 0.537 | 中文条目 |
| 用户的饮品习惯是什么? | 0.490 | 中文条目 |

两个结论:**同语言条目优先命中**(zh 模型下中文查询偏爱中文记忆——记忆语言和查询语言一致性影响排序);**问法敏感**:同一意图换个说法,分数从 0.63 掉到 0.49,而 threshold 是绝对值闸门 → **threshold 调高很容易把换了问法的正当查询闸没**(④ 实测 0.45→0.55 之间从 7 条骤降到 1 条)。

### ④–⑥ 快查

- **threshold**:默认 0.1 基本不闸;0.55 时 7→1 条——生产上这个值要按自己语料的分数分布标定,不能抄默认;
- **metadata 过滤**:自定义字段(如 `category`)可直接进 `filters` 与 `user_id` 并列——分域检索/多租户的基础,好用;
- **TTL**:`expiration_date`(YYYY-MM-DD)到期自动隐身,`show_expired=True` 可显影。注意这**不是** Zep 的事实失效——过期时间要写入时就预知,适合促销/会话类,救不了 staleness。

### ⑦ rerank=True:跑了,而且判错了 ⭐(单测归因,已定论)

绕过包装直接单测 LLMReranker:它**真实调用了 deepseek**(2.3–2.6s),分数写在 `rerank_score` 字段并据此排序,但展示的 `score` 字段保持原语义分——所以表面"纹丝不动"。真正的问题是判断质量:对「用户还能继续跑步训练吗?」,它给"每周跑步三次"打 **1.0**、给答案所在的"膝盖受伤禁跑"打 **0.0**。机制:它的 prompt 问的是通用相关性("文档和查询相关吗"),"跑步训练"当然和"每周跑三次"最相关——**通用相关性重排修不了"像 vs 答"的错位**,要答案感知得自定义 `scoring_prompt` 或用特化 cross-encoder。

## 面试可用的表述

> "读了 mem0 2.x 的打分源码并用 explain=True 验证过:实装是 semantic+BM25+实体 boost 的归一化和,宣传里的'时近性加权'并不在评分公式里,时序能力(add 带 timestamp)实际是平台版付费功能,OSS 直接报错。而且这套混合打分是'配置涌现'的——底座用 Chroma 就没有 BM25、不装 spaCy 就没有实体 boost,静默退化成纯向量检索,系统不会告诉你检索质量掉档了(只在启动时打一行 warning)。"

## 练习

1. 开 `MEM0_DEBUG`/logging 查 ⑦ 的 reranker 到底跑没跑;
2. 换 `sentence_transformer` reranker(本地 cross-encoder)重跑 ⑦,对比顺序与延迟;
3. 把语料翻倍成中英双语对照存储,系统测量"查询-记忆同语言加成"的平均分差——给"记忆该存什么语言"一个定量答案。
