# L2 · MemGPT 核心概念：LLM OS 的完整设计

本课是纯概念课（无 lab），讲透 MemGPT 论文的关键设计。这些术语是 Letta 框架（L3 起）的语言基础。

## 1. MemGPT 解决什么

控制 agent 行为的唯一途径是改它的输入（context window），但**怎么构造最优 context window 并不显然**——要塞外部数据、用户数据、历史消息、工具结果、推理链……MemGPT 的答案：**建一个替 LLM 管理 context window 的 OS，而这个 OS 本身也是 LLM agent**，记忆管理因此全自动。

## 2. 四个关键机制

### ① Self-editing Memory（自编辑记忆）
传统应用里 system instructions/个性化信息是**固定的**；MemGPT agent 能基于对话中学到的东西**更新自己的指令和个性化信息**。

### ② Inner Thoughts（内心独白）
Agent 永远在"自言自语"，即使不回复用户。**唯一不算工具调用的输出就是内心独白**。

### ③ 一切皆工具（连回复都是）
MemGPT agent **永远在调工具**——想跟用户说话？调 `send_message` 工具。这个统一化让"回复"和"行动"在机制上等价，循环控制变得纯粹。

### ④ Heartbeats（心跳）
Agent 调用任何工具时可附加 **request_heartbeat** 请求，触发一次后续调用——**实现循环**。例：用户说"我叫 Sarah" → agent 内心想"这值得记住" → 调记忆工具 **+ 心跳** → 被再次唤醒 → 调 `send_message` 回复。没有心跳，agent 存完记忆就沉默了,用户会一脸懵。

> **架构师视角**：心跳是把**循环控制权交给 LLM** 的机制——12a 的循环由代码 `for iteration in range(max_iterations)` 控制,LLM 只决定"调工具还是给答案";MemGPT 里 LLM 通过 heartbeat 参数**显式声明"我还没做完,再叫我一次"**。控制反转了。四个机制合起来 = **自治（能循环行动）+ 自我改进（能改长期记忆）**。

## 3. Agent State 与 Context Compilation

- **Agent State**：构成 agent 的全部数据（记忆、工具、消息全史）。
- 多数框架把 state 放在 **Python 变量**里,进程一死就没了;MemGPT 把 state 放**数据库**——关掉脚本重跑,agent 记得上次的一切。
- **Context Compilation**：每步把 agent state 编译成 prompt 的过程。消息多到塞不下时留谁去谁?这类决策就是 LLM OS 自动替你做的事。

> 12a 用"Memory Core = 数据库"表达了同样的持久化主张;12b 更进一步,**框架原生就长这样**——不是你把记忆写进库,而是 agent 本体活在库里。

## 4. 记忆分层全景（本课最重要的一张图）

```
┌─ Context Window 内（in-context）─────────────┐
│ System Prompt(含记忆编辑说明)                  │
│ Core Memory ← 永远可见、agent 可编辑、分块限长   │
│ Recursive Summary(递归摘要)                   │
│ External Memory Statistics(外部记忆统计)       │
│ Chat History(近期消息)                        │
└──────────────────────────────────────────────┘
┌─ Context Window 外（out-of-context,无限容量）──┐
│ Recall Memory   ← 消息历史的完整归档            │
│ Archival Memory ← 通用数据存储(文档/事实/代码)   │
└──────────────────────────────────────────────┘
```

### Core Memory（核心记忆）
- 上下文里的**特殊保留区**,不是聊天消息——无论如何**永远可见**
- 存用户/人格等个性化关键信息("和朋友聊天不同于和陌生人"的原因)
- 可分块(human/persona/自定义),**每块有字符上限**(如 2000)
- agent 用 `core_memory_replace` 等工具当场纠错(用户说"我其实叫 Sarah"→立即改)

### Recall Memory（回忆记忆）
- chat history 溢出时,**旧消息不删除**,搬进 recall memory(持久 DB)
- 窗口里换成**递归摘要**(recursive:新摘要概括旧摘要+被逐出消息)
- agent 用 `conversation_search` 工具找旧消息——类比聊天软件的搜索框
- **与多数框架的差异**:别人 truncate 是永久删,MemGPT 永不丢消息

### Archival Memory（档案记忆）
- Core memory 满了怎么办?同样有第二层无限存储
- agent 自主决定什么留 core(重要,常驻窗口)、什么进 archival(一般信息)
- 通用数据仓:可存 PDF、代码、员工手册……(RAG 的家,见 L5)

### External Memory Statistics（外部记忆统计）
关键补丁:外部存储在窗口外,agent **看不见内容,怎么知道该去搜**?
→ 窗口里有一段**统计信息**(archival/recall 各有多少条)。统计显示有几百条 → 先搜再答;统计显示为空 → 不必浪费一次搜索,直接答。

> **架构师视角**:这是个精妙的元数据设计——**不给内容,给"内容存在性"的信号**,让 agent 做出"要不要检索"的正确决策。12a 的对应物是摘要的"ID+描述"占位符(告诉 LLM 有什么可展开)。通用模式:**外部存储必须在上下文里留"目录/统计"级别的可见性,否则 agent 不知道自己不知道**。这条值得进 [[project_asset_reuse]]。

## 5. 溢出处理策略总结

| 溢出位置 | 处理 |
|---|---|
| Chat history 满 | 逐出(flush)一批旧消息 → 递归摘要顶替 + 原文进 recall memory |
| Core memory 块满 | agent 决策:不重要的信息直接进 archival;或先把 core 里较不重要的挪去 archival 腾位,再写入新信息 |

**硬约束**:system prompt + core memory + summary + chat history 必须一起塞进基座 LLM 的 context window。

## 6. 为什么要"能学习"的 agent

香草冰淇淋例子:无持久记忆的 chatbot 说过"最爱香草",过后再问就变卦——**沉浸感崩塌**。MemGPT agent 会把自己表达过的偏好写入长期记忆,保持一致。这是"agent 即产品"的体验底线,也是记忆系统最直观的商业价值。
