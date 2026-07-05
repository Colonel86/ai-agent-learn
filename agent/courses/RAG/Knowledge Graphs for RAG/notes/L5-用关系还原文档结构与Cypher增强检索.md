# L5 · 用关系还原文档结构 + Cypher 增强向量检索（Form 节点 / NEXT 链表 / retrieval_query）

> 课程：Knowledge Graphs for RAG（DeepLearning.AI × Neo4j）
> 本课任务：L4 构出的 Chunk 节点还是"一袋孤立节点"——有 embedding、无结构。本课给它们加上 **Form / NEXT / PART_OF / SECTION** 关系，把 10-K 文档的原生结构还原进图里；再用 `retrieval_query` 把向量检索升级成"**向量找入口 + 图扩上下文**"。

## 0. 本课目标与路线

Setup 与前几课相同：`Neo4jGraph` 连接 + 四个全局常量（索引名 `form_10k_chunks`、节点标签 `Chunk`、文本属性 `text`、向量属性 `textEmbedding`）。本课路线五步：**① 创建 Form 节点 → ② 每个 section 的 Chunk 串成 NEXT 链表 → ③ 挂 PART_OF / SECTION 关系 → ④ 用 path 做窗口查询 → ⑤ retrieval_query 增强 QA chain**。

## 1. 创建 Form 节点：元数据从 Chunk 里"提上来"

每个 Chunk 在 L4 导入时都随身带着表单级元数据（formId / source / cik / cusip6），任取一个 Chunk 就能拼出 Form 节点所需的全部信息：

```python
cypher = """
  MATCH (anyChunk:Chunk)
  WITH anyChunk LIMIT 1                # 任取一个 chunk 即可
  RETURN anyChunk { .names, .source, .formId, .cik, .cusip6 } as formInfo
"""                                    # {.prop} 是 map projection：只挑指定属性
form_info = kg.query(cypher)[0]['formInfo']   # 恰好就是一个现成的参数字典
```

然后用**参数化查询 + 字典参数**创建 Form 节点（L2 学过：字典整体作为一个参数传入，查询里用 `$param.key` 取值）：

```python
cypher = """
    MERGE (f:Form {formId: $formInfoParam.formId })   # 按 formId 幂等创建
      ON CREATE
        SET f.names = $formInfoParam.names,
            f.source = $formInfoParam.source,          # 回链 SEC 原始文档的 URL
            f.cik = $formInfoParam.cik,                # SEC Central Index Key
            f.cusip6 = $formInfoParam.cusip6           # 证券识别码（L6 靠它做 join）
"""
kg.query(cypher, params={'formInfoParam': form_info})

kg.query("MATCH (f:Form) RETURN count(f) as formCount")  # sanity check：=1
```

> **架构师视角**：`source` / `cik` / `cusip6` 这类"看似没用"的元数据是图谱的**外键预埋**——L6 的 Form 13 数据正是靠 `cusip6` 无痛并入。RAG 系统 ingest 阶段丢元数据 = 亲手锯掉未来做数据融合和溯源（citation）的桥。

## 2. NEXT 链表：一次"调试式"的查询迭代

目标：每个 section 内部的 Chunk 按顺序串成链表。讲师故意演示了一个**逐步发现 bug 的迭代过程**：

| 迭代 | 查询 | 发现的问题 |
|---|---|---|
| ① 按 formId 匹配 | `WHERE c.formId = $formIdParam` | chunkSeqId 乱序 |
| ② 加 `ORDER BY chunkSeqId ASC` | 排序了 | 出现**两个 0**——item7 和 item7a 各有自己的 seq 0 |
| ③ 再加 `AND c.f10kItem = $f10kItemParam` | 同 form + 同 section + 递增 0,1,2,3 | ✔ 正确 |

排好序后 `collect()` 聚成列表，交给 APOC 的链表工具一次性建边：

