# Building and Evaluating Advanced RAG — 第 03 课：RAG Triad 三元评估指标（中文整理）

> 来源：`subtitles/llamaindex-truera_c1_03_en.vtt` + `code/L3-RAG_Triad_of_metrics.md`
> 本课目标：深入讲解 **RAG 评估三元指标（RAG Triad）**，用 **Feedback Function** 抽象去定义 Answer Relevance / Context Relevance / Groundedness，并用 TruLens 在真实应用上跑出**逐条记录 + 聚合看板**。

---

## 一、本课讲什么

这一课把 L2 里"一行调用 `get_prebuilt_trulens_recorder`"这层黑盒拆开，重点讲：

1. RAG 的三大评估指标（**Context Relevance / Groundedness / Answer Relevance**）各自在评估什么；
2. 这三者都是 **Feedback Function** 的具体实例 —— 一个可扩展的、**程序化评估 LLM 应用**的框架；
3. 如何把任意**非结构化语料**合成成一个**评估数据集**；
4. 怎么在 Notebook 和 Streamlit Dashboard 里**逐条 + 聚合**地看评估结果，找到 Failure Mode。

---

## 二、准备工作与 RAG 应用搭建（复用上一课）

### 1) 环境

假设你已经 pip 安装好了 `trulens-eval` 和 `llama_index`，只需配置 OpenAI Key 即可。**Key 同时服务于两件事**：
- RAG 的 completion 步（生成回答）；
- TruLens 的评估实现（LLM-as-a-judge）。

```python
import warnings
warnings.filterwarnings('ignore')

import utils
import os
import openai
openai.api_key = utils.get_openai_api_key()
```

### 2) 初始化 TruLens

TruLens 的 `Tru` 类是整个评估系统的"中枢"。它持有一个本地数据库，用来记录：
- prompt / response / 各中间结果；
- 每个 feedback function 的输出分数和理由。

```python
from trulens_eval import Tru

tru = Tru()
tru.reset_database()
```

### 3) 加载文档并合并成单文档

仍然用 Andrew Ng 的 PDF《How to Build a Career in AI》：

```python
from llama_index import SimpleDirectoryReader
from llama_index import Document

documents = SimpleDirectoryReader(
    input_files=["./eBook-How-to-Build-a-Career-in-AI.pdf"]
).load_data()

document = Document(text="\n\n".join([doc.text for doc in documents]))
```

### 4) 构建 Sentence Window 索引 + Query Engine

本课直接**在上一课已经看过的 Sentence Window RAG 上跑评估**：

```python
from utils import build_sentence_window_index
from utils import get_sentence_window_query_engine
from llama_index.llms import OpenAI

llm = OpenAI(model="gpt-3.5-turbo", temperature=0.1)

sentence_index = build_sentence_window_index(
    document,
    llm,
    embed_model="local:BAAI/bge-small-en-v1.5",
    save_dir="sentence_index",
)

sentence_window_engine = get_sentence_window_query_engine(sentence_index)
```

### 5) 先跑一个问题看看输出

```python
output = sentence_window_engine.query("How do you create your AI portfolio?")
output.response
```

返回对象里会包含：最终 LLM 答案 + 中间检索到的 context + 相关 metadata。**这"三块"正是等会评估三指标要用到的材料**。

---

## 三、Feedback Function：一个统一抽象

### 什么是 Feedback Function

> Feedback Function：**在审视 LLM 应用的输入、输出、中间结果之后，给出 0~1 之间一个分数**的程序化评估器。

要点：
- **不必**用 LLM 实现。也可以用 BERT、甚至传统 NLP 指标（ROUGE / BLEU）；但 LLM 评估在"语义"层面比纯语法匹配（river bank 还是 financial bank）要强。
- 结构固定：**Provider（提供者，这里是 OpenAI GPT-3.5） + Function（具体 feedback 逻辑） + 输入来源（input/output/中间结果）**。

本课三大指标都是 Feedback Function 的实例。

### 打开 `nest_asyncio` 与设置 Provider

```python
import nest_asyncio
nest_asyncio.apply()

from trulens_eval import OpenAI as fOpenAI
provider = fOpenAI()
```

这里的 `fOpenAI` 是 TruLens 封装过的 OpenAI provider，供后面所有 feedback function 共用。

---

## 四、指标 1：Answer Relevance（答案相关性）

### 评估对象

**user query ↔ final response** —— 最终回答是否切题。

### 示例

