# Functions, Tools and Agents with LangChain — 第 07 课：Conversational Agent（中文整理）

> 来源：`subtitles/langchain_c3_07_en.vtt` + `code/L7-functional_conversation-student.md`
> 本课目标：把上一课的"单步 tool 调用"扩展成**完整 Agent 循环**，加上**记忆（memory）**和一个 **Panel 打造的 Web UI**，组装出一个近似 ChatGPT 的对话式 Agent。

---

## 一、什么是 Agent

Agent = **语言模型 + 代码**：
- **语言模型**负责推理"下一步做什么、传什么参数"；
- **代码**负责执行一个 **Agent Loop** —— 用模型选工具 → 调工具 → 观察 → 再问模型 → 直到满足停止条件。

### 停止条件可以是

- **模型自己说"不需要再调工具了"**（AgentFinish）—— 最常见；
- **硬编码规则**（最大步数、超时等）。

上一课我们已经做到了"选工具 + 调工具"的单步。本课就是把它**包进循环**。

---

## 二、复用上一课的工具

```python
from langchain.tools import tool
import requests, datetime, wikipedia
from pydantic import BaseModel, Field

# --- 工具 1: Open-Meteo 天气 ---
class OpenMeteoInput(BaseModel):
    latitude: float = Field(..., description="Latitude of the location to fetch weather data for")
    longitude: float = Field(..., description="Longitude of the location to fetch weather data for")

@tool(args_schema=OpenMeteoInput)
def get_current_temperature(latitude: float, longitude: float) -> dict:
    """Fetch current temperature for given coordinates."""
    ... # 与 L6 相同
    return f'The current temperature is {current_temperature}°C'

# --- 工具 2: Wikipedia ---
@tool
def search_wikipedia(query: str) -> str:
    """Run Wikipedia search and get page summaries."""
    ... # 与 L6 相同

tools = [get_current_temperature, search_wikipedia]
```

---

## 三、先重建上一课的单步 chain

```python
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.tools.render import format_tool_to_openai_function
from langchain.agents.output_parsers import OpenAIFunctionsAgentOutputParser

functions = [format_tool_to_openai_function(f) for f in tools]
model = ChatOpenAI(temperature=0).bind(functions=functions)

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are helpful but sassy assistant"),
    ("user", "{input}"),
])

chain = prompt | model | OpenAIFunctionsAgentOutputParser()

result = chain.invoke({"input": "what is the weather is sf?"})
result.tool         # 'get_current_temperature'
result.tool_input   # {'latitude': ..., 'longitude': ...}
```

---

## 四、Agent Scratchpad：让模型看到"已经做过什么"

要形成循环，模型必须在**第 N 轮**看到**前 N-1 轮**的工具调用和结果。这个"草稿纸"叫 **agent_scratchpad**。

### 改 prompt：加上 `MessagesPlaceholder("agent_scratchpad")`

```python
from langchain.prompts import MessagesPlaceholder

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are helpful but sassy assistant"),
    ("user", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

chain = prompt | model | OpenAIFunctionsAgentOutputParser()
```

### 第一轮：scratchpad 为空

```python
result1 = chain.invoke({
    "input": "what is the weather is sf?",
    "agent_scratchpad": [],
})

result1.tool         # 'get_current_temperature'
observation = get_current_temperature(result1.tool_input)
# observation ≈ 'The current temperature is 22.9°C'
```

### 把 `(action, observation)` 折叠成 message 列表

```python
from langchain.agents.format_scratchpad import format_to_openai_functions

format_to_openai_functions([(result1, observation)])
# → [
#     AIMessage(content='', additional_kwargs={'function_call': {...}}),   # 上一轮模型的决定
#     FunctionMessage(name='get_current_temperature', content='The current temperature is 22.9°C'),
#   ]
```

`result1.message_log` 保留着上一轮模型原始的 AIMessage，这就是为什么能把它**一比一**还原回去。

### 第二轮：带上 scratchpad 继续问

```python
result2 = chain.invoke({
    "input": "what is the weather is sf?",
    "agent_scratchpad": format_to_openai_functions([(result1, observation)]),
})

# → AgentFinish，带上 "The current temperature in San Francisco is 22.9°C"
```

