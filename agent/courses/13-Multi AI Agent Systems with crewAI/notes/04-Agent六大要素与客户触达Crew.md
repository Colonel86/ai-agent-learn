# 第 4 课：Agent 的六大要素 & 客户触达 Crew 实战

> 课程：Multi AI Agent Systems with crewAI
> 讲师：João Moura
> 原文件：
> - `subtitles/crewai_c1_04-1.vtt`（理论：让 Agent 变优秀的 6 大要素）
> - `subtitles/crewai_c1_04-2.vtt`（L3 Customer Support 视频实操讲解）
> - `subtitles/crewai_c1_04-3.vtt`（管理者思维框架 + 本课总结）
> - `code/L4_tools_customer_outreach.md`（L4 代码：Customer Outreach Campaign with Tools）

> 📌 本课文档分三部分：
> - **Part A · 理论** — 让 Agent 表现优异的 6 大要素
> - **Part B · 视频实操** — L3 Customer Support 代码逐步讲解 + 管理者思维框架
> - **Part C · 代码实战** — L4 Customer Outreach：工具的深度使用

---

# Part A：Agent 的 6 大核心要素

> **一个伟大的 Agent 之所以伟大，离不开 6 大要素——这些同时也是一个优秀员工的特征。**

| # | 要素 | 英文 |
|---|------|------|
| 1 | 角色扮演 | Role Playing |
| 2 | 聚焦 | Focus |
| 3 | 工具 | Tools |
| 4 | 协作 | Cooperation |
| 5 | 护栏 | Guardrails |
| 6 | 记忆 | Memory |

---

## 1️⃣ Role Playing（角色扮演）

### 1.1 对比实验

**同样的问题："给我分析特斯拉的股票"**

| Prompt | 回答特点 |
|--------|----------|
| 直接问 ChatGPT | 泛泛而谈——"有很多因素……"、"财务表现……" |
| 加上身份"**你是一名 FINRA 认证的金融分析师**" | 直接切入专业角度——Nasdaq、特斯拉股价、EV 制造业竞争 |

### 1.2 关键技巧：**选对"关键词"**

不是随便写"金融分析师"就行——`FINRA` 这个**专业术语**是关键：

> 它引导 LLM 进入**被监管合规培训过的分析师**的思维框架。

✅ **结论**：在 role / goal / backstory 中，**精心挑选关键词**，能显著提升输出质量。

---

## 2️⃣ Focus（聚焦）

### 2.1 反直觉：越长的上下文 ≠ 越好

虽然现代 LLM 上下文窗口越来越大，但：

> **把太多东西塞进一个 Agent（工具、信息、上下文），会让它**：
> - 丢失重要信息
> - 更容易幻觉
> - 无法判断该用哪个工具

### 2.2 正确做法

不要指望**一个 Agent 搞定所有事**，应该用**多个聚焦的 Agent 协同工作**。

业界实践：用多 Agent 的方案在**各个垂直领域**都比单 Agent 表现更好。

---

## 3️⃣ Tools（工具）

### 3.1 工具越多越乱

- 工具太多 → Agent 不知道该选哪个
- 该用的工具反而没用
- **用小模型时问题更严重**——它分不清哪个是工具、哪个是上下文、自己该干什么

### 3.2 黄金法则

> **像招聘员工一样给 Agent 挑工具：**
> 只给"完成本职工作所必需的关键工具"。

---

## 4️⃣ Cooperation（协作）

### 4.1 为什么 ChatGPT 多轮对话效果更好？

因为你在和它**来回交互、提供反馈**。

### 4.2 让 Agent 彼此"聊起来"

当多个 Agent 能**互相反馈、互相委派**，就能模拟这种"多轮反馈"机制，产出显著提升。

### 4.3 通用原则

不管用 crewAI 还是其他框架，都要**确保你的 Agent 具备协作能力**。

---

