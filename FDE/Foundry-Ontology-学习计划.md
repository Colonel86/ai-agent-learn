# Foundry / Ontology 学习计划（Palantir 特化 `[P]`）

> **用途**：[`FDE-缺口知识清单.md`](./FDE-缺口知识清单.md) 模块 2 中两项 `[P]` 缺口的详细学习内容、资源与分阶段计划。
> **创建日期**：2026-06-17
> **来源**：Palantir 官方文档 / learn.palantir.com / build.palantir.com + DeepLearning.AI + 权威第三方（见文末 Sources）

---

## 0. 先纠正认知:这两项是同一条链路

「数据建模与本体」和「Foundry/AIP 平台范式」**不是两门独立的学问**,而是同一条流水线:

```
Pipeline Builder  →   Ontology         →   Workshop / AIP
(把数据喂进来)        (建模成对象/属性/      (在对象层上搭运营应用
                      链接/动作 = 本体)        和 LLM Agent)
```

**Ontology(本体)是核心**,Pipeline Builder 是入口,Workshop/AIP 是出口。当**一条链**来学,不是两份清单。

---

## 1. 核心概念心智模型(先建立,再动手)

**Ontology = Foundry 的语义层 / 组织的"数字孪生"**,坐在数据集和模型之上,把它们映射成现实世界的实体。四大积木:

| 积木 | 含义 | 类比 |
|---|---|---|
| **Object Type** | 实体/事件类型(如"航班""机场") | 表的 schema(object = 行) |
| **Property** | 对象的特征(出发时间、乘客数) | 列 |
| **Link Type** | 两个对象类型间的关系 | 外键关系 |
| **Action Type** | 一组可一次性提交的修改 + 副作用 | 带事务的写操作 |

进阶:**Functions**(把代码逻辑挂到对象上)、**Shared Properties**、**Interfaces**(多态)。
分层:**语义层**(object/property/link)+ **动能层 kinetic**(action/function/动态权限)。
👉 官方明确的**学习优先级**:先吃透 object/property/link → 再 action → 再高级模式。

- **Pipeline Builder**:可视化无代码建管道,`输入数据 → transform(filter/join/聚合)→ 输出`,输出可**直接是 ontology object**。数据工程师/分析师用。
- **Workshop**:点选式应用搭建器,**以 Object 层为唯一数据源**,用 Layout 组件 + Events + Actions 搭运营应用(收件箱、告警 triage、态势监控)。

---

## 2. 学习资源(官方为正源 + 权威补充)

### A. Palantir 官方 —— 唯一正源(专有平台,只有官方教)

