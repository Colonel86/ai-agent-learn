# Building and Evaluating Advanced RAG — 第 04 课：Sentence Window Retrieval 深入（中文整理）

> 来源：`subtitles/llamaindex-truera_c1_04_en.vtt` + `code/L4-Sentence_window_retrieval.md`
> 本课目标：拆开 **Sentence Window Retrieval** 的内部实现（Node Parser / MetadataReplacement / Re-ranker），并用 TruLens 三元指标在 **window_size = 1 / 3 / 5** 上做实验，找到"质量 vs. 成本"的甜蜜点。

---

## 一、为什么需要 Sentence Window Retrieval

标准 RAG 一个根本矛盾：

- **Embedding-based 检索**：chunk 越**小**，语义匹配越精确；
- **LLM 合成答案**：chunk 越**大**，上下文越连贯，回答质量越好。

传统 RAG 的 chunk **embedding 时和 LLM 合成时用的是同一块文本**，两边被迫互相妥协。

**Sentence Window Retrieval 解耦了这两件事**：

1. **Embedding & 检索** → 用**单句**（更细粒度）；
2. **合成时** → 把匹配到的那句 **替换成它前后若干句组成的"窗口"** 喂给 LLM。

这样就能同时拿到"**精准检索 + 连贯合成**"两头的好处。

---

## 二、准备工作

和前几课一致：

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

数据：41 页 PDF，**合并成单文档**以便后续 sentence window 能在更连续的文本上切分。

---

## 三、核心组件一：SentenceWindowNodeParser

### 作用

**把文档切成句子 + 每句记录它周围的 window 文本**。

### 代码

```python
from llama_index.node_parser import SentenceWindowNodeParser

node_parser = SentenceWindowNodeParser.from_defaults(
    window_size=3,                         # 前后各 3 句
    window_metadata_key="window",          # 把窗口文本存在 metadata["window"]
    original_text_metadata_key="original_text",
)
```

### 玩具示例

```python
text = "hello. how are you? I am fine!  "
nodes = node_parser.get_nodes_from_documents([Document(text=text)])
```

- 3 句 → 被拆成 **3 个 node**，每个 node 只保留一句；
- 每个 node 的 `metadata["window"]` 存**那句话本身 + 前后相邻若干句**；
- `metadata["original_text"]` 存原句。

### 边界情况

```python
text = "hello. foo bar. cat dog. mouse"
nodes = node_parser.get_nodes_from_documents([Document(text=text)])
print(nodes[0].metadata["window"])
# 输出："hello. foo bar. cat dog."（第一个 node 前面没句子，只往后扩展）
```

**要点**：window 只是 metadata，**不是**节点本身的 text —— 这点对后面的 MetadataReplacement 很关键。

---

## 四、核心组件二：构建 Sentence Window Index

```python
from llama_index.llms import OpenAI
from llama_index import ServiceContext, VectorStoreIndex

llm = OpenAI(model="gpt-3.5-turbo", temperature=0.1)

sentence_context = ServiceContext.from_defaults(
    llm=llm,
    embed_model="local:BAAI/bge-small-en-v1.5",
    # embed_model="local:BAAI/bge-large-en-v1.5"   ← 可切换为大号模型
    node_parser=node_parser,
)

sentence_index = VectorStoreIndex.from_documents(
    [document],
    service_context=sentence_context,
)
```

一行 `from_documents` 里已经在做：**"句子切分 + 每句带 window metadata + embedding + 入索引"** 四件事。

### 持久化

```python
sentence_index.storage_context.persist(persist_dir="./sentence_index")
```

### 可选：存在则加载，否则重建

```python
import os
from llama_index import StorageContext, load_index_from_storage

if not os.path.exists("./sentence_index"):
    sentence_index = VectorStoreIndex.from_documents(
        [document], service_context=sentence_context
    )
    sentence_index.storage_context.persist(persist_dir="./sentence_index")
else:
    sentence_index = load_index_from_storage(
        StorageContext.from_defaults(persist_dir="./sentence_index"),
        service_context=sentence_context,
    )
```

---

## 五、核心组件三：MetadataReplacementPostProcessor（检索后做"扩窗"）

### 作用

**检索完成后、送给 LLM 之前**，把每个 node 的 `text` 替换为它 metadata 里的 `window`（即前后窗口）。

> 这是实现"**embedding 用小 chunk，合成用大窗口**"的关键。

### 代码

```python
from llama_index.indices.postprocessor import MetadataReplacementPostProcessor

postproc = MetadataReplacementPostProcessor(target_metadata_key="window")
```

### 验证一下

```python
from llama_index.schema import NodeWithScore
from copy import deepcopy

scored_nodes = [NodeWithScore(node=x, score=1.0) for x in nodes]
nodes_old = [deepcopy(n) for n in nodes]

nodes_old[1].text          # 原始：只有单句
replaced_nodes = postproc.postprocess_nodes(scored_nodes)
print(replaced_nodes[1].text)   # 替换后：扩展为前后窗口
```

---

