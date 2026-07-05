# L5 · 用户意图 Agent（perceive → approve 的 human-in-the-loop 目标确认）

> 课程：Agentic Knowledge Graph Construction（DeepLearning.AI × Neo4j，C2）
> 本课任务（对应课程 Lesson 4）：构建整个多 Agent 系统里**第一个真正的业务 Agent**——User Intent Agent。它的唯一产出是 `approved_user_goal`（一个 `kind_of_graph` + `description` 的字典），为下游所有 agent 定方向。核心是一个 **perceive → 用户确认 → approve** 的 human-in-the-loop 闭环。

## 0. 在架构里的位置

回顾 L2 的整体架构图：本课开始进入 **Structured Data Agent**（把 CSV 转成图的那条子流水线）的第一步。为什么先做意图？讲师原话：**"这第一阶段确立用户目标，会影响后面所有 agent 的行为，它设定整体方向。"** 目标错了，后面文件选型、schema 提案全都跑偏。所以这个 agent 值得把 prompt 写得格外用心。

- **输入**：无
- **输出**：`approved_user_goal = {kind_of_graph, description}`
- **工具**：`set_perceived_user_goal`、`approve_perceived_user_goal`

## 1. 双工具设计：perceive 和 approve 严格分离

这是本课最值钱的一个设计决策。agent 有两个工具，但它们**不对称**：

```
set_perceived_user_goal(kind_of_graph, description)   →  写 state["perceived_user_goal"]
approve_perceived_user_goal()   （无业务参数）        →  把 perceived 拷进 state["approved_user_goal"]
```

关键点（讲师"critically"强调）：**`set_perceived_user_goal` 永远无法自己设置 `approved_user_goal`**。只有 `approve_*` 能做这次拷贝，而 approve 又要求 perceived 必须已存在。于是 `approve_*` 成了一道 **guard / checkpoint**：确保"用户本人明确说了 yes"才把目标固化成已批准。

```
perceived_user_goal          approved_user_goal
   (working memory)              (work specification)
   ┌──────────────┐   approve    ┌──────────────┐
   │ agent 感知的  │ ──────────▶ │ 用户批准的     │
   │ 可反复覆盖    │  仅拷贝      │ 下游唯一可信源 │
   └──────────────┘             └──────────────┘
```

这个"感知/已批准"分离是**刻意的重复**：perceived 是"工作记忆"（agent 可以反复试错、覆盖），approved 是"工作规格说明"。**下游 agent 只准用 approved**。讲师补充：生产系统里 work specification 还应持久化，以支持 tracing 和 reproducibility。

## 2. 工具实现：trust, but verify

```python
PERCEIVED_USER_GOAL = "perceived_user_goal"
APPROVED_USER_GOAL  = "approved_user_goal"

def set_perceived_user_goal(kind_of_graph: str, graph_description: str, tool_context: ToolContext):
    """记录 agent 感知到的用户目标（两个必填分量：图的种类 + 描述）"""
    user_goal_data = {"kind_of_graph": kind_of_graph, "graph_description": graph_description}
    tool_context.state[PERCEIVED_USER_GOAL] = user_goal_data
    return tool_success(PERCEIVED_USER_GOAL, user_goal_data)

def approve_perceived_user_goal(tool_context: ToolContext):
    """仅当用户明确批准后调用；把 perceived 提升为 approved"""
    # trust, but verify —— 没有 perceived 就直接报错，且错误信息教 LLM 怎么补救
    if PERCEIVED_USER_GOAL not in tool_context.state:
        return tool_error("perceived_user_goal not set. Set perceived user goal first, "
                          "or ask clarifying questions if you are unsure.")
    tool_context.state[APPROVED_USER_GOAL] = tool_context.state[PERCEIVED_USER_GOAL]
    return tool_success(APPROVED_USER_GOAL, tool_context.state[APPROVED_USER_GOAL])
```

> **架构师视角**：`approve_*` 不接收任何目标参数——它只能拷贝已有的 perceived，无法凭空捏造一个目标。这是**用工具签名做约束**：把"不许绕过用户确认"这条业务规则编码进函数形参，而不是指望 LLM 自觉。加上那句结构化 `tool_error`（不仅说"错了"，还说"你应该先 set 或问澄清问题"），形成一条完整的纠错回路。讲师把这套叫 "trust, but verify"——信任 LLM 会做对，但在工具里加校验兜底，错误信息本身就是给 LLM 的下一步指令。这是把可靠性从 prompt 层下沉到工具层的典型手法。

## 3. Prompt 分块拼装：role/goal + hints + output + CoT

指令不是一坨写死，而是**四块拼起来**，每块职责单一、便于单独调：

| 块 | 作用 | 内容要点 |
|---|---|---|
| `agent_role_and_goal` | 定角色和目标 | "你是 KG 用例专家，帮用户想出一个 KG 用例" |
| `agent_conversational_hints` | 会话提示 | 用户没主意时给经典用例建议：社交网络 / 物流 / 推荐 / 反欺诈 / 流行文化 |
| `agent_output_definition` | 输出定义（few-shot） | user goal 有两分量：`kind_of_graph`（≤3 词）+ `description`（几句话），配示例 |
| `agent_chain_of_thought_directions` | 思维链步骤 | 明确的 5 步流程 |

