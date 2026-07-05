# L5：Human in the Loop（人类反馈循环）

本节目标：让 Agent **暂停**工作流，把已经填好的表单交给人查看，**用自然语言**给出反馈，Agent 把反馈纳入后再重跑——直到人类满意为止。

> LLM 很强，但**用来增强人类、而非替代人类**才是最佳实践。

## 1. 设计：要新增哪些零件

相对于上一课，新增 4 个变化：

1. 引入两个新的**特殊事件**：`InputRequiredEvent` 和 `HumanResponseEvent`——它们专门用于让工作流**暂停 / 接收外部输入**；
2. 把原来塞在 `parse_form` 里的两件事拆开：表单解析只做一次（结果存进 Context），**生成问题**变成独立的 `generate_questions` 步骤——这样反馈循环只需要回到"重新生成问题"，而不必每次都重新解析；
3. `fill_in_application` 发射 `InputRequiredEvent` 触发暂停；外部代码捕获后，用 `send_event` 把人类回复包成 `HumanResponseEvent` 喂回去；
4. 新增 `get_feedback` 步骤，**让 LLM 判断反馈是"OKAY"还是"FEEDBACK"**，决定停止还是回到 `generate_questions`。

新增的事件类型：

```python
from llama_index.core.workflow import InputRequiredEvent, HumanResponseEvent

class ParseFormEvent(Event):
    application_form: str

class QueryEvent(Event):
    query: str
    field: str

class ResponseEvent(Event):
    response: str

class FeedbackEvent(Event):
    feedback: str

class GenerateQuestionsEvent(Event):
    pass
```

## 2. 拆出 `parse_form` 和 `generate_questions`

`parse_form` 现在只负责解析表单、把字段列表存进 Context，然后发射 `GenerateQuestionsEvent`：

```python
@step
async def parse_form(self, ctx: Context, ev: ParseFormEvent) -> GenerateQuestionsEvent:
    parser = LlamaParse(
        result_type="markdown",
        content_guideline_instruction="This is a job application form. ...",
        formatting_instruction="Return a bulleted list of the fields ONLY."
    )
    result = parser.load_data(ev.application_form)[0]
    raw_json = self.llm.complete(
        f"... <form>{result.text}</form>. Return JSON ONLY, no markdown."
    )
    fields = json.loads(raw_json.text)["fields"]

    await ctx.set("fields_to_fill", fields)
    return GenerateQuestionsEvent()
```

`generate_questions` 同时接收 `GenerateQuestionsEvent` **或** `FeedbackEvent`——这就是反馈循环的入口：

```python
@step
async def generate_questions(
    self, ctx: Context, ev: GenerateQuestionsEvent | FeedbackEvent,
) -> QueryEvent:
    fields = await ctx.get("fields_to_fill")
    for field in fields:
        question = f"How would you answer this question about the candidate? <field>{field}</field>"
        ctx.send_event(QueryEvent(field=field, query=question))
    await ctx.set("total_fields", len(fields))
    return
```

## 3. 让工作流暂停：`InputRequiredEvent`

`fill_in_application` 收齐答案后，**不再直接 `StopEvent`**，而是把结果暂存到 Context，再发一个 `InputRequiredEvent`：

```python
@step
async def fill_in_application(
    self, ctx: Context, ev: ResponseEvent,
) -> InputRequiredEvent:
    total_fields = await ctx.get("total_fields")
    responses = ctx.collect_events(ev, [ResponseEvent] * total_fields)
    if responses is None:
        return None

    responseList = "\n".join(
        "Field: " + r.field + "\nResponse: " + r.response for r in responses
    )
    result = self.llm.complete(f"""
        You are given a list of fields in an application form and responses to
        questions about those fields from a resume. Combine the two into a list of
        fields and succinct, factual answers to fill in those fields.

        <responses>
        {responseList}
        </responses>
    """)

    await ctx.set("filled_form", str(result))

    return InputRequiredEvent(
        prefix="How does this look? Give me any feedback you have on any of the answers.",
        result=result,
    )
```

`InputRequiredEvent` 不会被任何 step 直接接住——这一步**没有下游 step 等它**。`HumanResponseEvent` 同样不会在 Workflow 内部产生，**必须从外部送进来**。