- 问题：*How can altruism be beneficial in building a career?*
- 回答：(某段 RAG 输出)
- 评估输出：**score = 0.9**（0~1 分）+ **Chain-of-Thought 理由**：指出答案中哪些部分让它"高度相关"。

### 代码

```python
from trulens_eval import Feedback

f_qa_relevance = Feedback(
    provider.relevance_with_cot_reasons,   # ← 带 CoT 的 relevance 函数
    name="Answer Relevance",               # ← 展示在 Dashboard 里的名字
).on_input_output()                         # ← 输入来自用户 query，输出来自 RAG response
```

要点：

- `relevance_with_cot_reasons`：不仅返回分数，还附带"链式推理"的理由 → Dashboard 里可直接解释"为什么打这个分"。
- `.on_input_output()`：用户输入 + 最终输出 **两项**做评估，不涉及中间结果。

---

## 五、指标 2：Context Relevance（上下文相关性）

### 评估对象

**user query ↔ 每个检索到的 context** —— 检索阶段是否真的找到了相关资料。

### 示例

- 同一问题，检索到两段 context；
- 左边得分 **0.5**，右边 **0.7**；
- 最终指标 = 两者**平均值** = 0.6。

### 关键：用 `context_selection` 指定中间结果位置

```python
from trulens_eval import TruLlama

context_selection = TruLlama.select_source_nodes().node.text
```

这行相当于告诉 TruLens：**"我想评估的中间结果，就是 LlamaIndex 每次检索命中的 source node 里的 text 字段。"**

### 定义 Context Relevance Feedback Function（带 CoT）

```python
import numpy as np

f_qs_relevance = (
    Feedback(
        provider.qs_relevance_with_cot_reasons,  # Q-Statement Relevance 带 CoT
        name="Context Relevance",
    )
    .on_input()                 # query
    .on(context_selection)      # 每一条 retrieved context
    .aggregate(np.mean)         # 多条 context 的分数取平均
)
```

要点：

- **每条** retrieved chunk 分别打分；
- `np.mean` 把多条分数聚合为一个指标；
- 开启 CoT 后，Dashboard 里每条 chunk 都会带一段"为什么 0.7"的说明。

对比 Answer Relevance：**Context Relevance 用到了中间结果**。这就是 feedback function 的强大之处 —— 可以在应用的任意层级（input / 中间 / output）打点评估。

---

## 六、指标 3：Groundedness（有据性 / 扎实性）

### 评估对象

**retrieved context ↔ final response** —— 回答里的每句话，是否都能在检索到的上下文里找到支持？

### 为什么重要

如果检索的 context 不够好，**LLM 往往会用自己预训练时学过的"内部知识"来补洞** —— 这会导致 groundedness 下降（因为这些信息并非来自检索结果）。

### 评估流程

1. 把 response 拆成若干句；
2. 每句在 retrieved context 中找"支持证据"；
3. 每句给 0~1 分 + CoT 理由；
4. 聚合得到整个 response 的 groundedness 分数。

### 代码

```python
from trulens_eval.feedback import Groundedness

grounded = Groundedness(groundedness_provider=provider)

f_groundedness = (
    Feedback(
        grounded.groundedness_measure_with_cot_reasons,
        name="Groundedness",
    )
    .on(context_selection)                              # 支撑材料：retrieved context
    .on_output()                                        # 被检验对象：final response
    .aggregate(grounded.grounded_statements_aggregator) # 按句聚合
)
```

---

## 七、把三指标组装到 Tru Recorder

有了三个 feedback function 后，把它们**挂到一个 query engine 上**得到 `TruLlama` —— 这是 TruLens 与 LlamaIndex 的集成点。

```python
from trulens_eval import TruLlama
from trulens_eval import FeedbackMode

tru_recorder = TruLlama(
    sentence_window_engine,     # 你的 RAG query engine
    app_id="App_1",             # 版本号：方便对比多个实验
    feedbacks=[
        f_qa_relevance,
        f_qs_relevance,
        f_groundedness,
    ],
)
```

> `app_id` 非常关键：**每次调参都换个 `app_id`**，Dashboard 就能并排对比多个版本。

---

## 八、跑评估

### 加载评估问题集

```python
eval_questions = []
with open('eval_questions.txt', 'r') as file:
    for line in file:
        item = line.strip()
        eval_questions.append(item)

eval_questions.append("How can I be successful in AI?")   # 你也可以自己追加问题
```

### 循环跑

```python
for question in eval_questions:
    with tru_recorder as recording:
        sentence_window_engine.query(question)
```

背后会发生的事：

- RAG 正常执行；
- **同时** tru_recorder 针对每一条 query 自动计算三项 feedback；
- prompt / response / 中间结果 / 分数 / 理由 **全部写入本地数据库**。

