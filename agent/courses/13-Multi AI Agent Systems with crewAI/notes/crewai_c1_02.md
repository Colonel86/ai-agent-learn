# 第 2 课：AI Agents 概览 & 第一个 Crew 实战

> 课程：Multi AI Agent Systems with crewAI
> 讲师：João Moura
> 原文件：
> - `subtitles/crewai_c1_02-1.vtt`（理论 · 上半）
> - `subtitles/crewai_c1_02-2.vtt`（理论 · 下半）
> - `code/L2_research_write_article.md`（代码实战）

---

## 第一部分：理论导读

### 1. 课程路线图

本课程会通过循序渐进的方式，带你构建一系列 **Crew（AI Agent 团队）**：

| 阶段 | Crew 项目 | 难度 |
|------|-----------|------|
| 入门 | **Research & Write Crew**（研究 + 写作） | ⭐ |
| 进阶 | 客户支持 Crew（Customer Support） | ⭐⭐ |
| 进阶 | 客户触达 Crew（Customer Outreach） | ⭐⭐ |
| 进阶 | 活动策划 Agent 系统（Event Planning） | ⭐⭐⭐ |
| 进阶 | 财务分析 Agent 系统（Financial Analysis） | ⭐⭐⭐ |
| 综合 | **简历定制 Crew**（根据岗位 JD 定制简历） | ⭐⭐⭐⭐ |

贯穿始终的核心概念：

- **Role-playing**（角色扮演）
- **Focus & Tool use**（聚焦与工具使用）
- **Cooperation**（协作）
- **Guardrails**（护栏，保证 Agent 稳定工作的关键）
- **Memory**（记忆，让 Agent 变得更强大）
- **协作模式**：顺序（Sequential）、层级（Hierarchical）、**异步（Asynchronous）**

> **Crew 的定义**：一个由多个 AI Agent 组成的团队，每个 Agent 都有明确定义的角色（role）。

---

### 2. 简历定制 Crew 案例（课程最终作品预告）

**场景**：Noah 是一位工程师，想投递一个 **Full-Stack Engineer** 职位。

#### 职位要求
- 前后端兼通
- 能独立编写 API
- 熟悉数据库
- ……

#### Noah 的原始简历
- 突出 **Leadership**（团队管理经验，远程 + 线下）
- 有数据科学 / 机器学习背景
- 提到过部署可扩展 AI 解决方案
- 掌握 Ruby / Python / JavaScript，从业 18 年

⚠️ 问题：他的简历**强调了与岗位关联度较低的"领导力"**，而 JD 需要的"全栈硬技能"被淹没了。

#### 解决方案：4 个 Agent 协作

| Agent | 职责 |
|-------|------|
| **Tech Job Researcher** | 研究目标岗位要求 |
| **Personal Profiler for Engineers** | 构建候选人画像 |
| **Resume Strategist for Engineers** | 针对岗位重写/优化简历 |
| **Engineering Interview Preparer** | 生成面试准备材料 |

配合工具：
- 联网搜索（Search the Internet）
- **RAG over your resume**（对简历做检索增强）

#### 优化后的效果对比

| 原简历 | 优化后 |
|--------|--------|
| 大量强调团队领导经验 | 强化匹配岗位的**硬技能**：JS / Python / Ruby / UI-UX / HTML / CSS |
| 数据科学为主 | 突出全栈开发经验 |

**核心信息：简历内容本身没变，只是"重新取景（framing）"后，更契合 JD。**

---

### 3. 什么是 Agentic Automation（智能体自动化）？

#### 旧式自动化的痛点

传统自动化流程：

```
输入 A → 代码逻辑 → 输出 B
```

随着**边缘情况（edge cases）**越来越多：

```
if X: do C
if Z: do D
elif ... : ...
```

最终会得到一个**充满条件判断、永远无法穷尽所有边界的庞大代码库**。

#### Agentic Automation 的优势

> **你不需要穷举地图（drown the map），只需要告诉 Agent 有哪些选项（show the options）。**

这是一种**全新的写软件的方式**。

---

### 4. 传统应用 vs AI 应用的根本差异

