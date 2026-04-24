# LangChain for LLM Application Development — 第03课：记忆（Memory）（中文字幕）

---

当你与这些模型交互时，它们本身并不记得之前说过的话或之前的对话内容。这在构建聊天机器人等应用时是个问题——你希望能与模型持续对话。

本节将介绍**记忆（Memory）**：如何记住对话的前几轮内容，并将其输入给语言模型，使模型能以连贯的方式与你交互。

LangChain 提供了多种管理记忆的复杂选项。

---

## ConversationBufferMemory（对话缓冲记忆）

```python
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationChain

llm = ChatOpenAI(temperature=0)
memory = ConversationBufferMemory()
conversation = ConversationChain(llm=llm, memory=memory, verbose=False)
```

示例对话：

```
用户：Hi，我叫 Andrew。
AI：你好，Andrew，很高兴认识你！
用户：1+1 等于多少？
AI：1+1 等于 2。
用户：我叫什么名字？
AI：你叫 Andrew，你之前提到过。
```

开启 `verbose=True` 可以看到 LangChain 生成的完整提示词，例如：

> "以下是一个人类与 AI 之间的友好对话。AI 非常健谈……"

**关键机制：** 大语言模型本身是无状态的，每次 API 调用都相互独立。聊天机器人之所以"有记忆"，是因为后台代码每次都将完整的对话历史作为上下文传入 LLM。

`memory.load_memory_variables({})` 可查看当前记忆内容。

---

## ConversationBufferWindowMemory（滑动窗口记忆）

只保留最近 k 轮对话，防止记忆无限增长：

```python
from langchain.memory import ConversationBufferWindowMemory
memory = ConversationBufferWindowMemory(k=1)  # 只记住最近1轮
```

实际使用时，k 通常设置为更大的值。当 k=1 时，如果你问"我叫什么"，它会回答"不知道"，因为只记得上一轮的数学问题，已忘记你介绍名字的那一轮。

---

## ConversationTokenBufferMemory（Token 数量限制记忆）

基于 Token 数量而非对话轮数来限制记忆容量，更直接对应 LLM 的调用成本：

```python
from langchain.memory import ConversationTokenBufferMemory
memory = ConversationTokenBufferMemory(llm=llm, max_token_limit=50)
```

不同 LLM 的 token 计数方式不同，因此需要指定使用哪种 LLM 的计数方式。超出限制后，会截断较早的对话内容，只保留最近的交流。

---

## ConversationSummaryBufferMemory（摘要缓冲记忆）

核心思想：不是限制 token 数量或对话轮数，而是**用 LLM 对已有对话生成摘要**，以摘要作为记忆。

```python
from langchain.memory import ConversationSummaryBufferMemory
memory = ConversationSummaryBufferMemory(llm=llm, max_token_limit=400)
```

**示例场景：** 对话内容包含长日程安排（"早上8点产品团队会议，需要 PPT……中午在意大利餐厅与客户共进午餐，带上电脑展示最新 LLM Demo"）。

- `max_token_limit=400` 时：记忆包含完整对话
- 降低到 `max_token_limit=100` 时：LLM 自动生成摘要，例如：
  > "人类与 AI 在日程开始前进行了闲聊；AI 告知人类上午有会议……午餐与对 AI 感兴趣的客户见面，需展示最新 AI 进展。"

这样后续对话仍能利用前面的上下文，同时将 Token 消耗控制在限额内。

---

## 其他记忆类型（LangChain 还支持）

| 类型 | 特点 |
|------|------|
| **Vector Data Memory** | 将对话内容存为向量嵌入，检索最相关的片段作为记忆 |
| **Entity Memory** | 专门记录特定人物、实体的详细信息 |
| **组合使用** | 可同时使用多种记忆类型（如摘要记忆 + 实体记忆） |

此外，开发者也常将完整对话存入传统数据库（键值存储或 SQL），用于审计或进一步优化系统。

---

## 本课小结

本课介绍了几种记忆类型：
- **Buffer Memory**：按对话轮数或 Token 数限制
- **Summary Buffer Memory**：对超出限额的内容自动摘要
- **Vector / Entity Memory**：更高级的记忆管理方式

这些记忆机制不仅适用于聊天场景，还适合任何需要不断接收新信息（如在线搜索事实）同时控制记忆总量的应用。

下一课将介绍 LangChain 的核心构建块——**链（Chains）**。
