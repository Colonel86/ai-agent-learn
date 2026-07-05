# 第 3 课：第一个 Crew 视频实操 & 客户支持 Crew 实战

> 课程：Multi AI Agent Systems with crewAI
> 讲师：João Moura
> 原文件：
> - `subtitles/crewai_c1_03.vtt`（L2 视频实操讲解：Research & Write Crew）
> - `code/L3_customer_support.md`（L3 代码：Customer Support 多智能体自动化）

> 📌 本课文档包含两部分：
> - **Part A**：c1_03 视频对 **L2 研究写作 Crew** 的完整实操讲解（逐步构建）
> - **Part B**：**L3 客户支持 Crew** 的代码实战（引入 6 大关键能力）

---

# Part A：视频实操讲解 —— 第一个多智能体系统

## 1. 本节目标

前面几节课我们已经了解了 Agent 的原理。现在**动手构建第一个多智能体系统**：

> 一个能够**自动研究并撰写文章**的 Crew（研究 + 写作 + 编辑）

João 明确表示：**他坚信多智能体系统是未来**，是企业构建和工程师职业影响力的关键驱动。

---

## 2. 起步：导入 & 配置

### 2.1 导入 crewAI 的三大核心类

```python
from crewai import Agent, Task, Crew
```

这三个类是 crewAI 构建多智能体系统的**基石**。

### 2.2 配置 LLM（Agent 的"大脑"）

crewAI 默认使用 **GPT-4**，但本例改用 **GPT-3.5 Turbo** 以降低成本：

```python
import os
os.environ["OPENAI_MODEL_NAME"] = 'gpt-3.5-turbo'
```

> 💡 crewAI 支持连接**任何 LLM**：OpenAI、本地模型（Ollama）、其他主流厂商均可。

---

## 3. 构建 Agents（三个角色）

### 3.1 Agent 的四大核心属性

| 属性 | 作用 |
|------|------|
| **role** | 角色身份 |
| **goal** | 目标 |
| **backstory** | 背景故事 |
| `allow_delegation` | 是否允许任务委派给其他 Agent |
| `verbose` | 是否打印内部思考过程 |

### 3.2 为什么要精心设计 role/goal/backstory？

> **Agent 在"角色扮演"状态下表现更好。**

设定的上下文越充分，Agent 越能**符合你的预期**去行动。

### 3.3 变量插值（Interpolation）

Agent 的 **role / goal / backstory** 中都可以使用 `{topic}` 这样的占位符：

```python
goal="Plan engaging and factually accurate content on {topic}"
```

运行时通过 `crew.kickoff(inputs={"topic": "..."})` 统一传入，**多个位置共享同一变量**。

### 3.4 三个 Agent

1. **Planner（内容规划师）**：做研究、确定结构、给出大纲
2. **Writer（写手）**：基于 Planner 的产出撰写正文
3. **Editor（编辑）**：校对、格式化、准备发布

---

## 4. 构建 Tasks（三个任务）

### 4.1 Task 的三大必备属性

| 属性 | 作用 |
|------|------|
| **description** | 任务描述——让 Agent 知道**该做什么** |
| **expected_output** | 期望产出——**强制你明确"成功长什么样"** |
| **agent** | 指派执行者 |

### 4.2 expected_output 的"强制思考"作用

> expected_output 是一个 **Forcing Function**。

它迫使你在任务开始前就**精确定义终态**，例如：

> "一份完整的内容规划文档，包含：大纲 / 受众分析 / SEO 关键词 / 参考资源。"

### 4.3 三个任务

- **Plan Task**：研究最新趋势、关键人物、热门新闻
- **Write Task**：产出 Markdown 博客文章，多个小节，每节 2-3 段
- **Edit Task**：校对，对齐品牌风格

---

## 5. 组装 Crew

```python
crew = Crew(
    agents=[planner, writer, editor],
    tasks=[plan, write, edit],
    verbose=2
)
```

### 5.1 三个核心属性

- **agents**：Agent 列表
- **tasks**：Task 列表
- **verbose**：日志详细度（可选 1 或 2，2 最详细）

### 5.2 ⚠️ 关键点：默认**顺序执行（Sequential）**

> **一个任务的输出，会作为下一个任务输入的一部分。**

因此 **tasks 列表的顺序至关重要**。

后续课程会讲到：
- **并行执行（Parallel）**
- **层级执行（Hierarchical）**

---

## 6. 启动 Crew

```python
result = crew.kickoff(inputs={"topic": "Artificial Intelligence"})
```

### 6.1 kickoff 的 inputs 参数

`inputs` 字典中的变量会被**插值到所有 Agent 和 Task 的占位符**中——这正是为什么 `{topic}` 可以一次写、多处用。

