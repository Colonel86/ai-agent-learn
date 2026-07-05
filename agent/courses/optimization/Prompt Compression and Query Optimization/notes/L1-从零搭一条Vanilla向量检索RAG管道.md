# L1 · 从零搭一条 Vanilla 向量检索 RAG 管道（MongoDB Atlas + Pydantic）

> 课程：Prompt Compression and Query Optimization（DeepLearning.AI × MongoDB）
> 本课任务：不加任何 filter，把最朴素的一条 RAG 管道跑通——**加载 Airbnb 数据 → Pydantic 建模 → 连 MongoDB → 灌数据 → 建 vector search index → 向量检索 → 交给 LLM 出推荐**。这是全课的地基，后面每课都在这条管道上加一个"省钱 stage"。

## 0. 从检索的第一性原理讲起

比较两个数据点有多"像"，传统做法是 **text search（关键词匹配）**：拿 query 关键词去数据点内容里找直接命中——这是最基础的信息检索，只能命中"字面相同"。

**vector search（向量/语义检索）** 换了个维度：把数据（结构化的表格，或非结构化的音频/图像/文本）喂给 **embedding model**，输出一个 **vector**（向量），这一步叫 vectorize。这个数值向量捕获了数据的语义与上下文。在高维 **vector space** 里，两个向量的距离就代表它们语义上有多接近。于是检索从"找字面相同"升级成"**找语义相近**"。

vector search 撑起了三类能力：semantic search（懂 query 语义）、recommendation system（预测偏好）、以及 **RAG**（给 LLM 输入补上下文）。

## 1. RAG 是什么、为什么值得

RAG（Retrieval Augmented Generation）是一种**系统设计模式**：用信息检索（含 vector search）+ 基础模型，给用户 query 生成准确且相关的回答。机制是——检索语义相近的数据来**补充** query 的上下文，再把「检索结果 + 原始 query」一起喂给 LLM。

| 无 RAG | 有 RAG |
|---|---|
| query → LLM → 回答 | query + 相关领域数据 → LLM → 上下文感知的回答 |
| 不用任何相关数据，容易跑偏 | grounding 在最新/相关信息上 |

RAG 的收益（讲师列的五条）：**① grounding，减少 hallucination；② 减少喂进 context window 的信息量；③ 某些场景免去 fine-tuning；④ 能用自己的私有/领域数据；⑤ 让回答满足特定需求。**

> **架构师视角**：注意收益②——RAG 本身就是一种"省 context"的手段（只喂相关的，不是全量）。本课接下来的 filtering / projection 是在 RAG 内部**再省一层**。理解这个嵌套关系很重要：RAG 决定"喂哪一类知识"，query optimization 决定"这一类里喂多少、喂哪几个字段"。

## 2. 为什么是 MongoDB：document model 与 aggregation pipeline

MongoDB 是一个 NoSQL 的开发者数据平台，自带 vector search。它在 AI 应用里能同时当 **vector database**（存向量）和**operational/transactional 数据存储**，因此可以做 LLM/Agent 的 memory provider。

**关系库 vs document model**（用"存房子"举例）：

| 关系库 | MongoDB document model |
|---|---|
| 房间/卫浴信息一张表，地址信息另一张表 | 一栋房子的所有属性（含地址）放进**一个 document** |
| 先定表结构，应用迁就数据 | 按**应用的访问方式**建模数据 |

- **document**：数据的基本单元，类似 JSON，一组 key-value，相当于关系库里的一行；
- **collection**：一堆 document，相当于关系库里的一张表；document 是 dynamic 的，同一 collection 里可以有不同字段结构。
- **data modeling 的黄金问题**：不要问"我的数据长什么样"，要问"**我的应用会怎么访问这些数据**"——访问方式决定建模结构。

**aggregation pipeline** 是 MongoDB 查询的核心抽象：一串**数据处理 stage**，数据流过每个 stage 被逐级变换（跟 ML/数据处理里的 pipeline 是同一个直觉）。复杂查询 = 若干 stage 组合。本课后面所有优化（filter / project / rerank）都是往这条 pipeline 里**插 stage**。

## 3. Pydantic：进数据库前的一道数据校验闸

AI 应用需要保证数据符合某个模型，减少生产事故。**Pydantic** 是 Python 的数据校验/建模库：定义 schema（对象+属性+类型+约束），数据不合规就 raise exception 并指出具体问题。本课用它给 Airbnb 数据建模，确保每条 listing 灌进 MongoDB 前结构正确。

数据集：HuggingFace 上 `MongoDB/airbnb_embeddings`，5000 条 Airbnb 房源，含 address / description / transit / reviews 等；每条自带**图片 embedding + 空间描述(space 字段)的文本 embedding**（讲师口播说文本 embedding 由 OpenAI `text-embedding-ada-002` 生成，维度 1536）。本课只用文本 embedding。

## 4. 代码走一遍：七步搭管道

### 4.1 加载数据（HuggingFace → pandas）

