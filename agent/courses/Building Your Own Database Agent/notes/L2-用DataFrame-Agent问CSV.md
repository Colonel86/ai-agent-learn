# L2 · 用 pandas DataFrame Agent 对 CSV 做自然语言查询

> 课程：Building Your Own Database Agent（DeepLearning.AI × Microsoft）· Lesson 2
> 本课任务：把一份 CSV（美国各州 COVID-19 统计，2020–2021）加载成 pandas DataFrame，用 LangChain 的 **pandas DataFrame agent** 直接用自然语言问它，并用 prefix/suffix 把提问工程化。

## 1. 从"问模型"到"问数据"：先厘清四种取数方案

讲师把"公司要建 database agent"这个真实诉求，拆成四条可选技术路线，本课先走最简单的 CSV：

| 方案 | 做法 | 适用/代价 | 本课 |
|---|---|---|---|
| **Fine-tuning** | 为特定 SQL 任务微调 GPT-4 | 能造 IP，但对本课太复杂 | ❌ |
| **RAG（本课）** | LangChain agent 连数据源（CSV/DB）当检索源 | 直接、简单，作为起点 | ✅ L2 用 CSV，L3 用 SQL |
| **Function calling** | 定义函数在后端执行 SQL，不把查询暴露给代码 | SQL 任务很有用 | 留到 L4 |
| **Assistants API** | 带状态管理，提供短期记忆和上下文 | 加 code interpreter | 留到 L5 |

本课明确用 RAG + CSV 作起点，L3 把同样方法换到 SQL 数据库。

> **架构师视角**：这张表是整门课的"选型地图"——四条路线不是并列备选，而是**沿复杂度递进、按需求分层**。用 CSV/DataFrame 起步是刻意的教学降维：先把"Agent 会自己写代码取数并解释推理"这件事跑通，再逐步换掉底层取数方式（→SQL→function calling→Assistants）。做架构时同理，先用最轻的方案验证价值，再按约束（安全、状态、规模）逐级升级，而不是一上来堆最重的。

## 2. 加载 CSV 与创建 DataFrame Agent

环境准备与 L1 相同（导库、配 Azure OpenAI）。新增的是数据源：

```python
# 加载 CSV → pandas DataFrame；fillna(0) 把空值统一填 0，避免后续计算踩坑
df = pd.read_csv("./data/all-states-history.csv").fillna(value=0)
# 数据集：美国各州 COVID-19 统计，2020 与 2021 年
```

关键一步——不是普通 agent，而是**专门的 pandas DataFrame agent**：

```python
from langchain.agents.agent_types import AgentType
from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent

# llm = L1 建好的模型；df = CSV 的 DataFrame 表示；verbose=True 打开推理轨迹
agent = create_pandas_dataframe_agent(llm=model, df=df, verbose=True)

# 调用入口仍是 invoke（和 L1 完全一致），但现在能问数据
agent.invoke("how many rows are there?")
```

数据集有 **20,780 行**。`verbose=True` 会打印 Agent 的完整推理链——这是本课的重头戏。

## 3. 读懂 Agent 的执行轨迹（trace）

`invoke` 之后 LangChain 打印出一条 **agent executor chain**，形态是经典的 ReAct 循环：

```
> Entering new AgentExecutor chain...
Thought:   我需要数一下行数
Action:    （执行 pandas 代码 / 观察 DataFrame）
Observation: 得到中间结果
Thought:   I now know the final answer
Final Answer: There are 20,780 rows.
> Finished chain.
```

要盯的是 `Finished chain`——任何 Agent 交互都以它收尾，前面是 input（你的问题）、后面是 output（结果）。讲师反复强调"花时间读 trace"，因为它把 Agent"怎么想的、跑了什么代码、看到什么"全暴露出来，是调试和信任的基础。

## 4. Prefix / Suffix：把提问工程化

单句问答之外，真实场景要更复杂、更可控。做法是把一次调用拆成三段文本拼接：**prefix + question + suffix**。

```python
# 前缀：给模型的"前置指令"——先把 pandas 显示选项设成展示所有列、取列名，再回答
CSV_PROMPT_PREFIX = """
First set the pandas display options to show all the columns,
get the column names, then answer the question.
"""

# 后缀：约束"回答的方式"——要求交叉验证、禁止编造、必须解释推理
CSV_PROMPT_SUFFIX = """
- **ALWAYS** before giving the Final Answer, try another method.
  Then reflect on the answers of the two methods and check they match.
- If methods disagree, retry until two methods agree.
- If still inconsistent, say you are not sure.
- If sure, produce a thorough Markdown response.
- **DO NOT MAKE UP AN ANSWER OR USE PRIOR KNOWLEDGE,
  ONLY USE THE RESULTS OF THE CALCULATIONS YOU HAVE DONE**.
- **ALWAYS** end with an "Explanation:" section naming the columns you used.
"""

QUESTION = ("How many patients were hospitalized during July 2020 in Texas, "
            "and nationwide as the total of all states? "
            "Use the hospitalizedIncrease column")

# 三段拼接后一次 invoke
agent.invoke(CSV_PROMPT_PREFIX + QUESTION + CSV_PROMPT_SUFFIX)
```

