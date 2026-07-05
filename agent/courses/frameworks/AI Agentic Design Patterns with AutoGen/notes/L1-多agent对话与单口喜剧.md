# L1 · 多 agent 对话与单口喜剧（ConversableAgent 入门）

> 课程：AI Agentic Design Patterns with AutoGen（DeepLearning.AI × Microsoft × Penn State）
> 本课任务：认识 AutoGen 的基础 agent 类 **ConversableAgent**，构建第一个两 agent 对话——让两个 stand-up comedian agent（Cathy & Joe）互讲段子，并掌握对话的检查、总结、终止与续聊。

## 0. 本课目标与路线

路线四步：**① ConversableAgent 概念与单 agent `generate_reply` → ② 两个喜剧演员 agent 用 `initiate_chat` 对话 → ③ 检查 ChatResult（history / cost / summary）→ ④ 终止条件与续聊**。

## 1. ConversableAgent：统一的 agent 抽象

AutoGen 里的 agent 是一个能**代表人类意图行动**的实体：发消息、收消息、执行动作、生成回复、与其他 agent 交互。内置的 `ConversableAgent` 类把不同类型的 agent 统一进同一个编程抽象，自带一组**可开关、可定制**的组件：

| 内置组件 | 作用 |
|---|---|
| LLM 配置列表 | 用大模型生成回复 |
| Code execution | 执行代码 |
| Function / tool execution | 执行函数与工具 |
| Human-in-the-loop | 保持人类介入、检查是否停止回复 |

每个组件都能单独打开/关闭并按应用需求定制——**用同一个接口创建不同角色的 agent**。

```python
from utils import get_openai_api_key
OPENAI_API_KEY = get_openai_api_key()          # 从环境读 OpenAI API key
llm_config = {"model": "gpt-3.5-turbo"}        # 本课全程用 gpt-3.5-turbo

from autogen import ConversableAgent

agent = ConversableAgent(
    name="chatbot",
    llm_config=llm_config,          # 给 agent 挂上 LLM，用它生成回复
    human_input_mode="NEVER",       # 永不征求人类输入，纯靠 LLM 回复
)
```

`human_input_mode="NEVER"` 表示 agent 永远不找人类要输入；换成 `"ALWAYS"` 则每次生成回复前都先问人。这只是最基本的设置——还可以再加 code execution 配置、function execution 等。

## 2. `generate_reply`：无状态的单发问答

最基本的用法：给 agent 一个 messages 列表，要一个回复。

```python
reply = agent.generate_reply(
    messages=[{"content": "Tell me a joke.", "role": "user"}]
)
# → "Why did the scarecrow win an award? Because he was outstanding in his field."

reply = agent.generate_reply(
    messages=[{"content": "Repeat the joke.", "role": "user"}]
)
# → 不会重复上一个笑话！
```

关键行为：**`generate_reply` 不改变 agent 的内部状态**。第二次调用时 agent 不知道自己刚讲过笑话，每次都是"全新的一问"——所以"Repeat the joke" 只会得到一个新笑话。想生成多样回复时这反而有用；但要让 agent 保持状态、连续完成一系列任务，就需要另一条路——对话。

> **架构师视角**：这是 AutoGen 状态模型的第一课——**状态不住在 agent 里，住在对话里**。`generate_reply` 是纯函数式的推理端点；记忆是由 `initiate_chat` 维护的消息历史赋予的。对比课程 12 Agent Memory 的分层：这里只有最朴素的 in-context conversation history，没有独立记忆层——所以"记得住"的边界就是这场 chat 的边界。

## 3. 两个喜剧演员：`system_message` 定制角色 + `initiate_chat` 开聊

用 `system_message` 把通用 agent 变成有人设的角色（不指定则为空消息，agent 表现为通用 assistant）：

```python
cathy = ConversableAgent(
    name="cathy",
    system_message="Your name is Cathy and you are a stand-up comedian.",
    llm_config=llm_config,
    human_input_mode="NEVER",
)

joe = ConversableAgent(
    name="joe",
    system_message="Your name is Joe and you are a stand-up comedian. "
    "Start the next joke from the punchline of the previous joke.",  # 更具体的接梗指令
    llm_config=llm_config,
    human_input_mode="NEVER",
)
```

