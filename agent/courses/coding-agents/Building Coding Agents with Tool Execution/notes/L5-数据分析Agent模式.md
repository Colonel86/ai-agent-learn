# L5 · 数据分析 Agent 模式（数据注入沙箱 + 单工具多轮分析 + Context Stack 可视化）

> 课程：Building Coding Agents with Tool Execution（DeepLearning.AI × E2B）
> 本课任务：不加任何新工具，把 L4 的 coding agent 变成**数据分析师**——数据文件写进沙箱、系统提示告知数据位置，agent 靠现写 pandas/matplotlib 代码完成探索、聚合、绘图；再用 Gradio UI 的 Context Stack 面板看清多轮对话的上下文构成。

## 1. 数据注入：pokemon.csv → 沙箱 data.csv

数据分析 agent 的第一步不是加工具，而是**把数据确定性地放进执行环境**：

```python
from lib.utils import create_sandbox

sbx = create_sandbox()                    # L4 的缓存重连逻辑：存在就连、不存在才建

with open("pokemon.csv", "r") as f:       # 宿主读本地数据集
    content = f.read()
sbx.files.write("data.csv", content)      # 写入沙箱，统一命名为 data.csv
```

注意改名这个细节：不管用户上传什么文件，落到沙箱都叫 `data.csv`——系统提示里就能写死这个名字，agent 不用先找文件。

> **对比课程 12a 的确定性工程**：12a 的原则是"能确定性完成的步骤绝不交给 LLM"。这里数据装载走 `files.write`（宿主代码，零 token、零失败面），而不是给 agent 一个 upload 工具让它自己"决定"去装数据；LLM 只从"数据已就位"之后开始工作。管道式前处理 + agent 式分析，边界切在**可确定 / 需推理**的分界线上。

## 2. 系统提示改造：一段话完成"变身"

agent 本体（`lib/coding_agent.py`）、工具集、schema 与 L4 完全相同，唯一的差异在系统提示：

```python
system = """You are a senior python programmer. 
You must run the code using the `execute_code` tool.
The user has uploaded a data.csv.                    # 告知数据位置
You help the user understanding the data 
by creating interesting plots.                        # 设定角色任务：理解数据 + 出图
"""

tools = {"execute_code": execute_code}   # 仍然只有这一个工具（这次用 lib.tools 版本）
```

> **架构师视角**：这就是"数据分析 agent"作为一种**模式**而非一种产品的含义——`通用 coding agent + 环境注入（数据文件）+ 提示注入（数据位置与角色）= 领域 agent`。没有 pandas 工具、没有 plot 工具、没有 SQL 工具；`execute_code` 一个动作面覆盖全部分析操作，领域化的成本只是一次 `files.write` 加三行提示词。对比工具式路线（每种分析一个工具）：那条路每加一种分析要改代码发版，这条路的能力上限就是 Python 生态本身。

## 3. 多轮分析对话：messages 数组贯穿始终

分析是对话式的，关键是**同一个 `messages` 数组在多次调用间传递**，沙箱也复用同一个（变量和文件都还在）：

```python
messages = []                                    # 第一轮从空开始

query = "What is the data about?"
messages, usage = log(coding_agent,
    messages=messages, query=query,              # 每轮把上一轮的 messages 传回去
    client=client, system=system,
    tools_schemas=[execute_code_schema], tools=tools,
    max_steps=10, sbx=sbx)                       # 分析任务步数放宽到 10

query = "Can you aggregate the pokemons by type?"
messages, usage = log(coding_agent, messages=messages, query=query, ...)  # 第二轮带历史
```

两轮的实际表现：

- **"What is the data about?"**：agent 自己写 pandas 代码——`head()` 看样例、看全部列、做 summary——回答"这是一个 Pokémon 数据集"，并列出 weight / height / attack / speed 等属性；
- **"aggregate by type"**：因为带着历史，agent 知道"the pokemons"指什么，跑 groupby 后**直接用 markdown 表格**回复（bug、dark、dragon、electric、fairy…各类型汇总）——表格这种回复格式是模型自发选的，tool result 里的数据它自己排版。

顺带一提，`coding_agent` 内置了上下文压缩兜底：token 用量超过 60k×0.7 就把前 70% 的消息交给 `gpt-5-nano` 压成一个 `<state_snapshot>`，长分析会话不会撑爆窗口。

## 4. 机制细节：图片走 metadata 旁路，不进上下文

L5 用的是 `lib/tools.py` 的 `execute_code`（比 L4 notebook 内联版多一步关键处理）：

```python
def execute_code(sbx: Sandbox, code: str, language: str = "python") -> Execution:
    execution = sbx.run_code(code, language)
    metadata = {}
    for result in execution.results:
        if result.png:
            metadata["images"] = [result.png]   # base64 PNG 摘出，走旁路给 UI/logger 渲染
            result.png = None                   # 从 Execution 里抹掉
            result.chart = None
    return execution.to_json(), metadata        # 回给模型的 tool result 里不含图片字节
```

