# Building and Evaluating Data Agents · 本地化

课程原版 (Snowflake + TruLens + DeepLearning.AI): 多 Agent 工作流跑在
o3/gpt-4o + Snowflake Cortex (Analyst text2sql + Search 检索) + Tavily 上,
TruLens 连 Snowflake connector。这些云依赖(课程方账号/token)本地均不可用。

## 本地化替换表

| 课程原版 | 本地化 | 位置 |
|---|---|---|
| o3 (json_object) / gpt-4o | DeepSeek (thinking disabled; planner/executor 走 json_object) | `local_stack.make_llm` |
| Snowflake Cortex Agent | 本地数据 agent: text2sql→sqlite 合成 deals 表 + fastembed 检索合成会议纪要 | `sales_data.py` + `workflow.py` |
| Tavily 搜索 | ddgs (DuckDuckGo, 免 key), 失败回退内置结果 | `workflow.web_search` |
| langchain_experimental PythonREPL | 本地 exec 实现 | `workflow.python_repl_tool` |
| TruLens 2.2 + Snowflake connector | TruLens 2.10 + 本地 sqlite (`local_demo.sqlite`, 不碰课程自带 default.sqlite) | 各课 main.py |
| trulens git 分支依赖 (GPA feedback) | 2.10 正式版已内置 GPA 四件套 | `evals.py` |

合成数据设计: 8 条 deals(3 条 pending) + 5 篇会议纪要(刻意埋「监管/合规」共同主题),
支撑课程的演示 query(pending deals + 监管变化 / 纪要共同主题)。

## 运行

```bash
cd code
uv venv --python 3.12 .venv
uv pip install -p .venv/bin/python -r requirements.txt

cd L2 && ../.venv/bin/python main.py   # 多 Agent 工作流 (planner/executor/web/chart)
cd L3 && ../.venv/bin/python main.py   # 数据 agent (text2sql + 纪要检索)
cd L4 && ../.venv/bin/python main.py   # TruLens 记录 + RAG Triad
cd L5 && ../.venv/bin/python main.py   # GPA 四种失败模式 + trace 级评估
cd L6 && ../.venv/bin/python main.py   # 内联评估 + 计划 prompt 改写, v1/v2 对比
```

## 已知坑 (DeepSeek + trulens 2.10)

1. trulens 对未知模型默认试 structured output → DeepSeek 返回纯文本, ValidationError
   白烧重试 → `local_stack.make_tru_provider` 子类声明不支持, 走文本解析
2. OTel tracing 模式下 feedback 只能 WITH_APP_THREAD(后台线程) → main.py 轮询
   records 直到 feedback 列填满再打印
3. deepseek 高峰期偶发 503 Service is too busy → ChatOpenAI max_retries=6
4. nltk 3.10 安全检查会拦「CWD 子目录里的模块」: 从 code/ 目录跑 python 会误伤
   .venv 里的 regex → 一律从各课子目录运行 (main.py 的既定运行方式)
5. langgraph 1.x 校验 Command[Literal[...]] 目标节点 → 图必须包含全部节点,
   L2 用 enabled_agents 排除数据 agent 而非删节点
6. OTel 模式下 trace 级 GPA feedback 由后台线程算, 脚本场景完成时机不可控
   (同一代码三轮跑出三种完成度), `retrieve_feedback_results` 又只读旧 ORM 表(空)
   → L6 改为从消息轨迹构造 trace 文本、同步调 provider 的 GPA 方法(确定性),
   TruGraph 只负责记录与内联评估; L4/L5 单 recorder 场景轮询仍可用