## 5️⃣ Guardrails（护栏）

### 5.1 为什么需要护栏？

AI 应用是 **Fuzzy（模糊）** 的——输入、转换、输出都不强类型。**但这不等于可以接受**：

- 幻觉（hallucination）
- 循环调用同一工具
- 响应太慢
- 随机死循环

### 5.2 crewAI 的内置护栏

早期 crewAI 确实有过"Agent 反复调用同一工具"的问题（尤其开源模型上）。经过多次迭代，crewAI 已在框架层面实现了多重护栏：

- 防止 Agent 偏航
- 在关键点"轻推"Agent 回到正轨
- 确保结果稳定一致

> 💡 在构建**自定义工具**时也要把护栏考虑进去。

---

## 6️⃣ Memory（记忆）

> **Memory 带来的提升，可能比其他 5 个要素加起来还大。**

### 6.1 crewAI 开箱即用的三种记忆

| 类型 | 生命周期 | 作用 |
|------|----------|------|
| **Short-term Memory**（短期记忆） | 仅在当前 Crew 执行过程中 | 不同 Agent 之间共享上下文 |
| **Long-term Memory**（长期记忆） | **跨执行持久化**（存本地数据库） | 从过往执行中学习、自我批评、下次做得更好 |
| **Entity Memory**（实体记忆） | 本次执行中 | 记录正在讨论的主题/实体（公司、人名等） |

### 6.2 长期记忆的"自我改进"机制

每完成一个任务，Agent 会**自我批评**：
- 哪里该做得更好？
- 遗漏了什么？
→ 把这些反思存下来 → 下次再跑时**调用这份记忆**，产出更可靠的结果。

### 6.3 没有记忆 vs 有记忆

| 无记忆 | 有记忆 |
|--------|--------|
| 每次跑都可能不同，不稳定 | 不仅更稳定，而且**越跑越好** |

---

---

# Part B：L3 视频实操 + 管理者思维框架

## 1. Customer Support Crew 代码走读

> 完整代码已在**第 3 课笔记**中列出，这里补充视频中的**设计动机**。

### 1.1 为什么 role 写 "Senior Support Representative"？

用 **"Senior"（资深）** 这个关键词 → 暗示我们期望**更精致、更到位的回答**（印证 Part A 中"关键词选择"的重要性）。

### 1.2 为什么 goal 写 "friendly and helpful"？

这种"语气"会**渗透到流程的每一步**，不是单纯的礼貌用语，而是 Agent 整体人格的塑造。

### 1.3 关键设计：**非对称的 `allow_delegation`**

| Agent | `allow_delegation` | 效果 |
|-------|---------------------|------|
| Support Agent | `False` | 必须自己回答，不能甩锅 |
| QA Agent | `True`（默认） | **可以反向委派回 Support** |

> ⚠️ **QA Agent 的 delegation 权限非常关键**：发现问题时，它可以把改进任务**交还给更合适的 Agent**，而不必自己修复。

### 1.4 什么时候 Agent 会真的委派？

这是 AI 工程 vs 传统工程的根本差异——**由 LLM 在运行时自行判断**：

- 简单问题 → 自己答
- 复杂问题 → 委派、追问
- **这是 AI 应用的"魔法"**——运行时动态决策

> 你**允许**它委派 ≠ **强制**它委派。

### 1.5 为什么推荐加一个 QA Agent？

> **crewAI 用户的普遍经验**：几乎所有多 Agent 系统加上一个"最终审核 Agent"后，质量都显著提升。

无论是写博客、客户触达、还是技术支持——**最后一关 QA** 都是值得的。

---

## 2. Tools、Guardrails、Memory 在代码中的体现

### 2.1 crewAI 内置工具

```python
from crewai_tools import SerperDevTool, ScrapeWebsiteTool, WebsiteSearchTool
```