---

## 九、查看结果

### 1) Notebook 里看 record 级视图

```python
records, feedback = tru.get_records_and_feedback(app_ids=[])
records.head()
```

想更清爽地看：

```python
import pandas as pd

pd.set_option("display.max_colwidth", None)
records[["input", "output"] + feedback]
```

每行 = 一次查询，展示 input / output + 三项得分。

### 2) Leaderboard 聚合视图

```python
tru.get_leaderboard(app_ids=[])
```

聚合视图会看到（示例）：
- `app_id` = `App_1`；
- Context Relevance ≈ **0.56**；
- Groundedness ≈ **0.86**；
- Answer Relevance ≈ **0.92**；
- Average Latency / Total Cost / Total Tokens。

### 3) Streamlit Dashboard

```python
tru.run_dashboard()
```

Dashboard 可以：

- 看聚合指标（全体 11 records 平均值）；
- 下钻到**单条记录**；
- 对某条记录**再下钻到每一个 feedback**，看 CoT 理由；
- 并排对比多个 app_id。

---

## 十、读懂 Dashboard：两个典型案例

### 案例 A：表现好的一条

- 问题：*"What is the first step to becoming good at AI?"*
- 回答：*"learn foundational technical skills"*
- Answer Relevance：**1.0**；
- 两条 context 各 0.8，Context Relevance 平均 **0.8**，并有 CoT 解释；
- Groundedness：**1.0**（回答里的每句都在 context 中找到了支持）。

### 案例 B：Groundedness 偏低的一条

- 问题：*"How can altruism be beneficial in building a career?"*
- 回答被拆成 4 句，前 2 句有据可依得分高，**后 2 句得分 0**：
  - 原因：如 "practicing altruism can contribute to personal fulfillment and a sense of purpose..." 这句，**在 retrieved context 里完全找不到支撑**；
  - 这种句子"听起来合理"，但其实是 LLM 拿自己预训练知识补的。
- 这就是经典的 **低 groundedness 失败模式**。

> **结论**：指标本身给你聚合分，CoT + record-level drill-down 告诉你**具体在哪一句、为什么掉分** —— 这正是"系统化 Error Analysis"所需的信息。

---

## 十一、常见 Failure Mode：Context 太小

- 检索 context 过小 → Context Relevance 低；
- **连带** Groundedness 也会低（因为 LLM 被迫用自己的知识补洞）；
- 增大 context 规模，**一般先出现 Context Relevance 和 Groundedness 同时上升**；
- 但是 **context 过大** 又会让无关信息混入，Answer Relevance / Groundedness 反而下降。

所以下一课会围绕 "**Sentence Window size 调参**" 做专门实验。

---

## 十二、Feedback Function 的其他形态

本课用 **LLM-as-a-judge** 实现了 3 个指标，但 feedback function 不只这一种做法：

| 类型 | 典型做法 | 优点 | 缺点 |
|------|-----------|------|------|
| Ground Truth Eval | 专家给"标准答案"打分 | 质量高 | 收集昂贵 |
| Human Eval | 普通用户打分 | 比专家快 | 信心较低、难 scale |
| LLM Eval | 用 LLM 打分 | **可 scale、可定制、可随域演进** | 依赖评估模型质量 |
| NLP Metric | ROUGE / BLEU | 轻量 | 纯语法，不懂"river bank vs. financial bank" |

**研究结论**：人与人之间的评分一致率约 **80%**，LLM 与人的一致率在 **80~85%** —— 意味着 LLM Eval 在已测过的 benchmark 上**和人类评估可比**。

> TruLens 开源库里还有更多评估：Honest / Harmless / Helpful 等，鼓励自己去挖。

---

## 十三、关键要点总结

1. **RAG Triad 三元评估**：Context Relevance（检索）/ Groundedness（有据）/ Answer Relevance（切题），三个相互印证，能定位失败发生在**哪一环**。
2. **Feedback Function** 把"评估"这件事抽象成**可编程、可组合、可解释（CoT）**的函数；输入可以来自 query / response / **任意中间结果**。
3. **App ID 是你的实验轴**：每次改动一个参数就换 ID，Dashboard 天然支持并排比较。
4. **Dashboard 的真正价值在于 drill-down**：聚合分数 → 单条记录 → 单个指标 → CoT 理由，一路追到具体那一句为什么出错。
5. **下一课预告**：深入 Sentence Window Retrieval 的内部实现，并用三元指标对比不同 window size 的影响。
