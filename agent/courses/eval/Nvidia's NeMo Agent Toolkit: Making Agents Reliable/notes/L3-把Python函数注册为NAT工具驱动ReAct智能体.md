# L3 · 把 Python 函数注册为 NAT 工具，驱动 ReAct 智能体

> 课程：Nvidia's NeMo Agent Toolkit: Making Agents Reliable（DeepLearning.AI × Nvidia）
> 本课任务：在 L2 那个"能跑、能 serve 成 REST API"的最小 NAT workflow 之上，把普通 Python 函数注册成 NAT 工具，把 workflow 从单次 LLM 调用升级成 **ReAct agent**，构建一个基于 NOAA 真实气候数据的分析助手。

## 0. 本课目标与路线

L2 的 workflow 只是一个简单聊天机器人（`_type` 是一次 LLM call）。本课让它"从聊天变成行动"：

1. 拿一组分析 NOAA 气候数据的**普通 Python 函数**；
2. 用 Pydantic 定义输入 schema、加工具描述，**注册**成 NAT 工具；
3. 打包成标准 Python package 并安装；
4. 在 YAML 配置里把 workflow 换成内置 `react_agent`，把工具挂上去，跑复杂查询。

数据集：NOAA 真实气温数据，**1210 条记录、1950–2025 年、横跨 10 国**（美/法/日/巴西等）。

## 1. ReAct agent：推理 + 行动的循环

ReAct = **Rea**soning + **Act**ing，是常见的 agentic 模式，本质是一个循环：

```
用户问题 → [Reason：LLM 思考下一步做什么]
              ↓
          [Act：形成并调用一个或多个 action（工具）]
              ↓
          [观察工具结果 → 继续 Reason]
              ↑______循环，直到 LLM 确认"已知最终答案"______↓
                                                     Final Answer
```

课程幻灯片上的 ReAct agent 挂了三个工具，**每个工具用完全不同的框架写成**——运行时 agent 自己决定用哪个、迭代到得出最终答案为止。这是 NAT 的核心卖点预告：框架无关的工具/agent 编排（L5 展开）。

## 2. 从 vanilla 函数到 NAT 工具：三件事

原始素材是普通 Python 函数，每个都**单一职责、返回 JSON**：

| 函数 | 职责 |
|---|---|
| `calculate_statistics(df, country=None)` | 计算气温基础统计量（country 可选，空则全球） |
| `filter_by_country` | 按国家过滤数据 |
| `find_extreme_years` | 找极端年份 |
| `create_visualization(plot_type, save_path)` | 生成可视化图并存成图片文件 |
| `list_countries` | 列出数据集覆盖的国家 |

把一个函数注册进 NAT，需要考虑三件事：

1. **输入 schema（Pydantic）**——告诉 LLM / agentic workflow 这个工具怎么调；
2. **配置类（Config）**——把 YAML 里的属性传进工具的通道；
3. **注册装饰器**——把工具接线进 NeMo Agent Toolkit。

以 `calculate_statistics` 为例（按口播摘录简化）：

```python
from pydantic import BaseModel, Field

# ① 输入 schema：LLM 依据它构造工具调用参数
class CalculateStatsInput(BaseModel):
    country: str = Field(
        description="Country name to filter by, leave empty for global statistics")

# ② 配置类：name 会成为 YAML 里引用它的 type
class CalculateStatisticsConfig(FunctionBaseConfig,
                                name="calculate_statistics"):
    pass          # 本工具不需要 YAML 配置；若需要，属性在这里声明

# ③ 注册装饰器：把工具接线进 NAT
@register_function(config_type=CalculateStatisticsConfig)
async def calculate_statistics_tool(config, builder):
    # config：YAML 里该工具的属性会注入到这里
    # builder：可从中拿 workflow 里定义的其他组件（LLM、retriever…）——本课不用，L5 会用
    df = load_climate_data()                     # 静态依赖在注册时准备好

    async def _wrapper(country: str = "") -> str:
        return calculate_statistics(df, country) # 真正干活的仍是原始 Python 函数

    yield FunctionInfo.create(                   # 向 NAT 描述这个函数怎么跑
        fn=_wrapper,
        input_schema=CalculateStatsInput,
        description="...")                       # 描述决定 agent 会不会选它
```

有一点样板代码（async 包装 + yield `FunctionInfo`），但 **NAT CLI 的 generate 命令能生成大部分样板**。

> **架构师视角**：这套注册协议里真正面向 LLM 的只有两样——`input_schema` 和 `description`，它们就是工具的"招牌"；Config 类和 builder 则面向运维——把工具参数化的部分抽到 YAML。**面向模型的契约**和**面向配置的契约**从第一行代码就分开，这比 LangChain `@tool` 只吐 docstring 的做法在生产上更可控。

## 3. 打包与脚手架：就是标准 Python 项目

打包**没有任何 NAT 特有的东西**：一个 `pyproject.toml`，给项目起名、声明 entry points，然后 `pip / uv pip install`。脚手架也有 CLI 一键生成：

```bash
nat workflow create climate_assistant   # 生成整套标准 Python 项目结构
nat workflow create --help              # 查看更多选项
```

## 4. 配置文件：workflow 从 LLM call 换成 react_agent

