# L2 · 最小 YAML 工作流与 nat serve 部署

> 课程：Nvidia's NeMo Agent Toolkit: Making Agents Reliable（DeepLearning.AI × Nvidia）
> 本课任务：创建并运行第一个 NAT workflow——最小 YAML 配置（llms + workflow 两段）→ `nat run` 跑通 → `nat serve` 变成 OpenAI 兼容 REST API → 接上 chatbot UI。展示 NAT 如何把生产能力带给哪怕最简单的 workflow。

## 0. 本课路线

NAT CLI 让你能快速运行 Agent，并把它 serve 成可被其他服务消费的 API。本课三步：**① 建一个简单但 production-ready 的 NAT agent → ② 用 NAT CLI 把它 serve 成 API → ③ 连上 UI 看它运行**。

## 1. 配置文件：NAT workflow 的心脏

NAT agent workflow 的核心是一个**简单 YAML 配置文件**，让我们能快速改变 Agent 的运行方式。最小示例只有两个顶层属性：

- **`llms`**：定义并配置如何连接大语言模型——本课连的是 NVIDIA NIM 容器，也可以是 OpenAI、Gemini 等；
- **`workflow`**：定义 Agent 做什么——示例里是 `react_agent`，引用下方定义的 LLM。

配置可简可繁：可以包含 evaluation 信息、observability 信息、给 Agent 定义多个工具，还有 retrievers / rerankers 等特性；也可以就像本课这样，一个 workflow 加几个 llms。

## 2. NAT CLI 命令一览

| 命令 | 作用 |
|---|---|
| `nat run` | 用单个输入跑一遍 workflow |
| `nat serve` | 对同一份配置文件启动 API server |
| `nat eval` | 跑评估（可进 CI/CD，也可自己手动跑） |
| `nat optimize` | 检查并优化 workflow（超参调优） |
| `nat validate` | 校验 YAML 配置是否合法 |

> **架构师视角**：五个动词共享**同一份配置文件**——run/serve/eval/optimize 只是同一 workflow 的不同"打开方式"。这是 config driven 的直接红利：开发（run）、上线（serve）、回归（eval）、调优（optimize）之间零改写，配置文件成为跨环节的单一事实源（single source of truth）。对比手写方案：serve 要包 FastAPI、eval 要另写 harness，每个环节一套代码。

## 3. 动手：最小配置（chat_completion 版）

notebook 里先安装（`pip install` NeMo Agent Toolkit + LangChain 依赖；课程环境已装好），然后写配置。按口播摘录简化：

```yaml
llms:                                   # 可定义多个 LLM，这里只需一个
  climate_llm:
    _type: nim                          # 类型决定如何连 LLM 提供方(openai/google/…)
                                        # nim = NVIDIA 推理容器
    model_name: meta/llama-3.1-70b-instruct
    base_url: ...                       # 告诉它调用哪里
    api_key: ...                        # 类型不同所需属性不同(如 OpenAI 需 API key)
    temperature: 0.7
    max_tokens: 2048

workflow:
  _type: chat_completion                # 内建类型:简单的输入→LLM→输出;也可自建类型
  llm_name: climate_llm                 # 引用上面定义的 LLM
  system_prompt: |
    You are a knowledgeable climate science assistant.
```

运行时 NAT 读取这份配置 → 加载 `chat_completion` workflow 类型 → 创建我们定义的 LLM 并注入该类型 → 把输入与 system_prompt 组合后运行，给出输出。

## 4. nat run：三问一个"裸 LLM"

```bash
nat run --config_file config.yml \
        --input "What is the difference between weather and climate?"
```

启动日志能看到配置概要（Number of LLMs = 1），然后是 workflow result。三次提问的结果：

| 问题 | 结果 |
|---|---|
| 天气 vs 气候的区别 | 答得不错——通识问题 |
| 工业化以来全球均温升了多少 | 有输出 |
| 需要真实数据分析的具体问题 | LLM 尽力了，但数字很可能不对 |

**暴露的局限**：这个 Agent 只是一次 LLM 调用，没有任何外部数据访问，只有训练时的通识。它虽然引了一些来源，但来源过时，而且可能是幻觉。

## 5. nat serve：一份配置变成 OpenAI 兼容 API