`get_feedback` 步骤等的就是这个 `HumanResponseEvent`：

```python
@step
async def get_feedback(
    self, ctx: Context, ev: HumanResponseEvent,
) -> FeedbackEvent | StopEvent:
    result = self.llm.complete(f"""
        You have received some human feedback on the form-filling task you've done.
        Does everything look good, or is there more work to be done?
        <feedback>
        {ev.response}
        </feedback>
        If everything is fine, respond with just the word 'OKAY'.
        If there's any other feedback, respond with just the word 'FEEDBACK'.
    """)
    verdict = result.text.strip()
    print(f"LLM says the verdict was {verdict}")
    if verdict == "OKAY":
        return StopEvent(result=await ctx.get("filled_form"))
    else:
        return FeedbackEvent(feedback=ev.response)
```

注意这里巧妙地**让 LLM 来判断意图**，比规则匹配灵活很多——用户输入"That's great"、"看着不错"、"行了"等等都能被识别为 OKAY。

## 4. 在外部驱动循环

回想 L2 里我们用过 `handler.stream_events()` 接收 `ProgressEvent` / `TextEvent`。`InputRequiredEvent` 一样是事件流里的事件，外层代码这样接它：

```python
w = RAGWorkflow(timeout=600, verbose=False)
handler = w.run(
    resume_file="data/fake_resume.pdf",
    application_form="data/fake_application_form.pdf",
)

async for event in handler.stream_events():
    if isinstance(event, InputRequiredEvent):
        print("We've filled in your form! Here are the results:\n")
        print(event.result)
        response = input(event.prefix)  # 从键盘读取
        handler.ctx.send_event(
            HumanResponseEvent(response=response)
        )

response = await handler
print("Agent complete! Here's your final result:")
print(str(response))
```

`handler.ctx.send_event(HumanResponseEvent(...))` 就是把"外部输入"塞进 Workflow 的方式。

## 5. 真正使用反馈：把反馈写进每个 question

第一版的循环虽然跑通了，但 LLM 收到的问题其实没变，所以输出也不会改进。修改 `generate_questions`，**当事件上挂着 `feedback` 字段时**（也就是来自 `FeedbackEvent`），把反馈追加到每一个问题里：

```python
@step
async def generate_questions(
    self, ctx: Context, ev: GenerateQuestionsEvent | FeedbackEvent,
) -> QueryEvent:
    fields = await ctx.get("fields_to_fill")
    for field in fields:
        question = f"How would you answer this question about the candidate? <field>{field}</field>"

        if hasattr(ev, "feedback"):
            question += f"""
                \nWe previously got feedback about how we answered the questions.
                It might not be relevant to this particular field, but here it is:
                <feedback>{ev.feedback}</feedback>
            """

        ctx.send_event(QueryEvent(field=field, query=question))
    await ctx.set("total_fields", len(fields))
    return
```

这是一种**朴素但有效**的做法——反馈被**广播**给每个字段，由 LLM 自己判断和当前字段是否相关（提示语里也明确告诉它"可能与本字段无关"）。**Laurie 也提示**：更精细的 Agent 会**只把反馈作用到相关字段**上，这就是你可以自己扩展的方向。

## 6. 跑一次完整循环

跑起来后：

1. 第一轮：`Portfolio` 字段被错误地列成项目清单；
2. 你输入"Portfolio should be a URL"；
3. LLM 判定为 `FEEDBACK`，工作流回到 `generate_questions`，把反馈注入每个问题再跑一轮；
4. 第二轮：`Portfolio` 已变成 URL；
5. 你输入"That's great"，LLM 判定为 `OKAY`，发射 `StopEvent` 返回最终结果。

## 小结

人在回路的关键技巧：

- **特殊事件 + 外部 send_event**：用 `InputRequiredEvent` / `HumanResponseEvent` 把工作流变成"可暂停可续跑"的对象；
- **Context 持久化中间产物**：`fields_to_fill`、`filled_form` 都存在 Context 里，避免在循环中反复重做昂贵的步骤；
- **让 LLM 解释意图**：用 LLM 把模糊的人类反馈映射到明确的内部状态（`OKAY` / `FEEDBACK`）。

下一课只剩一个"好玩"的升级——把键盘输入换成**语音输入**。