| 资源 | 是什么 | 免费? |
|---|---|---|
| **AIP Developer Tier**（[build.palantir.com](https://build.palantir.com/)） | 注册个人**免费实例**,动手前提。需身份验证(ID/自拍/信用卡——**仅验证,不扣费**) | ✅ |
| **Foundry Foundations**（[learn.palantir.com](https://learn.palantir.com/)） | 入门路径,**任何人可学**、不需公司环境,完成拿第一枚 Palantir Badge | ✅ |
| **Training Tracks**（[/page/training-tracks](https://learn.palantir.com/page/training-tracks)） | 按角色分轨:**Data Engineer**(含 Pipeline Builder)、**App Developer**(含 Ontology + Workshop)、Data Analyst | ✅ |
| **官方 Ontology 课** | "Understand and Explore Your Ontology" + "Developing Your Ontology",约 **60–90 分钟** | ✅ |
| **官方文档** | [Ontology overview](https://www.palantir.com/docs/foundry/ontology/overview) · [Core concepts](https://www.palantir.com/docs/foundry/ontology/core-concepts) · Pipeline Builder · Workshop docs | ✅ |
| **Build with AIP walkthrough**（[build.palantir.com](https://build.palantir.com/)） | 渐进式:基础 Q&A Agent → Workshop 集成的高级 Agent,**三种 agent 配置**手把手 | ✅ |
| **社区项目** | GitHub [palantir/aip-community-registry](https://github.com/palantir/aip-community-registry) | ✅ |

### B. 权威第三方 —— 可迁移的概念地基(不绑 Palantir)
- **数据建模(正统)**:Joe Reis《Fundamentals of Data Engineering》——star schema、Kimball vs Inmon、data vault。
- **本体/知识图谱思维**:见下方 DeepLearning.AI。

---

## 3. DeepLearning.AI 有没有这两块?

| 两项 | DL.AI 有吗 | 说明 |
|---|---|---|
| **Foundry / AIP 平台** | ❌ 没有 | Palantir 专有平台,只有官方教 |
| **数据建模与本体(概念层)** | ✅ 有,且可迁移 | 见下 3 门 |

**✅ 可用的 3 门(概念地基,迁移到 Ontology)**:
1. **[Knowledge Graphs for RAG](https://www.deeplearning.ai/courses/knowledge-graphs-rag)**（× Neo4j,免费短课）——节点/边/关系、Cypher、向量索引、LangChain 建 QA。**Ontology 概念近亲**:object≈node、property≈property、link≈edge。
2. **Agentic Knowledge Graph Construction**（× Neo4j,Andreas Kollegger,2025 新课）——RAG + 知识图谱、关系建模 + provenance。
3. **[Data Engineering Professional Certificate](https://www.deeplearning.ai/courses/data-engineering)**（Joe Reis × AWS,Coursera,~3 个月@10h/周）——capstone "Data Modeling, Transformation, and Serving" 讲 data vault / 星型 schema / Inmon vs Kimball。**正统数据建模**。

> **关键洞察**:DL.AI 给**可迁移地基**(数据建模 + 本体/图谱思维),**平台特化(Foundry/AIP)只能回 Palantir 官方**。
> 诚实差别:Palantir Ontology **≠** 普通知识图谱——多了动能层(actions/functions)和"运营应用层",用来**驱动业务操作**,不只检索。但语义建模直觉(实体/关系/属性)两边相通。

---

## 4. 分阶段计划(假设额外 ~3–4h/周)

| 阶段 | 时长 | 做什么 | 资源 |
|---|---|---|---|
| **0 准备** | 半天 | 注册免费 AIP Developer Tier;读 Ontology overview + core concepts 建心智模型 | build.palantir.com + docs |
| **1 概念地基** | 1–2 周 | KG for RAG 建 node/edge 直觉;扫 Joe Reis 数据建模章节(star schema/Kimball) | DL.AI(可迁移) |
| **2 官方核心** | 2–3 周 | Foundry Foundations 拿 Badge → 官方 Ontology 课 → 精读 object/property/link/action | learn.palantir.com |
| **3 平台动手** | 2–3 周 | Pipeline Builder 建 `input→transform→ontology object`;Workshop 搭最小运营 app | 免费实例 |
| **4 串起来(AIP)** | 1–2 周 | Build with AIP 做一个 AIP Agent;产出端到端 demo | build.palantir.com |

> **最高性价比一步**:**用 Argus 的真实数据(加密 K线/FGI/regime)在 Foundry 免费实例里复刻** Pipeline→Ontology→Workshop/AIP Agent。一举三得:学会 Foundry + 复用领域 + 产出端到端作品(命中模块 6 可见度 + "shipped in production" 硬筛题)。

---

## 5. 取舍提醒

Foundry/AIP 是**专有平台**,深学 ≈ 押注 Palantir,迁移性不如通用栈(SQL / Postgres / dbt / 知识图谱)。而 [`../FDE-Learning.md`](../FDE-Learning.md) 主目标是 **Anthropic**。所以:

- **阶段 0–1(数据建模 + 知识图谱地基)→ 现在就值得学**,任何数据密集型 FDE 都用得上;
- **阶段 2–4(Foundry/AIP 平台特化)→ 确认押 Palantir 方向再投入**,否则是高专有性沉没成本。

---

## Sources

- [Palantir Learn](https://learn.palantir.com/) · [Training Tracks](https://learn.palantir.com/page/training-tracks)
- [Build with AIP(免费开发者层 + walkthrough)](https://build.palantir.com/)
- [Ontology Overview](https://www.palantir.com/docs/foundry/ontology/overview) · [Core Concepts](https://www.palantir.com/docs/foundry/ontology/core-concepts) · [The Ontology System](https://www.palantir.com/docs/foundry/architecture-center/ontology-system)
- [palantir/aip-community-registry (GitHub)](https://github.com/palantir/aip-community-registry)
- [DeepLearning.AI — Knowledge Graphs for RAG](https://www.deeplearning.ai/courses/knowledge-graphs-rag) · [Data Engineering Professional Certificate](https://www.deeplearning.ai/courses/data-engineering)