| 工具 | 作用 |
|------|------|
| **SerperDevTool** | 通过 Serper 做 Google 搜索 |
| **ScrapeWebsiteTool** | 抓取指定 URL 的页面内容 |
| **WebsiteSearchTool** | 对网站做 **RAG（语义检索）** |

### 2.2 工具的"精准化"配置

通用抓取工具 vs **限定 URL** 的抓取工具：

```python
# 可抓任意 URL
scrape_tool = ScrapeWebsiteTool()

# 只能抓指定 URL（更安全可控）
docs_scrape_tool = ScrapeWebsiteTool(
    website_url="https://docs.crewai.com/how-to/Creating-a-Crew-and-kick-it-off/"
)
```

### 2.3 工具绑定：Agent 级 vs Task 级

| 级别 | 语义 |
|------|------|
| **Agent 级** | Agent 在**任何任务**中都可用 |
| **Task 级** | Agent 仅在**该特定任务**中可用 |

> 🔑 **Task 级工具会覆盖 Agent 级工具**：Agent 即使有 10 个工具，若 Task 只指定 3 个，执行该任务时**只能用这 3 个**。

### 2.4 Memory 一键开启

```python
crew = Crew(
    agents=[...],
    tasks=[...],
    memory=True        # 一行搞定：短期 + 长期 + 实体记忆全开
)
```

---

## 3. 🧠 管理者思维框架（Think Like a Manager）

### 3.1 核心心智模型

> **打造优秀多 Agent 系统 ≈ 做一名优秀的管理者**

优秀管理者思考的两件事：

1. **Goal**（目标是什么？）
2. **Process**（流程怎么走？）

### 3.2 推演四步法

面对新的 Crew 设计时，按顺序问自己：

```
1. 我要达成什么目标？
2. 为达成它，流程应该怎样？
3. 如果要雇人来做，我会雇什么样的人？
4. 这些"人"对应的 role / goal / backstory 该怎么写？
```

### 3.3 关键词反例 vs 正例

| ❌ 粗糙 | ✅ 精细 |
|---------|---------|
| Researcher | **HR Research Specialist**（HR 领域研究专员） |
| Writer | **Senior Copywriter**（资深文案） |
| Financial Analyst | **FINRA-Approved Analyst**（FINRA 认证分析师） |

> **社区观察**：产出最好结果的用户，都是"像招聘一样"思考 Agent 设计的人。

---

## 4. L3 小结（一句话回顾）

1. ✅ Agent 做得更好靠 **6 要素**：Role Playing / Focus / Tools / Cooperation / Guardrails / Memory
2. ✅ Agent 能通过 **Memory 自我改进**
3. ✅ crewAI 会**防止 Agent 掉进"兔子洞"**（循环、卡死）
4. ✅ crewAI 总是**努力让 Agent 给出答案**
5. ✅ **细粒度的任务 + 聚焦的 Agent** 胜过"大任务 + 全能 Agent"

---

---

# Part C：L4 代码实战 —— Customer Outreach Campaign

## 1. 本课聚焦的三大工具特性

> **Tools 是解锁有趣用例的钥匙。**

| 特性 | 英文 | 含义 |
|------|------|------|
| **多用途** | Versatility | 一个工具可以适配多种场景 |
| **容错性** | Fault Tolerance | 工具调用失败能自动恢复 |
| **缓存** | Caching | 重复调用走缓存，提速 + 省成本 |

---

## 2. 环境准备

```python
!pip install crewai==0.28.8 crewai_tools==0.1.6 langchain_community==0.0.29
```

```python
import warnings
warnings.filterwarnings('ignore')

from crewai import Agent, Task, Crew
```

### LLM 与 API 配置

```python
import os
from utils import get_openai_api_key, pretty_print_result
from utils import get_serper_api_key

openai_api_key = get_openai_api_key()
os.environ["OPENAI_MODEL_NAME"] = 'gpt-3.5-turbo'
os.environ["SERPER_API_KEY"] = get_serper_api_key()    # Serper API Key
```