```python
cypher = """
  MATCH (c:Chunk)
  WHERE c.formId = $formIdParam
    AND c.f10kItem = $f10kItemParam      // 同一 form + 同一 section
  WITH c ORDER BY c.chunkSeqId ASC
  WITH collect(c) as section_chunk_list  // 有序节点列表
    CALL apoc.nodes.link(
        section_chunk_list,
        "NEXT",                          // 相邻节点两两连 NEXT 边
        {avoidDuplicates: true}          // 幂等：重跑不会重复建边
    )
  RETURN size(section_chunk_list)
"""
for item in ['item1', 'item1a', 'item7', 'item7a']:   # 四个 section 各串一条链
  kg.query(cypher, params={'formIdParam': form_info['formId'],
                           'f10kItemParam': item})
```

`kg.refresh_schema()` 后可见新关系类型：`(:Chunk)-[:NEXT]->(:Chunk)`。（注：课程环境是小样本；完整 10-K 有数百个 chunk。）

## 3. PART_OF 与 SECTION：把文档的"树"挂回去

```python
# 每个 chunk 挂到所属 form（23 条关系）
MATCH (c:Chunk), (f:Form) WHERE c.formId = f.formId
MERGE (c)-[:PART_OF]->(f)

# form 指向每个 section 的第一个 chunk（4 条），关系本身带属性
MATCH (first:Chunk), (f:Form)
WHERE first.formId = f.formId AND first.chunkSeqId = 0
MERGE (f)-[r:SECTION {f10kItem: first.f10kItem}]->(first)  # 边上存 section 名
```

讲师说 SECTION 关系是"对看图人类的善意（a kindness for humans）"——从 Form 一跳直达任一 section 的链表头。这也是 LPG 的招牌能力：**关系可以带属性**。最终结构：

```
                 ┌────────── SECTION {f10kItem} ──────────┐
                 │  (×4，指向各 section 链表头)             ▼
   (Form) ◄── PART_OF ── (Chunk₀) ─NEXT→ (Chunk₁) ─NEXT→ (Chunk₂) …
                 ▲            每个 Chunk 都有 PART_OF 回指 Form
```

## 4. Path：图的结构本身就是信息

有了关系就能做纯向量库做不到的**结构化导航**：SECTION 找链表头 → 沿 NEXT 找下一个 → 三节点模式匹配取窗口：

```python
MATCH (c1:Chunk)-[:NEXT]->(c2:Chunk)-[:NEXT]->(c3:Chunk)
    WHERE c2.chunkId = $chunkIdParam      # 只需锚定中间那个
RETURN c1.chunkId, c2.chunkId, c3.chunkId # 三个 chunk 全回来了
```

被匹配到的"节点+关系"序列叫 **path**，可以整体赋给变量、量长度（长度 = 关系数，三节点 path 长度为 2）：

```python
MATCH window = (c1:Chunk)-[:NEXT]->(c2:Chunk)-[:NEXT]->(c3:Chunk)
    WHERE c1.chunkId = $chunkIdParam
RETURN length(window)                      # → 2
```

**边界问题**：把锚点换成 section 第一个 chunk，查询返回空——它没有前驱，硬模式匹配失败。解法是**变长 path**（`*下限..上限`），并用"取最长"消歧：

```python
MATCH window = (:Chunk)-[:NEXT*0..1]->(c:Chunk)-[:NEXT*0..1]->(:Chunk)
    WHERE c.chunkId = $chunkIdParam        # 前后各 0~1 跳，链表头/尾都能匹配
WITH window as longestChunkWindow
    ORDER BY length(window) DESC LIMIT 1   # 变长会匹配出多条 path，取最长
RETURN length(longestChunkWindow)
```

## 5. retrieval_query：向量检索的 Cypher 后处理钩子

本课机制核心。`Neo4jVector` 支持传入 `retrieval_query`：**向量相似度检索先跑，找到的 `node` 和 `score` 作为变量交给这段 Cypher 接力加工**，最终返回 `text` / `score` / `metadata` 三件套给 LangChain。先用一个玩具查询看清机制：

```python
retrieval_query_extra_text = """
WITH node, score, "Andreas knows Cypher. " as extraText  # node/score 来自向量检索
RETURN extraText + "\n" + node.text as text,   # 给检索文本前面拼一句私货
    score,
    node {.source} AS metadata
"""

vector_store_extra_text = Neo4jVector.from_existing_index(
    embedding=OpenAIEmbeddings(), ...,
    index_name=VECTOR_INDEX_NAME,
    text_node_property=VECTOR_SOURCE_PROPERTY,
    retrieval_query=retrieval_query_extra_text,   # NEW：挂上后处理钩子
)
# retriever → RetrievalQAWithSourcesChain(ChatOpenAI(temperature=0), "stuff", ...)
```

