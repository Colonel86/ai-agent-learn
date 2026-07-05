# L10 · 把 ADE 输出接入 RAG（六步管线、ChromaDB、chunk 级 grounding）

> 课程：Document AI: From OCR to Agentic Doc Extraction（DeepLearning.AI × LandingAI）
> 本课任务（David 的理论课）：回答「拿到 ADE 的干净结构化数据后做什么」——用它建 **RAG**，把一份 74 页 Apple 10-K 变成可查询知识库。讲清关键词检索为何失效、RAG 六步三阶段、chunk vs page 级 embedding、以及 ADE 的 chunk 级 grounding 为何是差异化卖点。本课是概念铺垫，动手实现在下一节（L11 Lab）。

## 0. 从 L9 接上：结构化数据的去处

前面学完了：OCR 为何失效、如何用版面、阅读顺序为何重要、ADE 如何用单一统一工作流给出干净、带 grounding 的输出。现在的问题是——**这些结构化数据拿来干嘛?** 一个答案是**建真实系统**，具体就是 RAG。

场景：给对冲基金建内部平台。分析师有 SEC 文件（如 Apple 10-K），想问「Apple 2023 净销售额多少?」「最大业务风险是什么?」「服务收入同比怎么变?」。信息在文档某处——可能第 28 页某表、第 45 页脚注、或散在 12/15/18 三页的风险披露里。

## 1. 为什么传统关键词检索失效

| 失效模式 | 说明 |
|---|---|
| **语义错配** Semantic mismatch | 搜 "revenue" 但文档写 "net sales"，字面不匹配 → 一无所获，尽管概念相同 |
| **上下文盲** Context blindness | "revenue" 在文档出现 75 次，关键词搜不知道哪一处才切题，不可扩展 |
| **信息碎片** Fragmentation | 「有哪些风险」需综合多页，关键词搜无法跨页合成 |

结论：你需要**语义理解 + 上下文感知检索**——一个懂用户在问什么、而非只匹配字符串的系统。这就是 RAG。

## 2. RAG 六步、三阶段

RAG（Retrieval-Augmented Generation）是当今几乎所有现代文档问答系统的底层架构。六步分属三阶段：

```
┌── 预处理 Preprocessing ──────────────┐
│ ① Parse   原始文档 → 干净结构化文本    │ ← ADE 在这里；garbage-in-garbage-out
│ ② Embed   文本 → 捕捉语义的向量        │
│ ③ Store   向量存进向量库（相似度检索优化）│ ← ChromaDB
├── 检索 Retrieval ────────────────────┤
│ ④ Query   问题也 embed，搜库找 top-k   │
│ ⑤ Retrieve 过滤掉相似度过低的，取回其余 │
├── 生成 Generation ───────────────────┤
│ ⑥ Generate 检索内容作上下文喂 LLM 生成  │
│            自然语言答案 + 对应内容供验证  │
└──────────────────────────────────────┘
```

第⑥步的「附带检索内容供 grounding/验证」对**重度监管组织（HRO）**——金融、医疗、生命科学——至关重要。

## 3. 关键洞察：解析质量是总闸门

> ADE 干净、带 grounding 的输出（阶段一）是整条管线成立的前提。若解析不可靠、喂进去的是失真 OCR 或丢失的表格/图表，**再聪明的 embedding、prompt 工程、检索都救不了你**。

这是本课的中心论点：**garbage in, garbage out**。ADE 把 L5/L6 里那些噪声（OCR 错误、搅乱的表格）在源头消掉，RAG 下游才有可能对。

> **架构师视角**：RAG 圈的注意力常年偏在下游（换 embedding 模型、调 chunk 大小、加 rerank、堆 prompt），但本课把因果链顶端钉死在**解析质量**。一个残酷的杠杆事实：上游解析每丢 5% 的表格数值，下游任何检索/生成优化都无法恢复那 5%——信息在入库前就没了。所以 RAG 选型的第一个决策不是「选哪个向量库」，而是「解析层能否可靠地把表格/图/手写变成结构化文本并带 grounding」。这对应 `3-retrieval.md` 的排序：ingest/parse > chunk > embed > retrieve，越靠上游的错误越不可逆。把预算先花在 parse，而非 rerank。

## 4. Embedding：chunk 级 vs page 级

每个 chunk 文本转成 **1536 维**向量（语义相近 → 向量相近），提问时用问题向量召回相似 chunk。两种粒度权衡：

| 粒度 | 优点 | 适用 |
|---|---|---|
| **Page-Level** | 实现简单、向量少、建库快 | 宽泛问题、短文档 |
| **Chunk-Level** | 检索更精准（精确到表/段）、上下文更细粒度 | 聚焦问题、复杂文档 |

ADE 甚至能给**复杂表格的单元格级 grounding**。Lab 用 chunk 级；生产按用例调。

> **对比课程「Preprocessing Unstructured Data for LLM Applications」**：那门课的核心正是这一步——如何 chunk（按元素/按标题/固定窗口）、如何处理表格与图、如何附 metadata，是「怎么切」的方法论主场。本课的取舍与之一致（chunk vs page 是切分粒度问题），但 ADE 把「切」的质量前置到了 Parse——chunk 边界不是事后按字符数硬切，而是 DPT 按**版面语义**天然切出（一个表是一个 chunk、一段是一个 chunk），且每 chunk 自带 type/bbox/page。也就是说 ADE 让「预处理非结构化数据」这门课里最费劲的分块+清洗，变成了 parse 的免费副产品。