## 六、核心组件四：Re-ranker（Sentence Transformer Rerank）

### 为什么还需要重排

窗口扩展后上下文更完整了，但**初始 embedding 搜索的排序**仍是基于单句的语义相似度 —— 可能不一定准。

**Re-ranker 的思路**：先让 embedding 检索一个**较大的候选集 top_k**，然后用一个**专门训练的排序模型**重新打分，只保留 **top_n** 最相关的。

### 玩具示例：看 re-ranker 是否真的比 embedding 更准

```python
from llama_index.indices.postprocessor import SentenceTransformerRerank

rerank = SentenceTransformerRerank(
    top_n=2,
    model="BAAI/bge-reranker-base",   # 与 embedding 同家族的 re-ranker
)

from llama_index import QueryBundle
from llama_index.schema import TextNode, NodeWithScore

query = QueryBundle("I want a dog.")

scored_nodes = [
    NodeWithScore(node=TextNode(text="This is a cat"), score=0.6),   # 初始分更高
    NodeWithScore(node=TextNode(text="This is a dog"), score=0.4),   # 初始分低
]

reranked_nodes = rerank.postprocess_nodes(scored_nodes, query_bundle=query)
print([(x.text, x.score) for x in reranked_nodes])
```

结果：re-ranker **把 "This is a dog" 提到了更高的位置** —— 初始 embedding 的错序被纠正。

---

## 七、组装完整的 Query Engine

```python
sentence_window_engine = sentence_index.as_query_engine(
    similarity_top_k=6,                          # 先取 6 条候选
    node_postprocessors=[postproc, rerank],      # 先扩窗 → 再重排（内部 top_n=2）
)
```

两个关键超参：

- `similarity_top_k=6` —— **embedding 阶段**取得宽一点，让 re-ranker 有"挑选余地"；
- Re-ranker 的 `top_n=2` —— 真正送给 LLM 的只有 2 条（经扩窗后的）最相关窗口。

### 试跑

```python
window_response = sentence_window_engine.query(
    "What are the keys to building a career in AI?"
)

from llama_index.response.notebook_utils import display_response
display_response(window_response)
```

回答大致：**"learning foundational technical skills, working on projects, and finding a job."**

---

## 八、封装为 helper function（L2/L3 里用的就是这个）

```python
import os
from llama_index import ServiceContext, VectorStoreIndex, StorageContext
from llama_index.node_parser import SentenceWindowNodeParser
from llama_index.indices.postprocessor import (
    MetadataReplacementPostProcessor,
    SentenceTransformerRerank,
)
from llama_index import load_index_from_storage


def build_sentence_window_index(
    documents,
    llm,
    embed_model="local:BAAI/bge-small-en-v1.5",
    sentence_window_size=3,
    save_dir="sentence_index",
):
    node_parser = SentenceWindowNodeParser.from_defaults(
        window_size=sentence_window_size,
        window_metadata_key="window",
        original_text_metadata_key="original_text",
    )
    sentence_context = ServiceContext.from_defaults(
        llm=llm,
        embed_model=embed_model,
        node_parser=node_parser,
    )
    if not os.path.exists(save_dir):
        sentence_index = VectorStoreIndex.from_documents(
            documents, service_context=sentence_context
        )
        sentence_index.storage_context.persist(persist_dir=save_dir)
    else:
        sentence_index = load_index_from_storage(
            StorageContext.from_defaults(persist_dir=save_dir),
            service_context=sentence_context,
        )
    return sentence_index


def get_sentence_window_query_engine(
    sentence_index,
    similarity_top_k=6,
    rerank_top_n=2,
):
    postproc = MetadataReplacementPostProcessor(target_metadata_key="window")
    rerank = SentenceTransformerRerank(
        top_n=rerank_top_n,
        model="BAAI/bge-reranker-base",
    )
    return sentence_index.as_query_engine(
        similarity_top_k=similarity_top_k,
        node_postprocessors=[postproc, rerank],
    )
```

调用：

```python
index = build_sentence_window_index(
    [document],
    llm=OpenAI(model="gpt-3.5-turbo", temperature=0.1),
    save_dir="./sentence_index",
)
query_engine = get_sentence_window_query_engine(index, similarity_top_k=6)
```

---

## 九、用 TruLens 做实验：`window_size = 1 / 3 / 5`

### 核心问题

**Window 多大最划算？** 我们希望在 RAG Triad（Context Relevance / Groundedness / Answer Relevance）上分数高，同时 cost 可控。

### 预期的行为规律（直觉）

- **window_size 太小**：上下文不足 → Context Relevance 低 → LLM 用自身知识补洞 → Groundedness 也低；
- **window_size 适中**：Context Relevance 提升 → Groundedness 提升；
- **window_size 太大**：无关内容进入 context → LLM 被噪声淹没 → **Groundedness 可能反降**；同时 **token 成本上升**。

所以 Context Relevance vs. window_size 一般是**先升后平/降**的曲线，Groundedness 跟随相似但更早开始下降。

---

