# L9 · 知识图谱构建 Part I：确定性构建 Domain Graph（CSV → Neo4j）

> 课程：Agentic Knowledge Graph Construction（DeepLearning.AI × Neo4j，C2）
> 本课任务：两份计划齐备，开始**执行**。用一个纯规则工具（**不需要 Agent**）把 CSV 按 construction plan 搬进 Neo4j，构出 domain graph，再用一段 Cypher 抽样验证关系全部建成。

## 0. 本课定位：从"计划"到"构建"

L5-L8 的多 Agent 工作流已产出完整规格：结构化的 `construction_plan` + 非结构化的 `entity_types / fact_types`。本课起进入 Knowledge Graph Construction Tool。

讲师给了一个大框架：整个构建系统若"慷慨"地叫，可称为 **neuro-symbolic agent**——语言模型（neuro）与规则系统（symbolic）的混合。但**本课的 domain graph 构建纯属 symbolic 一侧，不含任何 LLM 调用**。

```
construction plan ──► [construct_domain_graph 工具] ──► Domain Graph (Neo4j)
   (CSV → 节点/关系规则)        纯 Cypher，无 Agent
```

## 1. 为什么 domain graph 不用 Agent

Graph Construction Plan 做的事是"CSV 文件 → 节点类型"的**近 1:1 映射**（外加少量关系映射）。讲师原话：

> "你当然可以塞给一个大上下文窗口的 LLM 去做，但这是一个非常直接的机械过程,你已经把它收敛成了代码（converged to code）。"

于是这项工作交给单个工具 `construct_domain_graph`，它调用一组各有单一职责的 helper 函数。

> **对比 SAP KG 课（Knowledge Graphs for AI Agent API Discovery）**：SAP 课用 SPARQL `CONSTRUCT` 模板 + 通用 transform 把 5 张 CSV **声明式**地转成 RDF——零 LLM、完全确定性。本课 Neo4j 侧用 `LOAD CSV` + `MERGE` 的 Cypher **命令式**地把 CSV 转成属性图,同样零 LLM、完全确定性。两门课在"源数据自带 schema 就走确定性 ETL、不动模型"这一判断上完全一致；区别只是目标模型（RDF 三元组 vs 属性图）和风格（声明式 SPARQL vs 命令式 Cypher）。**有 schema 的结构化数据永远不该用 LLM 搬运**——这是跨两门课稳定的架构师直觉。

## 2. 准备数据库：唯一性约束

从"想数据文件"切到"想数据库",第一步是给即将导入的数据建 uniqueness constraint：某 label 上的某属性必须唯一,正好对应 CSV 里那个唯一 ID 列。

```python
def create_uniqueness_constraint(label, unique_property_key):
    constraint_name = f"{label}_{unique_property_key}_constraint"
    # label / property key 不能用查询参数，只能字符串拼接（Neo4j 限制）
    query = f"""CREATE CONSTRAINT `{constraint_name}` IF NOT EXISTS
    FOR (n:`{label}`)
    REQUIRE n.`{unique_property_key}` IS UNIQUE"""
    return graphdb.send_query(query)
```

两个诚实的技术细节（讲师主动点破）：
- `IF NOT EXISTS`：幂等,重复跑不报错;
- **label 和 property key 无法参数化**——Neo4j 不允许对它们用查询参数,只能字符串拼接。这是"不推荐的 unsafe 做法",生产里应加 sanitize 函数防注入,本课演示从简。

> **架构师视角**:约束**先于**导入建立,不是事后补。唯一性约束既保证数据完整性(不产生重复节点),又给后续 `MERGE` 和查询加速(底层建了索引)。"先立约束再灌数据"是图数据库 ETL 的标准次序;顺序反了,重复节点已经进去再想去重就是另一场噩梦。字符串拼接 label 的 SQL/Cypher 注入口子,是把"演示便利"与"生产安全"分清的典型点——记下来,别抄进生产。

## 3. 从 CSV 批量加载节点

```python
def load_nodes_from_csv(source_file, label, unique_column_name, properties):
    query = f"""LOAD CSV WITH HEADERS FROM "file:///" + $source_file AS row
    CALL (row) {{
        MERGE (n:$($label) {{ {unique_column_name} : row[$unique_column_name] }})
        FOREACH (k IN $properties | SET n[k] = row[k])
    }} IN TRANSACTIONS OF 1000 ROWS
    """
    return graphdb.send_query(query, {"source_file": source_file, "label": label,
        "unique_column_name": unique_column_name, "properties": properties})
```

拆解这段 Cypher：
- `LOAD CSV WITH HEADERS FROM "file:///" + $source_file`:文件 URL 相对于 Neo4j 的 **import 目录**——所以全程用相对路径;
- `MERGE (n:label {id: row[id]})`:MERGE = 先查后建,按唯一列判断节点是否已存在,不存在才建 → 幂等;
- `FOREACH (k IN $properties | SET n[k] = row[k])`:遍历属性名列表,逐个把 CSV 行的值 set 到节点上;
- `IN TRANSACTIONS OF 1000 ROWS`:放进子查询后可**分批提交**,不管 CSV 多大,每次只处理 1000 行——控内存、防大事务。

## 4. 编排:节点与关系两阶段

每个 CSV 先建约束再导节点:

```python
def import_nodes(node_construction):
    uniqueness_result = create_uniqueness_constraint(          # ① 先约束
        node_construction["label"], node_construction["unique_column_name"])
    if uniqueness_result["status"] == "error":
        return uniqueness_result
    return load_nodes_from_csv(                                # ② 再导入
        node_construction["source_file"], node_construction["label"],
        node_construction["unique_column_name"], node_construction["properties"])
```

