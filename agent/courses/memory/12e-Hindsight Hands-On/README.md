# 12e · Hindsight Hands-On(自设计动手课)

> **性质**:基于 Hindsight 官方仓库/文档(hindsight.vectorize.io,2026-07,v0.8.x)自设计的动手实验,
> 与 12c(mem0,消解派)、12d(Graphiti,时序真值派)组成**三方对照**;Hindsight 是"多策略检索 + 态度建模"派。
> 纸面研究见 [`Memory框架/Hindsight.md`](../Memory框架/Hindsight.md)——那里的 ⚠️/❓ 全部拿到本课来验证。
> **栈**:DeepSeek(**原生 provider,零适配**)+ 内置本地 embedding(bge-small-en-v1.5,默认就是 local)+ **嵌入式 PostgreSQL(pg0,零外部服务)**,Python embedded 模式连 docker 都不用。

## 三方对照速览(面试首答框架)

| | mem0(12c) | Graphiti(12d) | **Hindsight(12e)** |
|---|---|---|---|
| 核心操作 | add / search | add_episode / search | **retain / recall / reflect**(反思是一等公民) |
| 存储模型 | 事实条目 | 时序知识图谱 | 记忆库(bank):实体+关系+时序+稀疏/稠密双索引 |
| 检索 | 语义为主 | 语义+BM25+图 | **四路并行(语义/BM25/图/时序)+ RRF + cross-encoder + token 预算**(TEMPR) |
| 独有赌注 | 最少管线改动 | bi-temporal 历史真值 | **态度即状态**:observations 带证据演化,disposition 性格参数 |
| 工程形态 | 库 or server | 库(需 Neo4j) | **client-server**(embedded/docker),pg0 免运维 |

## 课程表(每课标注面试考点)

| 课 | 主题 | 面试常问的点(本课覆盖) |
|---|---|---|
| **L1** | 快速上手:embedded server + retain/recall/reflect 闭环 | "Hindsight 三操作和 mem0 add/search 的区别?"——reflect(更新/反思)被提为一等公民,不藏在写入路径里 |
| **L2** | retain 解剖:事实/实体/时序抽取,world vs experience 路由 | "事实和经历为什么分开存?"——四记忆网络的入口;`OUTPUT_LANGUAGE=Chinese` 实测中文保真 |
| **L3** | ⭐ TEMPR 解剖:四路检索 + RRF + rerank + token 预算 | **"如何设计 agent 记忆的检索层?"——Hindsight.md §7.1 说这是可直接引用的模板答案,本课把它跑成实感**;时序/多跳查询实测 |
| **L4** | ⭐ observations(知识巩固):证据支撑、proof count、信念演化 | "记忆怎么从事实变成认知?""态度怎么建模?"——对照 mem0 的覆盖式 UPDATE:观察是**被证据精炼**而不是被覆盖 |
| **L5** | CARA/disposition:mission/directives/性格参数(skepticism/literalism/empathy,1–5)对照实验 | "怎么让 agent 有稳定人设?"——同一 bank 不同 disposition 跑同一 reflect,肉眼对比;注意**只影响 reflect 不影响 recall** |
| **L6** | ⭐ 三方对照收官:同一批矛盾/时序/多跳问题,mem0 vs Graphiti vs Hindsight 对跑 | "这三家怎么选?"——用实测回答,完成 框架现状.md §2.7 与 Hindsight.md §五 的 ❓ 验证 |
| L7(可选) | LLM Wrapper 两行集成 + 自动存取的调试性代价 | Hindsight.md §6.2 那句"调试性是退步"的实测 |

## 面试速答弹药库(跑完逐课回填 notes/)

- **一句话定位**:Hindsight = 把 RAG 里成熟的「hybrid search + RRF + cross-encoder rerank」配方系统性搬进记忆层(TEMPR),再加上其它框架都没有的「态度建模」(observations 证据演化 + disposition 性格参数);
- **TEMPR 答题模板**(写入/读取两侧):写入时结构化抽取(实体+关系+时序+稀疏/稠密双表示);读取时多路并行 → RRF 融合 → 重排 → token 预算裁剪;
- **降温判断**(别只吹,引 Hindsight.md §3.3):检索层每个组件都不新,贡献是组合进 memory 场景 + 自动路由权重;真正难复制的是态度建模,但那部分没有生产验证;
- **选型判断**(Hindsight.md §七):个性化陪伴/长期助手(态度一致性值钱)有道理;企业事实检索,年轻框架的风险溢价换不回什么。

## 学习方法与目录

节奏同 12c/12d:跑 `code/Lx/main.py` → 对照观察点 → 蒸馏 `notes/Lx-*.md`(纯文字 + mermaid)。

```text
12e-Hindsight Hands-On/
├── README.md
├── code/          # 环境说明 + 每课 demo(共享 .venv;embedded 模式,无容器)
└── notes/
```

> **最后核对:2026-07**(hindsight v0.8.x)