由发起方调用 `initiate_chat` 启动对话：

```python
chat_result = joe.initiate_chat(
    recipient=cathy,                                     # 对话对象
    message="I'm Joe. Cathy, let's keep the jokes rolling.",  # 开场白
    max_turns=2,                                         # 两轮交换后结束
)
```

实际效果：Cathy 讲了 math book 的笑话（"too many problems"），Joe 果然**从上一个 punchline 接着开下一个梗**（"至少现在知道 math book 为什么总那么消极"），Cathy 再顺着续（"没法从书页里减去悲伤"）并抛出新笑话——system_message 里的行为指令真实地塑造了对话走向。两轮后对话按 `max_turns` 停止。

```
joe ──initiate_chat(message, max_turns=2)──▶ cathy
 │  "I'm Joe... keep the jokes rolling"        │
 │◀── 笑话 A（punchline!）─────────────────────┤
 ├── 从 punchline 接笑话 B ───────────────────▶│
 │◀── 续 B + 新笑话 C ─────────────────────────┤
 ▼ 到达 max_turns，停
```

## 4. 检查 ChatResult：history / cost / summary

对话结束后，`chat_result` 里能拿到三样东西：

```python
import pprint
pprint.pprint(chat_result.chat_history)  # 交换的全部消息（joe→cathy→joe→cathy）
pprint.pprint(chat_result.cost)          # token 用量与费用
pprint.pprint(chat_result.summary)       # 对话摘要
```

- **chat_history**：按序保存所有交换的消息；
- **cost**：本例 gpt-3.5-turbo 消耗 97 completion tokens + 219 prompt tokens = 316 total tokens，并给出美元费用；
- **summary**：**默认拿最后一条消息当摘要**——本例就是 Cathy 的一大段笑话，并不算好摘要。

换更好的摘要方法——`reflection_with_llm`，对话结束后再调一次 LLM 反思整场对话：

```python
chat_result = joe.initiate_chat(
    cathy,
    message="I'm Joe. Cathy, let's keep the jokes rolling.",
    max_turns=2,
    summary_method="reflection_with_llm",        # 用 LLM 反思生成摘要
    summary_prompt="Summarize the conversation",  # 摘要用的 prompt
)
```

这次 summary 变成"Joe 和 Cathy 互相分享笑话……用数学和角色相关的段子保持笑点"——像样的摘要了。细节：重跑时对话内容一字不差，因为 AutoGen **默认开启 caching**，相同输入直接返回缓存消息。

## 5. 终止条件：`is_termination_msg` 让对话自己知道何时停

`max_turns` 要求事先知道轮数。不知道时，改用**终止消息判断**——一个接收消息、返回 True/False 的布尔函数：

```python
cathy = ConversableAgent(
    name="cathy",
    system_message="Your name is Cathy and you are a stand-up comedian. "
    "When you're ready to end the conversation, say 'I gotta go'.",  # 教 agent 说暗号
    llm_config=llm_config,
    human_input_mode="NEVER",
    is_termination_msg=lambda msg: "I gotta go" in msg["content"],   # 听到暗号就停
)

joe = ConversableAgent(
    name="joe",
    system_message="... say 'I gotta go'.",
    llm_config=llm_config,
    human_input_mode="NEVER",
    is_termination_msg=lambda msg: "I gotta go" in msg["content"]
                                or "Goodbye" in msg["content"],  # 可以组合多个暗号
)

chat_result = joe.initiate_chat(
    recipient=cathy,
    message="I'm Joe. Cathy, let's keep the jokes rolling."  # 不再传 max_turns
)
```

机制：终止条件**配在每个 agent 身上**，agent 检查的是**收到的消息**——Joe 讲完最后说 "I gotta go"，Cathy 在收到的消息里检测到暗号，就停止回复。比固定轮数灵活：对话长度由内容自然决定（这次跑出了比两轮多得多的交换）。注意配套动作是**在 system_message 里教 agent 说出暗号**——终止是"prompt 约定 + 代码检测"两件套。