| 维度 | 传统应用 | AI Agentic 应用 |
|------|----------|-----------------|
| **输入** | 强类型（string / int / float 明确已知） | **Fuzzy**（模糊）——只知道是字符串，但不知是 markdown、表格还是数学题 |
| **变换逻辑** | 明确的数学/代数运算 | **Fuzzy**——由 LLM 决定如何转换 |
| **输出** | 确定、可复现 | **Fuzzy**——形式随输入与变换动态变化 |

> **现实世界本身就是一个"Fuzzy"的地方。** 这正是 ChatGPT 广受欢迎的根本原因——它符合人类对世界的实际体验。

✅ 传统代码和 AI 应用**各有所长**，选择哪种取决于你要构建什么。

---

### 5. 实际案例：Lead 生成流程的"Agentic 化升级"

#### 传统流程

```
网站表单 → 抓取潜客数据 → 基于规则的打分
  (是否 10+ 员工？是否在美国？…… → 不同得分)
→ 交给销售团队
```

#### Agentic 化升级版

在流程中加入 **AI Agent Crew**：

1. **Research Agent**：联网搜索、查内部数据库，补全潜客信息
2. **Comparison Agent**：与历史成功客户做对比
3. **Scoring Agent**：基于多维度综合打分
4. **Talking Points Agent**：生成个性化的首次接触话术

**结果**：销售团队拿到的是**极大丰富且可直接行动的情报**，而不是一张冷冰冰的评分表。

---

### 6. 什么是 Agent？从 LLM 说起

#### LLM 本身

- 有不同厂商：OpenAI、Hugging Face、Ollama……
- 核心任务：**预测下一个最可能的 Token**
- 使用方式：**prompt + 人工反馈**的循环迭代

#### ChatGPT 演示：痛点在哪？

```
用户："给 crewAI（一个构建 AI Agent 的平台）写一段营销文案"
ChatGPT：[给出一大段文字]
用户："太长了，精简一下"
ChatGPT：[优化]
```

✅ 通过**多轮交互**，结果会变好。
❌ 但**你成了瓶颈**——必须一直守在屏幕前提供反馈，无法并行做其他事。

#### Agent 的诞生

因为 LLM 在海量文本上训练过，它具备了一种**"认知状态"（cognition）**——

- 能在 A 和 B 之间做选择
- 能把词语合理组织起来

> **Agent 诞生的时刻**：当 LLM 能够**在自己的思考过程中自问自答**，并迭代优化到满意为止。

这样，你只需**把任务抛给它**，它就能自主推理出一个比"第一反应"更好的答案。

#### Agent 的关键能力拼图：Tools（工具）

（其他框架也叫 **Skills / Capabilities**）

工具让 Agent 能与**外部世界**交互：

- 调用 API
- 发布内容
- 获取数据
- ……

**LLM + 自主思考 + 工具使用 = 完整的 Agent**

---

### 7. 什么是多智能体系统（Multi-Agent Systems）？

建立在单 Agent 行为之上——现在你可以有**多个 Agent**，彼此之间可以**任务委派**，最终产出一个统一结果。

#### 相比单 Agent 的核心优势

| 优势 | 说明 |
|------|------|
| **专精**（Specialization） | 每个 Agent 只做一件事，做到极致。例如：Researcher 专注找资料与核查，Writer 专注写出最佳文稿 |
| **多模型混合** | Researcher 用 Llama-3，Writer 用 GPT-4，还能接入自己微调的模型 |
| **可组合性** | 可递归堆叠——Agent 团队里还能有"Agent 团队"（慎用，避免过度嵌套） |

---

### 8. 为什么本课程选择 crewAI？

> **crewAI** 是一个开源、简洁、面向生产的多智能体框架。

核心价值：

1. **简单的结构**：把复杂概念拆成清晰的原语
2. **有主见的模式**：已经替你设计好 Agent 如何串联
3. **丰富内置工具**：开箱即用
4. **可扩展**：支持自定义 Tool 和 Agent
5. **生产平台**：可直接把作品部署上线

> 本课程讲解的所有概念，**都适用于主流多 Agent 框架**——crewAI 只是载体。

---

### 9. 核心构建块速览

接下来的课程会围绕三个基础概念展开：