```yaml
llms:
  climate_llm: ...                # L2 定义过的 LLM，原样保留

functions:                        # 新增节：可供 agent 使用的工具
  calculate_statistics:
    _type: simple_tool_demo/calculate_statistics   # package_name/tool_name，NAT 靠它定位工具
    description: ...              # 可在此覆盖工具描述

workflow:
  _type: react_agent              # L2 是简单 LLM call，现在换成内置 ReAct agent
  tool_names: [calculate_statistics]   # 从上面 functions 节引用
  llm_name: climate_llm
  verbose: true                   # 打印详细的工具调用过程
```

引用规则记一条：**工具在 config 里以 `package_name/tool_name` 引用**。

## 5. 运行：看 ReAct 循环真实发生（包括踩坑）

```bash
nat run --config_file config.yml \
        --input "What is the global temperature trend per decade?"
```

verbose 输出完整展示了循环——包括一次真实的失败重试：

1. agent 推理后决定调 `calculate_statistics`；
2. 第一次调用**报错**：`no data found for country None`（口播原话："这是我们以后可以改进 agent 的地方"）；
3. agent 自己意识到应该传空字符串，**重试**成功；
4. 得出最终答案：**全球每十年升温 0.241°C**。

## 6. 挂满五个工具 + 迭代/重试上限

完整配置把五个工具全部注册进 `functions` 并传给 react_agent，另加两个小改动：

```yaml
workflow:
  _type: react_agent
  tool_names: [calculate_statistics, list_countries, filter_by_country,
               find_extreme_years, create_visualization]
  llm_name: climate_llm
  max_iterations: 5     # 工具多了，ReAct 可能要多轮迭代
  max_retries: 2        # 工具调用出错时允许重试
```

四组由易到难的查询验证多工具协作：

| 查询 | agent 行为 |
|---|---|
| 全球每十年升温趋势 | 单工具：`calculate_statistics` |
| 法国气候分析 | 多工具串联：`filter_by_country` → `calculate_statistics(France)` → LLM 汇总各工具的 JSON 成最终答案 |
| 哪些国家升温最快（要图） | `create_visualization` → 存出 top-5 国家升温趋势 PNG |
| 加拿大 vs 巴西谁升温快 + 全球趋势图 | 逐国 `calculate_statistics`，**中途重试了几次**，最终出图 + 给出结论 |

口播还点了一句关键伏笔：**config 文件不只是跑 agent 的——它同时承载 telemetry（OpenTelemetry tracing）和 evaluation 配置**，防止 agent 随时间回归。这正是 L4、L6 的主题。

> **对比 5-observability-eval.md 的子决策 3（配置/版本化）**：NAT 把工具清单、LLM 选择、`max_iterations`/`max_retries`、telemetry、eval 全收进一个 YAML——正是选型页说的"把 prompt·schema·模型版本当**代码资产**"路线的框架内置实现。代价同页也写了：这是一种软锁——config schema 是 NAT 私有的；收益是"换工具组合 = 改配置不改代码"，实验迭代成本极低。

> **架构师视角**：注意 `max_iterations: 5` 和 `max_retries: 2` 出现的位置——它们不在代码里，而在**配置**里。ReAct 的失控模式就是无限循环烧 token，把"预算上限"做成一等配置项，是"Making Agents Reliable"这门课标题的第一次落地：可靠性先从**给循环设围栏**开始，然后才是 L4 的观测和 L6 的评估。

## 7. 本课总结

| 要点 | 一句话 |
|---|---|
| ReAct agent | Reason → Act → 观察的循环，直到得出最终答案；NAT 内置 `react_agent` 类型 |
| 工具注册三要素 | Pydantic 输入 schema + Config 类（YAML 通道）+ `register_function` 装饰器 |
| FunctionInfo | `yield FunctionInfo(fn, input_schema, description)`，description 决定 agent 选不选 |
| 引用约定 | config 里 `package_name/tool_name`；打包就是标准 pyproject.toml |
| 脚手架 | `nat workflow create` 生成样板，手写只为理解原理 |
| 可靠性围栏 | `max_iterations` / `max_retries` 写进配置，防循环失控 |

> **记忆点（引出 L4）**：本课的 agent 已经"能干活"——但第 5 节那次 `country None` 报错重试，我们是靠 verbose 日志肉眼看到的。工具一多、循环一深，肉眼就不够了：agent 可能**答案正确但过程在空转烧 token**。L4 用几行配置接入 Phoenix tracing，把每次 LLM call、每次工具调用、token 和延迟全部变成可观测数据，抓出一个"正确但低效"的真实案例。

## 与我的资产映射

- 工具层选型：`agent/skills/agent-selection/4-tools.md`（工具描述/schema 设计——NAT 的 `FunctionInfo` 是又一种工具契约形态，可与 MCP、LangChain `@tool` 对照）
- 观测·eval 层：`agent/skills/agent-selection/5-observability-eval.md`（子决策 3 配置/版本化——NAT YAML 是框架内置实现）
- 课程 10-MCP：同为"把函数暴露给 agent"，MCP 是跨进程协议、NAT 注册是进程内装饰器，选型时先分清边界在哪
- [[project_selection_matrix]]
