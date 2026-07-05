# L10 · 知识图谱构建 Part II：非结构化抽取 + Entity Resolution（收官）

> 课程：Agentic Knowledge Graph Construction（DeepLearning.AI × Neo4j，C2）· 收官篇
> 本课任务：用 `neo4j_graphrag` 流水线把 markdown 评论切块成 **lexical graph**、按 schema 抽实体成 **subject graph**，再做 **entity resolution** 把 subject graph 连回上一课的 domain graph——得到一张完整连通的知识图谱。本步同样**纯工具、无 Agent**。

## 0. 本课定位：三张子图，最后一根线

上一课(L9)从 CSV 建出 domain graph。本课处理 markdown,产出另两张子图,并把它们缝合:

```
CSV ──(L9,规则)──► Domain Graph  ┐
                                  ├─ Entity Resolution ─► 完整连通 KG
markdown ─(L10,graphrag)─► Lexical Graph (chunks + Document)
                          Subject Graph (extracted entities) ┘
```

| 子图 | 来源 | 内容 |
|---|---|---|
| Domain Graph | CSV(L9) | Product / Part / Supplier / Assembly + BOM 关系 |
| Lexical Graph | markdown 切块 | Chunk 节点 + 互连 + 挂到 Document 节点 |
| Subject Graph | markdown 抽取 | 从文本抽出的实体(Product/Issue/Feature/Location)及其关系 |

讲师明确:本课**整段不是 agentic**,全部由工具处理。两个主工具 + 一堆 helper:`make_kg_builder`(每文件一个,做切块+抽取)、`correlate_subject_and_domain_nodes`(连接子图与域图)。

> **对比 Neo4j C1（Knowledge Graphs for RAG）**：C1 教你在**已有**知识图谱上做 GraphRAG 检索(vector index + Cypher 检索)。C2 这门课教你**从零构建**那张图——本课正是"构建侧"最难的一环:非结构化文本 → 图。C1 的检索质量,天花板由 C2 这里的抽取与实体消解质量决定。先会建图,C1 的检索才有好料可查。

## 1. neo4j_graphrag KG Builder 流水线七步

讲师端到端过了一遍 `SimpleKGPipeline` 的组件链,理解这七步就理解了整条流水线:

```
① Document Loader  载入文档(内置支持 PDF；本课用自定义 markdown loader)
② Text Splitter    切块(本课用正则按 "---" 切评论)
③ Chunk Embedder   每块算 vector embedding
④ Entity&Relation Extractor  LLM 按抽取计划抽实体与关系
⑤ Graph Pruner     (可选)清理图
⑥ KG Writer        把内存图写进 Neo4j
⑦ Entity Resolver  合并疑似同一实体的节点
```
①-⑤在内存里进行,⑥才落库。

## 2. SimpleKGPipeline 接口与自定义组件

```python
SimpleKGPipeline(
    llm=llm_for_neo4j,            # 抽实体/关系的 LLM
    driver=neo4j_driver,          # 写图的 Neo4j driver
    embedder=embedder,            # 给 chunk 算 embedding
    from_pdf=True,                # "算是 True"——因为塞了自定义 loader 冒充 PDF
    pdf_loader=MarkdownDataLoader(),        # 自定义 markdown 载入器
    text_splitter=RegexTextSplitter("---"), # 自定义切块器
    schema=entity_schema,                   # 约束抽取的实体/关系类型
    prompt_template=contextualized_prompt,  # 每块抽取用的提示词
)
```

**自定义切块器**——继承 `TextSplitter`,用正则把 markdown 按 `---`(评论间的分页符)切开,包成库要的 `TextChunk`:

```python
class RegexTextSplitter(TextSplitter):
    def __init__(self, re): self.re = re
    async def run(self, text):
        texts = re.split(self.re, text)
        chunks = [TextChunk(text=str(t), index=i) for i, t in enumerate(texts)]
        return TextChunks(chunks=chunks)
```

**自定义 markdown 载入器**——继承 `DataLoader`,伪装成解析 PDF(返回 `PdfDocument`),真正干的是读 markdown、用正则抽 H1 当标题塞进 `DocumentInfo`,把标题这类元数据带进后续 chunk 的上下文:

```python
class MarkdownDataLoader(DataLoader):
    def extract_title(self, md):                 # 抓第一个 # H1 当标题
        m = re.search(r'^# (.+)$', md, re.MULTILINE)
        return m.group(1) if m else "Untitled"
    async def run(self, filepath, metadata={}):
        md = open(filepath).read()
        return PdfDocument(text=md,
            document_info=DocumentInfo(path=str(filepath),
                                       metadata={"title": self.extract_title(md)}))
```

> **对比 3-retrieval.md（Chunking 策略）**：检索栈选型里 chunking 被列为"检索质量的真正瓶颈"。本课讲师也承认"文本切分本身就是一门艺术",这里做的是**结构感知切分**(按 markdown 分页符,而非盲目定长滑窗)——因为知道数据形状(每条评论一段),就能切在语义边界上。这正是 3-retrieval.md 强调的"解析/切分决定上限":切错了,后面 embedding 和抽取再强也救不回。

## 3. Entity Schema：把抽取锁进已批准类型

用 L8 产出的 `approved_entities` / `approved_fact_types` 装配抽取 schema——**把 LLM 的自由度锁死**:

```python
schema_node_types         = approved_entities                       # ['Product','Issue','Feature','Location']
schema_relationship_types = [k.upper() for k in approved_fact_types] # ['HAS_ISSUE','INCLUDES_FEATURE','USED_IN_LOCATION']
schema_patterns           = [[f['subject_label'], f['predicate_label'].upper(), f['object_label']]
                             for f in approved_fact_types.values()]  # (Product, HAS_ISSUE, Issue) 等

entity_schema = {
    "node_types": schema_node_types,
    "relationship_types": schema_relationship_types,
    "patterns": schema_patterns,
    "additional_node_types": False,   # False = 只准用上面这些类型，不许自造
}
```

`additional_node_types=False` 是关键闸门:抽取时只允许出现批准过的节点类型。这把 L8 的建模成果变成了 L10 抽取的硬约束——**计划真正约束了执行**。

抽取 prompt 是每块动态拼的:通用抽取指令(要求输出 JSON 的 nodes/relationships、给节点唯一 ID、尊重关系方向) + 注入 `{schema}` + 注入 `file_context`(文件头几行,给 chunk 补文档级上下文,让 LLM 知道"这块属于哪个文档"):

```python
def file_context(file_path, num_lines=5):        # 抓文件前几行当上下文
    ...
def make_kg_builder(file_path):
    ctx = file_context(file_path)
    contextualized_prompt = contextualize_er_extraction_prompt(ctx)
    return SimpleKGPipeline(... prompt_template=contextualized_prompt ...)
```

每个文件一个 builder(prompt 因文件内容而异),循环处理 10 个评论文件,每个约耗时到一分钟(取决于 OpenAI 响应)。跑完得到 lexical graph + subject graph。

## 4. Entity Resolution 第一步：找标签与键

图建好了但**没连**:subject graph 的 Product 和 domain graph 的 Product 是两拨节点。要做实体消解,分四步:找标签 → 找键 → 归一化键 → 值相似度连接。

先认清标记:graphrag 抽出的节点会带 `__Entity__`(还有 `__KGBuilder__`)特殊标签。据此区分两张图:**带 `__Entity__` = subject graph,不带 = domain graph**。

```python
# subject graph 的实体标签：匹配 __Entity__，UNWIND 打散，过滤掉 __ 前缀的内部标签
def find_unique_entity_labels():
    return graphdb.send_query("""MATCH (n) WHERE n:`__Entity__`
        WITH DISTINCT labels(n) AS entity_labels
        UNWIND entity_labels AS entity_label
        WITH entity_label WHERE NOT entity_label STARTS WITH "__"
        RETURN collect(entity_label) as unique_entity_labels""") ...
```
讲师强调用**查询实际结果**而非假设:计划里想抽 Location,但 LLM 可能没抽到——以图里真实出现的标签为准(得到 Product / Location / Issue / Feature)。

再对每个标签找**唯一属性键**。subject 侧(`find_unique_entity_keys`)和 domain 侧(`find_unique_domain_keys`)对称。差别很典型:
- domain 侧键**干净且一致**(全来自单个 CSV):`product_name / price / description / product_id`;
- subject 侧键**杂乱**(LLM 从各条评论自由抽,没约束属性):`name / material / shelf_depth ...` 一大堆,不同产品还不一致。

## 5. Entity Resolution 第二步：归一化 + 键关联

`normalize_key` 做 NLP 里 stemming 的简版:小写、去空白、去 label 前缀、内部空格转下划线——让两侧键可比:

```python
def normalize_key(label, key):
    lowercase = key.lower()
    unprefixed = re.sub(f"^{label.lower()}[_ ]*", "", lowercase)  # "Product_name" → "name"
    return re.sub(" ", "_", unprefixed)
# Product_name / Product Name / product name  →  name ；  price → price
```

再用 `rapidfuzz` 对两侧键做模糊匹配,超阈值的配成对(供下一步比值):

```python
from rapidfuzz import fuzz
def correlate_entity_and_domain_keys(label, entity_keys, domain_keys, similarity=0.9):
    correlated = []
    for ek in entity_keys:
        for dk in domain_keys:
            score = fuzz.ratio(normalize_key(label, ek), normalize_key(label, dk)) / 100
            if score > similarity:
                correlated.append((ek, dk, score))
    correlated.sort(key=lambda x: x[2], reverse=True)   # 最像的排前面
    return correlated
# Product: name↔product_name 1.0、price↔price 1.0、description↔description 1.0
```

## 6. Entity Resolution 第三步：值相似度 Jaro-Winkler → CORRESPONDS_TO

键对上了还不够,得比**值**:两个 Product 节点的 name 是否真是同一产品。用 Cypher 内置的 `apoc.text.jaroWinklerDistance`(编辑距离,0=完全一致,1=毫不相似):

```python
graphdb.send_query("""
MATCH (entity:$($entityLabel):`__Entity__`), (domain:$($entityLabel))   -- 笛卡尔积配对
WHERE apoc.text.jaroWinklerDistance(entity[$entityKey], domain[$domainKey]) < 0.1  -- 极严阈值
MERGE (entity)-[r:CORRESPONDS_TO]->(domain)   -- 相似则连一条 CORRESPONDS_TO
ON CREATE SET r.created_at = datetime()        -- MERGE 的 upsert 子句：首次创建
ON MATCH  SET r.updated_at = datetime()        -- 已存在则更新时间戳
...""", {"entityLabel":"Product","entityKey":"name","domainKey":"product_name"})
```

三处工程判断:
- **阈值要狠**:讲师演示 0.5 时 "Gothenburg Table" 竟和 "Stockholm Chair" 沾边,故实践取 0.1,尽量逼近真同;
- **MERGE = upsert**:`ON CREATE` / `ON MATCH` 两个子句让这段可反复运行而不产生重复关系;
- **距离 < 0.1** 而非相似度 > 0.9:Jaro-Winkler 返回的是距离,0 才是完美匹配,方向别搞反。

讲师也列了 Neo4j 提供的其他文本相似函数(Hamming / Levenshtein / Sørensen-Dice / fuzzyMatch)和向量余弦——不同数据集该挑不同度量,甚至可以"专门搞一个 Agent 来为你的数据选消解策略"。

## 7. 收尾：全标签循环连接

对所有 subject 标签循环:找键 → 关联键 → 取最匹配的键对 → 连节点:

```python
for entity_label in find_unique_entity_labels():
    entity_keys = find_unique_entity_keys(entity_label)
    domain_keys = find_unique_domain_keys(entity_label)
    correlated_keys = correlate_entity_and_domain_keys(entity_label, entity_keys, domain_keys, similarity=0.8)
    if correlated_keys:
        top = correlated_keys[0]                                   # 最像的键对
        correlate_subject_and_domain_nodes(entity_label, top[0], top[1])
    else:
        print("No correlation found")
```

结果符合预期:**Product 连上了**(建了 10 条 CORRESPONDS_TO),而 Location / Issue / Feature 在 domain graph 里本就没有对应节点,故无关联——这正确。至此三张子图缝合,得到一张完整连通的知识图谱。

## 全课收官

### ① Conclusion 要点

Conclusion 只有短短几句,提炼全课:你搭了一个**多 Agent 系统**,把**结构化 + 非结构化**数据一起转成知识图谱;学会了如何设置每个专家 Agent(用什么 prompt、定义什么 tool)、以及**如何在 Agent 之间共享 context**(贯穿全课的 session state 接力)。

### ② L1-L10 全课回顾表