### 1) 加载评估问题

```python
eval_questions = []
with open('generated_questions.text', 'r') as file:
    for line in file:
        eval_questions.append(line.strip())
```

> 课堂里还提供了 `generated_questions_01_05.text` 等分片文件（每个 5 条），跑起来更快、API 失败时也更容易重跑。

### 2) 通用 run_evals

```python
from trulens_eval import Tru
from utils import get_prebuilt_trulens_recorder

Tru().reset_database()

def run_evals(eval_questions, tru_recorder, query_engine):
    for question in eval_questions:
        with tru_recorder as recording:
            query_engine.query(question)
```

### 3) window_size = 1

```python
sentence_index_1 = build_sentence_window_index(
    documents,
    llm=OpenAI(model="gpt-3.5-turbo", temperature=0.1),
    embed_model="local:BAAI/bge-small-en-v1.5",
    sentence_window_size=1,
    save_dir="sentence_index_1",
)

sentence_window_engine_1 = get_sentence_window_query_engine(sentence_index_1)

tru_recorder_1 = get_prebuilt_trulens_recorder(
    sentence_window_engine_1,
    app_id='sentence window engine 1',
)

run_evals(eval_questions, tru_recorder_1, sentence_window_engine_1)
Tru().run_dashboard()
```

**观察（21 条 records 左右）**：

- Average Latency ≈ 4.57s；
- Total Cost ≈ $0.02，Total Tokens ≈ 9,000；
- **Answer Relevance、Groundedness 都还不错**；
- **Context Relevance 明显偏低** —— 这就是 window 过小的典型症状。

**Drill-down 案例**：某个关于 "ready-fire vs. ready-fire-aim" 的问题，retrieved context 太短，**丢掉了能让答案 grounded 的支撑信息**；同时 LLM 答案后几句找不到 context 里支撑 → groundedness 为 0。

---

### 4) window_size = 3（继续用上一次那条失败问题）

```python
sentence_index_3 = build_sentence_window_index(
    documents,
    llm=OpenAI(model="gpt-3.5-turbo", temperature=0.1),
    embed_model="local:BAAI/bge-small-en-v1.5",
    sentence_window_size=3,
    save_dir="sentence_index_3",
)
sentence_window_engine_3 = get_sentence_window_query_engine(sentence_index_3)

tru_recorder_3 = get_prebuilt_trulens_recorder(
    sentence_window_engine_3,
    app_id='sentence window engine 3',
)

run_evals(eval_questions, tru_recorder_3, sentence_window_engine_3)
Tru().run_dashboard()
```

**观察**：

- **Context Relevance 从 0.57 → 0.9**（大幅跃升）；
- **Groundedness 从较低 → 1.0**（LLM 有足够 context，不再"瞎编"）；
- Answer Relevance 也有提升；
- Cost 当然更高（token 变多了），但非常值得。

### 5) window_size = 5

**观察**：

- Total Tokens 继续上升 → 成本更高；
- Context Relevance / Answer Relevance **基本持平**；
- **Groundedness 反而下降** —— 原因：context 太大，**LLM 被无关信息干扰**，开始混入自身知识做摘要。

---

## 十、结论：window_size = 3 是本数据集的甜蜜点

| window_size | Context Relevance | Groundedness | Answer Relevance | Cost |
|-------------|-----------|-------------|------------------|------|
| 1 | 低 | 低（连带） | 还行 | 最低 |
| **3** | **高** | **高** | **高** | 中 |
| 5 | 平 | **下降** | 平 | 高 |

**核心发现**：

- 存在一个窗口大小的"甜蜜点"，超过后指标不升反降；
- **Context Relevance 和 Groundedness 高度相关** —— 当检索质量差，LLM 会用内部知识补洞导致 Groundedness 掉；
- 这个甜蜜点会**依赖文档类型**（合同 vs. 发票 vs. 长文）；没有通用值，必须用 RAG Triad 实际评估。

---

## 十一、本课小结

1. **Sentence Window Retrieval** 的三块关键拼图：
   - `SentenceWindowNodeParser` —— 按句切分，把"窗口"存进 metadata；
   - `MetadataReplacementPostProcessor` —— 检索后把单句替换为窗口文本；
   - `SentenceTransformerRerank` —— 宽召回 + 精排，解决初始 embedding 排序不准的问题。

2. **调参思路**：
   - `similarity_top_k` ≥ re-ranker 的 `top_n`（给 re-ranker 挑选空间）；
   - `window_size` 是最值得实验的超参；用 RAG Triad 做 grid search 一般能很快找到甜蜜点。

3. **评估方法论**：用 TruLens 把每个版本的 query engine **赋予不同 app_id**，Dashboard 并排比较 → 聚合分数看整体变化 → drill-down 看个别失败案例的原因。

---

## 十二、下一课预告

下一课会讲另一种高级 RAG —— **Auto-merging Retrieval**，它会解决 sentence window 无法解决的一类问题："**被查询相关的几个 chunk 分布在相近但不连续的位置**"。
