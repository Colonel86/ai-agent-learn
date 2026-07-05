# L6 · 构建工具调用 Agent 并封装 ResponsesAgent（Lab 2：agent.py）

> 课程：Governing AI Agents（DeepLearning.AI × Databricks）
> 本课任务：用 OpenAI SDK 构建 tool calling agent，把 Lab 1 注册在 Unity Catalog 的 UC function 挂成工具，并**包进 MLflow ResponsesAgent 接口**——为 L7 的评估与 Service Principal 部署备好 `agent.py`。

## 0. 本课目标与承接

L5 讲完概念（agent = LLM 大脑 + 工具 + system prompt，用 MLflow 与自定义评估指标走向 production ready），本课进 Lab 2 写代码。路线：**Lab 1 治理地基（已完成）→ Lab 2 `agent.py` 编排 → Lab 3 部署 notebook（用 Service Principal 凭据部署）**。

## 1. 前置一步：给 Service Principal 授权 Lab 文件夹

写代码前先回退一步做权限检查：进入存放全部数据/notebook 的文件夹 → **Share permissions** → 确认 Service Principal 已被加上。因为 L7 最终要以 Service Principal 的身份运行部署 notebook，它必须**先能读到这个文件夹**。

> **架构师视角**：这是"以非人类身份跑流水线"的通用前置——身份不仅要有**数据权限**（L4 的 views/functions GRANT），还要有**代码资产权限**（notebook 所在目录）。两者缺一个，部署都会在离产出最近的一步失败。CI/CD 里同理：机器账号对 repo 和对数据源的授权是两张独立的清单。

## 2. `agent.py` 依赖与 LLM 选择

```python
from databricks.sdk import WorkspaceClient
from databricks_openai import UCFunctionToolkit          # UC function → agent 工具
from databricks_openai import VectorSearchRetrieverTool  # 可选:做 RAG chatbot 时挂向量检索工具
from openai import OpenAI                                # 用 OpenAI SDK 编排
import mlflow

# 选一个 Databricks 原生托管、已启用 tool calling 的模型
LLM_ENDPOINT_NAME = "meta-llama-3.3-70b-instruct"
```

- LLM 可选 Databricks **原生托管**的 tool-calling 模型（本课用 Meta Llama 3.3 70B Instruct），也可**带自己的外部模型**（如自有 OpenAI key）；
- 想做 RAG，`VectorSearchRetrieverTool` 一行挂上向量检索。

## 3. SYSTEM_PROMPT 与 UC function 工具

```python
SYSTEM_PROMPT = """You are an HR Data Scientist and Analytics expert.
You have access to HR analytics tools that provide insights into
workforce performance, retention, and operational metrics.
..."""
# 结构三段:① 角色定位 ② 回答问题时的要求/反馈 ③ 可用工具清单

# Lab 1 已在 Unity Catalog 注册的用户自定义函数,直接声明为 agent 工具
UC_TOOL_NAMES = [
    "clientcare.hr_data.analyze_performance",   # 绩效分析
    "clientcare.hr_data.analyze_operations",    # 运营指标分析
]
```

工具就是 L4 里"建在匿名化 view 之上、注册进 Unity Catalog"的函数——**agent 拿到的不是表，而是治理过的函数**。想加向量库也可以在这里 easily enable。

> **对比 7-safety-guardrails.md**：SYSTEM_PROMPT 里写"你是 HR 分析专家、你有这两个工具"只是**软约束**（模型可被诱导偏离）；真正的硬边界在 Unity Catalog 权限层——agent 的身份根本 SELECT 不到裸表。7-safety-guardrails 的分层里这对应"prompt 层护栏 vs 系统层权限"：**prompt 决定 agent 想做什么，权限决定 agent 能做什么**，二者不可互替。

## 4. ToolCallingAgent：绑定 LLM 与工具，实现 ResponsesAgent 接口

`agent.py` 的收口：

```python
class ToolCallingAgent(ResponsesAgent):   # 实现 MLflow ResponsesAgent 接口
    def __init__(self, llm_endpoint, tools):
        ...                               # LLM 端点(大脑) + 工具(数据访问) 绑定

    def predict(self, request):           # 接口要求的方法之一
        ...                               # 包装既有 agent 的输出

    def predict_stream(self, request):    # 流式版本
        ...

AGENT = ToolCallingAgent(llm_endpoint=LLM_ENDPOINT_NAME, tools=TOOLS)
```

