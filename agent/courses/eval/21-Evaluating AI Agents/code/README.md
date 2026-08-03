## Course Outline
- **L0**: Introduction *(slides only)*
- **L1**: Evaluation in the time of LLMs *(slides only)*
- **L2**: Decomposing agents *(slides only)*
- **L3**: Lab 1: Building your agent *(notebook)*
- **L4**: Observing agents *(slides only)*
- **L5**: Lab 2: Tracing your agent *(notebook)*
- **L6**: Adding router and skill evaluations *(slides only)*
- **L7**: Lab 3: Adding router and skill evaluations *(notebook)*
- **L8**: Adding trajectory evaluations *(slides only)*
- **L9**: Lab 4: Adding trajectory evaluations *(notebook)*
- **L10**: Adding structure to your evaluations *(slides only)*
- **L11**: Lab 5: Adding structure to your evaluations *(notebook)*
- **L12**: Improving your LLM-as-a-judge *(slides only)*
- **L13**: Monitoring agents *(slides only)*
- **L14**: Conclusion *(slides only)*

## Sandbox
[Sandbox Link](https://s172-16-138-182p8888.lab-aws-staging.deeplearning.ai/lab/tree/SC-Arize-C1)

## 本地运行 (2026-08 本地化)

全量升级到最新稳定版栈（arize-phoenix 19 / phoenix-client 2 / phoenix-evals 3 / openai 2），
模型换 DeepSeek 兼容 API，每个 lab 一个 `main.py` 直接跑。原 notebook 保留作课程对照。

```bash
cd code
uv venv --python 3.12 .venv
uv pip install -p .venv/bin/python -r requirements.txt

# 终端 1: 起本地 Phoenix server (L5/L7/L9/L11 需要, UI 在 http://localhost:6006)
.venv/bin/python -m phoenix.server.main serve

# 终端 2: 逐课运行
cd L3  && ../.venv/bin/python main.py   # Lab 1: 构建数据分析 agent
cd L5  && ../.venv/bin/python main.py   # Lab 2: Phoenix tracing 埋点
cd L7  && ../.venv/bin/python main.py   # Lab 3: Router/Skill 评估 + 注解回写
cd L9  && ../.venv/bin/python main.py   # Lab 4: 轨迹收敛度实验
cd L11 && ../.venv/bin/python main.py   # Lab 5: 综合实验编排 (EDD v1/v2 对比)
```

配置在 `code/.env`（DeepSeek key/模型、Phoenix endpoint）。共享适配层在 `code/local_stack.py`。

### 新旧 API 对照（升级要点）

| 课程原版 (phoenix 7 / evals 0.x) | 本地化 (phoenix 19 / client 2 / evals 3) |
|---|---|
| `px.Client()` | `phoenix.client.Client()` (spans/datasets/experiments 资源化) |
| `px.Client().query_spans(SpanQuery()...)` | `Client().spans.get_spans_dataframe(query=...)`，`SpanQuery` 改从 `phoenix.client.types.spans` 导入，`select()` 不再支持改名（用 pandas rename） |
| `llm_classify(template, rails, OpenAIModel)` | `ClassificationEvaluator(llm=LLM(...), choices={label: score}) + evaluate_dataframe` |
| `px.Client().log_evaluations(SpanEvaluations(...))` | `evals.utils.to_annotation_dataframe` + `Client().spans.log_span_annotations_dataframe` |
| `phoenix.experiments.run_experiment(dataset, task)` | `Client().experiments.run_experiment(dataset=, task=, evaluators=)` |
| `@create_evaluator` 装饰器 | 普通函数即可（按参数名 input/output/expected 绑定） |
| `upload_dataset(dataframe=...)` | `Client().datasets.create_dataset(dataframe=...)` |

### DeepSeek 适配三坑

1. 不支持 `json_schema` response_format → agent 的结构化输出走 `json_object` + pydantic 校验；
   phoenix-evals 3 的分类器会自动降级到强制 tool calling（需坑 2 配合）
2. thinking 模式不支持强制 tool_choice → 所有调用注入 `extra_body={"thinking": {"type": "disabled"}}`
3. 长工具输出会把 messages 撑爆（网关 413）→ `local_stack.clip()` 截断工具返回