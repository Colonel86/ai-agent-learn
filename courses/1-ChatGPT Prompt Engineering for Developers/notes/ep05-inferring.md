# EP05: Inferring（推理与信息提取）

> 学习日期：2026-04-15
> 所属阶段：Phase 1 · 基石构建
> 课程来源：DeepLearning.AI × OpenAI（Andrew Ng + Isa Fulford）

---

## 传统 NLP vs LLM 对比

| 方式 | 传统 NLP | LLM |
|---|---|---|
| 开发流程 | 收集标注数据 → 训练模型 → 部署 → 推理 | 写 Prompt → 直接获得结果 |
| 每个任务 | 需要单独训练一个模型 | 一个 API 处理所有任务 |
| 开发速度 | 数天到数周 | 数分钟 |

---

## 常见推理任务

### 情感分析（Sentiment Analysis）

```python
prompt = f"""
以下产品评论的情感是什么？
用一个词回答：正面或负面。
评论：{lamp_review}
"""
# 输出：正面
```

### 情绪提取（Emotion Extraction）

```python
prompt = f"""
识别以下评论作者表达的情绪列表，不超过5项。
评论：{lamp_review}
"""
# 输出：满意、感激、轻微失望、印象深刻
```

### 愤怒检测（Anger Detection）

```python
prompt = f"""
评论作者是否在表达愤怒？
用布尔值回答：是/否。
评论：{lamp_review}
"""
# 输出：否
```

### 多字段联合提取

一次 Prompt 提取多个信息：

```python
prompt = f"""
从以下评论中提取：
- 情感（正面/负面）
- 是否愤怒（布尔值）
- 购买的商品
- 制造商

以 JSON 格式输出，字段：sentiment, anger, item, brand
评论：{lamp_review}
"""
# 输出：
# {"sentiment": "positive", "anger": false, "item": "lamp", "brand": "Lumina"}
```

---

## 话题推断（Topic Inference）

给定一篇新闻文章，提取主要话题：

```python
prompt = f"""
确定以下文本中讨论的五个话题，每项不超过两个词，用逗号分隔。
文本：{news_article}
"""
# 输出：政府调查, 工作满意度, NASA, 联邦政府, 员工福利
```

## Zero-Shot 话题分类

给定候选话题列表，判断文章是否涉及每个话题（0/1）：

```python
topic_list = ["NASA", "地方政府", "工程", "员工满意度", "联邦政府"]

prompt = f"""
判断以下每个话题是否在文本中出现，对每个话题给出0或1。
话题列表：{topic_list}
文本：{article}
"""
# 输出：NASA: 1, 地方政府: 0, 工程: 0, 员工满意度: 1, 联邦政府: 1
```

**Zero-Shot Learning**：不需要任何训练数据，仅凭 Prompt 就能完成分类——这是 LLM 相比传统 ML 的革命性优势。

实际应用：新闻监控报警系统，一旦出现 NASA 相关文章自动推送提醒。