### 6.2 渲染结果

```python
from IPython.display import Markdown
Markdown(result)
```

示例产出文章：
> **"The Rise of Artificial Intelligence: A Transformative Force in Today's World"**
> 含多个子小节，每节内容充实。

### 6.3 观察执行过程（verbose=2）

1. **Content Planner** 启动 → 输出研究大纲
2. **Content Writer** 接手大纲 → 输出 Markdown 博客
3. **Editor** 校对润色 → 输出最终版本

---

## 7. 彩蛋：crewAI 文档本身就是由 Crew 写的

> crewAI 的官方文档不再需要专人维护——**一个多智能体系统替代了文档团队**。

这说明多智能体系统在**工程领域**也有真实落地价值。

---

## 8. 课程小结（7 条核心洞察）

1. **Agent 的本质**：能"自言自语"的 LLM + 内部思考流程 + 工具使用 → 能给出远超普通 LLM 的复杂答案
2. **多 Agent 协作**：Agent 之间可以互相委派任务，各司其职
3. **crewAI 三大构建块**：Agent / Task / Crew
4. **Role-playing 提升效果**：精心设计 role/goal/backstory
5. **聚焦于 Goal 和 Expectations**：明确目标与期望产出
6. **1 个 Agent 可以承担多个 Task**（本例是 1:1，但不是硬性要求）
7. **粒度要细**：每个 Agent 聚焦于非常具体的一件事
8. **执行方式可选**：顺序 / 并行 / 层级——按需选择

---

---

# Part B：L3 代码实战 —— Customer Support 多智能体自动化

## 1. 本课要学的 6 大 Agent 核心能力

> 让 Agent 表现得**更出色**的 6 大要素：

| 能力 | 英文 | 说明 |
|------|------|------|
| **角色扮演** | Role Playing | role/goal/backstory 让 Agent"入戏" |
| **聚焦** | Focus | 每个 Agent 专注一件事 |
| **工具** | Tools | 与外部世界交互 |
| **协作** | Cooperation | Agent 之间互相委派 |
| **护栏** | Guardrails | 约束行为边界 |
| **记忆** | Memory | 跨任务共享上下文 |

---

## 2. 环境准备

```python
!pip install crewai==0.28.8 crewai_tools==0.1.6 langchain_community==0.0.29
```

```python
import warnings
warnings.filterwarnings('ignore')

from crewai import Agent, Task, Crew

import os
from utils import get_openai_api_key

openai_api_key = get_openai_api_key()
os.environ["OPENAI_MODEL_NAME"] = 'gpt-3.5-turbo'
```

---

## 3. Role Playing / Focus / Cooperation

### 3.1 Agent 1：资深客服代表

```python
support_agent = Agent(
    role="Senior Support Representative",
    goal="Be the most friendly and helpful "
         "support representative in your team",
    backstory=(
        "You work at crewAI (https://crewai.com) and "
        " are now working on providing "
        "support to {customer}, a super important customer "
        " for your company."
        "You need to make sure that you provide the best support!"
        "Make sure to provide full complete answers, "
        " and make no assumptions."
    ),
    allow_delegation=False,
    verbose=True
)
```

📌 注意：`allow_delegation=False` → **客服代表不能把任务甩给别人**，必须自己回答。

### 3.2 Agent 2：支持质量保障专员（QA）

```python
support_quality_assurance_agent = Agent(
    role="Support Quality Assurance Specialist",
    goal="Get recognition for providing the "
         "best support quality assurance in your team",
    backstory=(
        "You work at crewAI (https://crewai.com) and "
        "are now working with your team "
        "on a request from {customer} ensuring that "
        "the support representative is "
        "providing the best support possible.\n"
        "You need to make sure that the support representative "
        "is providing full"
        "complete answers, and make no assumptions."
    ),
    verbose=True
)
```

📌 注意这里**没有设置** `allow_delegation` → 默认为 `True`：

> **QA 可以把任务反向委派给客服代表**，形成来回协作的闭环。

### 3.3 三要素在本例中的体现

| 要素 | 实现方式 |
|------|----------|
| **Role Playing** | 两个 Agent 都有 role / goal / backstory |
| **Focus** | Prompt 中明确要求"入戏"、聚焦在各自角色 |
| **Cooperation** | QA 可以回委派给客服，形成**协作循环** |

---

## 4. Tools（工具）

### 4.1 导入内置工具

```python
from crewai_tools import SerperDevTool, \
                         ScrapeWebsiteTool, \
                         WebsiteSearchTool
```

### 4.2 可以用来自定义的工具场景