---

## 五、手写 Agent 循环

```python
from langchain.schema.agent import AgentFinish

def run_agent(user_input):
    intermediate_steps = []
    while True:
        result = chain.invoke({
            "input": user_input,
            "agent_scratchpad": format_to_openai_functions(intermediate_steps),
        })
        if isinstance(result, AgentFinish):
            return result

        tool = {
            "search_wikipedia": search_wikipedia,
            "get_current_temperature": get_current_temperature,
        }[result.tool]

        observation = tool.run(result.tool_input)
        intermediate_steps.append((result, observation))
```

### 把 scratchpad 预处理塞到 chain 里（更"真 Agent"）

每次都手动写 `format_to_openai_functions(...)` 繁琐，LCEL 可以直接把这一步塞进 chain：

```python
from langchain.schema.runnable import RunnablePassthrough

agent_chain = RunnablePassthrough.assign(
    agent_scratchpad=lambda x: format_to_openai_functions(x["intermediate_steps"])
) | prompt | model | OpenAIFunctionsAgentOutputParser()
```

`RunnablePassthrough.assign(key=fn)` = **原输入照传，再给 dict 多塞一个 key**。调用方只要传 `input` 和 `intermediate_steps`。

### 简化后的循环

```python
def run_agent(user_input):
    intermediate_steps = []
    while True:
        result = agent_chain.invoke({
            "input": user_input,
            "intermediate_steps": intermediate_steps,
        })
        if isinstance(result, AgentFinish):
            return result
        tool = {
            "search_wikipedia": search_wikipedia,
            "get_current_temperature": get_current_temperature,
        }[result.tool]
        observation = tool.run(result.tool_input)
        intermediate_steps.append((result, observation))
```

测试：

```python
run_agent("what is the weather is sf?")   # → 调 weather 工具，给出温度
run_agent("what is langchain?")            # → 调 wiki 工具，回答
run_agent("hi!")                            # → 直接回答，不调工具
```

---

## 六、用 `AgentExecutor` 代替手写循环

LangChain 提供了这个类，**等价于上面的 run_agent**，但额外增加：

- JSON 解析失败时的**错误处理**；
- 工具抛异常时的错误处理（把错误信息回传给模型让它更正）；
- `verbose=True` 可以看到每一步的思考过程。

```python
from langchain.agents import AgentExecutor

agent_executor = AgentExecutor(agent=agent_chain, tools=tools, verbose=True)

agent_executor.invoke({"input": "what is langchain?"})
```

**这就是 Agent 循环的"生产版本"**。它在内部做的事，跟 ChatGPT 的 Code Interpreter / Plugin 的调度非常相似 —— 先思考、再调工具、看结果、再思考……

---

## 七、加上"对话记忆"

目前的 Agent **没有记忆**：

```python
agent_executor.invoke({"input": "my name is bob"})
# → "Hello, Bob! How can I assist you today?"

agent_executor.invoke({"input": "what is my name"})
# → "I don't know your name."   ← 没记住
```

因为每次 invoke 都是**全新**的 intermediate_steps，没有跨轮状态。

### 修 prompt：再加一个 `MessagesPlaceholder("chat_history")`

```python
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are helpful but sassy assistant"),
    MessagesPlaceholder(variable_name="chat_history"),   # ← 位于 user 之前
    ("user", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

agent_chain = RunnablePassthrough.assign(
    agent_scratchpad=lambda x: format_to_openai_functions(x["intermediate_steps"])
) | prompt | model | OpenAIFunctionsAgentOutputParser()
```

### 用 `ConversationBufferMemory` 管理历史

```python
from langchain.memory import ConversationBufferMemory

memory = ConversationBufferMemory(
    return_messages=True,       # 返回成 message 对象（不是字符串），能喂给 MessagesPlaceholder
    memory_key="chat_history",  # 和 prompt 里的变量名对齐
)
```

### 把 memory 交给 AgentExecutor

```python
agent_executor = AgentExecutor(
    agent=agent_chain,
    tools=tools,
    verbose=True,
    memory=memory,
)
```

### 测试

