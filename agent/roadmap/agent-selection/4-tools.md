Tool/API 选择方案对比（100+ 工具规模）

> **本篇范围**：工具**已经接进来之后**，规模到 100+ 时"怎么选对"（路由/检索）。
> **不在本篇**：工具"从哪来、怎么标准化接入"——那是**协议层（MCP）**的事，与本篇正交。
> ⛓️ 接入用 MCP：选定框架后用 MCP Server 暴露工具，换框架时工具不重写。
>    画像见 [`2-framework/03-framework-profiles.md` §11](2-framework/03-framework-profiles.md)。
> 👉 完整链路：**MCP 接入工具** →（规模大时）**本篇做路由** → LLM 最终选择。

方案一览
方案	原理	延迟	准确率	实现成本	适合场景
Embedding 检索	向量相似度 top-K	~5ms	中	2-3天	第一阶段粗筛
Tool2Vec	为每个工具生成合成查询再 embed	~5ms	中高	1-2周	粗筛（比纯 embedding 好，最高 +27.3% Recall@K(ToolBench)/+30.5%(ToolBank)）
Embedding + Reranker	两阶段：embedding 粗筛 → cross-encoder 精排	~50-100ms	高	2-3周	你的场景最合适
LLM-as-Router	小模型 structured output 选工具	200-800ms	高	2-3天	40-80 工具，需推理能力
Fine-tuned 小模型	蒸馏/微调 7B 或 DeBERTa 分类器	10-50ms	很高	3-6周	高吞吐、工具集稳定
分层/分类树	先选类别再选工具	~10ms	中	1-2天	类别不重叠的场景
Graph-based	工具知识图谱 + 图遍历	50-200ms	高	3-6周	多步工具链规划
1. Embedding 检索（Tool RAG 基础版）
把工具描述 embed 成向量，查询时 cosine 相似度取 top-K。

关键发现（ACL 2025 ToolRet 论文）：通用 embedding 模型在工具检索上表现显著差于文档检索，因为工具描述短、结构化、语义重叠大
推荐模型：BGE-M3 或 Qwen3-Embedding（天然支持中英跨语言）
缺点：纯 embedding 无法区分"token-price"和"token-kline"这种高度重叠的工具
2. Tool2Vec（Embedding 增强版）⭐
不 embed 工具描述本身，而是为每个工具生成合成查询（"什么问题会用到这个工具？"），然后 embed 这些合成查询取平均。

效果：比纯描述 embedding 最高 +27.3% Recall@K（ToolBench）/ +30.5%（论文自建 ToolBank）
原理：捕获"什么问题能用这个工具"而非"工具描述说了什么"
论文：arXiv:2409.02141
3. Embedding + Cross-Encoder Reranker（两阶段）⭐⭐
查询 → Stage 1: Embedding 取 top 20-30 → Stage 2: Cross-encoder 精排 top 8-12
为什么比纯 embedding 好：Cross-encoder 同时看到查询和所有候选工具，能理解工具间的区别（"这个查询是衍生品，不是 K 线"）
推荐 reranker：BGE-reranker-v2-m3（中英跨语言）
Red Hat Emerging Tech 研究原型（2025-12，基于 MCP proxy 适配 ToolBench，博客自述 still in development、非受支持产品）：Tool2Vec + DeBERTa 分类器并行作为 Stage 1，ToolRefiner 作为 Stage 2
论文：arXiv:2409.02141 (ToolRefiner)
4. LLM-as-Router
用小模型（Haiku/GPT-4o-mini）+ structured output 直接选工具。LangChain 已有 LLMToolSelectorMiddleware。

优点：能推理，能理解"Uniswap 基本面"不需要 crypto-market-rank
缺点：100+ 工具描述（约 8-10K tokens）虽塞得进 200K+ 窗口，但真正代价是 token 浪费、注意力稀释、选择准确率下降、破坏 prompt cache（Anthropic Tool Search/defer_loading 省 ~85% token，把 Opus 工具选择准确率 49%→74%）；需要先粗筛
5. Fine-tuned 小模型
在你的领域数据上微调：

Gorilla（NeurIPS 2024，arXiv:2305.15334）：微调 LLaMA-7B，API 调用准确率超 GPT-4 20%
NexusRaven-V2（13B）：开源 function-calling 模型，超 GPT-4 7%
轻量路线：用 Claude 生成训练数据 → 蒸馏到 DeBERTa 多标签分类器，推理 10-50ms
6. Anthropic Tool Search Tool
标记工具为 defer_loading，Claude 内置 ToolSearch 按需加载——你的系统里已经在用这个（ToolSearch deferred tool）。

推荐方案：三阶段 Pipeline
适合你的场景（~200 ToolDocs，中文查询，英文工具描述，coinglass 枚举展开）：

用户查询（中文/英文）
        │
  [Stage 1] Tool2Vec + FAISS        ~5ms
  合成查询 embedding，BGE-M3 跨语言
  → top 20-30 候选
        │
  [Stage 2] Cross-Encoder Rerank    ~50-100ms
  BGE-reranker-v2-m3 精排
  → top 8-12 工具
        │
  [Stage 3] LLM 最终选择（现有）
  Claude Think 结构化输出选 3-5 个工具 + 参数
核心收益：Stage 1 解决"关键词匹配漏召回"（不需要维护 synonym 表），Stage 2 解决"语义相近工具区分"（token-price vs token-kline），Stage 3 保持现有推理能力。

实施节奏：

第 1 周：Tool2Vec embedding 生成 + FAISS 索引替换 _match_score
第 2 周：Cross-encoder reranker 集成
第 3 周：用现有 benchmark 对比评测
要深入某个方案的实现细节吗？