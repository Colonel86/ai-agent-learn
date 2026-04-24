# Building and Evaluating Advanced RAG — 第 05 课：Auto-merging Retrieval 深入（中文整理）

> 来源：`subtitles/llamaindex-truera_c1_05_en.vtt` + `code/L5-Auto-merging_Retrieval.md`
> 本课目标：拆开 **Auto-merging Retrieval** 的内部实现（Hierarchical Node Parser / Leaf-only Vector Index / AutoMergingRetriever / Re-rank），并用 TruLens 三元指标对比 **两层 vs 三层层级结构**的效果。

---

## 一、为什么还需要 Auto-merging（解决什么问题）

### 标准 RAG 的另一类痛点：**上下文碎片化**

标准 RAG 检索出来的 chunk 常常是：

- 来自**同一篇章**甚至**同一小节**，语义是连续的；
- 但作为独立 chunk 喂给 LLM，**没有保证它们之间的顺序**，也丢失了段落之间的自然衔接；
- chunk 越小，碎片化越严重。

→ LLM 在这些**零散片段**上做合成时，容易理解混乱，降低回答质量。

### Auto-merging 的思路

1. 把文档组织成**层级节点树**：若干较小的 child node → 归属同一个较大 parent node；
2. **检索时只查 leaf（最小节点）**；
3. 当某个 parent 的**大部分 child 都被命中**，就**把它们合并替换成对应的 parent**；
4. 最终喂给 LLM 的是**更连贯、更完整**的父节点文本。

对比 Sentence Window：**Auto-merging 还能处理"虽不相邻但隶属同一父节点"的分散命中**（这正是 sentence window 处理不了的场景）。

---

## 二、准备工作

```python
import warnings
warnings.filterwarnings('ignore')

import utils, os, openai
openai.api_key = utils.get_openai_api_key()

from llama_index import SimpleDirectoryReader, Document

documents = SimpleDirectoryReader(
    input_files=["./eBook-How-to-Build-a-Career-in-AI.pdf"]
).load_data()

print(type(documents), "\n", len(documents), "\n", type(documents[0]))

document = Document(text="\n\n".join([doc.text for doc in documents]))
```

依旧是 41 页 PDF → 合成单文档（以便 hierarchical parser 能处理更长的连续文本）。

---

## 三、核心组件一：HierarchicalNodeParser

### 作用

**按从大到小的多级 chunk size，把文档解析为一棵树**。

### 代码

```python
from llama_index.node_parser import HierarchicalNodeParser

node_parser = HierarchicalNodeParser.from_defaults(
    chunk_sizes=[2048, 512, 128],     # 从大到小排序
)
```

- 顶层节点：**2048 tokens**；
- 中间层节点：**512 tokens**（每个顶层节点含 4 个）；
- 叶子节点：**128 tokens**（每个中间节点含 4 个）；
- 4 倍递减是默认推荐（`2048 / 4 = 512, 512 / 4 = 128`），但你可以改。

### 获取所有节点 / 仅叶子节点

```python
nodes = node_parser.get_nodes_from_documents([document])
# 这一步返回的是【叶子 + 中间 + 顶层】所有节点的平铺列表

from llama_index.node_parser import get_leaf_nodes

leaf_nodes = get_leaf_nodes(nodes)
print(leaf_nodes[30].text)        # ← 单个叶子节点的文本（～128 tokens）
```

### 节点之间的 parent/child 关系

```python
nodes_by_id = {node.node_id: node for node in nodes}

parent_node = nodes_by_id[leaf_nodes[30].parent_node.node_id]
print(parent_node.text)           # ← 对应的 parent 文本（～512 tokens）
```

可以看到：parent 的文本**包含**它 4 个 children 的文本**加上一点点额外的内容**（因为 parent 是按 512 tokens 独立切出来的，不是简单拼接）。

---

## 四、核心组件二：索引的特殊构造（只 embed 叶子节点）

### 构造 Service Context