关键规则：

- 实现 `ResponsesAgent` 接口的类**必须有两个方法**：`predict` 和 `predict_stream`，它们包装既有 agent 的输出；
- **已有存量 agent？** 不用重写——直接用 ResponsesAgent 接口把它包一层即可；
- 框架无关：本课用 OpenAI SDK，但 Databricks 的 agent framework **兼容任意编排框架**——LlamaIndex、LangChain、纯 Python 都行（LangChain 版包装与多 agent 系统见官方文档）。

> **架构师视角**：ResponsesAgent 是"**部署契约**"——平台不关心你用什么框架写 agent，只要求暴露 `predict/predict_stream` 两个方法，换来的是统一的 logging、tracing、评估与 serving。这与 A2A 协议"对外统一接口、对内实现自由"是同一招：**在编排层之上再切一层稳定接口，框架选型就从架构决策降级为实现细节**（选型矩阵 2-frameworks 的"可替换性"判据）。

## 5. Playground 低代码路径：从试玩到生成 agent notebook

`agent.py` 也可以不手写——Playground 能"点"出来：

1. **选模型**：模型列表里带**工具 emoji** 标记的即已启用 tool calling（原生模型之外也可接入外部/自定义模型）；
2. **加工具**：直接选 UC functions——`clientcare.hr_data.analyze_operations`、`analyze_performance`；也可加 **Vector Search endpoints 或 MCP Servers**；
3. **填 system prompt**：正式版很长，试玩时放一小段看效果即可；
4. **试问**："tell me about performance" → 可见 LLM 调起 `analyze_performance` 函数并给出完整解释；问 operations 同理；**trace** 里能看到用了几个工具、总延迟；
5. **满意后点 Create agent notebook** → 生成 driver notebook。

driver notebook 与手写 `agent.py` 信息完全一致（LLM endpoint、system prompt、tools、ToolCallingAgent 类、MLflow logging），顶部的 **cell magic（`%%writefile`）跑一下就会重建出同一份 `agent.py`**。且这个 notebook 就是 Lab 3 要用的部署 notebook——唯一差别是 L7 会加自定义 evals。

> **对比 CrewAI 生产课的 enablement 治理**：CrewAI 课的思路是用模板/低代码让更多业务角色能造 agent，治理靠流程规范兜底；Databricks 的 Playground → notebook 路径把 enablement **内嵌进治理框架**——低代码入口选的工具本来就是 UC 注册的函数、生成的代码天然带 MLflow logging。判据：**enablement 工具生成的产物是否自动落在治理边界内**，落在内则规模化安全，落在外则每个低代码 agent 都是影子 IT。

## 6. 本课总结

| 要点 | 一句话 |
|---|---|
| 前置授权 | Service Principal 要先拿到 Lab 文件夹权限，才能跑部署 notebook |
| 工具来源 | agent 工具 = Unity Catalog 注册的 UC functions（治理过的函数，非裸表） |
| ResponsesAgent | 实现 `predict` + `predict_stream` 两方法即完成封装，存量 agent 包一层即可 |
| 框架无关 | OpenAI SDK / LangChain / LlamaIndex / 纯 Python 皆可，接口统一 |
| Playground | 低代码试玩 → Create agent notebook → `%%writefile` 重建 agent.py |

> **记忆点（引出 L7）**：`agent.py` 只是**定义**——它还没有被评估、没有版本、也没有自己的身份。L7 走完最后一公里：MLflow 评估（Correctness / Relevance / 自定义 safety guidelines）→ 注册进 Unity Catalog → **以 Service Principal 的身份**通过 Job 部署，然后在 Playground 里验证"问 SSN 拿不到、问部门拿得到"的治理闭环。

## 与我的资产映射

- 安全与护栏层：`agent/skills/agent-selection/7-safety-guardrails.md`（prompt 软约束 vs 权限硬边界的分层）
- 框架层：`agent/skills/agent-selection/2-frameworks.md`（ResponsesAgent 作为部署契约 → 框架可替换性判据）
- 面试包：`07-safety-guardrails`（"agent 不直接访问表，工具即治理断面"案例）
- [[project_selection_matrix]]
