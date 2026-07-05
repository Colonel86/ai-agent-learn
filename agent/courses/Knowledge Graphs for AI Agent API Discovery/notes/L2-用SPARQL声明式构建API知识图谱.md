# L2 · 用 SPARQL 声明式构建 API 知识图谱（rdflib + SPARQL CONSTRUCT）

> 课程：Knowledge Graphs for AI Agent API Discovery（DeepLearning.AI × SAP）
> 本课任务：把描述 API 的 5 张 CSV（源自 OData EDMX 规范）**声明式**地转换成 RDF 知识图谱，并可视化诊断它的"断连"问题。

## 0. 本课目标与路线

开场先展示两个交付物：一张 PurchaseOrder 与 PurchaseRequisition 两个 API 的子图（**互不相连**），一张完整知识图谱采样（有一个高度连接的核心——那是下一课业务流程数据才会带来的）。本课路线三步：**① 输入数据 → ② 知识图谱 Schema → ③ 知识图谱构建**。

技术栈：`pandas`（读 CSV）+ `rdflib`（构图与 SPARQL）+ `networkx`/`netgraph`（可视化）。数据源是 OData API 的 EDMX 规范，但方法论不限于 OData——任何 API 规范（OpenAPI 等）都适用。

## 1. 输入数据：描述 API 的 5 张 CSV

5 张 CSV 分别描述 OData API 的五类概念（每张表 = 图谱里的一类节点）：

```python
services_df = pd.read_csv("ro_shared_data/services.csv",
                          sep=',',
                          dtype={'version': 'string'}).fillna('')  # version 强制 string、空值统一填 ''
```

| CSV | 内容 | 示例行 |
|---|---|---|
| services | API 服务：name / version / description | PURCHASEORDER v4.0，"OData service for Purchase Order" |
| entity_types | 实体类型：name + 所属 service | PurchaseRequisitionItem ∈ PURCHASEREQUISITION |
| properties | 属性：service / entityType / name / label / type / maxLength / key / selectable | CashDiscount，Decimal 类型 |
| navigations | 导航：service / name / navigateFrom / navigateTo / **multiplicity** | PO Item → PO 是 `1`；PO → PO Item 是 `*`（一对多） |
| entity_sets | 实体集：实体实例的逻辑容器，每个 entityType 恰属一个 entitySet | — |

数据规模：**39 个 services、101 个 entity sets / entity types、126 个 navigations、2000+ 个 properties**。

> **架构师视角**：这 5 张表就是"API 目录"的关系化建模。multiplicity（`1` vs `*`）是被大多数工具检索方案丢掉的信息——向量检索一个 API 描述拿不到"采购订单可含多个行项目"这种基数约束，而 Agent 组合调用 API 时恰恰需要它。

## 2. 知识图谱 Schema（源自 Entity Data Model）

Schema（本体）定义图里允许出现的节点类型和边类型，是构图的蓝图，也是后续查询/推理/推断的依据。OData 的 Entity Data Model 直接给出了它：

```
Service ──(所属)── EntityType ──(property)── Property
              │         │
        EntitySet    Navigation(navigateFrom / navigateTo + multiplicity)
        (实例容器)
```

- **Service**：入口，以机器可读形式公布自己的数据模型，让通用客户端能以良定义的方式交互；
- **EntityType**：描述端点数据结构的基本单元（如 PO Header、PO Item）；
- **Property**：数据形状（type / maxLength / 是否 key / 是否 UI 可选）；
- **Navigation**：EntityType 之间的关联（Header ↔ Items，带基数）；
- **EntitySet**：EntityType 实例的逻辑容器。

> **对比 3-retrieval 的 GraphRAG**：GraphRAG 通常靠 LLM 从非结构化文本抽实体关系（有幻觉风险、需人工校验）；本课的源数据是**结构化 API 规范**，schema 直接从 EDMX 推导、映射完全确定性——**零幻觉构图**。判断用哪种：源数据本身有 schema 就走确定性 ETL，只有自然语言才动用 LLM 抽取。

## 3. SPARQL 速成：把 SQL 直觉迁移到 RDF

SPARQL 是 RDF 的标准查询语言，可理解为"RDF 界的 SQL"，语法上也确实相似。三个关键概念：

1. **Triple pattern**：像 RDF 三元组，但允许变量（`?` 开头）：`?service :name ?serviceName`；
2. **图模板匹配**：WHERE 子句定义一个图模板，求解 = 找到所有"变量 → RDF 项"的映射（solution mapping），使模板代入后成为图的子图；SELECT 的结果像 SQL 一样是表（列=变量，行=解）；
3. **查询形式**：SELECT（查询）、INSERT（增补三元组）、**CONSTRUCT（构造新图）**——本课构图的主角。

## 4. 声明式构建：CONSTRUCT 模板 + 通用 transform 函数

**"声明式"的含义**：图的形状写在 SPARQL CONSTRUCT 查询里（数据），而不是写在 Python 循环里（代码）。每类概念一个查询模板：

