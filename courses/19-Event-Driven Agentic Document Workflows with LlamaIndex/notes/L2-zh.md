# L2：构建 Workflow

本节目标：通过一系列由简到难的例子，**掌握 Workflow 的核心概念**——步骤定义、自定义事件、分支与循环、并发执行、收集事件、以及把中间过程**流式（streaming）**输出。

## 1. 最小工作流：一个 step 就够了

Workflow 本质上是普通的 Python 类。每一个**步骤（step）** 都接收某种类型的事件、并发射某种类型的事件。

```python
from llama_index.core.workflow import (
    StartEvent,
    StopEvent,
    Workflow,
    step,
    Context,
)

class MyWorkflow(Workflow):
    @step
    async def my_step(self, ev: StartEvent) -> StopEvent:
        return StopEvent(result="Hello, world!")
```

关键点：

- `@step` 装饰器把一个 `async` 函数声明为步骤；
- **`StartEvent`** 是特殊事件，Workflow 启动时**自动**触发；
- **`StopEvent`** 也是特殊事件，一旦被发射，Workflow 就会停止并把其 `result` 返回；
- `async` 让函数可被挂起 / 恢复，使得多个任务能交错运行——后面做并发时会大派用场。

运行方式：

```python
basic_workflow = MyWorkflow(timeout=10, verbose=False)
result = await basic_workflow.run()
print(result)
```

`timeout` 是超时秒数；Workflow 默认是 async 的，所以 notebook 里用 `await` 就行。在普通 Python 脚本里需要自己用 `asyncio.run(...)` 包一层 `main()`。

## 2. 可视化工作流

LlamaIndex 内置了一个 Workflow **可视化器（visualizer）**：

```python
from llama_index.utils.workflow import draw_all_possible_flows

draw_all_possible_flows(basic_workflow, filename="workflows/basic_workflow.html")
```

它会输出一个**交互式 HTML**，可以拖拽节点。在 notebook 里搭配 helper 函数能直接内嵌显示。

## 3. 多步骤：定义自定义事件

要让多个步骤串起来，就要定义自己的事件。事件类继承 `Event`，可以带任意字段：

```python
from llama_index.core.workflow import Event

class FirstEvent(Event):
    first_output: str

class SecondEvent(Event):
    second_output: str
```

然后写一个三步工作流：

```python
class MyWorkflow(Workflow):
    @step
    async def step_one(self, ev: StartEvent) -> FirstEvent:
        print(ev.first_input)
        return FirstEvent(first_output="First step complete.")

    @step
    async def step_two(self, ev: FirstEvent) -> SecondEvent:
        print(ev.first_output)
        return SecondEvent(second_output="Second step complete.")

    @step
    async def step_three(self, ev: SecondEvent) -> StopEvent:
        print(ev.second_output)
        return StopEvent(result="Workflow complete.")
```

`StartEvent` 上挂的字段是从 `run(...)` 调用时传入的：

```python
workflow = MyWorkflow(timeout=10, verbose=False)
result = await workflow.run(first_input="Start the workflow.")
```

Workflow 是通过"**每步收什么事件、发什么事件**"来定义数据流——不需要显式画图，类型签名本身就是图。

## 4. 循环：让步骤回头

只要让一个步骤**既能接收 LoopEvent，又能发射 LoopEvent**，循环就成立：

```python
class LoopEvent(Event):
    loop_output: str

class MyWorkflow(Workflow):
    @step
    async def step_one(self, ev: StartEvent | LoopEvent) -> FirstEvent | LoopEvent:
        if random.randint(0, 1) == 0:
            print("Bad thing happened")
            return LoopEvent(loop_output="Back to step one.")
        else:
            print("Good thing happened")
            return FirstEvent(first_output="First step complete.")
    # ... step_two / step_three 同前
```

注意类型注解里的 `|`——Workflow 用它推断"这个 step 可被这些事件触发，也可发射这些事件"。**循环可以来自任意一步、回到任意一步**，不局限于回到自己。

## 5. 分支：根据条件走不同子流程

构造方式和循环类似，把"二选一"放在第一步的返回类型里即可：

```python
class BranchA1Event(Event):
    payload: str
class BranchA2Event(Event):
    payload: str
class BranchB1Event(Event):
    payload: str
class BranchB2Event(Event):
    payload: str

class BranchWorkflow(Workflow):
    @step
    async def start(self, ev: StartEvent) -> BranchA1Event | BranchB1Event:
        if random.randint(0, 1) == 0:
            return BranchA1Event(payload="Branch A")
        else:
            return BranchB1Event(payload="Branch B")
    # 后续 step_a1 → step_a2 → StopEvent
    # 后续 step_b1 → step_b2 → StopEvent
```

