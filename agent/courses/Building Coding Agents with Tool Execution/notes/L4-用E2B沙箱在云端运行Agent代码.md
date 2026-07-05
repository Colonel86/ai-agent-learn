# L4 · 用 E2B 沙箱在云端运行 Agent 代码（Sandbox 生命周期 + execute_code 上云）

> 课程：Building Coding Agents with Tool Execution（DeepLearning.AI × E2B）
> 本课任务：把 L2 里"本地 exec 执行 LLM 生成代码"的危险做法，替换成 **E2B 云端沙箱**——学会 Sandbox 的创建/执行/列举/查询/文件系统全套 API，然后只改一个 `execute_code` 函数，agent 就获得了安全且可扩展的云端执行能力。

## 0. 本课目标与路线

L3 对比过工具执行环境的几条路线（本地 / 容器 / 云沙箱），本课落地云沙箱这条：先把 E2B Sandbox 当"远程 Jupyter"玩一遍（跑代码、画图、建文件、起网站），再把它接进 L2 的 agent loop。路线：**① Sandbox API 速成 → ② 生命周期管理 → ③ 文件系统与网站 → ④ 替换 execute_code → ⑤ 实战（骰子/文件/Snake 游戏）**。

技术栈：`e2b_code_interpreter`（Sandbox SDK）+ `openai`（Responses API）+ 课程自带 `lib/`（coding_agent、工具 schema、日志）。

## 1. Sandbox 速成：create / run_code / Execution

创建沙箱只要一个类方法，跑代码只要传字符串：

```python
from e2b_code_interpreter import Sandbox

sbx = Sandbox.create(timeout=60 * 60)   # timeout 单位秒：沙箱存活 1 小时后自动销毁
sbx.run_code("print('hello world')")    # 返回 Execution 对象
```

`Execution` 对象可以类比**一个 notebook cell 的输出**，有两条通道：

- `logs`：stdout/stderr——`print('hello world')` 出现在这里；
- `results`：表达式返回值——`sbx.run_code("a=5\na")` 时 `5` 出现在 `results` 数组里（就像 cell 最后一行表达式的显示值）。

E2B 支持多语言，默认 Python，一个参数切换：

```python
sbx.run_code("console.log('Hello, world!')", language="javascript")
```

画图也是同一条路：跑一段 matplotlib 代码，图以 **base64 PNG** 出现在 `results` 里，宿主侧解码显示：

```python
execution = sbx.run_code(code)   # code 里是 plt.scatter(...) + plt.show()
display(Image(data=base64.b64decode(execution.results[0].png)))  # 沙箱产物取回本地渲染
```

## 2. 生命周期管理：list / metadata / SandboxQuery / 缓存重连

沙箱是有生命周期的云资源，SDK 给了完整的管理面：

```python
running_sandboxes = Sandbox.list().next_items()      # 分页列出所有活着的沙箱
sbx_info.metadata / .sandbox_id / .started_at / .template_id   # 每个沙箱的关键字段

# 创建时打 metadata 标签，之后可按标签查询
sbx = Sandbox.create(metadata={"name": "find me!"})
Sandbox.list(SandboxQuery(metadata={"name": "find me!"},
                          state=[SandboxState.RUNNING]))  # 只要运行中的
```

沙箱会超时死掉，课程封装了 `create_sandbox()`（`lib/utils.py`）实现"**不存在就建、存在就重连**"：

```python
def create_sandbox(template=None, overwrite=False, **kwargs):
    name = 读取或生成本地缓存文件 sbx.cache 里的唯一名字   # uuid 落盘，跨 cell/跨会话稳定
    running = Sandbox.list(SandboxQuery(metadata={"name": name},
                                        state=[SandboxState.RUNNING])).next_items()
    if running:
        return Sandbox.connect(running[0].sandbox_id)     # 🔌 重连，不重建
    return Sandbox.create(timeout=60*60, metadata={"name": name}, ...)  # 🚀 新建并打标签
```

