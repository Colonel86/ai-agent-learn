# L4：解析申请表并自动填写

本节目标：让 Agent **读取一份职位申请表（job application form）**，把要填写的字段抽出来转成 JSON，再为每个字段并发地查询简历 RAG，最后聚合成一份填好的表。

## 1. 用 LlamaParse 抽取表单字段

上一课里，我们给 LlamaParse 传过 `content_guideline_instruction`。这次再增加一个 `formatting_instruction`，让它直接吐出**带项目符号的字段列表**：

```python
from llama_parse import LlamaParse

parser = LlamaParse(
    api_key=llama_cloud_api_key,
    base_url=os.getenv("LLAMA_CLOUD_BASE_URL"),
    result_type="markdown",
    content_guideline_instruction="This is a job application form. Create a list of all the fields that need to be filled in.",
    formatting_instruction="Return a bulleted list of the fields ONLY."
)

result = parser.load_data("data/fake_application_form.pdf")[0]
print(result.text)
```

输出会是一行行 `- Field Name` 的纯净列表。

## 2. 让 LLM 把列表转成 JSON

LLM 很擅长把"**人类可读**"的格式翻译成"**机器可读**"的格式。给它一个明确的 schema 提示：

```python
from llama_index.llms.openai import OpenAI

llm = OpenAI(model="gpt-4o-mini")

raw_json = llm.complete(f"""
    This is a parsed form.
    Convert it into a JSON object containing only the list
    of fields to be filled in, in the form {{ fields: [...] }}.
    <form>{result.text}</form>.
    Return JSON ONLY, no markdown.
""")

fields = json.loads(raw_json.text)["fields"]
for field in fields:
    print(field)
```

要点：

- 用 `<form>...</form>` 这种**伪标签**包裹输入，能让 LLM 更稳定地识别边界；
- 显式叮嘱 **"Return JSON ONLY, no markdown"**，避免 LLM 给你加上 ` ```json ` 围栏导致 `json.loads` 报错。

## 3. 把表单解析接入 Workflow（第一版）

在上一课的 `RAGWorkflow` 上加一个 `parse_form` 步骤。新增两个事件：

```python
class ParseFormEvent(Event):
    application_form: str

class QueryEvent(Event):
    query: str
```

`set_up` 不再直接发射 `QueryEvent`，而是发射 `ParseFormEvent`：

```python
class RAGWorkflow(Workflow):
    storage_dir = "./storage"
    llm: OpenAI
    query_engine: VectorStoreIndex

    @step
    async def set_up(self, ctx: Context, ev: StartEvent) -> ParseFormEvent:
        if not ev.resume_file:
            raise ValueError("No resume file provided")
        if not ev.application_form:
            raise ValueError("No application form provided")

        self.llm = OpenAI(model="gpt-4o-mini")
        # ... 与 L3 相同：建立或恢复 index，构造 query_engine ...

        return ParseFormEvent(application_form=ev.application_form)

    @step
    async def parse_form(self, ctx: Context, ev: ParseFormEvent) -> QueryEvent:
        parser = LlamaParse(
            api_key=llama_cloud_api_key,
            result_type="markdown",
            content_guideline_instruction="This is a job application form. Create a list of all the fields that need to be filled in.",
            formatting_instruction="Return a bulleted list of the fields ONLY.",
        )
        result = parser.load_data(ev.application_form)[0]
        raw_json = self.llm.complete(
            f"... <form>{result.text}</form>. Return JSON ONLY, no markdown."
        )
        fields = json.loads(raw_json.text)["fields"]
        for field in fields:
            print(field)
        return StopEvent(result="Dummy event")  # 暂时收尾

    @step
    async def ask_question(self, ctx: Context, ev: QueryEvent) -> StopEvent:
        response = self.query_engine.query(
            f"This is a question about the specific resume we have in our database: {ev.query}"
        )
        return StopEvent(result=response.response)
```

到这一步，工作流已经会"识别出表单字段"，下一步要做的就是**为每个字段生成一个问题**。

## 4. 为每个字段生成问题并并发查询（第二版）

回忆 **L2** 的并发模式：一个步骤可以用 `ctx.send_event` 一次性发射多个事件，让下游 step **并行**执行，再用 `collect_events` 聚拢。

变化点：

- `QueryEvent` 增加 `field` 字段，记录这条查询对应的是哪个表单字段；
- 新增 `ResponseEvent`，承载每条查询的回答；
- `parse_form` 不再发 `StopEvent`，改为为每个字段 `send_event` 一个 `QueryEvent`，并把字段总数写进 Context；
- `ask_question` 由 `StopEvent` 改为发射 `ResponseEvent`；
- 新增 `fill_in_application` 步骤，用 `collect_events` 等齐所有 `ResponseEvent`，再交给 LLM 聚合。

```python
class ParseFormEvent(Event):
    application_form: str

class QueryEvent(Event):
    query: str
    field: str

class ResponseEvent(Event):
    response: str

class RAGWorkflow(Workflow):
    # ...

    @step
    async def parse_form(self, ctx: Context, ev: ParseFormEvent) -> QueryEvent:
        # ... 抽取 fields ...
        for field in fields:
            ctx.send_event(QueryEvent(
                field=field,
                query=f"How would you answer this question about the candidate? {field}"
            ))
        await ctx.set("total_fields", len(fields))
        return

    @step
    async def ask_question(self, ctx: Context, ev: QueryEvent) -> ResponseEvent:
        response = self.query_engine.query(
            f"This is a question about the specific resume we have in our database: {ev.query}"
        )
        return ResponseEvent(field=ev.field, response=response.response)

    @step
    async def fill_in_application(self, ctx: Context, ev: ResponseEvent) -> StopEvent:
        total_fields = await ctx.get("total_fields")
        responses = ctx.collect_events(ev, [ResponseEvent] * total_fields)
        if responses is None:
            return None  # 还没收齐，先什么都不做

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
        return StopEvent(result=result)
```

运行：

```python
w = RAGWorkflow(timeout=120, verbose=False)
result = await w.run(
    resume_file="data/fake_resume.pdf",
    application_form="data/fake_application_form.pdf",
)
print(result)
```

## 5. 结果观察与下一步

跑出来的结果是一份带编号的字段-答案列表，绝大多数字段都填得相当不错，**但有些不那么理想**——比如 `Portfolio` 字段，原文档里其实是一个链接，LLM 却列出了项目内容。

这就引出了下一课的主题：**Human in the Loop（人类介入）**，让用户**用自然语言反馈**指出不满意的字段，由 Agent 重新生成。

## 小结

- `set_up` → `parse_form` → 多个并发 `ask_question` → `fill_in_application` 是典型的**扇出 / 扇入（fan-out / fan-in）** 模式；
- 用 Context 存"**这一轮总共要等多少事件**"，搭配 `collect_events`，就能实现动态数量的并发；
- 用 LLM 把"项目符号 → JSON"，是把后续步骤变得**可编程**的常用技巧。
