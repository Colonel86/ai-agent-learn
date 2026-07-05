# L5 · Agentic RAG 与外部记忆：两种接外部数据的方式

## 1. Agentic RAG vs 传统 RAG

| | 传统 RAG | Agentic RAG |
|---|---|---|
| 何时检索 | 每次请求**必然**检索（pipeline 固定） | **agent 决定**要不要检索 |
| 怎么检索 | query 通常就是用户原话（或固定改写） | **agent 自己构造 query**（可能是一个词/短语/句子） |
| 检索后 | 结果注入一次性上下文 | 结果进窗口，agent 可再检索、翻页、组合 |

MemGPT agent 用 recall + archival 两种外部记忆做 agentic RAG。L2 的"外部记忆统计"在这里发挥作用——统计告诉 agent 有没有必要去搜。

> **架构师视角**：这正式回答了 12a L1 提出的"RAG ⊂ Agent Memory"——在 Letta 里 RAG 甚至不是独立组件,**就是 archival memory 的使用方式之一**。检索决策从 pipeline 移进了 agent 的推理循环。代价是不可控性:检索行为变成概率性的(课程里也承认"为了可靠性,demo 里明说了 search archival")。生产取舍:**关键路径要保底检索(确定性),锦上添花交给 agent 判断**——又是 12a 那个"确定性 vs agent 触发"的 2×2。

## 2. 方式一：Data Source → 灌进 archival memory

Letta 的 **source** 概念 = 一组嵌入好的 passages,可挂载到 agent。完整流程:

```python
# ① 建 source(绑定嵌入模型)
source = client.sources.create(name="employee_handbook", embedding="openai/text-embedding-3-small")

# ② 上传文件 → 返回异步 job
job = client.sources.files.upload(source_id=source.id, file=open("handbook.pdf", "rb"))
while job.status != 'completed':           # ③ 轮询 job 状态
    job = client.jobs.retrieve(job.id); time.sleep(1)
# job.metadata: 11 个 passages, 1 个文档

# ④ 挂载到 agent → passages 复制进该 agent 的 archival memory
client.agents.sources.attach(agent_id=agent_state.id, source_id=source.id)
```

**两个工程细节**：
- **嵌入模型必须一致**：source 和 agent 的 embedding model 不同会出问题——一个 source/一个 agent 的 archival 内不允许混嵌入。
- **上传是异步 job**：created → running → completed,生产里要处理轮询/回调。

之后问"搜档案里公司的休假政策" → agent 调 `archival_memory_search(query="vacation policies")` → 从手册 passages 里召回并作答(课程梗:休假条件是"你得提供一个能力不低于你的 AI agent 替你上班")。

## 3. 方式二：自定义工具连外部数据库

不复制数据,**让 agent 带着工具去查你现有的库**:

```python
def query_birthday_db(name: str):
    """This tool queries an external database to lookup the birthday ...
    Args: name (str): The name to look up
    Returns: birthday (str): The birthday in mm-dd-yyyy format"""
    my_fake_data = {"bob": "03-06-1997", "sarah": "07-06-1993"}   # 假库,可换成真 DB
    return my_fake_data.get(name.lower())

birthday_tool = client.tools.upsert_from_function(func=query_birthday_db)
agent_state = client.agents.create(...,
    tool_ids=[birthday_tool.id],
    # tool_exec_environment_variables={"DB_KEY": "my_key"},  # ← 生产要点
)
```

**`tool_exec_environment_variables`**：按 agent 注入工具执行环境变量——API key/secret 不进 prompt、不进代码,走环境注入。demo 没用上,生产必用。

发"whens my bday????" → reasoning → 调 `query_birthday_db` (+heartbeat) → `send_message("你的生日是 1993-07-06")`。

## 4. 两种方式怎么选

| | Data Source(复制进 archival) | 自定义工具(远程查询) |
|---|---|---|
| 数据所有权 | Letta 托管一份副本 | 留在原库,零复制 |
| 新鲜度 | 上传时刻的快照 | 实时 |
| 检索方式 | 统一语义检索(archival_memory_search) | 你定义(SQL/API/任意逻辑) |
| 适合 | 静态文档(手册/PDF/知识库) | 动态业务数据(用户表/订单/CRM) |

> **架构师视角**:这个二分和企业数据集成的经典抉择完全同构——**ETL(复制) vs 联邦查询(virtualization)**。判断题只有一道:数据变不变?不变→复制进 archival 享受统一语义检索;常变→工具直连保新鲜。混合架构(手册进 source、订单走工具)是常态。这条对比可直接进 [[project_selection_matrix]] 检索层。
