# L06 · Lab：任务优先，构建你的第一个 AI Agent（Agent / Task / Crew 三件套）

> 课程：Design, Develop, and Deploy Multi-Agent Systems with CrewAI（DeepLearning.AI × CrewAI，Module 1）
> 本课任务：用 CrewAI 的三个核心原语 **Agent / Task / Crew** 搭出第一个单 agent 系统——一个 YouTube Shorts 内容策划 agent，并通过"坏例子 vs 好例子"的对照，体会**上一课的 context engineering 如何落地成 role / goal / backstory / description / expected_output 这几个字段**。

## 0. 本课定位：方法论 + 第一次动手

João（CrewAI 创始人）强调：本课的写法原则**不限于 CrewAI**——不管用什么框架，"agent 做工作、task 被指派给 agent"是全行业通用的心智模型。本课两段内容：先讲怎么想（任务优先 + 像经理一样思考），再进 notebook（`C1M1_Lab_L6_content_creation.ipynb`）跑通第一个 crew。

## 1. 80/20 法则：把时间花在 Task 上，而不是 Agent 上

课程给出的第一条实战建议：**80% 精力放在 task，20% 放在 agent**。

- 大量真实 use case 的经验：**清晰的 task 定义驱动了产出质量的大头**；
- agent 本身可以被**跨任务复用**（一个定义良好的 agent 能接很多不同 task）；
- 反过来，task 写得含糊，会让一个本来不错的 agent **严重 underperform**。

配套的思考方式是"**think like a manager**"——经理往往是最好的 agent 设计者，因为他们天然会问两个问题：

| 经理的问题 | 映射到 CrewAI |
|---|---|
| "这活我会雇一个什么样的人来干？" | Agent 的 role / goal / backstory |
| "成功长什么样？我怎么验收？" | Task 的 description / expected_output |

## 2. Task：single purpose, single output

Task 的设计原则是**单一目的、单一输出**，靠两个属性支撑：

- **`description`**：要完成什么（做什么、有哪些上下文和约束）；
- **`expected_output`**：成功长什么样——不只是格式，还包括内容应该是什么、怎么排版、语气如何、要多正面。

这两个字段不是"写给人看的注释"，而是 **context engineering 的原料**：CrewAI 会在不同时刻把它们注入 system prompt、role playing、写入 memory；agent 做**自我批判（self-critique）时，会拿最终结果回头对照 expected_output** 检查是否达标。写好 expected_output = 给 agent 一份可执行的验收标准。

> **架构师视角**：`expected_output` 本质上是**任务级的输出契约（output contract）**，与"把验收标准写进 prompt"的 eval 思路同源——它同时充当生成时的引导（prompt 特征）和生成后的自检基准（self-critique 锚点）。一份契约两次复用，这是 CrewAI 把 context engineering 产品化的典型手法；自己裸写 agent 时值得照抄这个结构：每个任务都显式带一份"成功定义"。

## 3. Agent：role / goal / backstory 三要素

| 字段 | 写法要点 |
|---|---|
| `role` | 尽量用**真实世界的职位头衔**，或非常具体地说明想让 LLM role play 成谁 |
| `goal` | 这个 agent **跨越多个 task 的最终目标**——对它而言"好"长什么样、每次接任务时在追求什么 |
| `backstory` | 可以"放飞"的地方：专业经验、工作风格、价值观……一切能强化 role playing、把输出拉向你想要的方向的信息 |

注意 role/goal/backstory 与 task 的分工：**goal 是 agent 级的、跨任务的追求；description/expected_output 是任务级的、一次性的验收**。这也是 agent 可复用而 task 不可含糊的原因。

## 4. Notebook：坏例子 vs 好例子

### 4.1 三个核心类 + 环境

```python
from crewai import Task, Agent, Crew        # CrewAI 三大 building block，普通 Python import
import os
from utils import get_openai_api_key
os.environ["OPENAI_API_KEY"] = get_openai_api_key()   # 配好 OpenAI key 即可
```

### 4.2 坏例子（视频演示）：随手写的 agent 和 task

需求：帮我们策划 30–45 秒的 YouTube Shorts 短视频。随手一写：

```python
agent = Agent(
    role="Content Creator Assistant",             # 泛泛的头衔
    goal="Come up with video ideas",              # 一句话目标
    backstory="Someone with lots of experience creating video content",  # 敷衍的背景
    llm="gpt-4o-mini",
)
task = Task(
    description="Come up with 5 new video ideas", # 没说平台、时长、风格
    expected_output="A list of those ideas",      # 没定义成功标准
    agent=agent,
)
```

跑出来的结果：五个泛泛的选题（极简主义生活 24 小时、舞蹈潮流演变、VR、世界美食、自然韧性）——**它根本不知道这是 30–45 秒的短视频而不是纪录片，也不知道平台是 YouTube、可以针对算法优化**。你没给的信息，LLM 不会替你脑补对。

### 4.3 好例子（notebook 实做）：信息即特征

前面课程讲过：**你喂给 LLM 的信息就是决定输出的 features**。好例子把所有约束显式写进去：

