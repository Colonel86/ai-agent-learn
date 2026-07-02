# L2：智能体的组成与本课程的示例智能体

本节先拆解智能体的三大组件，再走一遍课程中要构建的**数据分析智能体（Data Analysis Agent）**的结构。

## 智能体的三大组件

### 1. 路由器（Router）——智能体的"大脑"

路由器是主要的**规划者（Planner）**，负责决定调用哪个**技能（Skill）/工具（Tool）**来回答用户。它的实现可以是：

- 带**函数调用（Function Calling）**的 LLM——本课采用的方式，能力最广，但相对不稳定
- 一个简单的 **NLP 分类器**
- 甚至是**基于规则的代码**

> 经验法则：**路由器越简单，性能越稳定，但能力上限越低**。复杂路由器（如带 function calling 的 LLM）能力广，但需要靠评估去补齐可靠性。

也有一些框架（如 **LangGraph**、**OpenAI Swarm**）不集中实现路由，而是把路由逻辑**分散**到智能体的各个节点里。

### 2. 技能（Skills）

技能是智能体能完成的具体能力块——每一个智能体至少有一个技能（没技能就什么都做不了）。技能内部可以由 LLM 调用、应用代码、API 调用等多个步骤构成。

一个典型例子是 **RAG 技能（Retrieval-Augmented Generation Skill）**：包含 embedding、向量库检索、带上下文的 LLM 调用——整段流程**作为单一技能**对外暴露。也就是说，**一个完整的 LLM 应用，在智能体的视角下可以仅仅是"一个技能"**。

技能执行完通常会**返回给路由器**，由路由器决定继续调用别的技能还是直接回复用户。

### 3. 记忆与状态（Memory & State）

记忆/状态是智能体内所有组件**共享访问**的信息存储，常见用途：

- 已检索的上下文
- 配置变量
- **历史执行步骤的日志**（最常见）

很多 LLM API（比如 OpenAI 的 function calling）就要求你把"过往消息列表"完整传进去，再让模型决定下一步——这就是 messages-as-memory 的方式。本课程的路由器也采用这种模式。

## 本课程的示例智能体：数据分析助手

它能基于一份**门店销售数据库**回答你的问题，包含三个技能：

- **数据查询技能（lookup_sales_data）**：从数据库取数
- **数据分析技能（analyze_sales_data）**：基于数据做趋势分析与计算
- **数据可视化技能（generate_visualization）**：生成 Python 代码并画图

### 整体结构

用户的查询进入路由器（**GPT-4o-mini + function calling**），路由器在三个工具中选择：

```
User -> Router(GPT-4o-mini) -> [lookup_sales_data | analyze_sales_data | generate_visualization] -> Router -> User
```

> 这里我们用"工具（Tool）"是因为这是 GPT-4o-mini 在 function calling 下的术语，**它和我们说的"技能"是同一个概念**。

### 各技能的内部步骤

- **`lookup_sales_data`**：
  1. 准备本地数据库（读入 parquet 文件）
  2. 用 LLM 生成 SQL
  3. 执行 SQL，返回结果给路由器

- **`analyze_sales_data`**：
  1. 一次 LLM 调用即可——把数据和问题丢进去，拿到分析结果

- **`generate_visualization`**：**两次连续 LLM 调用**
  1. 先生成 **chart config**（图表类型、x/y 轴、标题等结构化字段）
  2. 再基于 config 生成 Python 绘图代码

> **为什么要拆成两步？** 直接让 LLM 一步生成绘图代码不够稳定。Python 图表代码有相对固定的"套路"，先用一次调用确定关键变量，再用第二次调用产生代码——把一个难任务拆成两个简单任务，结果会更可靠。

## 小结

本课你了解了智能体的三大组件（路由器、技能、记忆/状态），并预览了课程贯穿的数据分析智能体的结构。下一课，我们用 Python 真正把它写出来。
