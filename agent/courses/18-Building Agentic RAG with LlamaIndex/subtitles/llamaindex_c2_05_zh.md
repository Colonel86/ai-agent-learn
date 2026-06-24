# 第 4 课：构建多文档智能体（Multi-Document Agent）

上一课的智能体只针对单文档进行多步推理。本课要把它扩展到**多文档**，并且应对**文档数量逐渐变大**带来的扩展性挑战。我们会先做 **3 篇论文**的简单版本，再做 **11 篇论文**的进阶版本。

## 准备

```python
from helper import get_openai_api_key
OPENAI_API_KEY = get_openai_api_key()

import nest_asyncio
nest_asyncio.apply()
```

## 阶段一：3 篇论文上的智能体

下载三篇 ICLR 2024 论文：MetaGPT、LongLoRA、Self-RAG。然后用第 3 课打包好的 `get_doc_tools` 为**每篇论文**生成一对工具：

- `vector_tool`：向量检索 + 元数据过滤
- `summary_tool`：整篇摘要

```python
from utils import get_doc_tools
from pathlib import Path

papers = ["metagpt.pdf", "longlora.pdf", "selfrag.pdf"]

paper_to_tools_dict = {}
for paper in papers:
    print(f"Getting tools for paper: {paper}")
    vector_tool, summary_tool = get_doc_tools(paper, Path(paper).stem)
    paper_to_tools_dict[paper] = [vector_tool, summary_tool]

initial_tools = [t for paper in papers for t in paper_to_tools_dict[paper]]
```

把这 **3 篇 × 2 个工具 = 6 个工具** 全部交给智能体：

```python
from llama_index.llms.openai import OpenAI
from llama_index.core.agent import FunctionCallingAgentWorker, AgentRunner

llm = OpenAI(model="gpt-3.5-turbo")

agent_worker = FunctionCallingAgentWorker.from_tools(
    initial_tools, llm=llm, verbose=True,
)
agent = AgentRunner(agent_worker)
```

### 单文档内的多步推理

```python
response = agent.query(
    "Tell me about the evaluation dataset used in LongLoRA, "
    "and then tell me about the evaluation results"
)
```

智能体先调用 LongLoRA 的工具拿 eval 数据集（如 PG19 测试集），再继续追问 eval 结果。

### 跨文档摘要

```python
response = agent.query("Give me a summary of both Self-RAG and LongLoRA")
```

智能体先调用 `selfrag` 的 summary_tool，再调用 `longlora` 的 summary_tool，最后把两段总结综合成最终回答。

## 阶段二：11 篇论文 → 引入"工具检索"

继续往上堆，下载 11 篇 ICLR 2024 论文：

```python
papers = [
    "metagpt.pdf", "longlora.pdf", "loftq.pdf", "swebench.pdf",
    "selfrag.pdf", "zipformer.pdf", "values.pdf",
    "finetune_fair_diffusion.pdf", "knowledge_card.pdf",
    "metra.pdf", "vr_mcl.pdf",
]

paper_to_tools_dict = {}
for paper in papers:
    print(f"Getting tools for paper: {paper}")
    vector_tool, summary_tool = get_doc_tools(paper, Path(paper).stem)
    paper_to_tools_dict[paper] = [vector_tool, summary_tool]

all_tools = [t for paper in papers for t in paper_to_tools_dict[paper]]
```

11 篇 × 2 = **22 个工具**。如果继续把所有工具都塞进 LLM 的 prompt，会暴露三个问题：

1. **塞不下**：上下文窗口虽然在变长，但文档一多很容易爆。
2. **成本与延迟飙升**：prompt token 越多越贵越慢。
3. **选不对**：候选工具一多，LLM 容易混淆，选错工具。

### 解决思路：在工具层面做 RAG

类比文本检索的思路——**对工具本身做 retrieval augmentation**：

> 用户提问 → 先**检索一小批与问题相关的工具** → 只把这些工具喂给 agent 的推理 prompt，而不是把全部 22 个工具都给出去。

最简单的实现就是对工具做 top-k 向量检索；当然你也可以叠加各种高级检索策略。

### `ObjectIndex`：在 Python 对象上做索引

LlamaIndex 默认面向文本做索引，但工具是 Python 对象，需要序列化/反序列化。这就是 **`ObjectIndex`** 这个抽象要解决的问题——它把任意 Python 对象包装成可索引、可检索的形式，底层仍由 `VectorStoreIndex` 支撑。

```python
from llama_index.core import VectorStoreIndex
from llama_index.core.objects import ObjectIndex

obj_index = ObjectIndex.from_objects(
    all_tools,
    index_cls=VectorStoreIndex,
)
obj_retriever = obj_index.as_retriever(similarity_top_k=3)
```

### 验证工具检索

```python
tools = obj_retriever.retrieve(
    "Tell me about the eval dataset used in MetaGPT and SWE-Bench"
)
tools[2].metadata
```

返回结果是**直接拿到的工具对象**（不是文本）。在这个例子中：

- 第 1 个工具：MetaGPT 的 summary 工具 ✅
- 第 2 个：和问题不太相关的论文工具（检索质量取决于 embedding 模型）
- 第 3 个：SWE-Bench 的 summary 工具 ✅

### 装上 `tool_retriever` 的 Agent

`FunctionCallingAgentWorker` 支持传入 **`tool_retriever`** 而不是固定的 `tools` 列表——每次推理前先动态检索一批工具，再让 LLM 选择。

顺便展示一个可选项：**`system_prompt`**，用来给智能体额外的引导。

```python
from llama_index.core.agent import FunctionCallingAgentWorker, AgentRunner

agent_worker = FunctionCallingAgentWorker.from_tools(
    tool_retriever=obj_retriever,
    llm=llm,
    system_prompt=(
        "You are an agent designed to answer queries over a set of given papers.\n"
        "Please always use the tools provided to answer a question. "
        "Do not rely on prior knowledge."
    ),
    verbose=True,
)
agent = AgentRunner(agent_worker)
```

### 比较型查询

```python
response = agent.query(
    "Tell me about the evaluation dataset used "
    "in MetaGPT and compare it against SWE-Bench"
)
print(str(response))
```

智能体分别调用 MetaGPT 与 SWE-Bench 的 summary 工具，最后综合出对比答案。

```python
response = agent.query(
    "Compare and contrast the LoRA papers (LongLoRA, LoftQ). "
    "Analyze the approach in each paper first."
)
```

观察执行轨迹：智能体首先用 `obj_retriever` 拉到 LongLoRA、LoftQ 相关的工具，再分别用各自的 summary_tool 查询"approach"，最后把两份回答对照综合成最终答复。

---

**小结**：你现在拥有一个真正可扩展的研究型智能体——它不仅能在多个文档之间推理，还能通过 **ObjectIndex + tool_retriever** 模式把工具数量推到几十、上百乃至更多，而不会被 LLM 的上下文限制或工具混淆击垮。这是把 Agentic RAG 推向**通用、复杂、上下文增强的研究助手**的关键一步。