```python
content_creator_assistant = Agent(
    role="YouTube Shorts Micro-History Strategist",   # 具体到平台+品类的"职位"
    goal="Plan a 1-week slate of high-retention YouTube Shorts "
         "about surprising origins of everyday things.",   # 跨任务的追求：高留存
    backstory=(
        "You specialize in 30-45s micro-history that hooks fast, "
        "pays off with a twist, and drives comments. "
        "You keep ideas filmable by a solo creator at home with minimal props."
    ),                                                # 专长+工作风格+现实约束
    llm="gpt-4o-mini",
    verbose=True,        # 打印 agent 执行过程，学习/调试利器
)

task = Task(
    description=(
        "Create a 1-week video posting plan with 5 video blueprints. "
        "Platform: YouTube Shorts (vertical 9:16, 30-45s). "        # 平台/画幅/时长
        "Niche: Micro-History of Everyday Things ... "               # 垂类+举例
        "Primary goals: 1) thumb-stop hook in first 1s, 2) clear narrative "
        "with a surprise, 3) strong SEO phrasing, 4) comment-bait CTA. "
        "Context: solo creator, home-filmable, no special gear."     # 制作约束
    ),
    expected_output='''Output a JSON array following the schema below ...
        { "videos": [ { "title": "...", "hook_main": "<=12 words ...",
            "hook_alt": "...", "visuals": [...], "tags": [...], "cta": "..." } ] }
    ''',                                              # 直接给 JSON schema，锁定格式
    agent=content_creator_assistant,
)
```

### 4.4 组装 Crew 并 kickoff

```python
crew = Crew(
    agents=[content_creator_assistant],   # 哪怕只有一个 agent，也用 Crew 组织
    tasks=[task],
)
result = crew.kickoff()    # 执行整个 workflow
print(result.raw)          # 最终输出的原始文本
```

verbose 日志里能看到 agent 领任务、推理、给出 Final Answer 的全过程；最终输出正是我们要的 JSON——每条 blueprint 带 title、hook_main、hook_alt、visuals、tags、cta，可直接进下游工具链。**同一个模型，仅仅因为 task/agent 定义的密度不同，结果天差地别。**

> **对比课程 13《Multi AI Agent Systems with crewAI》（2024 同厂基础课）**：核心 API 惊人地稳定——`Agent(role, goal, backstory)` + `Task(description, expected_output)` + `Crew` + `kickoff()` 两年没变，这套抽象是 CrewAI 的"宪法层"。变的是**理念的讲法**：2024 版把要诀总结为 role-playing / focus / cooperation 等六要素，偏"多 agent 协作"叙事；2025 版改用 **context engineering** 统一解释（字段=喂给 LLM 的特征）、并给出更工程化的 **80/20 任务优先**与"think like a manager"启发式。学 2024 版的人不用重学 API，要更新的是设计方法论。

> **对比 AutoGen 的 conversation-first 范式**（《AI Agentic Design Patterns with AutoGen》）：AutoGen 的第一公民是**对话**——ConversableAgent 互发消息，任务在对话中"涌现"完成；CrewAI 的第一公民是**任务**——Task 显式声明 description 和 expected_output，再指派给 agent。conversation-first 灵活、适合探索式 PoC，但成功标准藏在对话里、难验收；task-first 把验收标准变成一等公民字段，输出更可预期。参见 `2-framework/03-framework-profiles.md`：新的多 agent 生产项目首推 crewAI，AutoGen/AG2 留给想法验证。

## 5. 从单 agent 到 crew：本例的扩展方向

课程末尾点题：这只是**单 agent 级别**的示范。同一 use case 可以扩成完整的内容生产 crew——起草脚本、深度调研、营销策划、跨社交网络分发……每个环节一个专职 agent。这正是下两课的主题。

## 6. 本课总结

| 要点 | 一句话 |
|---|---|
| 80/20 法则 | 精力优先投 task；task 含糊会让好 agent underperform |
| Think like a manager | agent=我会雇谁；task=成功怎么验收 |
| Task 双属性 | description（做什么）+ expected_output（成功长什么样，可含 JSON schema） |
| Agent 三要素 | role（真实职位）/ goal（跨任务追求）/ backstory（专长+风格+约束） |
| 字段即 context engineering | 这些字段被注入 system prompt / memory / self-critique 锚点 |
| 三件套 API | `Agent` + `Task` + `Crew(agents, tasks)` → `crew.kickoff()` → `result.raw` |

> **记忆点（引出 L7–L8）**：本课的单 agent 再强也只有一套 prompt、一套工具、一个专长。L7–L8 把"雇一个人"升级成"组一个团队"：多个各带专属工具与 backstory 的专职 agent，按 sequential 顺序接力（planner → researcher → fact checker → writer），用分工去啃高复杂度 use case——deep research crew 登场。

## 与我的资产映射

- 设计模式层：`agent/skills/agent-selection/11-design-patterns.md`——本课是"单 agent + 显式任务契约"的最小例，内容生产流水线正是其 §crewAI 线性角色协作甜区的入口形态
- 框架层：`agent/skills/agent-selection/2-framework/03-framework-profiles.md` §7 crewAI（Role+Task+Crew 抽象、甜区与反模式）
- 面试包：`agent/interview/jd-senior-agent-engineer/01-agent-run-loop-and-orchestration`（task-first vs conversation-first 的编排范式对比素材）
- [[project_selection_matrix]]