`log()` 侧配合：`function_call_output` 消息带 `_metadata`，发现 `images` 就 base64 解码 `display()`。下划线前缀字段在发给 LLM 前被 `clean_messages_for_llm` 剥掉。

> **架构师视角**：这是**双通道 tool result** 的教科书实现——"给模型看的"（结构化执行结果，供它判断成败与续写）与"给人看的"（PNG 渲染）分离。一张图的 base64 轻松几十万字符，塞进上下文一轮就爆窗口且对模型毫无信息量；模型其实只需要知道"图已生成"。同构于 Claude Code 工具输出的分页/截断设计：**上下文是最贵的总线，任何工具产物上总线前都要问一句——模型真的需要读它吗？**

## 5. Gradio UI 与 Context Stack：看见你的上下文

课程给了现成的聊天界面（`lib/ui.py`），传参与 `coding_agent` 一致：

```python
from lib.ui import ui

ui(coding_agent, messages,                # 可以带着 notebook 里聊过的历史进 UI
   client=client, system=system,
   tools_schemas=[execute_code_schema], tools=tools,
   max_steps=10, sbx=sbx).launch(share=True, height=800)
```

界面分两栏，右栏 **Context Stack** 是本课的点睛之笔——把 `messages` 数组画成一摞色块：

| 视觉编码 | 含义 |
|---|---|
| 色块高度 | 与该消息的 **token 数**成正比 |
| 蓝色 | system prompt |
| 绿色 | user 消息 |
| 紫色 | tool 调用与 tool 结果 |
| 黄色 | system message |

在 UI 里继续分析：问"最重的 Pokémon 是哪只"，右栏实时长出新的 user 块、`execute_code` 调用块，回答是 **Cosmoem 和 Celesteela，重量接近一吨**；agent 还主动提示"要不要画成图？"，追问"top 10 最重的柱状图"，它再跑一段 pandas + matplotlib，图直接渲染在聊天里。每一轮上下文长了多少、谁占大头（通常是紫色的 tool result），一眼可见。

> **对比 0-action-paradigm 的动作范式**：动作范式篇讲 JSON tool-calling 与 code-as-action 两条路线的取舍，本课是后者在数据分析域的完整实证——聚合、排序、绘图三类"操作"没有对应三个工具，全是 `execute_code` 里现生成的 pandas 代码。Context Stack 还暴露了这条路线的账单：它的紫色块（代码 + 执行结果）比 JSON 工具的参数块厚得多，**表达力换 token**，这正是需要第 4 节图片旁路和第 3 节自动压缩来对冲的原因。

## 6. Your Turn：unknown.csv 盲盒探索

收尾练习：同目录还有一个 `unknown.csv`（课程下载包里未附带，只在平台环境里有），内容完全未知。玩法与 pokemon 一样——新沙箱、写成 `data.csv`、清空 `messages`、开 UI——然后用自然语言让 agent 自己摸清这是什么数据。这个练习点破了本模式的真正价值：**分析流程对数据集零假设**，换数据不换代码。

## 7. 本课总结

| 要点 | 一句话 |
|---|---|
| 领域化公式 | 通用 coding agent + `files.write` 注入数据 + 系统提示告知位置/角色 = 数据分析 agent |
| 单工具分析 | 探索/聚合/绘图全部由 agent 现写 pandas/matplotlib 代码，经 `execute_code` 在沙箱执行 |
| 多轮状态 | `messages` 数组跨轮传递（对话记忆）+ 沙箱复用（变量与文件记忆），超限自动压缩成 state_snapshot |
| 图片旁路 | PNG 从 tool result 摘到 `_metadata`，UI 渲染给人看，不占模型上下文 |
| Context Stack | 消息按 token 高度、按角色着色可视化，上下文成本从抽象数字变成可观察对象 |

> **记忆点（引出 L6）**：数据分析 agent 的产出还只是"回答和图表"。L6 升级为 **Full Stack Agent**——用上 L4 铺垫的整套沙箱化文件工具与模板沙箱，生成并运行完整的复杂 Web 应用。

## 与我的资产映射

- 行动范式：`agent/skills/agent-selection/0-action-paradigm.md`（code-as-action 在分析域的实证 + "表达力换 token"的账单）
- 观测/eval：`agent/skills/agent-selection/5-observability-eval.md`（Context Stack 是最朴素的上下文观测面，比日志更直观的 token 归因）
- 记忆层：`agent/skills/agent-selection/6-memory.md`（messages 传递 + 压缩快照 = 最小可用的短期记忆管理）
- 面试包：`agent/interview/code-sandbox.md`、`agent/interview/jd-senior-agent-engineer/`（"如何防止工具输出撑爆上下文"高频题的实例答案）
- [[project_selection_matrix]]