- 加载客户数据
- 查询历史对话
- 从 CRM 拉取信息
- 查询现有 Bug 报告
- 查询功能请求
- 查询进行中的工单
- ……

### 4.3 基础用法

```python
search_tool = SerperDevTool()         # 联网搜索
scrape_tool = ScrapeWebsiteTool()     # 通用网页抓取
```

### 4.4 实例化文档抓取工具

锁定**单个 URL**（crewAI 官方文档页）：

```python
docs_scrape_tool = ScrapeWebsiteTool(
    website_url="https://docs.crewai.com/how-to/Creating-a-Crew-and-kick-it-off/"
)
```

### 4.5 工具绑定的两种方式

| 级别 | 作用范围 | 适用场景 |
|------|----------|----------|
| **Agent 级** | 该 Agent 执行的**所有任务** | 通用工具 |
| **Task 级** | 只在该特定任务中使用 | 精细控制 |

> ⚠️ **Task 级工具会覆盖 Agent 级工具**。

---

## 5. 创建 Tasks

### 5.1 Task 1：客户咨询解答（带工具）

```python
inquiry_resolution = Task(
    description=(
        "{customer} just reached out with a super important ask:\n"
        "{inquiry}\n\n"
        "{person} from {customer} is the one that reached out. "
        "Make sure to use everything you know "
        "to provide the best support possible."
        "You must strive to provide a complete "
        "and accurate response to the customer's inquiry."
    ),
    expected_output=(
        "A detailed, informative response to the "
        "customer's inquiry that addresses "
        "all aspects of their question.\n"
        "The response should include references "
        "to everything you used to find the answer, "
        "including external data or solutions. "
        "Ensure the answer is complete, "
        "leaving no questions unanswered, and maintain a helpful and friendly "
        "tone throughout."
    ),
    tools=[docs_scrape_tool],         # 🔧 Task 级工具绑定
    agent=support_agent,
)
```

### 5.2 Task 2：质量审核（不带工具）

QA 只需基于客服的产出做审核，**无需外部工具**：

```python
quality_assurance_review = Task(
    description=(
        "Review the response drafted by the Senior Support Representative for {customer}'s inquiry. "
        "Ensure that the answer is comprehensive, accurate, and adheres to the "
        "high-quality standards expected for customer support.\n"
        "Verify that all parts of the customer's inquiry "
        "have been addressed "
        "thoroughly, with a helpful and friendly tone.\n"
        "Check for references and sources used to "
        " find the information, "
        "ensuring the response is well-supported and "
        "leaves no questions unanswered."
    ),
    expected_output=(
        "A final, detailed, and informative response "
        "ready to be sent to the customer.\n"
        "This response should fully address the "
        "customer's inquiry, incorporating all "
        "relevant feedback and improvements.\n"
        "Don't be too formal, we are a chill and cool company "
        "but maintain a professional and friendly tone throughout."
    ),
    agent=support_quality_assurance_agent,
)
```

---

## 6. 组建 Crew（引入 Memory）

```python
crew = Crew(
    agents=[support_agent, support_quality_assurance_agent],
    tasks=[inquiry_resolution, quality_assurance_review],
    verbose=2,
    memory=True                # 🧠 开启记忆
)
```

### 🧠 Memory 的作用

`memory=True` 让 Crew 具备**跨任务的记忆能力**，Agent 间可以共享上下文，输出质量显著提升。

---

## 7. 运行 Crew

```python
inputs = {
    "customer": "DeepLearningAI",
    "person": "Andrew Ng",
    "inquiry": "I need help with setting up a Crew "
               "and kicking it off, specifically "
               "how can I add memory to my crew? "
               "Can you provide guidance?"
}
result = crew.kickoff(inputs=inputs)
```

### 🚧 Guardrails（护栏）

运行后会发现：**Agent 的行为始终在预期的范围内**——这就是 Guardrail 的体现。

护栏来自于：
- 精心设计的 **role / goal / backstory**
- 明确的 **description / expected_output**
- 工具权限的**细粒度控制**（Agent 级 vs Task 级）

### 渲染结果

```python
from IPython.display import Markdown
Markdown(result)
```

---

## 8. Part B 核心要点

| 维度 | 关键点 |
|------|--------|
| **协作机制** | `allow_delegation` 控制是否可委派；QA 可反向委派给客服 |
| **工具系统** | 内置 Serper / Scrape / WebSearch；支持自定义；Agent/Task 两级绑定 |
| **记忆系统** | Crew 层 `memory=True` 一键开启 |
| **护栏** | 来自 prompt + expected_output + 工具权限控制 |
| **输入注入** | `inputs` 字典可一次注入 `{customer}` `{person}` `{inquiry}` 等多变量 |

---

## 🎯 Part A 与 Part B 的连贯性

