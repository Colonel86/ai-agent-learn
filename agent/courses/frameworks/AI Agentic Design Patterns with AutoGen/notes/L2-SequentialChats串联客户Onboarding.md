# L2 · 用 Sequential Chats 串联客户 Onboarding 流程（initiate_chats + carryover）

> 课程：AI Agentic Design Patterns with AutoGen（DeepLearning.AI × Microsoft × Penn State，讲师 Chi Wang & Qingyun Wu，AutoGen 创始人）
> 本课任务：把"客户 onboarding"拆成三个子任务，用**一串两两对话（sequential chats）**让多个 agent 接力完成，并体验人类如何无缝进入 AI 系统的循环（human in the loop）。

## 0. 本课目标与路线

L1 里两个 agent 讲单口喜剧，是"一场对话"；本课升级为"**一串对话**"：多步任务 → 按步拆成多个 chat → 前一个 chat 的结论**摘要后传给**下一个 chat。路线三步：**① 任务分解 → ② 构建四个 agent → ③ 用 chats 列表 + `initiate_chats` 编排执行**。

## 1. 任务分解：onboarding 的三个子任务

典型 onboarding 流程：先收集客户信息 → 再调查兴趣 → 最后基于前两步的信息做互动。据此拆成三个子任务，每个子任务一个专职 agent：

```
┌────────────────┐    ┌────────────────┐    ┌────────────────┐
│ ① 信息收集      │ →  │ ② 兴趣调查      │ →  │ ③ 客户互动      │
│ 姓名 / 位置     │    │ 想读什么话题    │    │ 讲趣闻/笑话/故事 │
└────────────────┘    └────────────────┘    └────────────────┘
        └──── 每步的产出摘要（carryover）流向下一步 ────┘
```

> **架构师视角**：分解的依据不是"能不能塞进一个 prompt"，而是**每步的关注点和终止条件不同**——收集信息的 agent 被明确禁止多问（"Do not ask for other information"），互动 agent 则要放开发挥。单 agent 大 prompt 会让这些互相冲突的指令打架；拆开后每个 agent 的 system message 都短而专一，这是最朴素也最有效的"关注点分离"。

## 2. 构建四个 agent：三个 LLM 员工 + 一个人类代理

四个 agent 全部用 L1 学过的 `ConversableAgent`，差异全在配置上：

| agent | 背后是谁 | human_input_mode | 职责 |
|---|---|---|---|
| onboarding_personal_information_agent | LLM | NEVER | 只收集姓名和位置 |
| onboarding_topic_preference_agent | LLM | NEVER | 只收集感兴趣的新闻话题 |
| customer_engagement_agent | LLM | NEVER | 基于信息+话题讲趣闻/笑话/故事 |
| customer_proxy_agent | **无 LLM**（`llm_config=False`） | **ALWAYS** | 真人客户的代理，每轮都向人要输入 |

```python
onboarding_personal_information_agent = ConversableAgent(
    name="Onboarding Personal Information Agent",
    system_message='''你是客户 onboarding 助手，
    职责是收集客户的姓名和位置。不要询问其他信息。
    收集完成后返回 'TERMINATE'。''',   # 职责边界 + 终止暗号都写进 system message
    llm_config=llm_config,             # {"model": "gpt-3.5-turbo"}
    human_input_mode="NEVER",          # 回复完全由 LLM 生成，不找人
)
```

关键是**客户代理**这一个——human in the loop 的全部机关就在两个参数上：

```python
customer_proxy_agent = ConversableAgent(
    name="customer_proxy_agent",
    llm_config=False,                  # 不挂 LLM：它自己不会"想"
    human_input_mode="ALWAYS",         # 每轮都停下来，等真人敲键盘输入
    is_termination_msg=lambda msg: "terminate" in msg.get("content").lower(),
)                                      # 对方消息含 terminate 即结束本场 chat
```

> **架构师视角**：`human_input_mode` 是 AutoGen 里人机边界的**唯一开关**：`NEVER`＝全自动，`ALWAYS`＝人肉 agent，（还有折中的 `TERMINATE`＝仅终止前问人）。把"真人"建模成一个不挂 LLM 的 ConversableAgent，意味着人和 LLM 在编排层**同构**——chats 列表里换掉一个 agent 的这两个参数，就完成了"自动化↔人工审核"的切换，编排代码一行不改。

## 3. chats 列表：每场对话是一个 dict，衔接靠 carryover

三个子任务 → 三场两两对话（都是"某个 onboarding agent ↔ 客户代理"）。每场 chat 用一个 dict 描述，字段即机制：

```python
chats = [
    {   # ── 第 1 场：收集姓名/位置 ──
        "sender": onboarding_personal_information_agent,   # 由它发开场白
        "recipient": customer_proxy_agent,
        "message": "Hello, ... Could you tell me your name and location?",
        "summary_method": "reflection_with_llm",           # 结束后让 LLM 回看全程做摘要
        "summary_args": {"summary_prompt":                 # 定制摘要格式：只回 JSON
            "Return the customer information into as JSON object only: "
            "{'name': '', 'location': ''}"},
        "max_turns": 2,           # 最多两轮问答（名字一轮、位置一轮）
        "clear_history": True,    # 开场前清空历史
    },
    {   # ── 第 2 场：调查话题偏好 ──
        "sender": onboarding_topic_preference_agent,
        "recipient": customer_proxy_agent,
        "message": "Great! Could you tell me what topics you are interested in reading about?",
        "summary_method": "reflection_with_llm",  # 不给 summary_prompt → 用内建默认提示词
        "max_turns": 1,           # 一轮够了；想多挖信息就调大
        "clear_history": False,   # 不清历史：代理端保留上一场上下文
    },
    {   # ── 第 3 场：客户互动。这次由客户代理开场 ──
        "sender": customer_proxy_agent,
        "recipient": customer_engagement_agent,
        "message": "Let's find something fun to read.",
        "max_turns": 1,
        "summary_method": "reflection_with_llm",
    },
]
```

