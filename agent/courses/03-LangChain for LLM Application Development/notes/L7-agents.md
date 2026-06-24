# Lesson 6: Agents（智能体）

## 核心思路转变

| 传统 LLM 用法 | Agent 用法 |
|------------|---------|
| LLM 作为知识库 | LLM 作为**推理引擎** |
| 静态 prompt → 答案 | LLM 决定下一步行动 |
| 无法获取新信息 | 可调用外部工具 |

**Agent = LLM（大脑）+ Tools（手脚）+ ReAct 推理循环**

---

## ReAct 推理框架

Agent 以 **Thought → Action → Observation** 循环执行：

```
Thought: 我需要查 2022 世界杯的结果
Action: DuckDuckGo_search("2022 FIFA World Cup winner")
Observation: Argentina won the 2022 FIFA World Cup...
Thought: 我得到了答案
Final Answer: Argentina won the 2022 World Cup.
```

每次循环 LLM 决定：继续用工具 or 给出最终答案。

---

## 快速上手

```python
from langchain_openai import ChatOpenAI
from langchain.agents import load_tools, initialize_agent, AgentType

llm = ChatOpenAI(temperature=0)

# 加载内置工具
tools = load_tools(["llm-math", "wikipedia"], llm=llm)

# 初始化 Agent
agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.CHAT_ZERO_SHOT_REACT_DESCRIPTION,
    handle_parsing_errors=True,
    verbose=True
)

# 使用 Agent
agent.invoke("What is 25% of 300?")
agent.invoke("What book did Tom M. Mitchell write?")
```

---

## 内置工具示例

### llm-math
处理数学计算，避免 LLM 直接计算时出错：
```python
tools = load_tools(["llm-math"], llm=llm)
agent.invoke("What is the square root of 144?")
# → 12.0
```

### Wikipedia
查询维基百科，获取实体知识：
```python
tools = load_tools(["wikipedia"], llm=llm)
agent.invoke("Who is Alan Turing?")
```

### DuckDuckGo Search
搜索实时信息（模型知识截止日期之后的事件）：
```python
from langchain.tools import DuckDuckGoSearchRun
search = DuckDuckGoSearchRun()
tools = [search]
```

---

## 自定义工具⭐

用 `@tool` 装饰器把任意 Python 函数变成 Agent 可调用的工具：

```python
from langchain.agents import tool
from datetime import date

@tool
def get_today_date(text: str) -> str:
    """Returns today's date. Use this for any questions about today's date.
    The input should always be an empty string."""
    return str(date.today())

# 加入 Agent
agent = initialize_agent(
    tools=tools + [get_today_date],
    llm=llm,
    agent=AgentType.CHAT_ZERO_SHOT_REACT_DESCRIPTION,
    handle_parsing_errors=True,
    verbose=True
)

agent.invoke("What is today's date?")
```

**关键**：docstring 是工具的"说明书"，Agent 用它判断何时调用此工具，**写清楚输入格式和用途**。

---

## Python Agent⭐（让 Agent 写代码并执行）

除了调用工具，Agent 还可以**生成 Python 代码并立即执行**——这在数据处理、排序、计算等任务中非常强大。

```python
from langchain.agents.agent_toolkits import create_python_agent
from langchain.tools.python.tool import PythonREPLTool

agent = create_python_agent(
    llm,
    tool=PythonREPLTool(),
    verbose=True
)

customer_list = [
    ["Harrison", "Chase"],
    ["Lang", "Chain"],
    ["Dolly", "Too"],
    ["Elle", "Elem"],
    ["Geoff", "Fusion"],
    ["Trance", "Former"],
    ["Jen", "Ayai"],
]

agent.run(
    f"Sort these customers by last name and then first name "
    f"and print the output: {customer_list}"
)
```

**Agent 的内部行为**：
1. **Thought**：识别这是排序任务，需要写 Python 代码
2. **Action**：`Python_REPL`
3. **Action Input**：生成 `sorted(customer_list, key=lambda x: (x[1], x[0]))` 之类代码
4. **Observation**：捕获 print 输出
5. **Final Answer**：把排序结果返回给用户

### 调试 Python Agent

```python
import langchain
langchain.debug = True

agent.run(f"Sort these customers by last name and then first name and print the output: {customer_list}")

langchain.debug = False
```

调试输出会显示 LLM 生成的**完整 Python 代码**，方便检查代码质量与逻辑。

### 适用场景

| 场景 | 示例 |
|------|------|
| 数据排序/过滤 | 按字段排序客户列表 |
| 数学运算 | 复杂矩阵计算、统计 |
| 数据格式转换 | JSON ↔ CSV ↔ DataFrame |
| 临时数据探索 | "把这个列表去重后输出" |

⚠️ **安全警告**：`PythonREPLTool` 会真实执行代码，**生产环境慎用**——可能执行任意系统命令，必须在沙箱中运行。

---

## AgentType 说明

| AgentType | 适用场景 |
|-----------|---------|
| `CHAT_ZERO_SHOT_REACT_DESCRIPTION` | 聊天模型 + ReAct，最常用 |
| `ZERO_SHOT_REACT_DESCRIPTION` | 文本 LLM + ReAct |
| `STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION` | 工具有复杂结构化输入时 |

---

## 调试 Agent

```python
import langchain
langchain.debug = True

agent.invoke("Sort this list by last name: [['Alice', 'Smith'], ['Bob', 'Jones']]")

langchain.debug = False
```

调试输出显示每次 Thought/Action/Observation 的完整内容。

---

## 使用注意

1. **`handle_parsing_errors=True`**：Agent 输出格式有时不规范，此参数让它自动重试
2. **非确定性**：Agent 可能走不同路径到达答案，对相同问题多次运行结果可能不同
3. **成本**：每次 Thought-Action 循环都消耗 token，复杂任务成本较高
4. **工具 docstring**：是 Agent 路由决策的关键，必须准确描述工具的用途和输入格式

---

## 关键要点

1. LLM 作为**推理引擎**而非知识库，是 Agent 的核心思维转变
2. **ReAct 循环**（Thought → Action → Observation）让 LLM 能多步推理
3. **`@tool` 装饰器**让任何 Python 函数成为 Agent 工具，是扩展 Agent 能力的关键
4. Agents 是目前最前沿也最不稳定的部分，适合探索性使用
