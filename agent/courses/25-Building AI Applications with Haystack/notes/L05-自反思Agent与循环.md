# L05 自反思 Agent 与 Pipeline 循环

> 原始字幕：`subtitles/haystack_c1_L5.vtt`
> 配套代码：`code/Lesson_5.md`
> 关键能力：Pipeline 的 `max_loops_allowed` + Jinja `{% if %}` 模板

---

## 一、思想：让 LLM 自己审稿

任务：从文本里抽取实体（Person / Location / Date），并强制满足约束（类别名固定、不重复、空类别用空 list 等）。

**朴素做法**：一遍 LLM 调用 + 后处理。问题：约束多了 prompt 难写、解析难调。
**自反思做法**：LLM 第一遍抽 → Validator 检查 → 不合规则把"上一版结果 + 校验提示"再喂回给 LLM → 直到 LLM 自己输出 `DONE`。

---

## 二、关键拼图

### 2.1 Validator 组件：判定 + 分流

```python
@component
class EntitiesValidator:
    @component.output_types(entities_to_validate=str, entities=str)
    def run(self, replies: List[str]):
        if 'DONE' in replies[0]:
            return {"entities": replies[0].replace('DONE', '')}     # 出口①：终止
        else:
            print(Fore.RED + "Reflecting on entities\n", replies[0])
            return {"entities_to_validate": replies[0]}             # 出口②：回流
```

- 同一个 `run()` **根据条件返回不同 key** → 等同于"分支输出"。
- 哪个 key 被填充，连接到该 key 的下游才会被激活；另一支自然停下。
- 这正是 Haystack 实现循环的核心机制：**用输出端口的可选返回**控制图遍历。

### 2.2 Prompt 模板：Jinja `{% if %}` 区分两种角色

```jinja
{% if entities_to_validate %}
    Here was the text you were provided:
    {{ text }}
    Here are the entities you previously extracted:
    {{ entities_to_validate[0] }}
    Are these the correct entities?
    Things to check:
    - Categories must be exactly "Person", "Location", "Date"
    - No extra categories, no duplicates
    - Empty category → empty list
    If you are done say 'DONE' and return entities on next line.
    If not, return the best you can.
{% else %}
    Extract entities from the following text
    Text: {{ text }}
    Return as JSON: { "Person": [...], "Location": [...], "Date": [...] }
{% endif %}
```

> 同一个 prompt 模板**同时承担"第一次抽取"和"反思修订"两个角色**——靠 `{% if entities_to_validate %}` 区分。这是 Haystack 推荐的循环 prompt 模式。

---

## 三、拓扑：带环的 Pipeline

```
prompt_builder ──► llm ──► entities_validator
       ▲                          │
       │                          ├── entities (终点)
       └──── entities_to_validate ┘
```

```python
self_reflecting_agent = Pipeline(max_loops_allowed=10)

self_reflecting_agent.add_component("prompt_builder",      PromptBuilder(template=template))
self_reflecting_agent.add_component("entities_validator",  EntitiesValidator())
self_reflecting_agent.add_component("llm",                 OpenAIGenerator())

self_reflecting_agent.connect("prompt_builder.prompt",                   "llm.prompt")
self_reflecting_agent.connect("llm.replies",                             "entities_validator.replies")
self_reflecting_agent.connect("entities_validator.entities_to_validate", "prompt_builder.entities_to_validate")
```

调用：

```python
result = self_reflecting_agent.run({"prompt_builder": {"text": text}})
print(result['entities_validator']['entities'])
```

- 入参只给 `text` —— `entities_to_validate` 走回环路径。
- `max_loops_allowed=10` 是**硬上限**，防死循环；这是带环 Pipeline 的必备护栏。

---

## 四、架构取舍

- **为什么"DONE" 让 LLM 自己判？** —— LLM 是判定主体（理解约束），代码只做形式上的字符串识别。把"语义判定"与"流程控制"解耦，二者各自简单。
- **Validator 为什么不直接 raise 错误重试？** —— 重试需要把"上次错在哪"喂回去，错误信息是数据，不是异常；走数据流（端口）比走 exception 自然得多。
- **`max_loops_allowed` 该设多大？** —— 取决于任务收敛速度。实体抽取通常 2-3 轮内收敛；设 10 是给 LLM 抖动留余量，也防 prompt 写崩时一直转。
- **何时该上"自反思"？** —— 任务**有可机检的硬约束**（schema、格式、覆盖度），且一次生成达成率不够。如果约束模糊，反思反而会震荡。

---

## 五、与其他框架对照

| | Haystack | LangGraph | crewAI |
|---|---|---|---|
| 循环表达 | Component 选择性返回 + `max_loops_allowed` | 显式 Graph 的 conditional edge | Agent 之间消息传递 |
| 心智模型 | 数据流图 + 端口 | 状态机 | 多 Agent 协作 |

> 架构师视角：Haystack 的循环最"低耦合"——任何 Component 只要按需选择输出端口，整张图就有了反馈回路；不用引入 State 概念。

---

## 六、本节要点

- Pipeline 通过 **Component 条件性返回不同输出端口** 实现分支与循环，无需特殊原语。
- `Pipeline(max_loops_allowed=N)` 是带环 Pipeline 的安全闸。
- 用 Jinja `{% if %}` 让同一个 prompt 模板复用为"首次"+"反思"两种角色。
- 自反思适合有硬约束的结构化输出任务（实体抽取、JSON schema 校验等）。