> 📝 **注**：视频中用的是 `gpt-4-turbo`，课程环境免费所以改 `gpt-3.5-turbo`。本地运行可以切回 `gpt-4-turbo`。

---

## 3. 定义两个销售 Agent

### 3.1 Sales Representative（销售代表）—— 找线索

```python
sales_rep_agent = Agent(
    role="Sales Representative",
    goal="Identify high-value leads that match "
         "our ideal customer profile",
    backstory=(
        "As a part of the dynamic sales team at CrewAI, "
        "your mission is to scour "
        "the digital landscape for potential leads. "
        "Armed with cutting-edge tools "
        "and a strategic mindset, you analyze data, "
        "trends, and interactions to "
        "unearth opportunities that others might overlook. "
        "Your work is crucial in paving the way "
        "for meaningful engagements and driving the company's growth."
    ),
    allow_delegation=False,
    verbose=True
)
```

### 3.2 Lead Sales Representative（首席销售代表）—— 做触达

```python
lead_sales_rep_agent = Agent(
    role="Lead Sales Representative",
    goal="Nurture leads with personalized, compelling communications",
    backstory=(
        "Within the vibrant ecosystem of CrewAI's sales department, "
        "you stand out as the bridge between potential clients "
        "and the solutions they need."
        "By creating engaging, personalized messages, "
        "you not only inform leads about our offerings "
        "but also make them feel seen and heard."
        "Your role is pivotal in converting interest "
        "into action, guiding leads through the journey "
        "from curiosity to commitment."
    ),
    allow_delegation=False,
    verbose=True
)
```

---

## 4. 创建工具

### 4.1 内置工具

```python
from crewai_tools import DirectoryReadTool, \
                         FileReadTool, \
                         SerperDevTool

directory_read_tool = DirectoryReadTool(directory='./instructions')
file_read_tool = FileReadTool()
search_tool = SerperDevTool()
```

| 工具 | 作用 |
|------|------|
| **DirectoryReadTool** | 读取指定目录下的文件列表 |
| **FileReadTool** | 读取单个文件内容 |
| **SerperDevTool** | 联网搜索（Google） |

### 4.2 自定义工具：继承 BaseTool

```python
from crewai_tools import BaseTool
```

> 📌 **每个 Tool 必须有**：
> - `name`：工具名
> - `description`：工具说明（LLM 看这个判断何时调用）

#### 示例：情感分析工具（演示用，恒返回 positive）

```python
class SentimentAnalysisTool(BaseTool):
    name: str = "Sentiment Analysis Tool"
    description: str = ("Analyzes the sentiment of text "
                        "to ensure positive and engaging communication.")

    def _run(self, text: str) -> str:
        # 本地运行时把真实逻辑写在这里
        return "positive"

sentiment_analysis_tool = SentimentAnalysisTool()
```

> 💡 **关键点**：
> - 自定义工具只需继承 `BaseTool` + 实现 `_run` 方法
> - 本例为简化起见恒返回 `"positive"`；真实场景可接入情感分析 API

---

## 5. 创建 Tasks

### 5.1 Task 1：潜客画像（使用 3 个内置工具）

```python
lead_profiling_task = Task(
    description=(
        "Conduct an in-depth analysis of {lead_name}, "
        "a company in the {industry} sector "
        "that recently showed interest in our solutions. "
        "Utilize all available data sources "
        "to compile a detailed profile, "
        "focusing on key decision-makers, recent business "
        "developments, and potential needs "
        "that align with our offerings. "
        "This task is crucial for tailoring "
        "our engagement strategy effectively.\n"
        "Don't make assumptions and "
        "only use information you absolutely sure about."
    ),
    expected_output=(
        "A comprehensive report on {lead_name}, "
        "including company background, "
        "key personnel, recent milestones, and identified needs. "
        "Highlight potential areas where "
        "our solutions can provide value, "
        "and suggest personalized engagement strategies."
    ),
    tools=[directory_read_tool, file_read_tool, search_tool],
    agent=sales_rep_agent,
)
```