```python
from llama_index.llms import OpenAI
from llama_index import ServiceContext

llm = OpenAI(model="gpt-3.5-turbo", temperature=0.1)

auto_merging_context = ServiceContext.from_defaults(
    llm=llm,
    embed_model="local:BAAI/bge-small-en-v1.5",
    node_parser=node_parser,
)
```

### 关键：Storage Context 里放全部节点，但只给 VectorStoreIndex 叶子

```python
from llama_index import VectorStoreIndex, StorageContext

storage_context = StorageContext.from_defaults()
storage_context.docstore.add_documents(nodes)           # ← 全部节点都进 docstore

automerging_index = VectorStoreIndex(
    leaf_nodes,                                          # ← 只有叶子节点被 embed
    storage_context=storage_context,
    service_context=auto_merging_context,
)

automerging_index.storage_context.persist(persist_dir="./merging_index")
```

**机制说明**：

- 只 embed leaf nodes → 初始 top-k 检索返回的都是小 chunk，**匹配更精确**；
- 中间节点 / 根节点**只放在 docstore**（内存文档库），检索时按需动态取；
- 当后面 AutoMergingRetriever 判断需要合并时，就从 docstore 里取出对应 parent。

### 可选：存在就加载，不存在就重建

```python
import os
from llama_index import StorageContext, load_index_from_storage

if not os.path.exists("./merging_index"):
    storage_context = StorageContext.from_defaults()
    storage_context.docstore.add_documents(nodes)
    automerging_index = VectorStoreIndex(
        leaf_nodes,
        storage_context=storage_context,
        service_context=auto_merging_context,
    )
    automerging_index.storage_context.persist(persist_dir="./merging_index")
else:
    automerging_index = load_index_from_storage(
        StorageContext.from_defaults(persist_dir="./merging_index"),
        service_context=auto_merging_context,
    )
```

---

## 五、核心组件三：AutoMergingRetriever（合并逻辑）

### 机制

在 leaf 层检索得到 top-k 之后：

- 统计每个 parent 下**有多少个 child 命中**了；
- 如果**超过某个阈值（多数）**，就**把这些 children 替换为对应 parent**；
- 这样喂给 LLM 的 context **少而精**、**更连贯**。

### 为什么要把 top-k 设得大

叶子 chunk 太小（128 tokens），如果只取前几个，**很难让多个 child 落到同一 parent 下**，合并几乎不会触发。

> 一般做法：**leaf 层 top_k 很大（如 12），合并后再用 re-ranker 缩到 top_n（如 6）**。

### 代码

```python
from llama_index.retrievers import AutoMergingRetriever
from llama_index.indices.postprocessor import SentenceTransformerRerank
from llama_index.query_engine import RetrieverQueryEngine

automerging_retriever = automerging_index.as_retriever(
    similarity_top_k=12,                        # 叶子层宽召回
)

retriever = AutoMergingRetriever(
    automerging_retriever,
    automerging_index.storage_context,
    verbose=True,                                # ← 打开可在日志里看到合并过程
)

rerank = SentenceTransformerRerank(
    top_n=6,                                     # 合并后再保留 6 条
    model="BAAI/bge-reranker-base",
)

auto_merging_engine = RetrieverQueryEngine.from_args(
    automerging_retriever,                       # (注：课堂代码此处传入 automerging_retriever)
    node_postprocessors=[rerank],
)
```

### 试跑一个问题

```python
auto_merging_response = auto_merging_engine.query(
    "What is the importance of networking in AI?"
)

from llama_index.response.notebook_utils import display_response
display_response(auto_merging_response)
```

`verbose=True` 时，日志里会看到类似：

```
Merging 3 nodes into parent node ...
Merging 1 node  into parent node ...
```

表示 AutoMergingRetriever **真的触发了合并**，把 children 换成了 parent。

---

## 六、封装为 helper function

