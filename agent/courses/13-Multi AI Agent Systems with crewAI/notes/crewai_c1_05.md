# 第 5 课：优秀 Tools 的三大特性 & 活动策划 Crew 实战

> 课程：Multi AI Agent Systems with crewAI
> 讲师：João Moura
> 原文件：
> - `subtitles/crewai_c1_05-1.vtt`（理论：一个优秀 Tool 的三大要素）
> - `subtitles/crewai_c1_05-2.vtt`（L4 Customer Outreach 视频实操讲解）
> - `subtitles/crewai_c1_05-3.vtt`（小结）
> - `code/L5_tasks_event_planning.md`（L5 代码：Automate Event Planning —— Tasks 进阶）

> 📌 本课文档分三部分：
> - **Part A · 理论** — 优秀 Tool 的 3 大要素（Versatility / Fault Tolerance / Caching）
> - **Part B · 视频实操** — L4 Customer Outreach 代码走读 + 异常处理哲学
> - **Part C · 代码实战** — L5 活动策划：**Tasks 进阶**（异步执行 / 结构化输出 / 人工介入）

---

# Part A：一个优秀 Tool 的三大要素

> **Tools 是 Agent 连接外部世界的桥梁**——让 Agent 脱离"自说自话"的气泡，真正对流程、系统、用户、公司产生实际影响。

## 三大要素一览

| # | 要素 | 英文 | 核心价值 |
|---|------|------|----------|
| 1 | 多用途 | **Versatility** | 能处理 LLM 各种不同形态的输入 |
| 2 | 容错性 | **Fault Tolerance** | 失败时优雅降级，不中断整个 Crew |
| 3 | 缓存 | **Caching** | 避免重复请求，省时省钱避限流 |

---

## 1️⃣ Versatility（多用途）

### 1.1 核心问题

Tool 是 **AI 世界（模糊输入）** 与 **外部世界（强类型输入）** 的**翻译层**。

LLM 可能会传来：
- 各种格式的字符串
- 缺失必需参数
- 类型不匹配的数值

### 1.2 crewAI 的做法

crewAI 自动尝试把 Agent 的参数**转换为工具所需的正确类型**，处理 LLM 输出的各种细微差异。

### 1.3 自己写工具时

确保你的 `_run` 函数能**吸收**各种奇怪输入，并**内部转换**成可用的类型。

---

## 2️⃣ Fault Tolerance（容错性）

### 2.1 反面案例

Tool 抛异常 → Crew 执行中断 → **前面跑的几小时全没了**。

### 2.2 crewAI 的默认行为

> 🛡 **Tool 异常不会中断执行。** crewAI 会把错误信息**回传给 Agent**，让它自己决定下一步：
>
> - 重试
> - 换个参数
> - 换个工具
> - 直接跳过

### 2.3 其他框架的对比

| 框架策略 | 影响 |
|---------|------|
| **异常中断执行**（某些框架） | 需要你自己写一层包装处理异常，否则 Agent 会"崩溃"丢失进度 |
| **crewAI：异常降级反馈** | Agent 能从失败中学习，继续推进 |

> 💡 **企业级场景**（大量文档、金融数据）尤其需要容错——数字难读、文本难解析是常态。

---

## 3️⃣ Caching（缓存）

### 3.1 为什么关键？

Tools 多数在调外部 API：
- 避免重复请求
- 避免撞到 Rate Limit
- 减少 API 费用
- 显著加速 Crew 执行

### 3.2 crewAI 的亮点：**Cross-Agent Caching**

> 🔁 **跨 Agent 缓存**——不同 Agent 用**相同工具 + 相同参数**调用时，**第二次直接走缓存**，不发起 API 请求。

---

## Tool 类型概览

- 🌐 **联网搜索** / 🕷 网页抓取
- 🗄 数据库连接
- 📡 API 调用
- 📬 发送通知
- ……

> ✅ **crewAI 额外优势**：完全兼容 **所有 LangChain 工具**。

---

---

# Part B：L4 Customer Outreach 视频实操 + 关键洞察

> 代码已在第 4 课笔记给出，本节聚焦视频中讲解的**设计动机**与**运行时现象**。

## 1. 为什么升级到 GPT-4？

前几节都用 `gpt-3.5-turbo`，从本节开始切到 **`gpt-4`**：
- 要处理的数据量更大
- 需要更大的上下文窗口

## 2. 为什么 `directory='./instructions'` 要指定目录？

和 `ScrapeWebsiteTool(website_url=...)` 一个道理——**限制 Agent 的工具作用域**：

```
./instructions/
    ├── small_business.md
    ├── tech_startup.md
    └── enterprise.md
```

里面存放**如何与不同规模客户打交道的模板**（关键策略点、开场白、介绍要点）。

Agent 能读取这些文件，但**出不了这个目录** → 安全可控。

## 3. 自定义工具 `SentimentAnalysisTool` 的关键点