> 🚧 **Guardrails 伏笔**：
> `"Don't make assumptions and only use information you absolutely sure about."`
> 这类 prompt 明确禁止幻觉——属于**软护栏**。

### 5.2 Task 2：个性化触达（使用自定义工具 + 搜索工具）

```python
personalized_outreach_task = Task(
    description=(
        "Using the insights gathered from "
        "the lead profiling report on {lead_name}, "
        "craft a personalized outreach campaign "
        "aimed at {key_decision_maker}, "
        "the {position} of {lead_name}. "
        "The campaign should address their recent {milestone} "
        "and how our solutions can support their goals. "
        "Your communication must resonate "
        "with {lead_name}'s company culture and values, "
        "demonstrating a deep understanding of "
        "their business and needs.\n"
        "Don't make assumptions and only "
        "use information you absolutely sure about."
    ),
    expected_output=(
        "A series of personalized email drafts "
        "tailored to {lead_name}, "
        "specifically targeting {key_decision_maker}."
        "Each draft should include "
        "a compelling narrative that connects our solutions "
        "with their recent achievements and future goals. "
        "Ensure the tone is engaging, professional, "
        "and aligned with {lead_name}'s corporate identity."
    ),
    tools=[sentiment_analysis_tool, search_tool],
    agent=lead_sales_rep_agent,
)
```

---

## 6. 组建 Crew

```python
crew = Crew(
    agents=[sales_rep_agent,
            lead_sales_rep_agent],
    tasks=[lead_profiling_task,
           personalized_outreach_task],
    verbose=2,
    memory=True
)
```

---

## 7. 运行 Crew

```python
inputs = {
    "lead_name": "DeepLearningAI",
    "industry": "Online Learning Platform",
    "key_decision_maker": "Andrew Ng",
    "position": "CEO",
    "milestone": "product launch"
}

result = crew.kickoff(inputs=inputs)
```

渲染结果：

```python
from IPython.display import Markdown
Markdown(result)
```

> 💡 运行时 `{lead_name}` `{industry}` `{key_decision_maker}` `{position}` `{milestone}` 会被统一注入到 Task 描述、期望输出等所有出现占位符的位置。

---

## 📝 本课综合要点

### 理论侧（6 要素 Cheat Sheet）

| 要素 | 核心建议 |
|------|----------|
| Role Playing | **精选关键词**（FINRA、Senior、Specialist） |
| Focus | 多个聚焦 Agent > 一个全能 Agent |
| Tools | 给精选工具，不是越多越好 |
| Cooperation | 允许委派 / 互相反馈 |
| Guardrails | 框架层 + Prompt 层 + 自定义工具层多重防护 |
| Memory | `memory=True` 一键开启 3 种记忆 |

### 代码侧（新学的 API）

| API | 用途 |
|-----|------|
| `DirectoryReadTool` / `FileReadTool` | 读目录 / 读文件 |
| `SerperDevTool` | Google 搜索（需 SERPER_API_KEY） |
| `ScrapeWebsiteTool(website_url=...)` | 限定 URL 的抓取（安全） |
| `BaseTool` + `_run()` | 自定义工具 |
| Task 的 `tools=[...]` | Task 级工具绑定 |

### 心智模型

> **Think like a manager**：目标 → 流程 → 雇谁 → 角色定义

### 🎯 下一课预告

> 🚀 **Tools 深入**：将是解锁最多有趣用例的关键。下一节继续讲工具的高级玩法。

---

## 面试速答总结