```python
import os
from llama_index import (
    ServiceContext,
    StorageContext,
    VectorStoreIndex,
    load_index_from_storage,
)
from llama_index.node_parser import HierarchicalNodeParser, get_leaf_nodes
from llama_index.retrievers import AutoMergingRetriever
from llama_index.indices.postprocessor import SentenceTransformerRerank
from llama_index.query_engine import RetrieverQueryEngine


def build_automerging_index(
    documents,
    llm,
    embed_model="local:BAAI/bge-small-en-v1.5",
    save_dir="merging_index",
    chunk_sizes=None,
):
    chunk_sizes = chunk_sizes or [2048, 512, 128]
    node_parser = HierarchicalNodeParser.from_defaults(chunk_sizes=chunk_sizes)
    nodes = node_parser.get_nodes_from_documents(documents)
    leaf_nodes = get_leaf_nodes(nodes)

    merging_context = ServiceContext.from_defaults(
        llm=llm, embed_model=embed_model,
    )
    storage_context = StorageContext.from_defaults()
    storage_context.docstore.add_documents(nodes)

    if not os.path.exists(save_dir):
        automerging_index = VectorStoreIndex(
            leaf_nodes,
            storage_context=storage_context,
            service_context=merging_context,
        )
        automerging_index.storage_context.persist(persist_dir=save_dir)
    else:
        automerging_index = load_index_from_storage(
            StorageContext.from_defaults(persist_dir=save_dir),
            service_context=merging_context,
        )
    return automerging_index


def get_automerging_query_engine(
    automerging_index,
    similarity_top_k=12,
    rerank_top_n=6,
):
    base_retriever = automerging_index.as_retriever(similarity_top_k=similarity_top_k)
    retriever = AutoMergingRetriever(
        base_retriever, automerging_index.storage_context, verbose=True
    )
    rerank = SentenceTransformerRerank(
        top_n=rerank_top_n, model="BAAI/bge-reranker-base",
    )
    return RetrieverQueryEngine.from_args(
        retriever, node_postprocessors=[rerank],
    )
```

调用：

```python
index = build_automerging_index(
    [document],
    llm=OpenAI(model="gpt-3.5-turbo", temperature=0.1),
    save_dir="./merging_index",
)
query_engine = get_automerging_query_engine(index, similarity_top_k=6)
```

---

## 七、实验对比：两层结构 vs 三层结构

### 实验动机

"**层级越多**是否**效果越好**？" —— 不一定。如果两层就能拿到同等效果，**结构更简单、构建更快、检索更省**，就该选两层。下面用 TruLens 做 A/B。

### 初始化

```python
from trulens_eval import Tru
Tru().reset_database()

eval_questions = []
with open('generated_questions.text', 'r') as file:
    for line in file:
        eval_questions.append(line.strip())

def run_evals(eval_questions, tru_recorder, query_engine):
    for question in eval_questions:
        with tru_recorder as recording:
            query_engine.query(question)
```

---

### App 0：**两层结构**（leaf=512, parent=2048）

```python
auto_merging_index_0 = build_automerging_index(
    documents,
    llm=OpenAI(model="gpt-3.5-turbo", temperature=0.1),
    embed_model="local:BAAI/bge-small-en-v1.5",
    save_dir="merging_index_0",
    chunk_sizes=[2048, 512],               # ← 两层：2048 / 512
)

auto_merging_engine_0 = get_automerging_query_engine(
    auto_merging_index_0,
    similarity_top_k=12,
    rerank_top_n=6,
)

from utils import get_prebuilt_trulens_recorder

tru_recorder = get_prebuilt_trulens_recorder(
    auto_merging_engine_0,
    app_id='app_0',
)

run_evals(eval_questions, tru_recorder, auto_merging_engine_0)

Tru().get_leaderboard(app_ids=[])
Tru().run_dashboard()
```

**观察（24 条 records）**：

- Answer Relevance 和 Groundedness：都不错；
- **Context Relevance：明显偏低**。

**Drill-down 示例**：某个关于 "budgeting for resources" 的问题 —— 检索回 6 条 context，每条相关分只有 0.0~0.2，都不切题。

---

### App 1：**三层结构**（leaf=128, mid=512, root=2048，每层 4 个 child）

