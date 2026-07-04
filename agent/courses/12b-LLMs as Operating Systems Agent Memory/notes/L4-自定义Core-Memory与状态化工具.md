# L4 · 自定义 Core Memory：Memory Blocks 与状态化工具

## 1. Core Memory 的解剖：Block

Core memory = **memory blocks（数据）+ memory tools（操作）**。每个 block 三要素：

| 要素 | 作用 |
|---|---|
| `label` | 引用名（human / persona / 自定义），同一 agent 内唯一 |
| `limit` | 字符上限——限定该块最多占用多少窗口空间 |
| `value` | 实际进入 context 的数据 |

**渲染**：block 在推理时被编译进窗口，模板可查可改：

```python
client.agents.core_memory.retrieve(agent_id=...).prompt_template
# 形如:<human characters="123/2000">My name is Sarah</human>
```

标签里带 `已用/上限` 字符数——**agent 能看见自己的记忆配额**，这是它能自主决定"这块该腾位了"的信息基础（呼应 L2 的溢出处理）。

**Block 有全局唯一 ID、同步在数据库里** → 可以跨 agent 挂载同一个 block（L6 共享记忆的机制基础）。访问方式两种：`client.blocks.retrieve(block_id)` 或 `client.agents.blocks.retrieve(agent_id, block_label)`。

## 2. Stateful Tools：能改 agent 自身状态的工具

Letta 工具签名里可以声明特殊参数 `agent_state: "AgentState"`：

```python
def get_agent_id(agent_state: "AgentState"):
    """Query your agent ID field"""
    return agent_state.id

get_id_tool = client.tools.upsert_from_function(func=get_agent_id)
```

规则：
- **docstring 必须完整描述其它参数**（Letta 从 docstring 生成 schema——对照 12a L3 的 Memory Unit Augmentation，同一个"docstring 即接口"哲学）
- `agent_state` **不需要写文档**——LLM 根本不知道它存在，系统在执行时注入

> **架构师视角**：这是依赖注入（DI）模式在 agent 工具上的应用——**LLM 面对的 schema 和运行时真实签名解耦**。LLM 只生成业务参数，框架注入上下文对象。MCP 里我们靠 server 端闭包捕获上下文，本质同一件事。

## 3. 实战：自定义 Task Queue Memory

抛弃默认的 human/persona 结构，把 core memory 变成一个**任务队列**——展示记忆结构完全可编程：

```python
def task_queue_push(agent_state: "AgentState", task_description: str):
    """Push to a task queue stored in core memory. ..."""
    from letta_client import Letta
    client = Letta(base_url="http://localhost:8283")   # 工具内部再连回 client!
    block = client.agents.blocks.retrieve(agent_id=agent_state.id, block_label="tasks")
    tasks = json.loads(block.value); tasks.append(task_description)
    client.agents.blocks.modify(agent_id=agent_state.id, value=json.dumps(tasks), block_label="tasks")

def task_queue_pop(agent_state: "AgentState"):
    """Get the next task from the task queue ..."""
    # 取 tasks[0]，把 tasks[1:] 写回 block，返回剩余任务
```

**工具内部实例化 Letta client** 这步很妙也很绕：agent 调工具 → 工具连回服务 → 修改 agent 自己的记忆块。self-editing 的实现闭环。

创建专用 agent 的三个关键配置：

```python
task_agent = client.agents.create(
    system=open("task_queue_system_prompt.txt").read(),   # ① 换掉默认 system prompt(记忆管理方式变了)
    memory_blocks=[{"label": "tasks", "value": json.dumps([])}],  # ② 记忆结构 = 一个 JSON 列表
    tool_ids=[task_queue_pop_tool.id, task_queue_push_tool.id],
    include_base_tools=False,                              # ③ 禁掉默认 6 件套
    tools=["send_message"],                                #    但 send_message 必须留(否则没法回复)
)
```

运行效果：发"把 A、B 加成两个任务" → agent `push`×2 → （系统提示要求清空队列）`pop`×2 逐个执行 → 回复结果。`step_count=5`。LLM 有概率性，任务没清完就再发一句 "Complete your tasks"。

> **架构师视角（本课最大启发）**：**core memory 不只是"个人资料卡"，而是 agent 的可编程工作内存**。任务队列只是示例——同样手法可以做：滑动窗口 TODO、状态机、购物车、多轮表单收集。设计公式:**自定义 block 结构（数据） + 自定义配套工具（操作） + 换 system prompt（说明书） + 砍默认工具（收权）**。这四步就是 Letta 上"自定义记忆管理策略"的标准改装流程,面试可直接当案例讲。

> **对比 12a**:12a 的 WORKFLOW_MEMORY 存"过去怎么做"(向量检索参考);这里的 task queue 是"现在要做什么"(窗口内实时状态)。前者是长期程序性记忆,后者是工作记忆(working memory)——正好补上 12a L1 分类学里"短期记忆"的实现案例。
