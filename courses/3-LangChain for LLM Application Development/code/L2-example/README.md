# L2 - Memory（对话记忆）

## 本节主题

LLM 本身无状态，Memory 模块负责管理对话历史上下文。

| Memory 类型 | 限制策略 | 适用场景 |
|------------|---------|---------|
| `ConversationBufferMemory` | 无限制 | 短对话、调试 |
| `ConversationBufferWindowMemory` | 保留最近 k 轮 | 固定窗口大小 |
| `ConversationTokenBufferMemory` | 按 token 截断 | 精确控制成本 |
| `ConversationSummaryBufferMemory` | 旧对话压缩成摘要 | 长对话应用 ⭐ |

## 快速开始

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

## 核心 API

```python
from langchain.memory import ConversationSummaryBufferMemory
from langchain.chains import ConversationChain

memory = ConversationSummaryBufferMemory(llm=llm, max_token_limit=100)
conversation = ConversationChain(llm=llm, memory=memory, verbose=True)
response = conversation.predict(input="What would be a good demo?")
```

## 关键概念

- LLM 是**无状态**的，每次 API 调用独立
- Memory 把历史作为上下文拼入 prompt，模拟"记忆"
- `verbose=True` 可查看完整 prompt，了解 memory 如何注入