```python
from datasets import load_dataset
import pandas as pd

# streaming=True 流式加载，避免一次性拉全量；只取前 100 条做课堂演示
dataset = load_dataset("MongoDB/airbnb_embeddings", streaming=True, split="train")
dataset = dataset.take(100)
dataset_df = pd.DataFrame(dataset)   # 转 DataFrame 便于观察/改数据
```

### 4.2 Pydantic 建模（子模型 → 父模型 Listing）

先建子模型再拼父模型，父模型 `Listing` 把子模型挂成字段：

```python
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

class Location(BaseModel):
    type: str
    coordinates: List[float]
    is_location_exact: bool

class Address(BaseModel):
    street: str; government_area: str; market: str
    country: str; country_code: str
    location: Location            # 嵌套子模型

class Listing(BaseModel):          # 父模型：一条房源的全部信息
    _id: int
    name: str; summary: str; space: str; description: str
    accommodates: int             # 可住人数（后面 L2 用它做 filter）
    bedrooms: Optional[float] = 0  # 卧室数（后面 L2 用它做 filter）
    price: int
    address: Address              # 挂地址子模型
    host: Host                    # 挂房东子模型
    reviews: List[Review]         # 挂评论子模型列表
    text_embeddings: List[float]  # ★ 关键字段：space 的文本向量
```

灌库前两步预处理：把每条转 dict（`records`）→ 把 `NaT`/空值统一置 `None`（sanity check）→ 用 `Listing(**record).dict()` 逐条校验并转回 dict：

```python
records = dataset_df.to_dict(orient='records')
# 处理 NaT：list 型字段逐元素、标量字段直接判空，空的置 None
for record in records:
    for key, value in record.items():
        if isinstance(value, list):
            record[key] = [None if pd.isnull(v) else v for v in value]
        elif pd.isnull(value):
            record[key] = None
# 逐条过 Pydantic 校验；不合规会 raise ValidationError
listings = [Listing(**record).dict() for record in records]
```

### 4.3 连接数据库（MongoClient）

```python
from pymongo.mongo_client import MongoClient

database_name = "airbnb_dataset"
collection_name = "listings_reviews"

def get_mongo_client(mongo_uri):
    # appname 是给 MongoDB 端识别调用来源用的标签
    client = MongoClient(mongo_uri, appname="devrel.deeplearningai.lesson1.python")
    print("Connection to MongoDB successful")
    return client

mongo_client = get_mongo_client(MONGO_URI)
db = mongo_client.get_database(database_name)
collection = db.get_collection(collection_name)

collection.delete_many({})   # 先清空 collection，保证幂等（首次运行删 0 条）
```

### 4.4 灌数据（一行 insert_many）

```python
collection.insert_many(listings)   # 批量灌入，MongoDB 把这件事做成 trivial
```

### 4.5 建 vector search index（本课最关键一步）

index 决定向量检索能不能高效。用 `SearchIndexModel` 声明索引定义：

```python
from pymongo.operations import SearchIndexModel

text_embedding_field_name = "text_embeddings"       # 存向量的字段
vector_search_index_name_text = "vector_index_text" # 索引名，检索时要引用

vector_search_index_model = SearchIndexModel(
    definition={
        "mappings": {
            "dynamic": True,            # 文档里新出现的字段自动索引
            "fields": {
                text_embedding_field_name: {
                    "dimensions": 1536,   # 单个向量的维度
                    "similarity": "cosine",# 计算相似度的距离算法
                    "type": "knnVector",  # 声明该字段存的是向量
                }
            },
        }
    },
    name=vector_search_index_name_text,
)
# 建索引前先查重名（good practice），不存在才建；建完 sleep 等它初始化
if not index_exists:
    collection.create_search_index(model=vector_search_index_model)
    time.sleep(20)   # 等 vector index 完成初次 sync 再用
```

> **架构师视角**：`dynamic: True` 是"约定优于配置"——新字段自动进索引，开发快；但生产上你往往想**显式声明索引字段**（换取可控的索引体积和查询计划）。L2 的 pre-filter 就会为此专门建一个把 `accommodates`/`bedrooms` 声明成 `number` 的独立索引。记住这个分叉点：**dynamic 图省事，显式 filter 字段图性能。**

### 4.6 组装向量检索查询

查询要先把用户 query 也 embedding（用 OpenAI，代码里实际用 `text-embedding-3-small` + `dimensions=1536`，与库中向量维度对齐）：

```python
def get_embedding(text):
    if not text or not isinstance(text, str):
        return None
    return openai.embeddings.create(
        input=text, model="text-embedding-3-small", dimensions=1536
    ).data[0].embedding
```

核心是 `$vectorSearch` stage，塞进 aggregation pipeline 执行：