> **架构师视角**：这三件套（timeout、metadata 标签、query+reconnect）就是沙箱的**资源治理面**。沙箱按存活时长计费，timeout 是成本的硬闸门；metadata 是多租户/多任务隔离的索引键（生产上会放 user_id / session_id）；缓存重连把"沙箱"从一次性资源升格为**会话级持久环境**——agent 多轮对话中变量、文件、已装的包都还在，这是后面 L5 数据分析 agent 能连续追问的前提。

## 3. 文件系统与网站：沙箱是通用计算

沙箱有完整文件系统，`files` 命名空间四个动作：

```python
sbx.files.make_dir("/home/user/data")                          # 建目录
sbx.files.write("/home/user/data/hello.txt", "Hello from the sandbox")  # 写
content = sbx.files.read("/home/user/data/hello.txt")          # 读回宿主
sbx.files.remove("/home/user/data/hello.txt")                  # 删
```

沙箱不只是"代码解释器"，是**通用计算**——可以直接在里面起一个网站并拿到公网可访问的 host：

```python
sbx.files.write("index.html", simple_website)          # 写入一个最简 HTML
command = sbx.commands.run("python -m http.server 3000 --bind 0.0.0.0",
                           background=True)            # 后台起 HTTP 服务（commands 跑 shell）
host = sbx.get_host(3000)                              # 拿到该端口对应的公网域名
IFrame(f"https://{host}/index.html", width=800, height=300)  # notebook 里直接内嵌预览
```

> **对比《AutoGen》L5 的 code executor**：AutoGen 的方案是 `work_dir` 本地目录 + `DockerCommandLineCodeExecutor` 本地容器——隔离靠自己搭 Docker，产物躺在本地目录，没有网络暴露能力。E2B 把这三件事都搬到云端服务：隔离是托管的（不用本机装 Docker）、并发可横向扩（每个用户/任务一个沙箱）、`get_host` 直接给公网 URL（本地容器要自己折腾端口映射和内网穿透）。取舍：E2B 引入外部依赖和按时长计费；数据不能出域的场景仍要回退自托管容器方案。

## 4. 关键一步：execute_code 从本地换成沙箱

L2 的 `execute_code` 在**宿主进程里** exec LLM 生成的代码；现在只改函数体，工具 schema、agent loop 一行不动：

```python
def execute_code(code: str, sbx: Sandbox) -> Tuple[Execution, dict]:
    execution = sbx.run_code(code)      # 唯一的变化：本地 exec → 沙箱 run_code
    return execution.to_json(), {}      # 序列化后作为 tool result 回给模型

tools = {"execute_code": execute_code}  # 工具注册表原样重建
```

两个机制细节值得记：

1. **`sbx` 不进 LLM 的视野**：`execute_code_schema` 里只有 `code` 一个参数；沙箱句柄由 agent loop 的 `execute_tool(name, args, tools, sbx=sbx)` 在运行时注入（`tools[name](**args, **kwargs)`）。模型只负责生成代码，**基础设施句柄由 runtime 管**——这是工具设计里"LLM 参数面 ≠ 函数签名面"的标准分法。
2. **`execution.to_json()` 作为 tool result**：Execution 里的 logs / results / error 全部结构化回传，模型能看到自己代码的报错并自我修正。

> **对比 7-safety-guardrails 的沙箱红线**：guardrails 篇的红线是"**LLM 生成的代码永远不在宿主进程执行**"。L2 的本地 exec 恰好踩线（教学上故意的），本课就是赎罪的一步：换成沙箱后，`rm -rf`、挖矿、读环境变量窃取密钥这类攻击面全部被封在一台随时可销毁的临时 VM 里，宿主只暴露 `run_code` 一个 API。判断题变简单了：代码来自 LLM/用户 → 必须沙箱；代码来自自己代码库 → 才可以本地。

## 5. 实战三连：agent 在云端干活

系统提示只有两句（资深 Python 程序员 + 必须用 `execute_code` 工具跑代码），三个任务递进：

