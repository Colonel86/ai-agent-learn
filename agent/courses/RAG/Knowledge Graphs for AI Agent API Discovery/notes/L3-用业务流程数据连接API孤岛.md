# L3 · 用业务流程数据连接 API 孤岛（BPMN → RDF + 图合并 + Property Path）

> 课程：Knowledge Graphs for AI Agent API Discovery（DeepLearning.AI × SAP）
> 本课任务：把**业务流程数据**（从 BPMN 提取、已转 RDF）合并进 L2 的 API 知识图谱，让断连的 PurchaseRequisition / PurchaseOrder 两个 API 子图经由流程 activity 节点连通，并给 Agent 提供"API 在流程中的依赖关系"上下文。

## 0. 本课目标与路线

L2 结尾诊断出的问题：两个 API 子图**互不相连**——图谱只知道每个 API 长什么样，不知道它们在业务里如何配合。本课的交付物就是往图里加一批**红色节点**（业务流程的 activities），让 API 靠流程信息连起来。路线四步：**① 定义流程 Schema → ② 加载两个图谱 → ③ 合并成一个图 → ④ 查询/可视化验证连通**。

技术栈与 L2 完全相同：`rdflib`（图与 SPARQL）+ `networkx`/`netgraph`（可视化），无新增依赖。

## 1. 业务流程 Schema：Process 与 Activity 两个概念

简化的流程本体只有两个主概念：

```
Process ──(pr:start)──> Activity ──(pr:hasNext)──> Activity ──(pr:hasNext)──> …
(name/description/version)   │ (name/description)
                             └──(pr:entitySet)──> EntitySet   ← 挂到 API 图谱的锚点
```

- **Process**：一组按特定顺序执行的 activities 的集合；有 name / description / version，并链到该流程的**起始 activity**；
- **Activity**：有 name / description，通过 `hasNext` 链到流程中的**下一个 activity**（链表结构）；
- **连接机制**：在适用处把 activity 链到 API 图谱里的 **EntitySet**——比如"Create Purchase Requisition"这个 activity 链到 PurchaseRequisition entity set。
- **简化声明**：本课省略 gateways（分支/汇合），只处理**纯顺序**的流程。

示例：**Procurement of Direct Materials**（直接物料采购）流程，通常由采购员执行——先创建 purchase requisition，审批通过后由它创建 purchase order，经过若干中间步骤后关闭 purchase order。"创建 PR"和"创建 PO"两步各自链到对应 EntitySet，于是 Agent 能推导出：**在这个流程的上下文里，PurchaseOrder entity set 依赖 PurchaseRequisition**。

> **架构师视角**：注意依赖的表述方式——不是给两个 API 之间画一条硬编码的 "depends_on" 边，而是让依赖**经由流程节点间接成立**（PR-activity →hasNext→ PO-activity）。同一对 API 在不同流程里可以有不同关系，依赖是"某流程上下文中的依赖"。这比扁平的 API 依赖表多保留了一层语境，代价只是查询时多走一跳。

## 2. 加载两个图谱：API KG + Process KG

先把 L2 落盘的 API 图谱读回来（验证 14,000+ 三元组，与上一课一致）：

```python
api_kg = Graph()
api_kg = api_kg.parse("ro_shared_data/api_knowledge_graph.ttl",
                      format="turtle")     # L2 序列化的产物直接复用
# → API KG size: 14000+ triples
```

流程数据这边，课程已提前把若干流程从 **BPMN**（Business Process Model Notation，定义业务流程的行业标准）图**提取并转换成 RDF**，同样以 turtle 文件提供：

```python
process_kg = Graph()
process_kg = process_kg.parse('ro_shared_data/business_processes.ttl',
                              format='turtle')
# → Business Process Graph size: ~150 triples（相比 API 图谱小两个数量级）
```

用一个最简 SPARQL SELECT 看看里面有哪些流程：

```python
process_query = """
PREFIX pr: <http://example.org/process#>
SELECT ?name
WHERE {
    ?process a pr:Process .        # 找所有 Process 类型节点
    ?process pr:name ?name .       # 取其 name，只投影名字
}
"""
```