三套机制拆开看：

1. **两两对话的生命周期**：sender 把 `message` 发给 recipient 开场 → 双方来回，直到 **`max_turns` 用完**或收到**终止消息**（`is_termination_msg` 命中 TERMINATE）；
2. **summary_method（摘要）**：sequential 场景下任务彼此依赖，所以每场结束用 `reflection_with_llm` 让 LLM 回看对话生成摘要；`summary_args.summary_prompt` 可指定格式——第 1 场就是靠它把姓名/位置压成 `{'name': '', 'location': ''}` 的 JSON；
3. **carryover（衔接）**：前面**所有** chat 的摘要会作为 carryover 自动拼进下一场 chat 的开场消息（以 `Context: ...` 附在 message 后）。第 3 场的互动 agent 之所以知道"Alice、New York、喜欢狗"，不是因为共享了聊天记录，而是收到了前两场的摘要。

```
chat1 ──summary──► {'name':'Alice','location':'New York'} ─┐
chat2 ──summary──► "Alice 对狗相关话题感兴趣" ──────────────┤ carryover
                                                           ▼
chat3 开场消息 = "Let's find something fun to read." + Context: 前两条摘要
```

> **对比课程 13 crewAI 的 sequential process**：crewAI 里 Task 按序执行、上个 task 的 output 自动进下个 task 的 context——和这里"chats 列表 + carryover"是同一个抽象的两种拼法。差异在颗粒度：crewAI 传递的是**任务产物**（output 全文），AutoGen 传递的是**对话摘要**（且可用 summary_prompt 声明格式，如压成 JSON）。摘要即压缩：多步流水线越长，"每步只带结构化摘要前行"对 token 成本和信噪比越友好——这一手在哪个框架里都值得抄。

## 4. 执行与检查：initiate_chats、summary、cost

编排好后一行启动（注意这是模块级函数，不是某个 agent 的方法——因为它统筹的是**多场**对话）：

```python
from autogen import initiate_chats
chat_results = initiate_chats(chats)   # 依序执行，控制台上三场对话依次展开
```

运行体验（视频 demo）：第 1 场问姓名（Alice）和位置（New York）；第 2 场问想读的话题（dog）；第 3 场互动 agent 直接用上姓名、位置和话题讲狗的趣闻——carryover 生效的直观证据。

事后审计，每场一个 `ChatResult`：

```python
for chat_result in chat_results:
    print(chat_result.summary)   # 各场摘要：JSON 客户信息 / 兴趣一句话 / 互动内容
for chat_result in chat_results:
    print(chat_result.cost)      # 各场成本：总费用 + prompt/completion token 明细
```

> **架构师视角**：`ChatResult` 把 summary 和 cost 按场拆开，等于免费送了一层**最小可观测性**——多步流水线哪一步烧 token 最多、哪一步摘要质量差，不接观测平台也能定位。生产化时这就是埋点的天然锚点（对应选型包 5-observability-eval 的 trace 粒度问题：per-chat 正是合理的 span 边界）。

## 5. 本课总结

| 要点 | 一句话 |
|---|---|
| 任务分解 | 按"关注点+终止条件不同"拆成三个子任务，每个配专职 agent |
| human in the loop | `llm_config=False` + `human_input_mode="ALWAYS"` 把真人建模成 agent |
| chats 列表 | 每场对话一个 dict：sender/recipient/message/max_turns/summary 全声明式 |
| summary_method | `reflection_with_llm` 结束后摘要，summary_prompt 可强制 JSON 格式 |
| carryover | 前序各场摘要自动拼进下一场开场消息，任务链靠它衔接 |
| ChatResult | 每场的 summary 与 cost 可单独审计 |

> **记忆点（引出 L3）**：本课的 chats 是**平铺的链**——一场接一场、全在明面上。L3 把"一串对话"折叠进**单个 agent 的内心独白**：critic 收到稿件后，先在肚子里开一场多 reviewer 的 nested chat 审完，再对外回复——这就是用 nested chat 实现的 **Reflection** 设计模式。

## 与我的资产映射

- 模式层：`agent/skills/agent-selection/11-design-patterns.md`——sequential chats ≈ workflow 谱的 **prompt chaining** 档（固定步骤序列、步间传摘要）
- 框架层：`agent/skills/agent-selection/2-framework/03-framework-profiles.md` §8——AutoGen 已转维护模式，本课学的是**对话式编排的思想**（可迁移至 MAF / AG2 / crewAI），非生产选型背书
- 对照课程：`courses/13-Multi AI Agent Systems with crewAI`（sequential process 的 crewAI 版）
- 面试包：`agent/interview/jd-senior-agent-engineer/01-agent-run-loop-and-orchestration`（多步编排 + 步间状态传递的实例）
- [[project_selection_matrix]]