生产中直接在终端跑 `nat serve --config_file config.yml`（notebook 环境里只能用 subprocess 包一层）。`nat run` 是单输入单跑；`nat serve` 把同一 agentic workflow 变成**自包含 API**。

测试用标准 `requests` 库——如果你熟悉 OpenAI API 的 chat completions 端点，这里会非常眼熟：

```python
import requests

resp = requests.post(
    "http://localhost:8000/v1/chat/completions",   # OpenAI 兼容端点
    json={
        "messages": [{"role": "user",
                      "content": "What causes El Niño and how does it affect global weather?"}],
        "stream": False,                            # 不流式,拿自包含 JSON
    },
)
if resp.status_code == 200:
    # 按 OpenAI 兼容格式解析: choices → 第一个 choice → message → content
    print(resp.json()["choices"][0]["message"]["content"])
else:
    print(resp.text)                                # 出错则打印错误
```

跑通：拿到 200，返回对 El Niño 这一复杂天气现象的描述。

> **对比 9-serving-deployment.md**：`nat serve` 落在选型表的**同步请求-响应形态**（也支持 stream 开关），且直接对齐 OpenAI 兼容协议——这一步等于免费拿到"最轻起步"阶梯的第一级：任何会调 OpenAI API 的客户端/网关/UI 都能即插即用。选型笔记里手搓这级要自己包 FastAPI + 定协议；NAT 把协议决策（用 OpenAI 兼容）也一并替你做了——省事，但也意味着接受它的协议约定。

## 6. 接上 UI：chat 界面对话 agentic workflow

NAT 的 API 可以被**任何 UI** 消费，同时官方自带一个 production ready 的 NeMo Agent Toolkit UI（notebook 里展示复杂，课程用 `ui_manager` 辅助类拉起；后续课程再深入，本课只是快速一瞥）。

UI 能力与常见 chatbot UI 类似：新建会话、搜索历史会话、**连接 MCP servers**、导入/导出数据等。当前它连着我们刚建的 simple climate assistant。发一条 "What's the weather like in Florida?"——Agent 没有接地（grounded）到任何真实数据集，只能从 LLM 知识里给出佛罗里达天气的泛泛信息，并附上追问建议以便继续对话。Agent 虽简单，但盖上 UI 后与 agentic workflow 交互的工具立刻强大起来——课程系列 notebook 最终会建成能就多年气候数据深入问答的强大气候+数学 Agent。

最后停掉 server，为下一个 notebook 清理环境。

## 7. 本课总结

| 要点 | 一句话 |
|---|---|
| 配置即心脏 | 最小 YAML = `llms` + `workflow` 两个顶层属性，可按需长出 tools/eval/observability |
| LLM 声明 | `_type` 决定连接方式与所需属性（nim/openai/google…），换供应商改配置不改码 |
| chat_completion | 内建 workflow 类型：输入 + system_prompt → LLM → 输出 |
| CLI 五动词 | run / serve / eval / optimize / validate，共享同一份配置 |
| OpenAI 兼容 serve | localhost:8000 `/v1/chat/completions`，choices[0].message.content 解析 |
| 裸 LLM 局限 | 无外部数据、来源过时、可能幻觉——需要真实数据的问题答不可靠 |

> **记忆点（引出 L3）**：本课的气候助手只是"会聊天的 LLM"，碰到需要真实数据的问题就露馅。L3 把 workflow 升级为 **ReAct agent**：注册 Python 函数为工具、用 **Pydantic 定义输入 schema**、写好工具描述让 Agent 会挑工具——从 simple chatbot 变成对 NOAA 气候数据采取"智能的数据驱动行动"的 Agent。

## 与我的资产映射

- 部署层：`agent/skills/agent-selection/9-serving-deployment.md`（同步/流式形态 + OpenAI 兼容协议 = 最轻起步第一级）
- 可观测/评估层：`agent/skills/agent-selection/5-observability-eval.md`（子决策 3：本课的 YAML 就是将来 eval 对照实验的版本化单元）
- 工具层预告：`agent/skills/agent-selection/4-tools.md`（L3 的函数注册 + Pydantic schema 对应这层）
- [[project_selection_matrix]]