三段各司其职：

| 段 | 作用 | 本例内容 |
|---|---|---|
| prefix | 前置动作指令 | 先展示所有列、取列名 |
| question | 用户真实问题 | 7 月德州 + 全国住院人数 |
| suffix | 行为约束/输出规范 | 双方法交叉验证、禁编造、必须解释、指定列 |

讲师强调 suffix 里的**双方法交叉验证 + 禁用先验知识**是可靠性的关键：Agent 会用两种算法各算一遍、比对一致才给答案，且只用实际算出的结果、不许瞎编。"The magic"在于 prefix/suffix 可按应用场景做不同模板——纯语言学，让模型理解你要什么。

> **对比 L3 的 SQL prefix**：本课 prefix/suffix 是**通用文本约束**（针对 pandas 场景）；L3 会把 prefix 升级成专门的 SQL agent 模板——加"你是操作 SQL 数据库的 agent"的角色声明、`{dialect}`/`{top_k}` 占位符、禁 DML（INSERT/UPDATE/DELETE）等安全护栏。同一套"prefix 定角色与约束、suffix/format 定输出格式"的模式，随数据源升级而加码。这正是 4-tools.md 里"给工具调用套护栏"思想在 prompt 层的体现。

## 5. 一个真实结果：Agent 会"忠于数据"

问"2020 年 7 月德州住院多少人"，Agent 的推理轨迹里能看到它：import pandas → 按日期过滤到 July 2020 → 再过滤 Texas → 求和。结果：

- **德州 = 0**（CSV 里该时段无住院记录）
- **全国合计 ≈ 63K**

讲师现场解读：从探索性数据分析（EDA）角度，德州为 0 很可能是"那段时间没在追踪该指标"，但 **Agent 严格按文件里的数据回答、不臆测**（suffix 已禁编造）。Agent 还会在 `Explanation:` 段说明用了哪些列、怎么算的。输出也提供 JSON 形态，方便下游程序消费（互操作性好）。

> **架构师视角**：`德州=0` 这个反直觉结果恰是护栏生效的证据。没有 suffix 的"禁用先验知识"，模型很可能"脑补"一个看起来合理的非零住院数——那才是 data agent 最危险的失败模式。**data agent 的可信度不在它多聪明，而在它肯不肯承认"数据里就是没有"**。这也是为什么要配 Snowflake 那门评测课：光看单个答案漂亮不够，得系统度量"忠于数据"的比例。

## 本课总结

| 要点 | 一句话 |
|---|---|
| 四种取数方案 | fine-tuning / RAG / function calling / Assistants，按复杂度递进，本课用 RAG+CSV |
| DataFrame agent | `create_pandas_dataframe_agent(llm, df)`，调用仍是 `invoke` |
| trace | `verbose=True` 打印 ReAct 轨迹，`Finished chain` 收尾，必读 |
| prefix/suffix | 前置指令 + 问题 + 输出约束三段拼接，可做模板 |
| 忠于数据 | 双方法交叉验证 + 禁用先验知识，德州=0 就是 0 |

> **记忆点（引出 L3）**：L2 里数据"活在内存的 DataFrame 里"，Agent 写的是 pandas 代码。L3 把同一份 CSV 灌进 **SQLite 数据库**，换成 LangChain 的 **SQL agent + SQLDatabaseToolkit**，Agent 从此写的是真正的 SQL 查询——`invoke` 入口不变、prefix/suffix 模式不变，但取数从"内存计算"升级为"数据库查询"，并把生成的 SQL 轨迹显式暴露出来（既能答问，也能教用户 SQL）。

## 与我的资产映射

- 检索层：`agent/skills/agent-selection/3-retrieval.md`（结构化数据 RAG 的 CSV 实例）
- 工具层：`agent/skills/agent-selection/4-tools.md`（suffix 护栏 = prompt 层的工具调用约束）
- 对照课程：Snowflake《Building and Evaluating Data Agents》（"忠于数据"需要系统评测才能度量）
- [[project_selection_matrix]]