```python
class SentimentAnalysisTool(BaseTool):
    name: str = "Sentiment Analysis Tool"
    description: str = "Analyzes the sentiment of text ..."

    def _run(self, text: str) -> str:
        # 这里可以调 API、发邮件、查数据库……
        return "positive"
```

| 要求 | 说明 |
|------|------|
| 继承 `BaseTool` | crewAI 的工具基类 |
| **必须有 `name`** | 工具的唯一标识 |
| **必须有 `description`** | **LLM 据此判断何时调用该工具**（极其关键） |
| **必须实现 `_run` 方法** | 真正的业务逻辑 |

## 4. 🔥 运行现场观察：Fault Tolerance 实战

视频中出现了一个真实的错误场景：

### 现象

Agent 想读取一个 URL，但**误用了 `FileReadTool`**（这工具只能读本地文件，不能读 URL）。

### 传统框架的下场

> ❌ 抛异常 → 执行中断 → 前面的 research 成果全部丢失

### crewAI 的处理

> ✅ 异常被捕获 → 错误信息回传给 Agent → Agent **意识到不能用 FileReadTool 读 URL** → 改用 Google 搜索 → **继续推进**

**这是 Part A 中"容错性"在真实场景中的完美体现。**

## 5. Caching 实战观察

第二个 Agent（Lead Sales Rep）做重复搜索时，**直接命中缓存**——
- 省 API 调用
- 避免撞 Rate Limit
- 整体跑得更快

## 6. 结果：多个个性化邮件草稿

最终产出 3 封邮件草稿给 Andrew Ng，主题包括：
- "Enhance DeepLearning.AI's Educational Impact with crewAI's Advanced Analytics"
- 以 AI 工具为核心
- 以合作伙伴关系为核心

> 🔎 邮件中甚至引用了 **The Batch**（DeepLearning.AI 的 newsletter）——**这是 Agent 自己搜到的，我们从未告诉过它**。

## 7. Sales 是多 Agent 系统的黄金场景

销售流程天然适合 Agent：
- 📊 报告生成（Reporting）
- 🔍 信息调研（Research）
- 💬 个性化触达（Engagement）

这些都能被 Agent 自动化。

---

---

# Part C：L5 代码实战 —— 活动策划 Crew

> **本课聚焦：Task 的进阶能力**——异步执行 / 结构化输出 / 人工介入

## 1. 环境准备

```python
import warnings
warnings.filterwarnings('ignore')

from crewai import Agent, Crew, Task

import os
from utils import get_openai_api_key, get_serper_api_key

openai_api_key = get_openai_api_key()
os.environ["OPENAI_MODEL_NAME"] = 'gpt-3.5-turbo'
os.environ["SERPER_API_KEY"] = get_serper_api_key()
```

> 📝 **注**：视频中使用 `gpt-4-turbo`，课程环境免费故改用 `gpt-3.5-turbo`。本地运行可切回 `gpt-4-turbo`。

---

## 2. 工具初始化

```python
from crewai_tools import ScrapeWebsiteTool, SerperDevTool

search_tool = SerperDevTool()
scrape_tool = ScrapeWebsiteTool()
```

---

## 3. 定义三个 Agent

### 3.1 场地协调员（Venue Coordinator）

```python
venue_coordinator = Agent(
    role="Venue Coordinator",
    goal="Identify and book an appropriate venue "
         "based on event requirements",
    tools=[search_tool, scrape_tool],        # 🔧 Agent 级工具
    verbose=True,
    backstory=(
        "With a keen sense of space and "
        "understanding of event logistics, "
        "you excel at finding and securing "
        "the perfect venue that fits the event's theme, "
        "size, and budget constraints."
    )
)
```

### 3.2 物流经理（Logistics Manager）

```python
logistics_manager = Agent(
    role='Logistics Manager',
    goal=(
        "Manage all logistics for the event "
        "including catering and equipmen"
    ),
    tools=[search_tool, scrape_tool],
    verbose=True,
    backstory=(
        "Organized and detail-oriented, "
        "you ensure that every logistical aspect of the event "
        "from catering to equipment setup "
        "is flawlessly executed to create a seamless experience."
    )
)
```

### 3.3 营销传播员（Marketing & Communications Agent）

```python
marketing_communications_agent = Agent(
    role="Marketing and Communications Agent",
    goal="Effectively market the event and "
         "communicate with participants",
    tools=[search_tool, scrape_tool],
    verbose=True,
    backstory=(
        "Creative and communicative, "
        "you craft compelling messages and "
        "engage with potential attendees "
        "to maximize event exposure and participation."
    )
)
```

---

## 4. 🎯 新知识点：结构化输出（Pydantic）

### 4.1 定义输出 Schema

```python
from pydantic import BaseModel

class VenueDetails(BaseModel):
    name: str
    address: str
    capacity: int
    booking_status: str
```

### 4.2 作用

让 Agent 的输出**强制符合结构化格式**，便于下游程序处理。

> ⚠️ 这是 AI 应用中"Fuzzy Output"的一个重要解药——**用 Pydantic 为模糊输出套上强类型外壳**。

