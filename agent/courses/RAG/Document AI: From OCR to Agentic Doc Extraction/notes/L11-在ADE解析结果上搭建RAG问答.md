# L11 · 在 ADE 解析结果上搭建 RAG 问答（ChromaDB + Hybrid Search + LangChain）

> 课程：Document AI: From OCR to Agentic Doc Extraction（DeepLearning.AI × LandingAI）
> 本课任务（Lab 5）：把上一课 ADE 解析出的 chunk 灌进向量库，实现一个能回答"文档里问题"的完整 RAG 工作流，并用 **visual grounding** 把每个答案追溯回原始 PDF 的确切位置。

## 0. 本课定位与衔接

L10 讲清了 RAG 的动机：解析和抽取解决了"把文档变成干净数据"，但用户真正要的是"就这份文件问问题"。L10 的路线是 **ADE 解析 → chunk 存进向量库 → 检索并回答**。L11 是它的动手实验：库和数据已预置，重点是走通检索到生成的整条链。

三阶段 RAG（贯穿全课）：

```
① Preprocess  解析成 chunk → 向量化 → 入库
② Retrieve    把问题向量化 → 找语义最近的 chunk
③ Generate    把检索到的 chunk 当上下文喂给 LLM → 生成 grounded 答案
```

技术栈：`OpenAI`（embedding + LLM）、`ChromaDB`（向量库）、`LangChain`（把检索结果接进 prompt）、`Pillow`（可视化 chunk）。文档是 **Apple 10-K**（美股公司必须报送 SEC 审计的年报，大量财务表格）。

## 1. 输入数据：ADE 的 markdown + JSON 双产物

ADE 已提前在这份 10-K 上跑过，产物落在 `ade_outputs/`：

| 文件 | 内容 |
|---|---|
| `apple_10k.md` | 整份文档转成结构化 markdown，内嵌 **anchor tag**（HTML 小片段，携带每个 chunk 的唯一 ID） |
| `apple_10k_chunks.json` | 每个 chunk 的元数据 |

anchor tag 是把 markdown 里的文字**链回** JSON 元数据的桥梁。加载后看第一个 chunk 的结构——五个关键字段：

```python
# chunk 的五个字段
{
  "chunk_id":   "...",        # 唯一标识（= markdown 里 anchor 的 ID）
  "chunk_type": "text",       # text / table / figure ...
  "text":       "...",        # 实际内容（含 anchor tag）
  "bbox":       [x0,y0,x1,y1],# 边界框，归一化到 0-1
  "page":       0             # 来自第几页（0 起）
}
```

> **架构师视角**：`bbox` 是 LandingAI 与普通解析器的分水岭。字幕原话——"Every chunk traces back to its exact location in the original document"。多数 OCR/切块方案只吐文字，位置信息在切块那一步就丢了；ADE 让每个 chunk 天生带坐标，于是检索到一段内容后能**当场高亮它在原页的出处**。在受监管场景（金融、医疗、法务），这个"可追溯"不是锦上添花，而是能不能上线的前提。

## 2. 向量库 ChromaDB 搭建

```python
CHROMA_DB_PATH = Path("./chroma_db")
COLLECTION_NAME = "ade_documents"
EMBEDDING_MODEL = "text-embedding-3-small"

chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)   # 持久化到磁盘，kernel 重启不丢
collection = chroma_client.get_or_create_collection(name=COLLECTION_NAME)  # 有则加载、无则新建
```

两个要点：`PersistentClient` 把数据落盘（对比内存版）；`get_or_create_collection` 幂等，重复运行不炸。本实验已预灌 **453 个 chunk**，所以后面"灌库"步骤实际会新增 0 条。

## 3. 灌库：chunk → embedding + metadata

灌库循环的内核（简化）：

```python
for chunk in loaded_chunks:
    if chunk["chunk_id"] in existing_ids:      # 已存在则跳过
        continue
    text = chunk.get("text", "")
    if not text.strip():                       # 跳过空 chunk
        continue
    emb = openai.embeddings.create(            # 用同一个 embedding 模型向量化
        input=text, model=EMBEDDING_MODEL
    ).data[0].embedding
    metadata = {                               # 拍平成简单类型才能进 Chroma
        "chunk_type": chunk.get("chunk_type", "unknown"),
        "page": chunk.get("page"),
        # bbox_* 坐标 → 供后续 visual grounding
    }
    # collection.add(ids=..., documents=text, embeddings=emb, metadatas=metadata)
```

关键：**metadata 必须是简单类型**（Chroma 不吃嵌套结构），所以 bbox 要拍平成 `bbox_x0/…`。metadata 是第 5 节 hybrid search 的过滤依据。

## 4. rag_query：检索函数

```python
def rag_query(question, top_k=3, threshold=0.25, show_images=True):
    # 1. 把问题向量化（和 chunk 用同一个 embedding 模型——这是可比性的前提）
    # 2. collection.query 找 top_k 最近向量
    # 3. 解析出 documents / metadatas / distances / ids
    # 4. 按 threshold 过滤（相似度 = 1 - L2 距离）
    # 5. 用 helper 从原 PDF 裁剪并高亮该 chunk（visual grounding）
```