| # | 主题 | 核心产物 | Agent? |
|---|---|---|---|
| L1 | 知识图谱是什么 + 数据集 | 关系型 schema → 图的直觉 | — |
| L2 | 多 Agent 系统设计 | agent = LLM + 循环 + switch 的控制流算子;整体架构 | — |
| L3 | Google ADK 单 Agent | 会建/跑一个 agent | — |
| L4 | Agent 团队 | root + 两个 sub-agent 协作 | 是 |
| L5 | User Intent Agent | `approved_user_goal`(头脑风暴图谱目标) | 是 |
| L6 | File Suggestion Agent | `approved_files`(选相关 CSV) | 是 |
| L7 | 结构化 Schema 提案 | `approved_construction_plan`;critic + refinement loop | 是 |
| L8 | 非结构化 Schema 提案 | `approved_entity_types` + `approved_fact_types`;NER + fact 双专家 | 是 |
| L9 | 构建 Part I:Domain Graph | CSV → 属性图,纯 Cypher 规则构建 | **否** |
| L10 | 构建 Part II:Lexical/Subject + 消解 | graphrag 抽取 + entity resolution → 完整连通 KG | **否** |

一条主线:**L5-L8 用 Agent 产出各种"计划",L9-L10 用确定性工具"执行计划"**。判断力交给 Agent,机械活交给代码。

### ③ 架构师的裁决

> **架构师的裁决——多 Agent 构建 KG（本课）vs 单管道确定性构图（SAP 课）**：
>
> **走 SAP 课那种单管道确定性构图**(SPARQL CONSTRUCT / Cypher LOAD CSV,零 LLM),当:① 源数据自带 schema(OData EDMX、CSV 表头、数据库导出);② 映射稳定、可枚举;③ 要可复现、可审计、零幻觉;④ 规模大、成本敏感。这类"搬运"任务上多 Agent 是纯浪费——本课 L9/L10 的 domain graph 与 pipeline 抽取本身就退回了确定性工具,印证了这一点。
>
> **上本课这种多 Agent 建模**,只在**真正需要判断力**的环节:① 从自然语言里**决定图谱该长什么样**(哪些实体值得建、哪些事实值得抽、well-known vs discovered);② 目标模糊、需与人来回澄清(user intent、schema 的 critic/approve 闭环);③ 非结构化文本无既定 schema,必须靠 LLM 做 NER 与 triple 抽取。
>
> **裁决线**:**"数据有没有 schema"** 是第一刀——有 schema 走确定性 ETL,无 schema 才动 LLM。**"要不要人来拍板"** 是第二刀——要判断/要审批就上 Agent + human-in-the-loop,否则收敛成代码。本课最漂亮之处恰恰是**在一条流水线里同时用了两者**:建模阶段多 Agent(L5-L8),执行阶段纯工具(L9-L10)。别把整条链都塞给 Agent,也别指望纯代码去做开放式建模——**按环节分层,才是架构师的答案**。

## 本课总结

| 要点 | 一句话 |
|---|---|
| 三张子图 | domain(CSV)/ lexical(chunks)/ subject(抽取实体),最后缝合 |
| graphrag 流水线 | loader→splitter→embedder→extractor→pruner→writer→resolver 七步 |
| 结构感知切块 | 自定义 RegexTextSplitter 按 markdown `---` 切,切在语义边界 |
| schema 锁抽取 | `additional_node_types=False`,只准用 L8 批准的类型 |
| entity resolution | 找标签→归一化键→rapidfuzz 关联键→Jaro-Winkler 比值→MERGE CORRESPONDS_TO |
| 阈值与方向 | 阈值要狠(0.1);Jaro-Winkler 是距离,0 才完美,别反 |
| 全程无 Agent | 抽取与消解都是确定性工具,判断力早在 L5-L8 花完 |

## 与我的资产映射

- 检索层:`agent/skills/agent-selection/3-retrieval.md`(结构感知 chunking = 检索质量瓶颈;GraphRAG 构建侧;entity resolution 作为图谱数据治理)
- 设计模式层:`agent/skills/agent-selection/11-design-patterns.md`(全课"建模用 Agent、执行用代码"的分层裁决)
- 记忆/状态层:`agent/skills/agent-selection/6-memory.md`(session state 跨 Agent 接力共享 context)
- 面试包:`08-foundations-function-calling-and-rag`(NER/triple 抽取 + entity resolution)、`04-multi-layer-memory`(状态接力)
- 上游课程:Neo4j C1《Knowledge Graphs for RAG》(检索侧)、SAP《Knowledge Graphs for AI Agent API Discovery》(确定性 SPARQL 构图对照)
- [[project_selection_matrix]] · [[project_asset_reuse]]