可视化器可以直接接收**类**而非实例：`draw_all_possible_flows(BranchWorkflow, ...)`。

## 6. 并发执行：Context 与 send_event

要并行触发多个事件，需要引入 **`Context`** 对象——它是 Workflow 各步骤间的**共享内存**。把它声明为 step 参数即可自动注入：

```python
class StepTwoEvent(Event):
    query: str

class ParallelFlow(Workflow):
    @step
    async def start(self, ctx: Context, ev: StartEvent) -> StepTwoEvent:
        ctx.send_event(StepTwoEvent(query="Query 1"))
        ctx.send_event(StepTwoEvent(query="Query 2"))
        ctx.send_event(StepTwoEvent(query="Query 3"))

    @step(num_workers=4)
    async def step_two(self, ctx: Context, ev: StepTwoEvent) -> StopEvent:
        await asyncio.sleep(random.randint(1, 5))
        return StopEvent(result=ev.query)
```

要点：

- `ctx.send_event(...)` 替代 `return`，可以**一次发射多个事件并发执行**；
- `@step(num_workers=4)` 控制并行度（默认就是 4）；
- 第一个发射的 `StopEvent` 会**立刻结束整个 Workflow**——所以你只会看到三个查询里**最先完成**的那个。

## 7. 收集事件：collect_events

如果想等三个分支**全部完成**再继续，用 `Context.collect_events`：

```python
class ConcurrentFlow(Workflow):
    @step
    async def step_three(self, ctx: Context, ev: StepThreeEvent) -> StopEvent:
        result = ctx.collect_events(ev, [StepThreeEvent] * 3)
        if result is None:
            print("Not all events received yet.")
            return None
        print(result)
        return StopEvent(result="Done")
```

工作机制：

- 每次 `step_three` 被触发时调用 `collect_events`；
- 还没收够 → 返回 `None`，step 直接返回 `None`，什么也不做；
- 收够 → 返回一个**按到达顺序排列的事件数组**。

这就是 **map-reduce** 风格的关键：未来你可以用 `ctx.set("num_events", N)` 把总数存进上下文，让 `collect_events` 动态等待——后面的课正是这么做的。

### 收集不同类型的事件

`collect_events` 不止能等同类型事件，也可以等"A、B、C 各一份"：

```python
events = ctx.collect_events(
    ev,
    [StepCCompleteEvent, StepACompleteEvent, StepBCompleteEvent],
)
```

**注意：返回数组的顺序与你传入的类型列表顺序一致**，可以据此知道哪个元素对应哪种事件。

## 8. 流式输出（Streaming）

Agent 跑起来可能很慢。让用户傻等是糟糕的体验，所以 Workflow 支持把**中间事件流式回传**给用户：

```python
class TextEvent(Event):
    delta: str

class ProgressEvent(Event):
    msg: str

class MyWorkflow(Workflow):
    @step
    async def step_one(self, ctx: Context, ev: StartEvent) -> FirstEvent:
        ctx.write_event_to_stream(ProgressEvent(msg="Step one is happening"))
        return FirstEvent(first_output="First step complete.")

    @step
    async def step_two(self, ctx: Context, ev: FirstEvent) -> SecondEvent:
        llm = OpenAI(model="gpt-4o-mini", api_key=api_key)
        generator = await llm.astream_complete("...")
        async for response in generator:
            ctx.write_event_to_stream(TextEvent(delta=response.delta))
        return SecondEvent(second_output="...", response=str(response))
```

- `ctx.write_event_to_stream(...)`：往 Workflow 的事件流写一个事件；
- `llm.astream_complete(...)`：**异步流式**调用，每次拿到一段"delta"就立刻发出去。

**消费端**用 `run` 拿到的 handler，不再 `await` 而是直接迭代它的事件流：

```python
workflow = MyWorkflow(timeout=30, verbose=False)
handler = workflow.run(first_input="Start the workflow.")

async for ev in handler.stream_events():
    if isinstance(ev, ProgressEvent):
        print(ev.msg)
    if isinstance(ev, TextEvent):
        print(ev.delta, end="")

final_result = await handler
print("Final result = ", final_result)
```

按事件**类型**过滤是关键——Workflow 内部会发射大量事件，全部打印会噪音过大。

## 小结

到这里，你已经掌握了 Workflow 的全部基本拼图：

- 步骤 + 事件 = 基本骨架；
- 自定义 Event = 多步流转；
- 类型联合（`A | B`）= 分支与循环；
- `Context.send_event` + `collect_events` = 并发与汇集；
- `write_event_to_stream` + `stream_events` = 流式 UX。

下一课，你将把 **RAG** 接进这套 Workflow。
