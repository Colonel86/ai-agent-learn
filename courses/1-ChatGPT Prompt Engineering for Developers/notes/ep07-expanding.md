# EP07: Expanding（扩写）

> 学习日期：2026-04-15
> 所属阶段：Phase 1 · 基石构建
> 课程来源：DeepLearning.AI × OpenAI（Andrew Ng + Isa Fulford）

---

## 什么是 Expanding

将**简短文本**（如说明、要点列表）扩写成**更长的内容**（如完整邮件、文章）。

**合理使用场景：** 头脑风暴伙伴、起草初稿
**需注意：** 大量生成垃圾邮件/虚假内容等是不负责任的用法

---

## 实战：根据评论情感自动生成客服回复

```python
sentiment = "negative"
review = "搅拌机盖子飞了，把厨房弄得一团糟..."

prompt = f"""
你是一个客服 AI 助手。
你的任务是向客户发送邮件回复。
根据下面用三重反引号括起来的客户邮件，生成一封回复。
如果情感是正面或中性，感谢他们的评论。
如果情感是负面，道歉并建议他们联系客服。
确保使用评论中的具体细节，语气简洁专业，
署名为"AI客服助理"。
客户评论：```{review}```
评论情感：{sentiment}
"""
```

**重要原则：** 当 AI 生成的文本展示给用户时，必须让用户知道这是 AI 生成的内容（透明度原则）。

---

## Temperature 参数详解

`temperature` 控制模型输出的**随机性/创造性**。

**原理示例：** 对于 "my favorite food is ___"：
- 模型预测的最可能下一个词是 "pizza"，其次是 "sushi"，再次是 "tacos"（约 5% 概率）

| Temperature | 行为 | 适用场景 |
|---|---|---|
| `0` | 永远选概率最高的词（pizza）| 需要**可预测、一致**的输出（如分类、提取、摘要）|
| `0.3~0.7` | 偶尔选次优词 | 平衡创意与稳定 |
| `0.7~1.0` | 更多随机探索（可能选 tacos）| 需要**多样化创意**的输出（如写作、头脑风暴）|

```python
# 可预测场景：temperature=0（默认）
response = get_completion(prompt, temperature=0)

# 创意场景：temperature=0.7
response = get_completion(prompt, temperature=0.7)
# 每次运行会得到不同的输出
```

**核心建议：**
- 构建可靠系统（RAG、问答、分类）→ `temperature=0`
- 创意写作、内容生成 → `temperature=0.7` 或更高