```python
construct_services = """
PREFIX odata: <http://example.org/odata#>
CONSTRUCT {
    ?service a odata:Service .            # 声明节点类型
    ?service odata:description ?description .
    ?service odata:version ?version .
    ?service odata:name ?name .
}
WHERE {
    BIND(IRI(CONCAT("http://data.example.org/Service/", UCASE(?name)))
    AS ?service)                          # 用 name 拼出全局唯一 URI
}
"""
```

配一个**通用 transform 函数**，5 张表复用同一个内核：

```python
def transform(df, construct_query, first=False):
    query = prepareQuery(construct_query)
    for _, row in df.iterrows():
        # 每行 CSV → {变量名: 值} 绑定（跳过空值列）
        binding = dict((headers[k], Literal(row[k]))
                       for k in df.columns if len(str(row[k])) > 0)
        # initBindings 把变量代入模板并执行
        results = query_graph.query(query, initBindings=binding)
        for result in results:
            result_graph.add(result)      # 每行实例化出一小块图
    return result_graph
```

单行试跑验证（`first=True`）：PURCHASEORDER 服务生成 4 条三元组（type / description / name / version），turtle 序列化肉眼可查。然后依次处理 5 张表，图谱滚雪球增长：

| 处理阶段 | 图谱规模（三元组） |
|---|---|
| services | 156 |
| + entity_sets | 457 |
| + entity_types | 700+ |
| + properties | **14,316**（2000+ 属性贡献大头） |
| + navigations | 更多（最终图谱） |

> **架构师视角**：`模板(数据) + 通用执行器(代码)` 是可迁移的 ETL 模式——schema 演化只改 SPARQL 字符串、不动 Python。与课程 12 Procedural Memory 的"prompt 即数据"同构：**把易变的逻辑从代码里抽出来变成数据，系统就获得了不发版演化的能力**。

## 5. 断连诊断：图谱结构完整 ≠ 语义完整

构好的图谱 Agent 已可用来与单个 API 交互，**但缺"这些 API 在业务流程中如何配合"的上下文**。用 PurchaseRequisition（采购申请）和 PurchaseOrder（采购订单）验证——它们在直接物料采购流程中明明有先后依赖：

```python
# ① SPARQL SELECT + FILTER 查出两个 entity set 节点的 URI
for res in kg.query(find_entity_set_query.format(name="PurchaseOrder")):
    PO_node = str(res.uri)

# ② RDF → NetworkX，取各自可达子图并合并可视化
G = rdf_to_nx(kg)
G_po = G.subgraph(nx.shortest_path(G, PO_node))   # PO 可达子图
G_pr = G.subgraph(nx.shortest_path(G, PR_node))   # PR 可达子图
G_prpo = nx.union(G_pr, G_po)
```

netgraph 可视化用形状编码节点类型：**○ Service、□ EntityType、△ Property、▽ Navigation**；蓝色 = PurchaseRequisition API、灰色 = PurchaseOrder API。结果一目了然：**两簇完全不相连**——每个 API 内部连通（service 居中、entity types 环绕、properties 成雾），跨 API 之间零边。

> **对比课程 10-MCP 的工具发现**：MCP 的 `list_tools` 给 Agent 的是**平面工具清单**，工具间关系为零；本课的图谱把"API 之间怎么协作"显式建模成边。当工具规模到几百上千（4-tools.md 的工具爆炸问题），平面清单+向量检索只能按"描述相似"找工具，图谱才能按"流程相邻"找工具——这正是面试包 `02-tool-gateway` 的核心素材。

**收尾**：`kg.serialize(destination='api_knowledge_graph.ttl', format='turtle')` 落盘（turtle 是紧凑的人类可读 RDF 序列化：`@prefix` 缩写 + 分号/逗号合并同主语三元组），供下一课复用。

## 6. 本课总结

| 要点 | 一句话 |
|---|---|
| 声明式构图 | 图形状写在 SPARQL CONSTRUCT 模板里，不写在代码里 |
| 通用 transform | CSV 行 → initBindings 变量代入 → 三元组，5 张表一个内核 |
| Schema 先行 | 从 EDMX 推导本体，构图前先定蓝图 |
| 断连诊断 | API 图谱结构完整但缺业务流程语义，PO/PR 两簇不相连 |

> **记忆点（引出 L3）**：本课构出的图谱是一座座"API 孤岛"——每个 service 内部连通、彼此断连。L3 引入**业务流程数据**把孤岛连成大陆，Agent 才能回答"完成采购需要依次调哪些 API"这类跨 API 的发现问题。

## 与我的资产映射

- 工具层选型：`agent/skills/agent-selection/4-tools.md`（工具爆炸 → 图谱化工具发现是向量检索之外的另一条路线）
- 检索层：`agent/skills/agent-selection/3-retrieval.md`（GraphRAG 一节——确定性构图 vs LLM 抽取构图的分野）
- 面试包：`02-tool-gateway`（图谱驱动的 API/工具发现）
- [[project_selection_matrix]]
