# 12d · Zep / Graphiti Hands-On(自设计动手课)

> **性质**:基于 Graphiti 官方仓库与 Zep 文档(2026-07)自设计的动手实验,与 [`12c-Mem0 Hands-On`](../12c-Mem0 Hands-On/README.md) 成对——
> mem0 代表"消解派"(矛盾就地覆盖),Zep/Graphiti 代表"时序真值派"(矛盾标失效不删除)。
> [`Memory框架/框架现状.md`](../Memory框架/框架现状.md) §七说 staleness 的唯一系统性解法是 Zep/Graphiti,本课就是去亲手验证这句话。
> **对象**:**Graphiti**(Zep 的开源核心引擎,Apache 2.0)。Zep 平台本体已是纯云服务,其 user/thread/context block 概念在 L5 做映射。
> **栈**:DeepSeek(经 OpenAIGenericClient)+ fastembed 自定义 embedder + **Neo4j docker**(带 Browser 可视化,学习期看得见图比轻量更重要;FalkorDB 备选)。

## 与 12c(mem0)的对照关系

| | mem0(12c) | Graphiti(12d) |
|---|---|---|
| 存储模型 | 事实条目(向量库为主) | **时序知识图谱**(实体节点 + 事实边) |
| 矛盾处理 | LLM 消解,UPDATE/DELETE **就地覆盖** | **edge invalidation**:旧边标 `invalid_at`,不删除 |
| 历史真值 | ❌ 旧事实消失 | ✅ "他当时在哪家公司"可查 |
| 检索 | 语义(+可选 BM25/图) | 语义 + BM25 + 图遍历,RRF/图距离重排 |

## 课程表(每课标注面试考点)

| 课 | 主题 | 面试常问的点(本课覆盖) |
|---|---|---|
| **L1** | 环境 + 第一张图:add_episode → 实体/边抽取,Neo4j Browser 看图 | "Zep 和 mem0 架构上的根本区别?"——存的不是事实条目,是图 |
| **L2** | ⭐ bi-temporal 核心:矛盾信息 → invalid_at 失效;时点查询 | "记忆过期/staleness 怎么解决?""怎么支持『他当时…』这种历史查询?"——**本课是全课程最重的面试点**,拿 12c L1 那个消解失败样本对照跑 |
| **L3** | 检索:hybrid search + search recipes(节点/边搜索、center-node 图距离重排) | "图记忆的检索和 RAG 有什么不一样?"——语义+BM25+图遍历三路,呼应 Hindsight.md 的 RRF 笔记 |
| **L4** | 自定义实体类型(pydantic schema)+ JSON episode(业务数据入图) | "怎么把业务领域知识建模进记忆?"——不止聊天,结构化数据同样入图 |
| **L5** | 组装 context block:手搓 Zep `thread.get_user_context` 平替,注入聊天 loop | "检索出的图数据怎么进 prompt?"——Zep 云端 Context Block 的本地复刻 |
| **L6** | ⭐ 对照收官:同一批矛盾/时序/多跳问题,mem0 vs Graphiti 对跑 | "mem0 和 Zep 怎么选?"——用自己的实测数据回答,同时完成 框架现状.md §2.7 "和 mem0 对着跑一遍"的验证 |
| L7(可选) | Zep Cloud 免费层:thread API / user graph 真机体验;或 FalkorDB 换底座 | 托管版形态、graph 底座可插拔 |

## 面试速答弹药库(跑完逐课回填 notes/)

- **一句话定位**:Zep = 把 agent 记忆建成**双时间轴知识图谱**——每条事实(边)带四个时间戳:`valid_at`/`invalid_at`(事实在现实世界的有效区间)+ `created_at`/`expired_at`(系统何时得知/何时作废),**事件时间和摄入时间分离**,这是"bi-temporal"的准确含义;
- **staleness 答法**:新事实到来不覆盖旧事实,而是给旧边写 `invalid_at`——查"现在"走有效边,查"当时"按时间区间过滤,历史永不丢;对比 mem0 的 UPDATE 就地覆盖(12c L1 实测连覆盖都可能失败,直接矛盾并存);
- **代价答法**(别只吹):图谱摄入比 mem0 的条目抽取更重(每个 episode 要抽实体+关系+时序判断,多次 LLM 调用),写入延迟/成本更高;Neo4j 运维复杂度 > 向量库;窄领域仍然是"结构化表 + 代码写入"最优。

## 学习方法与目录

节奏同 12c:跑 `code/Lx/main.py` → 对照观察点 → 蒸馏 `notes/Lx-*.md`(纯文字 + mermaid)。

```text
12d-Zep Graphiti Hands-On/
├── README.md
├── code/          # 环境说明 + 每课 demo(共享 .venv 与 Neo4j 容器)
└── notes/
```

> **最后核对:2026-07**(graphiti-core v0.29.x)