```python
agent_chain_of_thought_directions = """
    Think carefully and collaborate with the user:
    1. Understand the user's goal (a kind_of_graph with description)
    2. Ask clarifying questions as needed
    3. When you think you understand, use 'set_perceived_user_goal' to record your perception
    4. Present the perceived goal to the user for confirmation
    5. If the user agrees, use 'approve_perceived_user_goal' to approve it
"""
complete_agent_instruction = f"{agent_role_and_goal}\n{agent_conversational_hints}\n" \
                             f"{agent_output_definition}\n{agent_chain_of_thought_directions}"
```

讲师反复强调的一个原则：**同一件事在 prompt、tool description、tool error 三处都要说一遍**。"你说的次数越多，LLM 做错的可能越低。" 比如"user goal 由 kind_of_graph + description 两分量组成"这句，在 output_definition、set 工具的 docstring、CoT 步骤里各出现一次。

> **对比 SAP KG 课的声明式构图**：SAP 那门课里 schema 是**确定性**从 EDMX 规范推导、SPARQL CONSTRUCT 硬编码的——源数据本身有 schema，构图零幻觉。本课相反：**用户想建什么图这件事没有任何规格文件**，只能靠对话把模糊意图逼成结构化的 `{kind_of_graph, description}`。所以这里必须动用 LLM + human-in-the-loop，而 SAP 那步纯 ETL 不需要人。判断分野：**上游有无既定规格**——有就走确定性管道，没有（意图、非结构化文本）才请 LLM 出场并加人类 checkpoint。

## 4. 跑一遍：澄清问题是常态

脚本对话（讲师承认 LLM 随机性，同一 prompt 每次表现可能不同）：

```python
async def run_conversation():
    await user_intent_caller.call(
        "I'd like a bill of materials graph (BOM) from suppliers to finished product, "
        "which can support root-cause analysis.")
    if PERCEIVED_USER_GOAL not in session_start.state:      # agent 可能先反问澄清 → perceived 还没设
        await user_intent_caller.call("I'm concerned about possible manufacturing or supplier issues.")
    await user_intent_caller.call("Approve that goal.", True)   # 乐观假定批准
```

实际轨迹：初始 `state={}` → 用户发首条消息 → agent **先反问澄清**（"你是想追溯产品从供应商到各制造阶段的组件吗？"）→ 因为代码检查到 perceived 未设，补发一条澄清答复 → agent 满意，调 `set_perceived_user_goal` 并复述"我理解你要的图是这样、描述是这样，对吗？" → 用户"Approve" → agent 调 `approve_perceived_user_goal` → 最终 `state` 里同时有 `perceived_user_goal` 和 `approved_user_goal`。

讲师提醒：这段可能要**多跑几次**——agent"某天心情"可能想多聊几轮才肯 set perceived。这正是 LLM Agent 的非确定性本质，代码里的 `if PERCEIVED_USER_GOAL not in state` 兜底就是为此。

> **对比 11-design-patterns.md 的 evaluator-optimizer**：本课的 perceive→confirm→approve 还只是**单向 human gate**（人当评估者，一次点头就过）。L7 会把"评估"这一环也自动化——引入 critic agent 自动挑刺、循环精炼，逼近 evaluator-optimizer（≈Reflection）模式。可以把 L5 看成"人肉 critic"版本，L7 是"AI critic + 人兜底"版本。

## 5. 本课总结

| 要点 | 一句话 |
|---|---|
| 唯一产出 | `approved_user_goal = {kind_of_graph, description}`，为全流水线定向 |
| perceive/approve 分离 | set 只写感知值；approve 是 guard，仅拷贝且要求人已确认 |
| 工具签名即约束 | approve 无业务参数 → 无法绕过用户凭空造目标 |
| trust but verify | 工具内校验 + 结构化 error 信息（既报错又教补救） |
| prompt 分四块 | role/goal · hints · output(few-shot) · CoT，一件事说三遍 |

> **记忆点（引出 L6）**：意图确定了，但 agent 还不知道**手上有哪些数据文件、哪些跟这个目标相关**。L6 构建 **File Suggestion Agent**：它复用本课的 set/approve 双工具模式（`set_suggested_files` / `approve_suggested_files`），但**从 memory 而非对话历史读取** `approved_user_goal`（靠 `get_approved_user_goal` 工具），再用 `list_available_files` + `sample_file` 巡检 Neo4j import 目录，挑出相关 CSV。你会第一次看到"agent 靠 get 工具读上游 agent 写入的 state"这条跨 agent 协作链真正闭合。

## 与我的资产映射

- 记忆层：`agent/skills/agent-selection/6-memory.md`（working memory `perceived` vs 已批准规格 `approved` 的分离；控制权——写入只经工具）
- 安全/护栏层：`agent/skills/agent-selection/7-safety-guardrails.md`（human-in-the-loop approval gate、trust-but-verify 工具内校验，是把可靠性下沉到工具层的样例）
- Agent UX：`agent/skills/agent-selection/10-agent-ux.md`（perceive→confirm 的确认式交互，避免 agent 自作主张）
- 面试包：`agent/interview/jd-senior-agent-engineer/`（"如何防止 agent 跳过人工确认"→ 答案是工具签名约束 + guard 工具）
- [[project_selection_matrix]] · [[project_interview_prep]]