结果包括 **Procurement of Direct Materials、Sell from Stock、External Transportation Planning** 等——大多数公司都会有的典型流程。

## 3. 合并：一个 `+` 号，靠共享 URI 缝合

两个图合并只需一行：

```python
kg = api_kg + process_kg           # rdflib 图加法 = 三元组集合并
# → Combined KG size = 两图规模之和（无重复三元组）

kg.serialize(destination='odata_knowledge_graph.ttl', format='turtle')  # 落盘供后续课复用
```

合并后规模**恰好等于**两个图各自规模之和——两图没有重复三元组。那连接从哪来？来自**共享 URI**：process 图里 activity 的 `pr:entitySet` 三元组，其宾语就是 API 图里 EntitySet 节点的那个 URI。RDF 的全局标识符让两个独立构建的图在合并时**自动缝合**，不需要任何对齐代码。

> **架构师视角**：这是 RDF 相对属性图（Neo4j 等）最被低估的优势——**合并即 set union**。两个团队各自建图，只要 URI 命名约定一致，集成成本趋近于零；换成两个 Neo4j 库则要写实体对齐 ETL。做多源知识集成（API 目录 + 流程库 + 权限模型…）时，这一条足以左右选型。

## 4. 用 Property Path 查询"流程 → API"的连接

合并后就能问跨域问题了：**Procurement of Direct Materials 流程涉及哪些 activities，它们各挂在哪个 API 的哪个 entity set 上？**

```python
connect_query = """
PREFIX odata: <http://example.org/odata#>
PREFIX pr: <http://example.org/process#>
SELECT DISTINCT ?activityName ?entitySetName ?serviceName
{
    ?process pr:name "Procurement of Direct Materials" .   # ① 定位目标流程
    ?process pr:start ?activity .                          # ② 找到起始 activity
    ?activity pr:hasNext* ?nextActivity .                  # ③ property path：* = 沿 hasNext 走 0..n 步，遍历整条链
    ?nextActivity pr:entitySet ?entity_set .               # ④ 只留挂了 entity set 的 activity
    ?entity_set odata:name ?entitySetName .
    ?entity_set odata:entityType/odata:service ?service .  # ⑤ 路径表达式：两跳直达所属 service
    ?service odata:name ?serviceName .
}
"""
```

两处 **property path** 是本课的查询主角：

| 写法 | 语义 | SQL 里的等价物 |
|---|---|---|
| `pr:hasNext*` | 沿 `hasNext` 边走 **0 到任意多步**（含起点自身） | 递归 CTE（WITH RECURSIVE），写起来重得多 |
| `odata:entityType/odata:service` | 两条边**串联**成一跳写完 | 两次 JOIN |

查询结果把断连问题的答案摆在了桌面上：

```
Activity 'Create Purchase Requisition' → EntitySet 'PurchaseRequisition' in Service 'API_PURCHASEREQUISITION_2'
Activity 'Create Purchase Order'       → EntitySet 'PurchaseOrder'       in Service 'API_PURCHASEORDER_2'
```

> **对比 4-tools.md 的工具路由**：工具编排框架（LangGraph 之类）里"先调 API-A 再调 API-B"的依赖通常**写死在编排代码/DAG 里**，加一条流程要改代码发版；本课把执行顺序建模成图谱里的 `hasNext` 边，依赖是**可查询的数据**——Agent 用一句 property path 查询就能现场推导调用顺序，新流程只是往图里添三元组。与 L2 "声明式构图" 一脉相承：把易变逻辑从代码搬进数据。

## 5. 可视化验证：孤岛连成大陆

重复 L2 的可视化流程，但有个关键差别：**只需要一个种子节点**。L2 里 PO 和 PR 两个子图互不可达，得分别取子图再 union；现在经由流程信息互相可达，从任一侧出发即可：