---

## 5. 🎯 三个 Task 中的进阶特性

### 5.1 Venue Task：结构化输出 + 人工反馈

```python
venue_task = Task(
    description="Find a venue in {event_city} "
                "that meets criteria for {event_topic}.",
    expected_output="All the details of a specifically chosen"
                    "venue you found to accommodate the event.",
    human_input=True,                       # 🧑 执行中暂停等人工反馈
    output_json=VenueDetails,               # 📦 输出必须符合 VenueDetails
    output_file="venue_details.json",       # 💾 自动写入 JSON 文件
    agent=venue_coordinator
)
```

| 属性 | 作用 |
|------|------|
| `human_input=True` | 任务完成前会**询问人工**是否满意；可给出反馈要求修改 |
| `output_json=VenueDetails` | **强制结构化输出**，符合 Pydantic Schema |
| `output_file="venue_details.json"` | 自动把结果持久化到文件 |

### 5.2 Logistics Task：异步执行 + 人工反馈

```python
logistics_task = Task(
    description="Coordinate catering and "
                 "equipment for an event "
                 "with {expected_participants} participants "
                 "on {tentative_date}.",
    expected_output="Confirmation of all logistics arrangements "
                    "including catering and equipment setup.",
    human_input=True,
    async_execution=True,                  # ⚡ 与后续 Task 并行
    agent=logistics_manager
)
```

| 属性 | 作用 |
|------|------|
| `async_execution=True` | 本任务**与后面的任务并行运行**，不阻塞下游 |

### 5.3 Marketing Task：异步 + 文件输出

```python
marketing_task = Task(
    description="Promote the {event_topic} "
                "aiming to engage at least"
                "{expected_participants} potential attendees.",
    expected_output="Report on marketing activities "
                    "and attendee engagement formatted as markdown.",
    async_execution=True,
    output_file="marketing_report.md",     # 💾 Markdown 文件输出
    agent=marketing_communications_agent
)
```

---

## 6. 组建 Crew

```python
event_management_crew = Crew(
    agents=[venue_coordinator,
            logistics_manager,
            marketing_communications_agent],
    tasks=[venue_task,
           logistics_task,
           marketing_task],
    verbose=True
)
```

### ⚡ 异步任务对顺序的影响

> **由于 `logistics_task` 和 `marketing_task` 都设置了 `async_execution=True`**，它们**在 tasks 列表中的相对顺序不重要**——会并行执行。

---

## 7. 运行 Crew

### 7.1 传入事件详情

```python
event_details = {
    'event_topic': "Tech Innovation Conference",
    'event_description': "A gathering of tech innovators "
                         "and industry leaders "
                         "to explore future technologies.",
    'event_city': "San Francisco",
    'tentative_date': "2024-09-15",
    'expected_participants': 500,
    'budget': 20000,
    'venue_type': "Conference Hall"
}

result = event_management_crew.kickoff(inputs=event_details)
```

### 7.2 🧑 人工介入提示

因为设置了 `human_input=True`，执行中会**暂停等你反馈**。

> ⚠️ 提示出现时，**先用鼠标点击文本框再输入**。

### 7.3 查看结构化输出文件

```python
import json
from pprint import pprint

with open('venue_details.json') as f:
    data = json.load(f)

pprint(data)
```

### 7.4 查看 Markdown 报告

```python
from IPython.display import Markdown
Markdown("marketing_report.md")
```

> ⚠️ **时序坑**：`kickoff` 成功返回后，还需等**约 45 秒** `marketing_report.md` 才会完全生成。若看到只显示文件名，再等等重试。

---

## 📝 Part C 三大核心新能力

| 能力 | API | 价值 |
|------|-----|------|
| **结构化输出** | `output_json=<PydanticModel>` | 给 Fuzzy Output 套上强类型外壳 |
| **文件持久化** | `output_file="path"` | 输出自动写入 JSON / Markdown 等文件 |
| **人工介入** | `human_input=True` | 关键节点暂停等人工审核/反馈 |
| **异步并行** | `async_execution=True` | 独立任务并行执行，大幅提速 |

---

## 🎯 本课综合速查表

### Tools 的三大要素（理论）

| 要素 | 一句话 |
|------|--------|
| **Versatility** | 能吸收 LLM 的各种奇怪输入 |
| **Fault Tolerance** | 失败不能让 Crew 整个崩溃 |
| **Caching** | 特别是 crewAI 的**跨 Agent 缓存** |

### Task 的进阶属性（代码）

```python
Task(
    description="...",
    expected_output="...",
    agent=<agent>,

    # 进阶
    tools=[...],                # Task 级工具绑定（覆盖 Agent 级）
    human_input=True,           # 人工介入
    async_execution=True,       # 并行
    output_json=<PydanticModel>,# 结构化输出
    output_file="path",         # 持久化
)
```

### 🎯 下一课预告

下一节将解锁**更多有趣的用例**——继续深入多 Agent 的威力。