问 "What topics does Andreas know about?"——LLM 把私货和检索到的 10-K 文本**混在一起编**：Andreas 既懂 Cypher 又懂自然灾害（10-K 风险章节的内容）。这是一次现场幻觉演示；把问题改成 "What **single** topic..." 才勉强纠偏。

> **架构师视角**：这个玩具实验暴露了 RAG 的本质——**检索结果就是 prompt 注入面**。retrieval_query 里拼什么，LLM 就信什么。正向用是上下文增强（下一节），反向想是安全课题：图谱内容被污染 = 稳定的间接注入通道。凡是"检索→拼接→生成"的链路，拼接层都该被当作特权代码来 review。

## 6. 窗口检索链 vs 裸向量链

把第 4 节的"最长窗口" path 查询装进 retrieval_query，就得到**查询期动态扩窗**的检索器：

```python
retrieval_query_window = """
MATCH window = (:Chunk)-[:NEXT*0..1]->(node)-[:NEXT*0..1]->(:Chunk)
WITH node, score, window as longestWindow
  ORDER BY length(window) DESC LIMIT 1     # 围绕命中 chunk 取最长窗口
WITH nodes(longestWindow) as chunkList, node, score
  UNWIND chunkList as chunkRows            # path 里的节点逐个展开
WITH collect(chunkRows.text) as textList, node, score
RETURN apoc.text.join(textList, " \n ") as text,  # 前后文拼成完整上下文
    score, node {.source} AS metadata
"""
```

建两条链对比：`windowless_chain`（Neo4jVector 默认查询，只回命中的单个 chunk）vs `chain_window`。问 "In a single sentence, tell me about NetApp's business."——答案大体相似，但**窗口版多捕捉到了 NetApp Keystone（其旗舰产品）**：相邻 chunk 里的信息补全了单 chunk 截断的语义。

> **对比课程 04/05 的纯向量 RAG**：那条路线里"句子窗口检索"（sentence-window retrieval）是**索引期**烘焙的——窗口大小在建索引时定死，改窗口 = 重建索引。本课把顺序关系存成图里的 NEXT 边，窗口在**查询期**由 Cypher 现算：改 `*0..1` 为 `*0..2` 就是改一个字符串，零重建。代价是每次检索多一跳图遍历。数据结构进库、策略进查询——又一个"把易变逻辑从固化产物里抽出来"的实例。

> **记忆点（引出 L6）**：本课的所有增强还局限在**一份文档内部**——窗口扩的是同一 10-K 的相邻 chunk。L6 引入第二个 SEC 数据集（Form 13，机构投资人持仓），用 `cusip6` 把外部结构化数据接进图谱，检索上下文第一次跨出文档边界。

## 7. 本课总结

| 要点 | 一句话 |
|---|---|
| Form 节点 | 元数据从任一 Chunk 的 map projection 提上来，字典参数 MERGE |
| NEXT 链表 | 排序 → collect → `apoc.nodes.link`，按 section 分链、avoidDuplicates 幂等 |
| PART_OF / SECTION | 还原文档树；SECTION 边带 f10kItem 属性直达链表头 |
| Path 与变长匹配 | `NEXT*0..1` + 取最长，优雅处理链表头尾边界 |
| retrieval_query | 向量检索输出 node/score，Cypher 接力加工上下文——本课最核心机制 |
| 窗口链对比 | 查询期动态扩窗，窗口版答案多出 Keystone 细节 |

## 与我的资产映射

- 检索层选型：`agent/skills/agent-selection/3-retrieval.md`（"向量找入口 + 图扩上下文"正是 GraphRAG 混合检索的最小实现；查询期扩窗 vs 索引期烘焙窗口可补进取舍表）
- 观测与安全：retrieval_query 作为 prompt 注入面的案例，可作为间接注入攻击面的分析素材
- 对照课程：04/05 纯向量 RAG 的 sentence-window / auto-merging 检索
- [[project_selection_matrix]]