关系导入不需要唯一性约束(关系本身无身份,靠两端节点唯一 + 每行一条自然去重):

```python
def import_relationships(relationship_construction):
    query = f"""LOAD CSV WITH HEADERS FROM "file:///" + $source_file AS row
    CALL (row) {{
        MATCH (from_node:$($from_node_label) {{ {from_col} : row[$from_col] }}),
              (to_node:$($to_node_label)   {{ {to_col}   : row[$to_col]   }})
        MERGE (from_node)-[r:$($relationship_type)]->(to_node)   // 先 MATCH 已有节点，再 MERGE 关系
        FOREACH (k IN $properties | SET r[k] = row[k])
    }} IN TRANSACTIONS OF 1000 ROWS
    """
    ...
```

`MERGE` 关系的幂等性讲师用 "ABK likes coffee" 举例:即便 CSV 里有两行,两端节点已唯一、`likes` 关系已存在,MERGE 就不会再建第二条。

主函数 `construct_domain_graph` 因此几乎无逻辑,只负责**正确排序**——先建全部节点,节点在了才能连关系:

```python
def construct_domain_graph(construction_plan):
    # ① 先 node（关系需要两端节点已存在）
    for nc in [v for v in construction_plan.values() if v['construction_type'] == 'node']:
        import_nodes(nc)
    # ② 后 relationship
    for rc in [v for v in construction_plan.values() if v['construction_type'] == 'relationship']:
        import_relationships(rc)
```

本课数据的 schema(取自 `approved_construction_plan`):

```
(:Product)-[:Contains]->(:Assembly)
(:Part)-[:Is_Part_Of]->(:Assembly)
(:Part)-[:Supplied_By]->(:Supplier)
```
节点:Assembly / Part / Product / Supplier(各自一个 CSV);关系:Contains / Is_Part_Of / Supplied_By。这就是一张多层 BOM(bill of materials,物料清单)图,支撑"从投诉回溯到零件/供应商"的根因分析。

## 5. 验证:一段 fancy Cypher 抽样每种关系

构建完没有输出,讲师改用一段查询来"验收"——目标不是拉全图,而是**每种关系构建规则至少存在一个实例**:

```python
relationship_constructions = [v for v in approved_construction_plan.values()
                              if v.get("construction_type") == "relationship"]

cypher = """
UNWIND $relationship_constructions AS construction         -- 列 → 多行，每行一条规则
CALL (construction) {                                       -- 对每条规则跑一次子查询
    MATCH (from)-[r:$(construction.relationship_type)]->(to)
    RETURN labels(from) AS fromNode, type(r) AS relationship, labels(to) AS toNode
    LIMIT 1                                                 -- 每种关系只取一个样本
}
RETURN fromNode, relationship, toNode
"""
graphdb.send_query(cypher, {"relationship_constructions": relationship_constructions})
```

三个进阶 Cypher 特性:`UNWIND`(把列表打散成行)、`CALL (construction) { ... }`(带参子查询,对每行执行一次)、`$(construction.relationship_type)`(从查询参数动态取关系类型)。结果如期返回三个三元组:`Product-Contains-Assembly`、`Part-Is_Part_Of-Assembly`、`Part-Supplied_By-Supplier`——与构建规则一致,domain graph 建成。

> **对比 SAP KG 课的"断连诊断"**:SAP 课构完图后用 SPARQL SELECT + NetworkX 可视化,发现两个 API 子图**互不相连**(缺业务流程语义)。本课构完后用 Cypher UNWIND + 子查询抽样,验证的是**每种关系都存在**。两门课都在"构建 ≠ 完成"上留了一道结构验证关;而本课真正的"断连"在下一课——domain graph 与即将从 markdown 抽出的 subject graph 尚未连接。

## 本课总结

| 要点 | 一句话 |
|---|---|
| domain graph 不用 Agent | CSV→节点近 1:1 映射,机械过程"收敛成代码",零 LLM |
| 先约束后导入 | uniqueness constraint 先建,保完整性 + 加速 MERGE |
| LOAD CSV + MERGE + 批处理 | 相对 import 目录、幂等 MERGE、`IN TRANSACTIONS OF 1000 ROWS` |
| 两阶段构建 | 先全部节点后全部关系,关系靠两端节点已存在 |
| 抽样验证 | UNWIND 规则 + 子查询 MATCH 每种关系 LIMIT 1,证明关系全建成 |
| 诚实的坑 | label 不能参数化→字符串拼接有注入风险,生产需 sanitize |

> **记忆点（引出 L10）**：domain graph 已从 CSV 建成,但它只是最终图谱的一块。L10 处理 markdown:用 neo4j_graphrag 流水线把评论切块成 **lexical graph**、抽实体成 **subject graph**,再做 **entity resolution** 把 subject graph 里的 Product 和 domain graph 里的 Product 连起来——这一步同样**纯工具、无 Agent**。

## 与我的资产映射

- 检索层:`agent/skills/agent-selection/3-retrieval.md`(GraphRAG 一节——确定性 Cypher 构图 vs LLM 抽取构图的分野;与 SAP 课的确定性 SPARQL 并列为"有 schema 走 ETL"的证据)
- 成本层:`agent/skills/agent-selection/8-cost-economics.md`(机械搬运不调 LLM,把 token 预算留给建模)
- 面试包:`08-foundations-function-calling-and-rag`(图谱构建 ETL)、`02-tool-gateway`(单一职责工具编排)
- [[project_selection_matrix]]
