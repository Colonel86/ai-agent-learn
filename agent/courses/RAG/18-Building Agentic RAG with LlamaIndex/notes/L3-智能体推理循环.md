# 第 3 课：构建智能体推理循环（Agent Reasoning Loop）

## 为什么需要"循环"？

到目前为止，我们的查询都是**单次前向通过（single forward pass）**：拿到问题 → 选工具 → 填参数 → 返回答案。但这显然不够用：

- 如果用户的问题是**多步骤复合的**怎么办？
- 如果问题**模糊、需要澄清**怎么办？

本课就要把"工具调用"从 single-shot 升级为**完整的智能体推理循环**——智能体能够**在工具之上跨多步推理**。我们将使用 LlamaIndex 的 **`FunctionCallingAgentWorker`**，它原生对接 LLM 的 function calling 能力。

## 准备工作

```python
from helper import get_openai_api_key
OPENAI_API_KEY = get_openai_api_key()

import nest_asyncio
nest_asyncio.apply()
```

继续沿用 MetaGPT 论文。第 2 课里"vector + 元数据过滤的工具"和"summary 工具"已经被打包到 `utils.get_doc_tools` 中，一行调用即可：

```python
from utils import get_doc_tools

vector_tool, summary_tool = get_doc_tools("metagpt.pdf", "metagpt")
```

## LlamaIndex 中智能体的两层结构

在 LlamaIndex 里，一个智能体由两个组件构成：

- **`AgentWorker`（智能体工作单元）**：负责**执行下一步**——给定对话历史、记忆、当前用户输入，用 function calling 决定下一个要调的工具，调用它，并决定是否要返回最终答案。
- **`AgentRunner`（智能体调度器）**：整体任务调度者，负责**创建任务**、**编排 worker 多次运行**、**返回最终响应**。它是你直接交互的高层接口。

```python
from llama_index.llms.openai import OpenAI
from llama_index.core.agent import FunctionCallingAgentWorker, AgentRunner

llm = OpenAI(model="gpt-3.5-turbo", temperature=0)

agent_worker = FunctionCallingAgentWorker.from_tools(
    [vector_tool, summary_tool],
    llm=llm,
    verbose=True,
)
agent = AgentRunner(agent_worker)
```

## 高层接口：query 一次性问答

```python
response = agent.query(
    "Tell me about the agent roles in MetaGPT, "
    "and then how they communicate with each other."
)
```

观察 `verbose` 日志，能看到智能体把**这个复合问题拆成两步**：

1. 第一步：调 `summary_tool`，输入"agent roles in MetaGPT"——返回 product manager、architect、project manager、QA、engineer 等角色。
2. 第二步：基于第一步结果做**链式思考（chain of thought）**，触发下一个问题"communication between agent roles in MetaGPT"——返回它们之间通过共享消息池（shared message pool）和订阅机制进行结构化通信。
3. 综合两步结果，生成最终答案。

> 小提示：这里第一步用了 `summary_tool`，其实 `vector_tool` 可能给出更精准的段落。`gpt-3.5-turbo` 在工具选择上不算完美，更强的模型（GPT-4 Turbo、Claude 3 Sonnet/Opus）会做得更好。

来源也可追溯：

```python
print(response.source_nodes[0].get_content(metadata_mode="all"))
```

## 维护对话记忆：agent.chat

`agent.query` 是**无状态**的一次性问答。而 `agent.chat` 会**维护对话历史**——智能体把所有交互写入 **conversation memory buffer**（默认是一个按上下文窗口大小滚动的扁平列表）。

下面看一个典型的"上下文引用"场景：

```python
response = agent.chat("Tell me about the evaluation datasets used.")
# → 调用 summary_tool，得到 HumanEval / MBPP / SoftwareDev

response = agent.chat("Tell me the results over one of the above datasets.")
# → "the above datasets" 只有靠历史才能解析
# 智能体把"上文 + 当前问题"翻译成 vector_tool 上的查询"results over HumanEval"
```

如果没有对话历史，第二个问题根本无法回答。

## 低层接口：可调试性与可控性

LlamaIndex 同时暴露了**低层 API**，让你对智能体做**细粒度控制**：

- **可调试性（Debuggability）**：智能体跑错了，你想看清每一步到底干了什么、在哪一步出了岔。
- **可引导性（Steerability）**：在执行中途**注入用户反馈**，引导后续步骤——比如通过异步队列接收人类输入，立刻打断并改写当前任务方向，而不必等任务全部跑完。

### 创建任务并单步执行

```python
agent_worker = FunctionCallingAgentWorker.from_tools(
    [vector_tool, summary_tool], llm=llm, verbose=True
)
agent = AgentRunner(agent_worker)

task = agent.create_task(
    "Tell me about the agent roles in MetaGPT, "
    "and then how they communicate with each other."
)
```

`create_task` 返回一个 `task` 对象，里面包含输入和任务状态。

```python
step_output = agent.run_step(task.task_id)
```

执行一步后，可以看到它只跑了第一段——调用 `summary_tool` 处理"agent roles in MetaGPT"，然后**停下来**等下一次指令。

### 查看已完成与待执行步骤

```python
completed_steps = agent.get_completed_steps(task.task_id)
print(f"Num completed for task {task.task_id}: {len(completed_steps)}")
print(completed_steps[0].output.sources[0].raw_output)

upcoming_steps = agent.get_upcoming_steps(task.task_id)
print(f"Num upcoming steps for task {task.task_id}: {len(upcoming_steps)}")
```

待执行步骤里的 `input` 是 `None`——因为智能体可以**从对话历史自动生成下一步动作**，不需要外部新输入。

> 这一刻就是天然的"断点"：你完全可以在这里**暂停并取走中间结果**，不必跑完整个流程。

### 中途注入用户输入（Steerability）

现在演示**改写智能体执行方向**——原始问题里没问"agents 如何共享信息"，但我们想插进去：

```python
step_output = agent.run_step(
    task.task_id,
    input="What about how agents share information?"
)
```

这条 user message 被加入记忆，下一步智能体就会去回答"how agents share information in MetaGPT"。

### 跑完最后一步并合成响应

```python
step_output = agent.run_step(task.task_id)
print(step_output.is_last)  # True，说明已经是最后一步

response = agent.finalize_response(task.task_id)
print(str(response))
```

`finalize_response` 把整个任务的轨迹合成为最终回答。

---

**小结**：你掌握了两种交互方式——

- **高层接口** `agent.query` / `agent.chat`：方便日常使用，支持对话记忆。
- **低层接口** `create_task` / `run_step` / `get_completed_steps` / `get_upcoming_steps` / `finalize_response`：用于调试、单步审查、人类反馈注入。

下一课，我们要把智能体推向**多文档**场景。