- **Agent**（智能体）
- **Task**（任务）
- **Crew**（团队）

---

## 第二部分：Lesson 2 实战 —— Research & Write Article

> **目标**：构建一个 3 人 Crew（Planner + Writer + Editor），给任意主题写一篇博客文章。

### 1. 环境准备

```python
# 安装依赖（课堂环境已装好；本地需执行）
!pip install crewai==0.28.8 crewai_tools==0.1.6 langchain_community==0.0.29
```

```python
# 屏蔽警告 + 导入核心类
import warnings
warnings.filterwarnings('ignore')

from crewai import Agent, Task, Crew
```

```python
# 配置 LLM（使用 OpenAI gpt-3.5-turbo）
import os
from utils import get_openai_api_key

openai_api_key = get_openai_api_key()
os.environ["OPENAI_MODEL_NAME"] = 'gpt-3.5-turbo'
```

> 💡 crewAI 也支持 **Hugging Face / Mistral / Cohere / 本地 Ollama (Llama)** 等模型（见文末）。

---

### 2. 定义 Agents

每个 Agent 需提供三要素：

- **role**：角色身份
- **goal**：目标
- **backstory**：背景故事（帮助 LLM 更好地"入戏"）

> 🧠 **关键技巧**：LLM 在**角色扮演（Role-playing）**状态下表现更佳。

#### 🪄 字符串拼接的小贴士

```python
# ✅ 推荐：多个独立字符串自动拼接，无多余空白
varname = ("line 1 of text"
           "line 2 of text")

# ❌ 不推荐：三引号会保留缩进空白和换行符
varname = """line 1 of text
             line 2 of text
          """
```

#### Agent 1：Content Planner（内容规划师）

```python
planner = Agent(
    role="Content Planner",
    goal="Plan engaging and factually accurate content on {topic}",
    backstory="You're working on planning a blog article "
              "about the topic: {topic}."
              "You collect information that helps the "
              "audience learn something "
              "and make informed decisions. "
              "Your work is the basis for "
              "the Content Writer to write an article on this topic.",
    allow_delegation=False,
    verbose=True
)
```

#### Agent 2：Content Writer（内容写手）

```python
writer = Agent(
    role="Content Writer",
    goal="Write insightful and factually accurate "
         "opinion piece about the topic: {topic}",
    backstory="You're working on a writing "
              "a new opinion piece about the topic: {topic}. "
              "You base your writing on the work of "
              "the Content Planner, who provides an outline "
              "and relevant context about the topic. "
              "You follow the main objectives and "
              "direction of the outline, "
              "as provide by the Content Planner. "
              "You also provide objective and impartial insights "
              "and back them up with information "
              "provide by the Content Planner. "
              "You acknowledge in your opinion piece "
              "when your statements are opinions "
              "as opposed to objective statements.",
    allow_delegation=False,
    verbose=True
)
```

#### Agent 3：Editor（编辑）

```python
editor = Agent(
    role="Editor",
    goal="Edit a given blog post to align with "
         "the writing style of the organization. ",
    backstory="You are an editor who receives a blog post "
              "from the Content Writer. "
              "Your goal is to review the blog post "
              "to ensure that it follows journalistic best practices,"
              "provides balanced viewpoints "
              "when providing opinions or assertions, "
              "and also avoids major controversial topics "
              "or opinions when possible.",
    allow_delegation=False,
    verbose=True
)
```

#### 📌 关键参数说明

| 参数 | 作用 |
|------|------|
| `allow_delegation=False` | 禁止该 Agent 把任务再委派给别人 |
| `verbose=True` | 打印执行过程日志 |
| `{topic}` | 占位符，运行时通过 `inputs` 注入 |

---

### 3. 定义 Tasks

每个 Task 需提供：

- **description**：任务步骤
- **expected_output**：期望产出
- **agent**：执行者

#### Task 1：Plan

```python
plan = Task(
    description=(
        "1. Prioritize the latest trends, key players, "
            "and noteworthy news on {topic}.\n"
        "2. Identify the target audience, considering "
            "their interests and pain points.\n"
        "3. Develop a detailed content outline including "
            "an introduction, key points, and a call to action.\n"
        "4. Include SEO keywords and relevant data or sources."
    ),
    expected_output="A comprehensive content plan document "
        "with an outline, audience analysis, "
        "SEO keywords, and resources.",
    agent=planner,
)
```