```python
# 只查 PurchaseOrder 一个 entity set 的 URI 作种子
for res in kg.query(find_entity_set_query.format(name="PurchaseOrder")):
    PO_node = str(res.uri)

G = rdf_to_nx(kg)                                  # RDF → NetworkX
G_po = G.subgraph(nx.shortest_path(G, PO_node))    # PO 可达子图——现在已包含 PR 那一簇
```

着色逻辑直接写出了三方结构（形状编码同 L2：○ Service、□ EntityType、△ Property、▽ Navigation）：

```python
for node in G_po:
    if "API_PURCHASEORDER_2" in node:
        node_color[node] = "#404040"      # 灰 = PO API 信息
    elif "API_PURCHASEREQUISITION_2" in node:
        node_color[node] = "#0000FF"      # 蓝 = PR API 信息
    else:
        node_color[node] = "#c00000"      # 红 = 业务流程 activity 节点（本课新增）
```

图上一目了然：蓝簇（PR API）和灰簇（PO API）之间由一串**红色 activity 节点**架桥——L2 结尾的断连图，到这里连通了。

```
L2:   [PR API 子图]          [PO API 子图]        ← 两簇零边
L3:   [PR API 子图]─(红:Create PR)→(红:…)→(红:Create PO)─[PO API 子图]
```

## 6. 整图鸟瞰：太大，塞不进 context

最后看全图。Schema 本身只有寥寥几个概念，但**实例数据**（真实 API 定义 + 流程）撑出来的图谱又大又复杂，只能随机采样可视化：

```python
edges_query = """
SELECT ?node1 ?node2
WHERE { ?node1 ?edge ?node2 . }    # 任意一条边
ORDER BY RAND()                    # 随机打乱
LIMIT 1000                         # 只取 1000 条
"""
```

画出的 1000 条边**只占全图约 6%**，已经密不可辨。结论被讲师点破：**整个知识图谱太大太复杂，不可能整体作为 context 喂给 Agent**——必须有"只取相关部分"的检索机制，这正是下一课的主题。

> **对比 12a Agent Memory**：这和记忆系课程的结论同构——12a 里长期记忆存量再大，每轮也只 retrieve top-k 相关记忆进 prompt；这里图谱再全，也只能检索相关子图给 Agent。**"存储层可以无限大，context 窗口永远是稀缺资源"** 是两条线共同的第一性约束，解法都是"外置存储 + 按需检索"。

## 7. 本课总结

| 要点 | 一句话 |
|---|---|
| 流程 Schema | Process →start→ Activity →hasNext→ Activity 链表，省略 gateways 只做顺序流 |
| BPMN → RDF | 流程源自 BPMN 标准图，转 RDF 后仅 ~150 三元组（API 图的 1%） |
| 挂接机制 | Activity 经 `pr:entitySet` 指向 API 图的 EntitySet URI——共享 URI 即连接 |
| 图合并 | `api_kg + process_kg` 集合并，规模=两图之和，零对齐代码 |
| Property Path | `hasNext*` 一行遍历整条 activity 链，`entityType/service` 串联跳 |
| 依赖推导 | PO 依赖 PR 是"流程上下文中的依赖"，经流程节点间接成立 |
| 连通验证 | 单种子节点即可达两个 API 簇，红色 activity 节点架桥 |
| 规模问题 | 全图 6% 采样已不可辨，整图塞不进 context → 需要检索 |

## 与我的资产映射

- 工具层选型：`agent/skills/agent-selection/4-tools.md`（工具依赖从编排代码下沉为图谱数据——工具路由的另一条实现路线）
- 检索层：`agent/skills/agent-selection/3-retrieval.md`（GraphRAG 一节——多跳 property path 查询正是图检索优于向量检索的场景）
- 面试包：`02-tool-gateway`（"Agent 如何知道 API 调用顺序"的图谱答案：流程边 + property path）
- [[project_selection_matrix]]

> **记忆点（引出 L4）**：孤岛已连成大陆，但大陆太大——1000 条边只是全图 6%，整图不可能塞进 Agent 的 context。L4 讲**用语义 embedding 从知识图谱中做 API discovery**：design time 为检索做准备，runtime 接住用户查询、只捞出相关的 API 子图。
