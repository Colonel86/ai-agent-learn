# LangChain for LLM Application Development — 第07课：智能体（Agents）（中文字幕）

---

人们有时将大语言模型视为知识库，认为它从互联网上记住了大量信息，所以才能回答问题。

但更有用的理解方式是：将 LLM 视为一个**推理引擎（Reasoning Engine）**——你可以给它文本块或其他信息来源，LLM 会利用从互联网上学到的背景知识，结合你提供的新信息，帮助你回答问题、对内容进行推理，甚至决定下一步做什么。

这正是 LangChain 的 **Agents 框架**所要实现的。

---

## 为什么 Agents 令人兴奋？

Agents 是 LangChain 中最令人兴奋、最强大、也最前沿的部分之一。很多相关内容对整个领域来说都是全新的，还在快速发展中。

本课将介绍：
- 什么是 Agent，如何创建和使用
- 如何为 Agent 配备不同工具（如 LangChain 内置的搜索引擎）
- 如何创建**自定义工具**，让 Agent 访问任意数据源、API 或函数

---

## 入门配置

```python
from langchain.agents import load_tools, initialize_agent, AgentType
from langchain.chat_models import ChatOpenAI

# 安装依赖
# pip install duckduckgo-search wikipedia

# 初始化语言模型（作为推理引擎）
llm = ChatOpenAI(temperature=0)

# 加载工具
tools = load_tools(["ddg-search", "wikipedia"], llm=llm)

# 初始化 Agent
agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.CHAT_ZERO_SHOT_REACT_DESCRIPTION,
    handle_parsing_errors=True,
    verbose=True
)
```

**关键说明：**
- `CHAT_ZERO_SHOT_REACT_DESCRIPTION`：优化用于聊天模型
- **ReAct**：一种让语言模型产生更好推理的提示策略
- `handle_parsing_errors=True`：处理输出解析错误（将 LLM 的字符串输出解析为具体的行动和行动输入）

---

## 示例一：搜索近期事件

模型训练截止日期约为 2021 年，无法回答 2022 年世界杯的问题：

```
用户：谁赢得了 2022 年世界杯？
```

Agent 的推理过程：
1. 判断需要使用 DuckDuckGo 搜索
2. 搜索 "2022 World Cup winner"
3. 获取大量信息，但初始判断"2022年世界杯还未举行"（信息理解偏差）
4. 继续搜索更多信息
5. 最终回答："阿根廷赢得了2022年世界杯"

这说明 Agent 仍处于探索阶段——有时需要多轮搜索才能得出正确答案。

---

## 示例二：查询 Wikipedia

```
用户：Tom M. Mitchell 是哪位美国计算机科学家？他写了哪本书？
```

Agent 的推理过程：
1. 识别应使用 Wikipedia 工具
2. 搜索 "Tom M. Mitchell Wikipedia"
3. 再次搜索 "Tom M. Mitchell Machine Learning" 进行确认
4. 最终回答："Tom M. Mitchell 写了教材《Machine Learning》"

---

## 自定义工具：创建 Time 工具

Agents 的强大之处在于可以连接到**你自己的数据源、API 和函数**。

```python
from langchain.agents import tool
from datetime import date

@tool
def time(text: str) -> str:
    """
    返回今天的日期。在需要知道今天是几号时使用此工具。
    输入应始终为空字符串，此工具不需要输入参数。
    """
    return str(date.today())
```

**关键点：**
- `@tool` 装饰器：将任意函数转换为 LangChain 可调用的工具
- **文档字符串（Docstring）非常重要**：Agent 通过它判断何时以及如何调用这个工具
  - 例如："输入应始终为空字符串" → Agent 会传入空字符串
  - 如果工具需要搜索查询或 SQL 语句，就要在文档字符串中明确说明

```python
# 将 time 工具添加到 Agent
agent = initialize_agent(
    tools=tools + [time],
    llm=llm,
    agent=AgentType.CHAT_ZERO_SHOT_REACT_DESCRIPTION
)

agent.run("今天是几号？")
# Agent 识别需要 time 工具
# Action: time
# Action Input: ""（空字符串，符合文档说明）
# Observation: 2023-05-21
# 最终回答："今天是 2023-05-21"
```

---

## 本课小结

**Agents 的核心理念：** 将 LLM 用作推理引擎，而不仅仅是知识库。

| 工具类型 | 说明 |
|----------|------|
| **内置工具** | DuckDuckGo 搜索、Wikipedia、计算器等 |
| **自定义工具** | 用 `@tool` 装饰任意 Python 函数即可接入 |

**自定义工具技巧：**
- 文档字符串要详细，描述输入格式和使用场景
- Agent 完全依赖文档字符串来决定是否以及如何调用工具

这节课展示了如何将语言模型用作推理引擎，让它主动决定采取什么行动、连接哪些函数和数据源。这是 LangChain 中最新且最令人兴奋的部分。