> **对比课程 13（crewAI 的 role-playing 多 agent）**：crewAI 用 role / goal / backstory 三字段结构化人设，agent 间协作由框架按 task 列表调度，开发者不直接编排"谁跟谁说"；AutoGen 的人设就是一条自由文本 `system_message`，协作则由开发者显式发起（`initiate_chat`）并用 max_turns / is_termination_msg 控制边界。crewAI 是"填表式"高抽象，AutoGen 是"编排式"低抽象——后者自由度更高，也把停机责任完整交回给你。对比课程 11 LangGraph 则是第三种：终止是图里显式的边与条件路由，而非消息内容里的暗号。

## 6. 续聊：状态真的保住了吗

对话结束后还能续。这次换 Cathy 用 `send` 直接给 Joe 发消息，顺便测试状态：

```python
cathy.send(message="What's last joke we talked about?", recipient=joe)
```

Joe 答对了："The last joke we talked about was the scarecrow winning an award because he was outstanding in his field."——**agent 保住了之前对话的状态**（对比第 2 节无状态的 `generate_reply`）。而且续聊仍遵守同一套终止条件：Cathy 说出 "I gotta go"，Joe 识别暗号停止回复。

至此完整演示了对话的生命周期：**发起对话 → 继续对话 → 记住聊到哪。**

> **架构师视角**：`is_termination_msg=lambda msg: "I gotta go" in msg["content"]` 值得警惕地欣赏——终止条件依赖 LLM 按 prompt 约定说出暗号字符串，这是**概率性停机**：模型不说暗号就停不下来（生产上必须叠加 max_turns / 超时 / 预算熔断兜底）。选型矩阵 11-design-patterns.md 里评估任何多 agent 框架的第一问就是：**终止与预算控制是显式机制还是 prompt 约定？** AutoGen 在这一课给出的答案是两者可叠加，责任在开发者。

## 7. 本课总结

| 要点 | 一句话 |
|---|---|
| ConversableAgent | 统一 agent 抽象：LLM 回复 / code execution / tool execution / human-in-the-loop 组件可开关 |
| human_input_mode | `NEVER` 纯自动，`ALWAYS` 每次回复前先问人 |
| generate_reply | 无状态单发问答，不改变 agent 内部状态 |
| system_message | 一条自由文本定制角色与行为（接梗指令真的生效） |
| initiate_chat | 由发起方启动两 agent 对话，状态存在对话历史里 |
| ChatResult | chat_history / cost（token 与美元）/ summary 三件套 |
| summary_method | 默认取最后一条消息；`reflection_with_llm` + summary_prompt 让 LLM 反思出摘要 |
| is_termination_msg | 布尔函数检测收到的消息，"prompt 教暗号 + 代码验暗号"实现弹性停机 |
| 续聊 | `send` 继续已结束的对话，agent 记得之前聊了什么 |

> **记忆点（引出 L2）**：本课的对话是"一场"——两个 agent、一个话题、聊完为止。真实业务任务往往是"一串"：收集客户信息 → 调研偏好 → 生成个性化建议，每步的产物要喂给下一步。L2 的 **Sequential Chats** 就是把多场两两对话按顺序串起来、用 summary 在对话间传递上下文，以 customer onboarding（客户入职）流程为例。

## 与我的资产映射

- 模式层：`agent/skills/agent-selection/11-design-patterns.md`——multi-agent conversation 模式的最小可运行样本；终止条件"显式机制 vs prompt 约定"的评估锚点
- 框架层：`agent/skills/agent-selection/2-framework/03-framework-profiles.md`——AutoGen 编程模型一手素材：ConversableAgent 统一抽象 + 对话即编排 + ChatResult 自带 cost 观测
- 面试包：`agent/interview/jd-senior-agent-engineer/01-agent-run-loop-and-orchestration`——generate_reply（无状态推理）vs initiate_chat（有状态编排）的分界；多 agent 停机策略
- [[project_selection_matrix]]
