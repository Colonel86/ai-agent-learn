# LangChain: Chat with Your Data — 第01课：课程介绍（中文字幕）

---

大家好！我很高兴与大家分享这门新课程——如何使用 LangChain 与你的数据对话。本课程由我与 LangChain 联合创始人兼 CEO **Harrison Chase** 合作打造。

---

## 为什么需要"与数据对话"？

大语言模型（LLM），如 ChatGPT，能够回答许多主题的问题。但**孤立的 LLM 只知道它被训练时学到的内容**，而这些内容并不包括：

- 你的**个人数据**（例如公司内部文件，未公开发布在互联网上的专有文档）
- LLM 训练结束后才出现的**新数据或新文章**

因此，如果你或你的客户能够直接与自己的文档对话，并利用其中的信息来获取解答，这将非常有价值。本课程正是为此而生。

---

## 课程结构

### LangChain 简介

LangChain 是一个用于构建 LLM 应用的**开源开发者框架**，由多个模块化组件以及更完整的端到端模板组成。其核心组件包括：

- **提示词（Prompts）**
- **模型（Models）**
- **索引（Indexes）**
- **链（Chains）**
- **智能体（Agents）**

> 如需了解这些组件的详细内容，可参阅第一门课程《LangChain for LLM Application Development》。

---

### 本课程聚焦：与你的数据对话

本课程将深入探讨 LangChain 最受欢迎的用例之一：**如何让 LLM 与你的私有数据进行对话**。

课程内容涵盖以下模块：

| 模块 | 内容 |
|------|------|
| **文档加载（Document Loaders）** | 从多种来源加载数据 |
| **文档分割（Text Splitting）** | 将文档拆分为语义连贯的块（Chunks）；看似简单，实则有很多细节 |
| **语义搜索（Semantic Search）** | 基础检索方法；会介绍常见失败场景及修复方法 |
| **问答（QnA over Documents）** | 利用检索到的文档让 LLM 回答问题 |
| **记忆与对话（Memory & Chatbot）** | 补全"缺失的那块拼图"——记忆，构建完整的聊天机器人体验 |

---

## 课程制作团队

- **LangChain 团队**：Ankush Gola、Lance Martin（负责所有课程材料）
- **DeepLearning.AI 团队**：Geoff Ladwig、Diala Ezzeddine

---

## 前置推荐

如果你在学习本课程时希望复习 LangChain 基础，建议先学习或回顾第一门短期课程：

**《LangChain for LLM Application Development》**

---

下一课：Harrison 将演示如何使用 LangChain 丰富的**文档加载器（Document Loaders）**从各类数据源加载文档。