```python
auto_merging_index_1 = build_automerging_index(
    documents,
    llm=OpenAI(model="gpt-3.5-turbo", temperature=0.1),
    embed_model="local:BAAI/bge-small-en-v1.5",
    save_dir="merging_index_1",
    chunk_sizes=[2048, 512, 128],          # ← 三层
)

auto_merging_engine_1 = get_automerging_query_engine(
    auto_merging_index_1,
    similarity_top_k=12,
    rerank_top_n=6,
)

tru_recorder = get_prebuilt_trulens_recorder(
    auto_merging_engine_1,
    app_id='app_1',
)

run_evals(eval_questions, tru_recorder, auto_merging_engine_1)

Tru().get_leaderboard(app_ids=[])
Tru().run_dashboard()
```

**观察**：

| 指标 | App 0（两层, leaf=512） | App 1（三层, leaf=128） |
|------|----------|-------------|
| **Context Relevance** | 较低 | **提升约 20%** |
| Groundedness | 一般 | **明显提升** |
| Total Cost | 高 | **约为 App 0 的一半** |

**为什么三层更好**：

- 叶子更小（128 tokens） → embedding 匹配**颗粒度更细、更精准**；
- 多个 children 命中同一 parent 的几率更高 → **合并更容易触发**；
- 合并后喂给 LLM 的仍是 512~2048 tokens 的连贯父节点，上下文更完整；
- **在这份数据集上三层 > 两层**。

在同一问题 "budgeting for resources" 上 drill-down，App 1 返回的 context 明显更切题，groundedness 也明显高。

---

## 八、Auto-merging vs Sentence Window：互补关系

把一棵树的 4 个 child 标号为 ①②③④：

- **Auto-merging**：如果 ① 和 ④ 都命中了查询（尽管**在文本里不连续**），而它们共享同一 parent，就会被合并 → LLM 看到完整 parent。
- **Sentence Window**：因为是"在命中句周围扩窗"，**不会把 ① 和 ④ 跨距离合并**起来。

→ 两种技术**解决的是不同场景的痛点**，可以组合使用。

---

## 九、关键要点总结

1. **Auto-merging Retrieval 的三件套**：
   - `HierarchicalNodeParser` —— 多粒度切分，建节点树；
   - `VectorStoreIndex(leaf_nodes, storage_context=...)` —— **只 embed 叶子节点**，父节点放 docstore 动态取；
   - `AutoMergingRetriever` —— 根据命中密度自动把 children 合并为 parent。

2. **超参调优方向**：
   - `chunk_sizes` 的**层数和大小**（两层 / 三层 / 其他层级比例）；
   - `similarity_top_k`（叶子层宽召回越大，合并越容易触发，但 token 成本也上升）；
   - `rerank_top_n`（最终喂给 LLM 的数量）。

3. **观察到的规律**：
   - 合适层数的 **三层结构在本数据集上优于两层**（context relevance ↑20%，cost 减半）；
   - **不同文档类型的最佳结构会变**（合同 vs. 发票 vs. 长文，都应自己用 RAG Triad 实验挑）；
   - **Auto-merging 与 Sentence Window 互补**。

4. **评估方法论保持一致**：
   - 每个 app 配一个 `app_id`；
   - 先看 leaderboard 聚合指标；
   - 遇到指标异常再 drill-down 到 record 级别，用 CoT 理由分析失败模式。

---

## 十、课程整体总结

我们用了 5 节课，系统性地学到了：

- **两种高级 RAG 检索技术**：Sentence Window Retrieval 和 Auto-merging Retrieval；
- **一个评估三元组**：Context Relevance、Groundedness、Answer Relevance；
- **一套实验方法论**：Feedback Function 抽象 + TruLens Dashboard + app_id 追踪 + 聚合/下钻两级视图。

通过把这些技术与评估方法结合起来，可以把 RAG 应用**从"能工作"推到"可靠、可迭代、可生产化"**。

TruLens 还内置了"Honest / Harmless / Helpful"等一系列其他评估，鼓励自己探索。