## 5. 向量库 ChromaDB

Lab 用 ChromaDB（本地、开源，适合学习/原型）。要点：

- **一行安装**；
- **持久化**：向量自动落盘，关了 notebook 明天回来数据还在，不必重嵌——高效迭代关键；
- **快速相似检索**：底层 HNSW 索引（Hierarchical Navigable Small World，近似最近邻 SOTA），几千向量也毫秒级返回；
- **本地=生产同 API**：ChromaDB 有 client-server 模式，本地代码直接连远程 server，扩展时**无心智切换**；
- **富 metadata**：每 chunk 存 `chunk_type / page / bbox 坐标`，支持按条件过滤检索；加入时用 ADE 给的**原始 chunk id 作 ChromaDB id**。

（本课的 Lab 讲义提到「lesson six 换成 AWS Bedrock Knowledge Base，但概念不变」——即本地打基础、生产照搬同一数据流。）

### 5.1 为什么本地起步

| 理由 | 说明 |
|---|---|
| 更快迭代 | 改代码、重跑 cell、2 秒见结果，无部署开销 |
| 更低成本 | 初次 API 调用后本地实验几乎免费，不烧云算力 |
| 更清晰学习 | 剥掉云复杂度，专注 RAG 机制与数据流 |

## 6. 检索函数与 chunk 级 grounding

检索一步的五个动作：

```
① Embed   问题 → 向量（同 embedding 模型、同维度）
② Search  查 ChromaDB 取 top-k（默认 k=3）最相似 chunk
③ Score   距离 → 相似度：similarity = 1 - distance（越高越好，可调）
④ Filter  按相似度阈值剔除弱匹配
⑤ Visualize  显示 chunk 文本/id/分数/页码/类型 + 用 bbox 坐标画 grounding 图
```

**Grounding 图是 David 最爱、也是 LandingAI 区别于商品化文档 AI 的地方**：每个 chunk 可生成一张 PNG——从原 PDF 裁出的视觉切片。为何在生产里至关重要：

- **建立信任 → 保证采用**：用户不盲信答案、不被 LLM 幻觉骗；亲眼验证几次正确后就信任系统；
- **合规审计追踪**：金融/医疗/法律要能证明信息来源。「这个数来自 Q3 10-K 第 28 页表 3 第 5 行第 6 列，这是视觉证据」；
- **人审风险缓释**：grounding 图给了 human-in-the-loop 的抓手。

最后用 **LangChain** 编排：`create_retrieval_chain` 组合检索+生成；从 ChromaDB 建 retriever 作为「取信息并塞进 prompt 上下文」的组件。若召回 chunk 过多超出 LLM 上下文窗，LangChain 可把多 chunk 合并进单 prompt，或分多轮迭代喂入。

## 本课总结

| 要点 | 一句话 |
|---|---|
| 关键词检索三失效 | 语义错配 / 上下文盲 / 信息碎片 → 需语义+上下文感知检索 |
| RAG 六步三阶段 | 预处理(parse/embed/store) → 检索(query/retrieve) → 生成 |
| 总闸门 | 解析质量决定成败，garbage-in-garbage-out，ADE 守上游 |
| embedding 粒度 | chunk 级(精准,复杂文档) vs page 级(简单,宽问题)，1536 维 |
| ChromaDB | HNSW 毫秒检索、持久化、本地=生产同 API、富 metadata |
| 检索五步 | embed→search(top-k)→score(1-distance)→filter→visualize |
| grounding 图 | 每 chunk 的原文视觉裁片 = 信任+合规审计+人审抓手 |
| LangChain | create_retrieval_chain 组合检索+生成，超窗则合并/迭代喂入 |

> **记忆点（引出 L11）**：本课把 RAG 讲透了「为什么」和「有哪些步」。L11（Lab）动手把 Apple 10-K 的 ADE 输出（已提供 markdown + JSON chunks，跳过 parse）跑成完整 RAG：用 `text-embedding-3-small` 逐 chunk 嵌入、存进持久化 ChromaDB（chunk id 直接用 ADE 的）、写 `rag_query(question, top_k, threshold)` 做语义检索+阈值过滤+grounding 图，最后用 LangChain `create_retrieval_chain` + `gpt-4o-mini` 生成带出处的答案。亲手验证「干净解析 → 可信 RAG」这条链。

## 与我的资产映射

- 检索层：`agent/skills/agent-selection/3-retrieval.md`（RAG 六步、上游 parse 优先、chunk vs page 粒度、向量库/HNSW 选型）
- 安全护栏：`agent/skills/agent-selection/7-safety-guardrails.md`（grounding 图作合规审计追踪 + 人审抓手，反幻觉）
- 观测·eval 层：`agent/skills/agent-selection/5-observability-eval.md`（相似度阈值、检索命中作可评估指标）
- 部署层：`agent/skills/agent-selection/9-serving-deployment.md`（本地 ChromaDB → client-server → 云 KB 的同 API 扩展路径）
- 对比课程：`agent/courses/Preprocessing Unstructured Data for LLM Applications`（分块方法论）；`agent/courses/Retrieval Augmented Generation (RAG)`
- [[project_selection_matrix]]
