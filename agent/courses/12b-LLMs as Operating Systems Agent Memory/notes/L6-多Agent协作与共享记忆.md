# L6 · 多 Agent 协作与共享记忆：HR 招聘流水线实战

## 1. 前提：Agent 即服务 → 多 Agent 即多服务

Letta agent 以服务形态运行（app 通过 REST API 与 Letta server 交互，server 背靠数据库）。那么**跑在不同服务上的 agent 怎么协作**？两条路：

1. **互发消息**：agent 间发送消息（甚至可跨 server 发 POST）
2. **共享记忆块**：block 存在共享持久层，多 agent 挂载同一 block ID，上下文同步

实战场景：**招聘流水线**——`eval_agent`（评估简历，拒/转）+ `outreach_agent`（给强候选人写 outreach 邮件），共享一块公司信息记忆。

## 2. 共享记忆块（Shared Memory Block）

```python
company_block = client.blocks.create(value="The company is called AgentOS ...",
                                     label="company", limit=10000)
# 两个 agent 创建时都挂:block_ids=[company_block.id]
```

**同一 block ID 挂到多个 agent = 各自窗口里的这段内容是同一行数据库记录**。验证环节很精彩：告诉 outreach_agent"公司改名 Letta 了" → 它调 `core_memory_replace` 改块 → **eval_agent 的窗口内记忆同步变了**（它自己从没编辑过）。

> **架构师视角**：这是把多进程共享内存（shared memory segment）搬到 agent 架构——**通过存储层共享状态，而不是通过消息传递**。对比消息方案：共享块适合**缓变的公共事实**（公司信息、团队规范、共同任务板），消息适合**事件性协调**（"这个候选人给你，去写邮件"）。本课两者同时用了，分工清晰。这是 12a 完全没覆盖的维度——12a 是单 agent 的记忆纵深，12b L6 给了记忆的**横向共享**。

## 3. 方式一：工具驱动的 agent 间通信

### 关键配置逐条拆解（eval_agent）

```python
eval_agent = client.agents.create(
    name="eval_agent",
    memory_blocks=[{"label": "persona", "value": eval_persona}],
    tool_ids=[reject_tool.id],
    tools=['send_message_to_agent_and_wait_for_reply'],   # ① Letta 内置跨 agent 通信工具
    include_base_tools=False,                             # ② 收权:只留必需工具
    block_ids=[company_block.id],                         # ③ 挂共享块
    tool_rules=[{"type": "exit_loop",                     # ④ 工具规则:调完通信工具就退出循环
                 "tool_name": "send_message_to_agent_and_wait_for_reply"}],
)
```

- **① 内置通信工具**：`send_message_to_agent_and_wait_for_reply`(指定目标 agent ID + 消息)。也可以用 client 自己写(前几课的 stateful tool 手法)。
- **④ tool_rules 是新概念**：**用规则约束 agent 行为**——这里声明"调完这个工具就终止执行",防止 agent 无限循环。
- **目标 agent ID 写在 persona 里**："强候选人发给 agent ID xxx"——路由信息作为记忆注入。

> **记忆点**:tool_rules 是把 12a"确定性控制"塞回自治 agent 的钩子——**LLM 决定调什么,规则决定调完之后的控制流**。生产多 agent 系统里这类"围栏"比 prompt 约束可靠得多。

### 运行链路（Tony Stark 的简历）

1. 给 eval_agent 发简历 → reasoning:"档案强" → `send_message_to_agent_and_wait_for_reply`(候选人信息 → outreach_agent ID) → 按规则退出
2. outreach_agent 收到**system message**(带来源 agent ID + 提示"记得最后调 send_message 回复") → 调 `draft_candidate_email` 起草 → `send_message` 把邮件草稿回给 eval_agent
3. 双方各自的消息史独立可查(`messages.list`),usage 分开计

## 4. 方式二：Multi-Agent Group（组抽象）

更简单的协作方式——**把 agent 编组,共享一个群聊**:

```python
round_robin_group = client.groups.create(
    description="This team is responsible for recruiting candidates.",
    agent_ids=[eval_agent.id, outreach_agent.id],   # 按序轮转(round-robin)
)
client.groups.messages.create_stream(group_id=round_robin_group.id,
    messages=[{"role": "user", "content": f"Evaluate: {resume}"}])
```

- **单一共享消息线程**:所有 agent 看得见彼此的消息和用户消息(方式一是各有各的线程,靠工具传话)
- 这次不需要给 agent 配任何通信工具
- 消息带 `name` 字段区分说话者
- SpongeBob 的简历:eval 调 reject → outreach **看见了整个过程**,主动起草了拒信(甚至没人叫它做——群聊模式下行为更难约束,课程也承认"你可以试着 prompt 它别发")

## 5. 两种多 Agent 模式的选型

| | 工具通信(独立线程) | Group(共享群聊) |
|---|---|---|
| 上下文 | 各自独立,按需传递 | 全员共享全部消息 |
| 控制力 | 强(tool_rules + 显式路由) | 弱(全靠各自 persona 自觉) |
| Token 成本 | 低(只传必要信息) | 高(每个 agent 背全量群聊) |
| 适合 | 流水线/明确交接的工作流 | 头脑风暴/需要全景的协作 |

> **架构师视角**:这就是消息队列点对点 vs 广播 topic 的老抉择。默认选**工具通信**——上下文隔离即成本隔离、故障隔离;群聊模式的"人人全知"随 agent 数量平方级膨胀 token,且行为耦合(SpongeBob 拒信事件就是例证)。与我面试包里 multi-agent 编排(supervisor/swarm)的对照:Letta 的 group≈swarm 的共享消息,工具通信≈handoff 模式。
