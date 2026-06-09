# FAISS 和 Milvus：向量检索工具

两个都是**向量数据库 / 向量检索工具**，用来在海量 embedding 中快速找出"最相似的几个"。

---

## 共同要解决的问题

假设你有 **1000 万条**文本的 embedding，用户查询时也生成一个 embedding，你要找出最相似的 Top 10。

- 暴力做法：跟 1000 万个向量逐个算余弦相似度 → 慢到不可用
- 向量数据库：用 **ANN（近似最近邻，Approximate Nearest Neighbor）** 算法，毫秒级返回结果

FAISS 和 Milvus 就是干这个的。

---

## 1. FAISS（Facebook AI Similarity Search）

- **出品方**：Meta（Facebook）开源
- **定位**：一个**库（library）**，不是数据库
- **语言**：C++ 核心 + Python 绑定
- **特点**：
  - 极致性能，支持 GPU 加速
  - 算法丰富（IVF、HNSW、PQ 量化等）
  - **本地、单机、嵌入式**使用：`pip install faiss-cpu` 就能跑
  - **没有**服务化能力：不支持网络访问、用户权限、数据持久化管理、分布式

```python
import faiss
import numpy as np

# 建索引
index = faiss.IndexFlatL2(768)      # 768 维向量
index.add(embeddings)               # 加入数据

# 搜索
distances, ids = index.search(query_vec, k=10)
```

**适合**：原型开发、单机应用、研究、数据量不大（百万级）。

---

## 2. Milvus

- **出品方**：Zilliz 开源
- **定位**：完整的**向量数据库**（产品级）
- **特点**：
  - 底层也用 FAISS / HNSWlib 等做索引，但**包装成了一个数据库系统**
  - 支持：分布式、水平扩展、数据持久化、增删改查、过滤、元数据、权限、监控、备份
  - 提供 SDK（Python / Go / Java / Node）和 RESTful API
  - 适合**亿级以上**向量

```python
from pymilvus import MilvusClient

client = MilvusClient("http://localhost:19530")
client.insert(collection_name="docs", data=[...])
results = client.search(collection_name="docs", data=[query_vec], limit=10)
```

**适合**：生产环境、大数据量、多服务共享、需要工程化能力。

---

## 对比一句话

| 维度 | FAISS | Milvus |
|---|---|---|
| 形态 | 库（嵌入到你代码里） | 数据库（独立服务） |
| 规模 | 单机，百万~千万级 | 分布式，亿级+ |
| 部署 | `pip install` 即用 | Docker / K8s 部署 |
| 持久化 | 自己管（存文件） | 内置 |
| 元数据过滤 | 弱 | 强 |
| 适用阶段 | 原型 / 研究 / 小项目 | 生产环境 |

> **类比**：FAISS 像 SQLite（嵌入式），Milvus 像 MySQL / PostgreSQL（独立数据库服务）。

---

## 同类产品（顺便了解）

- **Chroma**：轻量、易用，适合 RAG 原型（课程 `6-Advanced Retrieval for AI with Chroma`）
- **Pinecone**：商业云服务，免运维
- **Weaviate**：开源，带 GraphQL 接口
- **Qdrant**：Rust 写的，性能好
- **pgvector**：PostgreSQL 扩展，已有 PG 数据库时方便

**选型经验**：

- 学习 / 原型 → Chroma 或 FAISS
- 中小生产 → Qdrant 或 pgvector
- 大规模生产 → Milvus 或 Pinecone

---

## 关键术语速查

| 术语 | 英文 | 一句话解释 |
|---|---|---|
| 近似最近邻 | ANN (Approximate Nearest Neighbor) | 牺牲少量精度换取大幅速度提升的向量检索算法 |
| 倒排文件索引 | IVF (Inverted File Index) | 先把向量聚类成桶，查询时只搜最近的几个桶 |
| 分层导航小世界 | HNSW (Hierarchical Navigable Small World) | 基于图的高性能 ANN 算法，召回率高 |
| 乘积量化 | PQ (Product Quantization) | 把向量切片压缩存储，节省内存 |
| 向量数据库 | Vector Database | 专门存储和检索高维向量的数据库 |
