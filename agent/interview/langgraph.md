# LangGraph的command函数的参数

`Command` 是 LangGraph 里**从 node 返回的一个对象**,作用是把"更新 State"和"决定下一步去哪个 node"**合二为一**——以前要靠 node 返回值 + 条件边两件事,现在一个对象搞定。这个特殊类型从 node 返回时,不仅指定对 state 的更新(一如往常),还指定下一步去哪个 node,让 node 能更直接地控制后续执行哪个节点。

## 四个参数

完整签名(Python):`Command(self, *, graph=None, update=None, resume=None, goto=())`

| 参数 | 类型 | 作用 |
|---|---|---|
| `update` | dict(或 State 对象) | 对 graph state 的更新 |
| `goto` | 节点名 / 节点名列表 / `Send` | 下一步去哪个 node(替代边) |
| `graph` | `None` 或 `Command.PARENT` | 跨子图导航时跳到父图 |
| `resume` | 任意可序列化值 | 配合 `interrupt()` 恢复执行(人在回路) |

逐个说:

**1. `update`** — 状态更新。写进 state 的方式,就跟这个 node 直接返回这个值、而不是返回 Command 对象一样。也就是说 `update={"foo": "bar"}` 和普通 node `return {"foo": "bar"}` 对 state 的效果完全一样,一样会走 reducer 合并。

**2. `goto`** — 控制流,**替代边**。值可以是:
- 单个节点名(string)
- 节点名列表(同时去多个,fan-out)
- `Send` 对象(map-reduce 时带着特定输入派发)

**3. `graph`** — 子图导航。用子图时,如果想从子图里的某个 node 跳到父图的另一个节点,在 Command 里指定 `graph=Command.PARENT`。

**4. `resume`** — 人在回路恢复。配合 `interrupt()` 使用,用来恢复执行的值。

## 最常见的用法:更新 + 路由

```python
from langgraph.types import Command
from typing import Literal

def node_a(state: State) -> Command[Literal["node_b", "node_c"]]:
    return Command(
        update={"foo": "bar"},   # 状态更新
        goto="node_b",           # 路由到下一个 node
    )
```

注意那个返回类型标注 `Command[Literal["node_b", "node_c"]]` ——**这个不是可选的**。这是图渲染和校验所必需的,它告诉 LangGraph 这个 node 可以导航到哪些节点。没有它图画不出来、也校验不了可达性。

## 跨子图跳转

```python
def subgraph_node(state: State) -> Command[Literal["parent_node"]]:
    return Command(
        update={"foo": "bar"},
        goto="other_subgraph",      # 父图里的节点名
        graph=Command.PARENT,       # 关键:跳到父图
    )
```

## Command vs 条件边:什么时候用哪个

这是面试可能追问的点。需要在一个 node 函数里**同时**更新 state 并路由到另一个 node 时,用 Command;只是根据 state 在节点间路由、不和状态更新绑在一起时,用条件边。

`Command` 的价值在多 Agent 场景特别明显:它让 handoff(控制权交接)变得容易——可以指定跳到图里任意节点,包括父图节点,这对层级式 agent 架构里的通信和交接很有帮助。这正好对应你之前聊的"多 Agent 拓扑里控制权怎么交接"——答案就是 `Command` handoff。

---

一个**坑**提醒你:用 Pydantic model 当 state 时,`Command(update=State(foo='foo'))` 这种写法可能会把没显式赋值的字段覆盖成 `None`(社区有 issue 反馈过)。所以 `update` 更稳的写法是只传要改的字段的 dict,比如 `update={"foo": "foo"}`,而不是传整个 model 对象。

要不要我把 `Command` 同时做"状态更新 + 路由"这个机制画成一张图,或者补进你那份面试复习文档里?


# langgraph的compile函数的参数