| 任务 | 现象 | 说明的问题 |
|---|---|---|
| 掷 6 面骰子函数并运行 | agent 写 `roll_dice`、在沙箱执行、返回点数 | 基本闭环：生成→执行→读结果→答复 |
| 创建 file.txt 写入 hello world 再读回 | agent 用 Python `open()` 完成文件读写 | **没有文件工具也能操作文件**——执行 Python 的能力本身就覆盖了增删改查 |
| 纯 vanilla JS 的 Snake 游戏（10×10 网格、方向键、随机 emoji 食物、撞墙死、重开按钮、复古绿黑配色，`gpt-5-mini`，约 3-4 分钟） | 生成 index.html → 沙箱起 http.server → IFrame 里直接玩 | 沙箱产物可以是**可运行的应用**，不只是计算结果 |

游戏还能带回本地：`sbx.files.read("/home/user/index.html")` 读出内容写到宿主磁盘，浏览器直接打开玩——沙箱与宿主之间文件双向流动。（用 GPT-5 系列生成，每次的游戏都会略有不同。）

## 6. 延伸源码：lib 里备好的"沙箱化文件工具"（sbx_tools.py）

本课 agent 只有 `execute_code` 一个工具，但 `lib/` 已经为后续课备好了整套文件工具的沙箱版，机制很妙——**工具代码本身被上传进沙箱**：

```python
# lib/utils.py · setup_sandbox（Next.js 模板沙箱初始化时调用）
sbx.files.write("sbx_tools.py", content)   # 把本地 sbx_tools.py 原样写进沙箱
sbx.run_code("from sbx_tools import *")    # 沙箱内 import，函数常驻解释器

# lib/tools.py · 宿主侧每个文件工具 = 一行"远程函数调用字符串"
"read_file": lambda **a: execute_code(
    a["sbx"],
    f"read_file(secure_path({repr(a.get('file_path'))}), ...)"),  # 经 run_code 远程执行
```

`sbx_tools.py` 里是 L2 同款工具（list_directory / read_file / write_file / replace_in_file / search_file_content / glob），外加两道通用防线：

- `secure_path()`：realpath 解析后强制锁在 working_dir 内，越界抛 `ToolError`——**沙箱内仍做路径约束**（防 agent 误操作系统文件，纵深防御不因有沙箱就省）；
- `_paginate_results()`：所有列表型结果统一分页（默认 16、上限 64）——工具输出是要进上下文窗口的，分页是控 token 的第一道闸。

## 7. 本课总结

| 要点 | 一句话 |
|---|---|
| Sandbox API | `create(timeout)` → `run_code(code, language)` → `Execution`（logs=打印 / results=返回值与图） |
| 生命周期 | timeout 控成本、metadata 打标签、SandboxQuery 按标签+状态查、缓存文件+reconnect 实现会话级复用 |
| 文件与网站 | `files.make_dir/write/read/remove`；`commands.run` 后台起服务 + `get_host` 拿公网 URL |
| 工具上云 | 只改 `execute_code` 函数体（exec→run_code），schema 与 loop 不动；sbx 句柄 runtime 注入不进 LLM |
| 沙箱化工具 | 工具源码上传进沙箱常驻，宿主工具调用退化为 run_code 一行调用字符串；secure_path + 分页两道防线 |

> **记忆点（引出 L5）**：agent 现在能在云端安全地跑任意代码，但它操作的都是自己现写的玩具数据。L5 把**用户上传的 CSV** 写进沙箱，配一句系统提示，同一个 agent 就变身**数据分析师**——探索数据集、回答问题、生成图表，全程不出沙箱。

## 与我的资产映射

- 安全护栏：`agent/skills/agent-selection/7-safety-guardrails.md`（"LLM 代码不落宿主进程"红线的正面实现；secure_path 是沙箱内的第二层纵深）
- 行动范式：`agent/skills/agent-selection/0-action-paradigm.md`（execute_code 单工具 = code-as-action 路线，文件任务无需专用工具即可完成的实证）
- 面试包：`agent/interview/code-sandbox.md`（E2B vs 自托管 Docker 的选型对比素材）、`agent/interview/jd-senior-agent-engineer/`
- [[project_selection_matrix]]
