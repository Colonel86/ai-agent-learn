# L6 - Agents（智能体）

## 本节主题

LLM 作为**推理引擎**，动态决定调用哪个工具、何时结束。

```mermaid
flowchart LR
    A[用户输入] --> B["LLM 推理（Thought）"]
    B --> C["调用工具（Action）"]
    C --> D["获得观察（Observation）"]
    D --> E[继续推理 or 给出最终答案]
```

## 快速开始

安装依赖（需要 Wikipedia 工具）：

```bash
pip install -r requirements.txt
```

创建 `.env` 文件：

```
OPENAI_API_KEY=sk-...
```

运行：

```bash
python main.py
```

## 文件说明

| 文件 | 说明 |
|------|------|
| `main.py` | Agent 演示：内置工具 + 自定义工具 |
| `requirements.txt` | 依赖包 |

## 核心 API

```python
from langchain.agents import load_tools, initialize_agent, AgentType, tool

# 加载内置工具
tools = load_tools(["llm-math", "wikipedia"], llm=llm)

# 初始化 Agent
agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.CHAT_ZERO_SHOT_REACT_DESCRIPTION,
    handle_parsing_errors=True,
    verbose=True,
)

# 自定义工具
@tool
def my_tool(text: str) -> str:
    """详细描述工具用途和输入格式（LLM 靠此决定何时调用）"""
    return "result"
```

## 关键注意

- `@tool` 的 **docstring** 是 Agent 路由决策的关键，必须准确
- `handle_parsing_errors=True` 处理 LLM 输出格式偶发错误
- Agent 具有**非确定性**，调试时设 `verbose=True`
- Agents 是最前沿也最不稳定的 LangChain 功能