| 维度 | Part A（Research & Write） | Part B（Customer Support） |
|------|----------------------------|----------------------------|
| Agent 数 | 3（Planner/Writer/Editor） | 2（Support/QA） |
| 委派（Delegation） | 全部禁用 | QA 可回委派给 Support |
| 工具（Tools） | ❌ 无 | ✅ 文档抓取工具 |
| 记忆（Memory） | ❌ | ✅ `memory=True` |
| 执行模式 | Sequential | Sequential |
| 输入变量 | `{topic}` | `{customer}` `{person}` `{inquiry}` |

📌 **Part A 是最小可用骨架，Part B 引入了 Tools / Memory / Cooperation，逐步把 Agent 系统推向生产级。**

---

## 面试速答总结

**一句话**：从零搭一个多 agent 系统就四步——**Agent(role/goal/backstory) → Task(description/expected_output/agent) → Crew(agents+tasks，列表顺序=执行顺序) → kickoff(inputs 插值)**；升级到生产级靠六大能力：Role Playing / Focus / **Tools（Agent 级与 Task 级两级绑定，Task 级覆盖）** / **Cooperation（`allow_delegation` 控制委派方向）** / Guardrails / **Memory（`memory=True` 一键开启）**。核心心法：`expected_output` 是 **Forcing Function**——强迫你在任务开始前就精确定义"成功长什么样"。

### 面试回答骨架（问"手把手搭一个多 agent 系统 / crewAI 里工具、记忆、委派怎么用"）

> 1. **最小骨架四步**（Part A）：① 定义 Agent——role/goal/backstory 三件套让 LLM"入戏"（实测显著提升表现），`allow_delegation` 决定能否转委派；② 定义 Task——description（做什么）+ **expected_output（成功长什么样）** + agent（谁做）；③ 组装 Crew——**tasks 列表顺序就是 Sequential 执行顺序，前一个任务的输出自动进下一个任务的输入**；④ `kickoff(inputs={...})`——占位符 `{topic}` 一次传入、多处插值（agent 和 task 里共享）。
> 2. **强调 expected_output 的设计价值**：它不是可选注释，是 **Forcing Function**——迫使你先定义终态（"含大纲/受众分析/SEO 关键词的规划文档"），这就是验收标准前置的思想。
> 3. **升级到生产级的三个机制**（Part B 客服 Crew）：**委派方向设计**——客服 `allow_delegation=False`（不许甩锅）、QA 默认 `True`（可以打回去返工），一来一回就形成"生成→审核→修订"闭环；**工具两级绑定**——Agent 级对所有任务生效、Task 级只在该任务生效**且覆盖 Agent 级**，用它做工具权限的细粒度控制；**记忆**——Crew 层 `memory=True`，跨任务共享上下文。
> 4. **护栏从哪来**：不是单独的组件，而是 role/goal/backstory + 明确的 expected_output + 工具权限三者叠出来的行为边界——agent 始终在预期范围内行动。

### 关键判断（加分点）

- **"QA 可反向委派"就是 Reflection/evaluator-optimizer 模式的 crewAI 写法**：生成者(Support)↔评估者(QA)循环——面试时能把框架特性对到设计模式谱系，比背 API 高一档。
- **expected_output ≈ rubric 前置**：与 SDD 里"验收标准在 spec 阶段写清、可判定"完全同源——好的多 agent 系统从"定义成功"开始，不是从写 prompt 开始。
- **Task 级工具覆盖 = 最小权限原则**：通用工具挂 Agent、敏感/专用工具只挂对应 Task，让"谁在什么任务里能用什么"显式可控——这是工具安全边界的落点。
- **1 Agent 可担多个 Task、粒度宁细勿粗**：拆分依据是"聚焦"（每个 agent 只做好一件事），不是 1:1 的形式对称。
- **真实落地案例**：crewAI 官方文档本身由一个 Crew 维护——回答"多 agent 有没有生产价值"时可用的具体例证。

**一句话收尾**：crewAI 把多 agent 系统降维成"四步组装"，但生产级差距在细节——expected_output 定义成功、委派方向设计出审核闭环、两级工具绑定控制权限、memory 串起上下文；护栏不是加出来的，是 role+预期+权限三者约束出来的。

> 关联：`02-AI-Agents概览与第一个Crew实战.md`（三原语与 Fuzzy 范式）、`04-Agent六大要素与客户触达Crew.md`（六大要素系统展开）、`../../../skills/agent-selection/11-design-patterns.md`（evaluator-optimizer/Reflection 模式）、`../../../skills/agent-selection/spec-kit-workflow.md`（§四 rubric 方法论——expected_output 的同源思想）。