**一句话**：让一个 Agent 变优秀有**六大要素**——**Role Playing / Focus / Tools / Cooperation / Guardrails / Memory**,本质就是"一个优秀员工的特征";设计时用**管理者思维**(目标→流程→雇谁→怎么写 role/goal/backstory),而其中 **Memory 带来的提升可能比其余五个加起来还大**,crewAI 用 `memory=True` 一键开启短期/长期/实体三种记忆。

### 面试回答骨架（问"怎么让 agent 表现更好 / 多 agent 系统怎么设计角色"）

> 1. **给六要素框架(要会背)**：**Role Playing**(精选关键词,`FINRA 认证分析师` > `金融分析师`,专业术语把 LLM 带进对应思维框架)、**Focus**(反直觉——上下文越长越差,别指望一个全能 Agent,用多个聚焦 Agent)、**Tools**(像招人一样只给必需工具,工具太多小模型尤其分不清)、**Cooperation**(让 Agent 互相反馈/委派,模拟 ChatGPT 多轮的增益)、**Guardrails**(防幻觉/防循环调用/防死循环,框架层+prompt 层+工具层多重)、**Memory**(提升最大)。
> 2. **强调设计心法 = 像管理者思考**：面对新 Crew 就问四步——我要什么目标?流程怎么走?要雇什么样的人?这些人的 role/goal/backstory 怎么写?产出最好结果的用户都是"像招聘一样"设计 Agent 的。
> 3. **展开 Memory(最高频追问)**：crewAI 三种记忆——**短期**(本次执行内跨 Agent 共享上下文)、**长期**(跨执行持久化到本地库,每完成任务**自我批评**存反思,下次调用→越跑越好)、**实体**(记录本次讨论的公司/人名等实体)。没记忆每次不稳定,有记忆不仅稳还自我改进。
> 4. **落地细节**：`allow_delegation` 的**非对称设计**很关键——Support Agent 设 False(必须自己答不能甩锅),QA Agent 设 True(发现问题可反向委派回 Support);且**几乎所有多 Agent 系统加一个最终 QA Agent,质量都显著提升**。

### 关键判断（加分点）

- **Focus 与"大上下文窗口"是两回事**:窗口大 ≠ 该把所有东西塞给一个 Agent——塞太多会丢信息、更易幻觉、选错工具。这是"细粒度任务 + 聚焦 Agent > 大任务 + 全能 Agent"的依据。
- **委派是"允许"不是"强制"**:`allow_delegation=True` 只是给权限,真正是否委派由 **LLM 运行时自行判断**(简单问题自己答、复杂问题才委派)——这正是 AI 工程区别于传统工程的"魔法"。
- **护栏要分层**:框架内置护栏(防兔子洞) + prompt 软护栏(`Don't make assumptions`) + 自定义工具里的护栏,三层配合;Fuzzy 是特性但幻觉/死循环不可接受。
- **加一个 QA/审核 Agent 是低成本高回报的通用模式**,可迁移到任何多 agent 系统。

### 为什么这是高分答法

- 不零散背要素,而是把**六要素 + 管理者四步法**串成设计方法论,并突出 Memory 这个"最大杠杆";
- 答出 `allow_delegation` 非对称、委派是允许非强制、QA Agent 通用模式这些**实战细节**,证明真做过。

**一句话收尾**：优秀 Agent 的六要素本质是"优秀员工特征"的工程化,设计时把自己当管理者(目标→流程→雇谁→怎么带);其中 Memory 是最大杠杆(自我批评→越跑越好),护栏要分层兜住 Fuzzy 的不确定性——这套心法适用于所有多 agent 框架,crewAI 只是把它做成了 `memory=True` 这样的一键原语。

> 关联：`02-AI-Agents概览与第一个Crew实战.md`(Role-playing 起源)、`../../12-Long-Term Agentic Memory With LangGraph/notes/L1-Agent三大记忆类型与邮件助理蓝图.md`(记忆三类型的更深展开)、`05-优秀Tools三大特性与活动策划Crew.md`(Tools 要素细化)。