#### Task 2：Write

```python
write = Task(
    description=(
        "1. Use the content plan to craft a compelling "
            "blog post on {topic}.\n"
        "2. Incorporate SEO keywords naturally.\n"
        "3. Sections/Subtitles are properly named "
            "in an engaging manner.\n"
        "4. Ensure the post is structured with an "
            "engaging introduction, insightful body, "
            "and a summarizing conclusion.\n"
        "5. Proofread for grammatical errors and "
            "alignment with the brand's voice.\n"
    ),
    expected_output="A well-written blog post "
        "in markdown format, ready for publication, "
        "each section should have 2 or 3 paragraphs.",
    agent=writer,
)
```

#### Task 3：Edit

```python
edit = Task(
    description=("Proofread the given blog post for "
                 "grammatical errors and "
                 "alignment with the brand's voice."),
    expected_output="A well-written blog post in markdown format, "
                    "ready for publication, "
                    "each section should have 2 or 3 paragraphs.",
    agent=editor
)
```

---

### 4. 组建 Crew

```python
crew = Crew(
    agents=[planner, writer, editor],
    tasks=[plan, write, edit],
    verbose=2
)
```

⚠️ **重要**：本例是**顺序执行（Sequential）**——任务彼此依赖，所以列表中的**顺序就是执行顺序**。

---

### 5. 启动 Crew

```python
result = crew.kickoff(inputs={"topic": "Artificial Intelligence"})
```

在 Notebook 中以 Markdown 渲染结果：

```python
from IPython.display import Markdown
Markdown(result)
```

#### 🧪 自己试试

```python
topic = "YOUR TOPIC HERE"
result = crew.kickoff(inputs={"topic": topic})
Markdown(result)
```

> 💡 同样输入每次结果可能不同——这就是"Fuzzy Output"的体现。

---

### 6. 拓展：切换其他 LLM

#### Hugging Face

```python
from langchain_community.llms import HuggingFaceHub

llm = HuggingFaceHub(
    repo_id="HuggingFaceH4/zephyr-7b-beta",
    huggingfacehub_api_token="<HF_TOKEN_HERE>",
    task="text-generation",
)
# 然后传入 agent
```

#### Mistral

```bash
OPENAI_API_KEY=your-mistral-api-key
OPENAI_API_BASE=https://api.mistral.ai/v1
OPENAI_MODEL_NAME="mistral-small"
```

#### Cohere

```python
from langchain_community.chat_models import ChatCohere
os.environ["COHERE_API_KEY"] = "your-cohere-api-key"
llm = ChatCohere()
```

#### 本地 Ollama（Llama 等）

参阅官方文档：[crewAI - Connecting to any LLM](https://docs.crewai.com/how-to/LLM-Connections/)

---

## 📝 本课核心要点总结

### 概念层面

| 关键词 | 一句话解释 |
|--------|-----------|
| **Fuzzy Input/Output** | AI 应用的输入、变换、输出都不确定——这正是它的威力所在 |
| **Agentic Automation** | 不用枚举所有分支，而是告诉 Agent"有哪些选项" |
| **Agent = LLM + 自主思考 + 工具** | 三位一体 |
| **Multi-Agent** | 专精分工 + 多模型协作 + 可递归组合 |

### 实战层面

| 核心 API | 三要素 |
|----------|--------|
| `Agent` | role / goal / backstory |
| `Task` | description / expected_output / agent |
| `Crew` | agents / tasks / (执行顺序由列表顺序决定) |

### 最佳实践

- ✅ **Role-playing** 显著提升 LLM 输出质量
- ✅ 使用**多字符串拼接**而非三引号，避免多余空白
- ✅ `verbose=True` 在学习阶段非常有价值
- ✅ 占位符 `{topic}` 用 `inputs` 动态注入，提升复用性

### 🎯 下一课预告

下一课正式深入 **Agents / Tasks / Crews** 的三大构建块，并构建**你的第一个真正的多智能体系统**。