```python
def vector_search(user_query, db, collection, vector_index="vector_index_text"):
    query_embedding = get_embedding(user_query)   # 用户 query → 向量

    vector_search_stage = {
        "$vectorSearch": {
            "index": vector_index,                # 用哪个索引
            "queryVector": query_embedding,       # query 向量
            "path": text_embedding_field_name,    # 文档里比对哪个字段
            "numCandidates": 150,                 # 候选考虑数（召回粗筛）
            "limit": 20                           # 最终返回 top 20
        }
    }
    pipeline = [vector_search_stage]              # vanilla：pipeline 里只有这一个 stage
    results = collection.aggregate(pipeline)

    # 用 explain 命令拿执行统计（不真正跑），读出 stage 耗时
    explain = db.command('explain',
        {'aggregate': collection.name, 'pipeline': pipeline, 'cursor': {}},
        verbosity='executionStats')
    millis = explain['stages'][0]['$vectorSearch']['explain']['collectors']\
                    ['allCollectorStats']['millisElapsed']
    print(f"execution: {millis} milliseconds")
    return list(results)
```

`numCandidates`(150) 与 `limit`(20) 是 ANN 检索的两个旋钮：先粗召 150 个候选，再精排返回 20 个——候选越多召回越全但越慢。

### 4.7 处理用户 query（检索 → 喂 LLM → 出推荐）

用一个精简的 Pydantic 模型 `SearchResultItem` 约束返回字段，转成 DataFrame 当 context 喂给 `gpt-3.5-turbo`：

```python
class SearchResultItem(BaseModel):
    name: str
    accommodates: Optional[int] = None
    address: Address
    summary: Optional[str] = None
    # ...只保留推荐需要的字段

def handle_user_query(query, db, collection):
    get_knowledge = vector_search(query, db, collection)      # 检索
    search_results_df = pd.DataFrame(                          # 结果 → 规整表
        [SearchResultItem(**r).dict() for r in get_knowledge])
    completion = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a airbnb listing recommendation system."},
            {"role": "user",
             "content": f"Answer this user query: {query} with the following context:\n{search_results_df}"}
        ])
    return completion.choices[0].message.content
```

跑一个真实 query："想住个 warm and friendly、离餐厅不远的地方"——vector search 耗时 **0.02 ms**（极快），系统推荐了加拿大 Plateau 区的一处 cozy 房源并给出理由。

> **对比《Semantic Caching for AI Agents》(Redis)**：两门课都把"用户 query → embedding → 在向量空间找近邻"当核心动作，但**目的相反**。Redis 语义缓存拿这个近邻去问"这个问题以前答过吗？命中就直接返回旧答案、跳过 LLM"；本课的 vector search 拿近邻去"**取知识**、再喂 LLM 生成新答案"。同一套向量检索原语，一个用于**旁路 LLM**，一个用于**喂养 LLM**——这是 `3-retrieval.md` 里"向量检索既是缓存键也是知识索引"的两个面。

> **架构师视角**：这条 vanilla 管道每一步都被 `explain` 埋了耗时探针（`millisElapsed`）。别小看它——后面 L2 加 filter、L3 加 projection，判断"这个 stage 到底省没省钱/省没省时"全靠对比这个数。**优化前先有度量**，管道从第一版就带上可观测性，是架构师和调库工程师的分水岭。

## 本课总结

| 要点 | 一句话 |
|---|---|
| vector search 本质 | 数据→embedding→高维空间比距离，从"字面匹配"升级到"语义匹配" |
| RAG 模式 | 检索语义相近数据补充 query，再一起喂 LLM；顺带减 hallucination、省 context |
| document model | 一条房源全属性进一个 document；按"应用怎么访问"而非"数据长什么样"建模 |
| aggregation pipeline | 一串可组合 stage，vanilla 版里只有一个 `$vectorSearch` |
| Pydantic 闸门 | 灌库前逐条校验，schema 不合规就报错，挡住生产脏数据 |
| 关键索引 | `SearchIndexModel` 声明 `knnVector` 字段 + dimensions + cosine，检索靠它高效 |
| 可观测性 | `explain` + `millisElapsed` 给每个 stage 埋耗时探针 |

> **记忆点（引出 L2）**：本课的 vanilla 管道**只按语义相似度返回 20 条**，完全不管用户的硬约束——他要"美国境内、能住 2-5 人"的房子，vanilla 版照样给你返回加拿大的。L2 引入 **metadata filtering**：把 country / accommodates / bedrooms 这类结构化字段作为过滤条件，分 **post-filter（检索后过滤）** 和 **pre-filter（检索前过滤）** 两种插法插进 aggregation pipeline，并对比两者返回结果的差异——这是"让检索返回得更小更准"的第一刀。

## 与我的资产映射

- 检索层：`agent/skills/agent-selection/3-retrieval.md`（vector search index 的 dimensions/similarity/numCandidates 旋钮；"向量检索既是缓存键也是知识索引"的两面）
- 成本经济学：`agent/skills/agent-selection/8-cost-economics.md`（`explain`+`millisElapsed` 作为 stage 级成本/延迟度量，是优化前必须先建的基线）
- 面试包：`05-context-engineering-and-caching`（同一套向量检索原语在"旁路 LLM"与"喂养 LLM"两种用法的对照）
- [[project_selection_matrix]]