`compile()` 是把你用 `StateGraph` 搭好的"图蓝图"**编译成一个可执行对象**(`CompiledStateGraph`)的方法。编译后的图实现了 Runnable 接口,可以被 invoke、stream、batch 和异步运行。所有 node、edge 都加完之后调用它,才能真正跑。

## 完整参数(Python,最新版)

`compile(self, checkpointer=None, *, cache=None, store=None, interrupt_before=None, interrupt_after=None, debug=False, name=None, transformers=None)`

| 参数 | 类型 | 作用 |
|---|---|---|
| `checkpointer` | `Checkpointer` | 持久化 State 的存储器;有它才有记忆/恢复/HITL |
| `store` | `BaseStore` | 跨线程的长期记忆存储,可挂向量索引 |
| `interrupt_before` | `list[str]` / `All` | 在指定 node **执行前**暂停 |
| `interrupt_after` | `list[str]` / `All` | 在指定 node **执行后**暂停 |
| `cache` | `BaseCache` | 任务级缓存 |
| `debug` | `bool` | 开 debug 模式,默认 `False` |
| `name` | `str` | 编译后图的名字 |
| `transformers` | `Sequence[Callable]` | 流式输出的自定义转换器 |

最常用的就是前四个。逐个说重点:

### 1. `checkpointer`(最核心)

持久化 State 的存储后端。编译图时传入一个 checkpointer 实例,把图的执行逻辑连接到你的存储后端;调用时还要在 config 里给一个唯一的 `thread_id`。

```python
from langgraph.checkpoint.memory import InMemorySaver
graph = builder.compile(checkpointer=InMemorySaver())
```

选型:开发用 MemorySaver,单机生产用 SqliteSaver,需要多实例横向扩展时用 PostgresSaver。

它是很多能力的地基——长期记忆(几天后还能续上对话)、错误恢复(崩溃后从上个 checkpoint 重放,省时省 API 成本)、人在回路,都建立在它之上。没有 checkpointer,`interrupt()` 也无法工作。

### 2. `store`(长期记忆)

和 checkpointer 分工不同:checkpointer 是**线程内、整状态快照**,store 是**跨线程、长期 KV**(可挂向量索引做语义检索)。对应你之前面试聊的"记忆三层"里的长期记忆层。

### 3. `interrupt_before` / `interrupt_after`(人在回路)

在编译时设置暂停点:在 `compile()` 时通过 `interrupt_before` 或 `interrupt_after` 设置中断点。

```python
graph = builder.compile(
    checkpointer=checkpointer,
    interrupt_before=["execute_payment"],  # 这个 node 跑之前停下来等人
)
```

**两者区别是面试容易追问的坑**:早期常犯的错是该用 interrupt_before 时用了 interrupt_after——用 interrupt_after,node 会先执行再暂停,意味着你想要审批的那个动作其实已经执行了。审批要"门控"某个动作时用 interrupt_before;想让人审查刚发生的事再继续时用 interrupt_after。

恢复执行用 `graph.invoke(None, config)`,LangGraph 会从暂停处精确续上。

## 一个最小例子

```python
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver

builder = StateGraph(State)
builder.add_node("step", step_fn)
builder.add_edge(START, "step")
builder.add_edge("step", END)

# 关键:编译,挂上 checkpointer
graph = builder.compile(checkpointer=InMemorySaver())

# 调用时给 thread_id
config = {"configurable": {"thread_id": "user-1"}}
graph.invoke({"value": 0}, config)
```

---

**注意版本差异**:`interrupt_before/after` 是较早的静态中断方式;新版本更推荐在 node 内部用动态的 `interrupt()` 函数(配合 `Command(resume=...)` 恢复),更灵活。但 `interrupt()` 同样**依赖 compile 时传了 checkpointer**才能工作。两种方式底层都靠 checkpointer 存状态。

要不要我把 `checkpointer` 和 `store` 这两套存储在 compile 里的分工,连同 compile 的参数一起补进你那份面试复习文档?