四个参数：`question`、`top_k`（默认 3）、`threshold`（默认 0.25，最低相似度）、`show_images`（默认 True，是否画出原 PDF 里的位置）。

测试用 `rag_query("What was Apple's net sales in 2023?", top_k=5, threshold=0.32)`。看 5 条结果的现实感：第 1 条给出按产品/服务分年的净销售明细（正解），第 2/3/5 条是"沾边但没正面回答"的 tangential 内容，第 4 条与第 1 条同源。字幕点破：**语义相似 ≠ 正确答案**，生产里要靠调 `top_k`/`threshold` 逼近真正想要的结果。

## 5. Hybrid Search：语义 + metadata 过滤

财务数据大量藏在**表格**里。纯语义检索会把"顺带提了一句 revenue 的叙述段落"也捞上来。Hybrid search 用 `where` 参数按 metadata 收窄：

```python
results = collection.query(
    query_embeddings=[q_embed],           # 仍走语义："total revenue" ≈ "net sales"
    n_results=5,
    include=["documents", "metadatas", "distances"],
    where={"chunk_type": "table"},        # 只在表格 chunk 里找
)
```

语义负责"按意思匹配"（total revenue 对上 net sales），metadata 过滤负责"只看表格"。字幕提示还可按 `page`、`chunk_type` 等其他字段过滤。

> **对比 Preprocessing Unstructured Data for LLM Applications**：那门课的主线是"把 PDF/HTML/PPT 切成干净 chunk 再喂 LLM"，切块质量决定 RAG 上限，但产出的 chunk 是**扁平文本**——丢了类型和坐标。本课 ADE 的 chunk 自带 `chunk_type` 与 `bbox`，于是同一套 RAG 多出两种能力：hybrid search 能"只搜表格"、检索结果能"高亮回原页"。判断分野：如果下游只是纯文本问答，Unstructured 式切块够用；一旦要按结构过滤或要可追溯，就需要 ADE 这种带结构化 metadata 的解析。

## 6. LangChain RAG 链：从查表到跨 chunk 推理

前 5 节能"取回相关 chunk"，但**跨 chunk 对比**（如"2022 vs 2023 iPhone 收入趋势"）需要 LLM 来推理。用 LangChain 把检索器接成一条链：

```python
# ① Chroma 集合包成 LangChain 检索器
vectordb = Chroma(collection_name=COLLECTION_NAME,
                  embedding_function=OpenAIEmbeddings(model=EMBEDDING_MODEL),
                  persist_directory=str(CHROMA_DB_PATH))
retriever = vectordb.as_retriever()

# ② prompt 模板：{context} 由 LangChain 注入检索到的 chunk，{input} 放用户问题
system_prompt = ("Use the following pieces of retrieved context to answer the "
                 "user's question. If you don't know the answer, say that you don't know."
                 "\n\n{context}")
prompt = ChatPromptTemplate.from_messages([("system", system_prompt), ("human", "{input}")])

# ③ LLM + 组链
llm = ChatOpenAI(model="gpt-5-mini", temperature=1)   # 开场介绍写的是 gpt-4o-mini，代码用 gpt-5-mini
rag_chain = create_retrieval_chain(retriever, prompt | llm)

response = rag_chain.invoke({"input": "How did total revenue trend between 2023 and 2022 for iPhone sales?"})
```

`create_retrieval_chain` 自动串起"取问题 → 检索 chunk → 注入 prompt → 生成答案"。字幕点出这套能力可外推到：跨文档找不一致、取法律文件某条修正案的最新版并列全部版本、给某主题做带来源的摘要、分析研究论文/监管文件用于药物商业化。

## 本课总结

| 要点 | 一句话 |
|---|---|
| 三阶段 RAG | Preprocess（切块入库）→ Retrieve（语义检索）→ Generate（grounded 生成） |
| 双产物入库 | markdown（anchor tag）+ JSON（chunk 五字段），anchor ID 把两者对齐 |
| 向量库 | ChromaDB `PersistentClient` 落盘 + `get_or_create_collection` 幂等 |
| Hybrid Search | 语义相似 + `where` metadata 过滤（只搜 table），治"顺带提及" |
| 可追溯 | 每个 chunk 的 bbox → 检索结果高亮回原 PDF，审计友好 |
| 跨 chunk 推理 | LangChain `create_retrieval_chain` 让 LLM 对比多段做趋势/差异分析 |

> **记忆点（引出 L12）**：本课整条流水线全跑在**本地**——本地存文件、本地跑 ADE、OpenAI 做 embedding、ChromaDB 是本地库。文档一多、并发一上就扛不住。L12 把这四个本地组件逐一换成 AWS 托管服务（S3 / Lambda / Bedrock），并用**事件驱动**让"上传即自动解析"，把 demo 变成能弹性伸缩的生产架构。

## 与我的资产映射

- 检索层选型：`agent/skills/agent-selection/3-retrieval.md`（hybrid search = 语义 + metadata 过滤；相似度阈值调参是召回/精度的取舍旋钮）
- 可观测·可追溯：`agent/skills/agent-selection/5-observability-eval.md`（visual grounding 作为 RAG 答案的溯源/审计手段）
- 面试素材：RAG 三阶段 + hybrid search + grounded citation，是「资深 Agent 工程师」RAG 环节的标准答法
- [[project_selection_matrix]]