```python
agent_executor.invoke({"input": "my name is bob"})
# → "Hello, Bob..."

agent_executor.invoke({"input": "whats my name"})
# → "Your name is Bob."    ← 记住了！

agent_executor.invoke({"input": "whats the weather in sf?"})
# → 调 weather 工具，正常给天气
```

**工具调用 + 多轮对话**，两件事同时具备。

---

## 八、做一个能跑的 Web UI（用 Panel）

### 加个有趣的工具

```python
@tool
def create_your_own(query: str) -> str:
    """This function can do whatever you would like once you fill it in """
    print(type(query))
    return query[::-1]   # 简单地把字符串反转

tools = [get_current_temperature, search_wikipedia, create_your_own]
```

### 把上面的组装逻辑包成一个 class

```python
import panel as pn; pn.extension()
import param

class cbfs(param.Parameterized):
    def __init__(self, tools, **params):
        super().__init__(**params)
        self.panels = []
        self.functions = [format_tool_to_openai_function(f) for f in tools]
        self.model = ChatOpenAI(temperature=0).bind(functions=self.functions)
        self.memory = ConversationBufferMemory(return_messages=True, memory_key="chat_history")
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", "You are helpful but sassy assistant"),
            MessagesPlaceholder(variable_name="chat_history"),
            ("user", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        self.chain = RunnablePassthrough.assign(
            agent_scratchpad=lambda x: format_to_openai_functions(x["intermediate_steps"])
        ) | self.prompt | self.model | OpenAIFunctionsAgentOutputParser()
        self.qa = AgentExecutor(agent=self.chain, tools=tools, verbose=False, memory=self.memory)

    def convchain(self, query):
        if not query: return
        inp.value = ''
        result = self.qa.invoke({"input": query})
        self.answer = result['output']
        self.panels.extend([
            pn.Row('User:', pn.pane.Markdown(query, width=450)),
            pn.Row('ChatBot:', pn.pane.Markdown(self.answer, width=450, styles={'background-color': '#F6F6F6'})),
        ])
        return pn.WidgetBox(*self.panels, scroll=True)

    def clr_history(self, count=0):
        self.chat_history = []
        return
```

### 绑定到 UI

```python
cb = cbfs(tools)
inp = pn.widgets.TextInput(placeholder='Enter text here…')
conversation = pn.bind(cb.convchain, inp)

tab1 = pn.Column(
    pn.Row(inp),
    pn.layout.Divider(),
    pn.panel(conversation, loading_indicator=True, height=400),
    pn.layout.Divider(),
)

dashboard = pn.Column(
    pn.Row(pn.pane.Markdown('# QnA_Bot')),
    pn.Tabs(('Conversation', tab1)),
)
dashboard
```

### 跑起来大致体验

- "hi, my name is Bob" → "Hello Bob…"
- "what's my name?" → "Your name is Bob."
- "What's the weather in SF?" → 调 weather 工具，返回温度
- "what tools do you have available?" → 列出三个工具
- "call the create_your_own tool with input I love LangChain" → 返回 `niahCgnaL evol I`

一个**可聊天 + 可调工具 + 有记忆**的 Agent，完整跑起来。

---

## 九、关键要点总结

1. **Agent = 循环调用 chain**：直到 `AgentFinish` 为止；每轮把 `(action, observation)` 累积到 scratchpad。
2. **agent_scratchpad**：借助 `MessagesPlaceholder` + `format_to_openai_functions(...)` 把中间历史还原为消息列表。
3. **RunnablePassthrough.assign**：在链里"临时加字段"的利器，让 chain 只需对外暴露 `input` 和 `intermediate_steps`。
4. **`AgentExecutor`** 是 run_agent 循环的官方实现，额外带错误处理与 verbose 日志。
5. **记忆 = `ConversationBufferMemory` + `MessagesPlaceholder("chat_history")`**；`memory_key` 必须与 prompt 变量名对齐。
6. 这套循环在机制上非常接近 **ChatGPT 的 Code Interpreter / Plugin 调度**。

---

## 十、下一步（课程即将结束）

下一课是课程结语（L8）。在结束前可以试：

- 加更多工具（SQL、搜索、私有 API...）；
- 改 system prompt 把 Agent 调成有人格/专业领域风格；
- 多跳任务（让它连续调多个工具完成一件事）。
