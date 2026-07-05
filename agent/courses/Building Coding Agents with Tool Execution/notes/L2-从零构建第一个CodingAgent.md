# L2 · 从零构建第一个 Coding Agent（工具注册 → 单轮调用 → Agent Loop）

> 课程：Building Coding Agents with Tool Execution（DeepLearning.AI × E2B）
> 本课任务（lab）：从零搭出第一个 coding agent——给它**真实的工具**去执行代码、读写文件，并实现**多步推理循环**与退出条件。

## 0. 本课目标与路线

开场先跑一个"成品预告"：`coding_agent_demo_ui()` 启动一个带 UI 的数据分析 agent，输入 *"Can you create a function that draws an emoji and run it?"*——agent 生成 matplotlib 代码并执行（画出来的是个哭脸，讲师也觉得有趣）。UI 右侧实时显示 **context 增长条**：颜色沿用幻灯片的消息配色、**高度正比于 token 量**——这个可视化贯穿后续课程，是"context 是稀缺资源"的直观提醒。

然后回到主线，从零搭建，路线五步：**① LLM 封装 → ② 第一个工具 execute_code → ③ 工具分发器 execute_tool → ④ 单轮 agent → ⑤ 文件工具 + Agent Loop**。模型用 OpenAI GPT 系列（Responses API，默认 `gpt-4.1-mini`）。

## 1. LLM 封装：`llm()` 函数

一个薄封装管掉调用样板（`code/L2/llm.py`）：

```python
def llm(client, messages, system="You are an helpful assistant",
        name="gpt-4.1-mini", **kwargs):
    system_message = {"role": "developer", "content": system}  # Responses API 用 developer 角色放系统提示
    if name.startswith("gpt-4"):
        kwargs["temperature"] = 0        # gpt-4 系列固定 temperature=0，保证可复现
    return client.responses.create(
        model=name,
        input=[system_message, *messages],  # 系统提示 + 消息历史拼成 input
        **kwargs,                            # tools=... 等参数从这里透传
    )
```

## 2. 第一个工具：`execute_code`（exec + stdout 捕获）

工具 = **agent 可以调用的真实函数**。第一个工具让 agent 能跑任意 Python 代码：

```python
class Execution(TypedDict):   # 约定工具返回结构：结果与错误分开装
    results: list[str]
    errors: list[str]

def execute_code(code: str) -> Execution:
    execution = {"results": [], "errors": []}
    old_stdout = sys.stdout
    try:
        sys.stdout = StringIO()          # 重定向 stdout，才能捕获 print 输出
        exec(code)                        # Python 内置 exec 直接执行代码字符串
        execution["results"] = [sys.stdout.getvalue()]
    except Exception as e:
        execution["errors"] = [str(e)]   # 出错也不抛，装进 errors 返回
    finally:
        sys.stdout = old_stdout          # 无论如何恢复 stdout
        return execution
```

`execute_code("print('Hello World!')")` → `{"results": ["Hello World!\n"], "errors": []}`。

> **对比 0-action-paradigm.md（行动范式层）**：这一格代码就是 **CodeAct 档的最小实现**——"执行任意代码"作为一个超级工具。但注意它用 `exec` **直接在 notebook 进程里跑**，零隔离：LLM 生成的代码能读写本机任何文件、能 `import os; os.system(...)`。选型矩阵写的"CodeAct 必须沙箱"在这里被教学场景刻意豁免了，L3 整课就是补这个洞。

## 3. 工具 Schema 与注册表：让模型"看见"工具

模型不能直接读 Python 函数——要用 **JSON Schema** 向它描述工具长什么样：

```python
execute_code_schema = {
    "type": "function",
    "name": "execute_code",                      # 名字要与注册表键一致
    "description": "Execute Python code and return the result or error.",
    "parameters": {
        "type": "object",
        "properties": {
            "code": {"type": "string",
                     "description": "Python code to execute as a string"},
        },
        "required": ["code"],
        "additionalProperties": False,           # 禁止模型自造参数
    },
}

tools = {"execute_code": execute_code}   # 注册表：工具名 → 真实函数，后续新工具都加在这
```

再配一个**分发器** `execute_tool`：按名字查注册表、解析参数、执行并返回——三层错误全部**当数据返回而不是抛异常**：

```python
def execute_tool(name: str, args: str, tools: dict[str, Callable]):
    try:
        args = json.loads(args)                        # 模型给的参数是 JSON 字符串
        if name not in tools:                          # ① 模型幻觉出不存在的工具
            return {"error": f"Tool {name} doesn't exist."}
        result = tools[name](**args)                   # 查表 + 解包调用
    except json.JSONDecodeError as e:                  # ② 模型生成的参数不是合法 JSON
        result = {"error": f"{name} failed to parse arguments: {str(e)}"}
    except KeyError as e:                              # ③ 缺参数
        result = {"error": f"Missing key in arguments: {str(e)}"}
    except Exception as e:
        result = {"error": str(e)}
    return result
```

## 4. 单轮 Agent：把三块拼起来

```python
def coding_agent(client, query, system, tools, tools_schemas):
    messages = [{"role": "user", "content": query}]
    response = llm(client, messages, system, tools=tools_schemas)
    for part in response.output:            # Responses API 的输出是多个 part
        if part.type == "message":          # 模型想对人说话 → 打印内容
            print(part.content)
        elif part.type == "function_call":  # 模型想调工具 → 走分发器
            result = execute_tool(part.name, part.arguments, tools)
            print(f"[{part.name}] {result}")
```

**System prompt 设计**是这里的隐形主角，三句话对应三类指令：

```python
system = """You are a Senior Python programmer.                # ① 角色
You must always use the `execute_code` tool to run code.       # ② 工具使用规则（must always）
You collect user's inputs by using the `input` python function.# ③ IO 约定
"""
```

测试任务："问我今天喝了几杯咖啡，换算成写了多少行代码"。输入 5 杯 → 215 行（caffeine = productivity）。这是一次**完整往返**：agent 收到 query → 推理 → 决定调哪个工具 → 生成代码 → 执行 → 返回结果。

## 5. 文件系统工具：read_file / write_file 与 ToolError

Coding agent 必须能读写文件。两个新 schema 的设计细节值得抄：

- **`read_file`**：除 `file_path` 外还有 `limit` 和 `offset`（读多少字符、从哪读起）——文件可能很大，**让模型自己决定读多少，才能保住 context 干净**；
- **`write_file`**：`content` + `file_path`，返回只保留一句 `"Written N bytes to ..."` ——**结果刻意做小**，同样是省 context。

实现侧引入**自定义异常 `ToolError`**：不把冗长的 stack trace 塞回给模型，而是给**具体、简洁的错误反馈**：

```python
class ToolError(Exception):
    """工具失败专用异常——短句反馈，不给长 stack trace"""

def read_file(file_path, limit=None, offset=0):
    if not os.path.exists(file_path):
        raise ToolError(f"File does not exist: {file_path}")  # 精确告诉模型"文件不存在"
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        if offset > 0:
            f.seek(offset)
        content = f.read(limit) if limit else f.read()
    return {"content": content, "size": len(content)}
    # PermissionError / UnicodeDecodeError 同样各转成一句 ToolError
```

注册进 `tools` 字典后三连测：
1. **建空文件**：agent 调 `write_file` 写入 text.txt（0 bytes）——prompt 里要**显式告知 working directory**；
2. **读不存在的文件**：agent 调 `read_file`，拿回**结构化 error 字典**而不是崩溃——这让 agent 能**自我恢复、重试**；
3. **写后读**：一个 query 两步（创建 file1.txt 再读回），模型在**同一次响应里连发两个 function_call**，先 write 后 read。

> **架构师视角**：本节浓缩了工具工程的三条铁律——**错误是数据不是异常**（error 进消息流，模型才能看见并纠错）、**工具结果为 context 而设计**（limit/offset 分页、返回值刻意做小）、**schema description 就是给模型的文档**（写给模型看，不是写给人看）。这与面试包 `01-agent-run-loop-and-orchestration` 讲的"失败当 observation 回喂"是同一件事：工具层把失败降级成结构化数据，loop 层才有 Reflexion 式重试的原料。

## 6. Agent Loop：从单轮到多步迭代

目前 agent 只能跑一轮，而**真 agent 应当迭代执行任务、完成时自行停止**。最简单的两个退出条件：**模型不再调工具**（认为任务完成）或**到达 max_steps 上限**（防止无限打转）。

```python
def coding_agent(client, query, system, tools, tools_schemas,
                 messages=None, max_steps=5):
    if messages is None:
        messages = []
    messages.append({"role": "user", "content": query})   # 初始用户消息入历史
    steps = 0

    while steps < max_steps:                     # 退出闸 ①：步数上限
        response = llm(client, messages, system, tools=tools_schemas)
        has_function_call = False

        for part in response.output:
            messages.append(part)                # 模型输出的每个 part 都进历史
            if part.type == "message":
                print(f"[agent] {response.output_text}")
            elif part.type == "function_call":
                has_function_call = True
                result = execute_tool(part.name, part.arguments, tools)
                messages.append({                # 工具结果也进历史——下一圈的 observation
                    "type": "function_call_output",
                    "call_id": part.call_id,     # 用 call_id 与请求配对
                    "output": json.dumps(result),
                })

        if not has_function_call:                # 退出闸 ②：模型不再调工具 = 任务完成
            print("[agent] all tasks completed")
            break
        steps += 1
```

结构上就是三件事：**循环（while steps < max_steps）+ 记忆（messages 里累积 user 消息、模型每个 part、每个工具结果）+ 退出条件（no function call / max steps）**。

测试任务是六步的 Caesar cipher：写函数 → 问用户消息 → 问 shift → 运行 → 打印密文 → 存 secret.txt。输入 "Francesco"、shift 3，agent 顺利跑完。一个有意思的观察：**输出里看不到 write_file 调用**——agent 大概率直接用 Python（execute_code）写了文件；`!cat secret.txt` 验证密文确实落盘了。

> **对比《AI Agentic Design Patterns with AutoGen》L5**：AutoGen 把"写码 agent + 执行 agent"拆成**两个 agent 对话**，代码经 `LocalCommandLineCodeExecutor` 提取执行、且默认人工确认每一步；本课则是**单 agent + while 循环 + 工具注册表**的裸实现，无人审、靠 max_steps 兜底。两者是同一个 loop 的框架版与手写版——手写版让你看清 AutoGen 藏在 `initiate_chat` 里的每一行控制流。Caesar cipher 测试暴露的"agent 用 execute_code 绕过 write_file"也说明：**CodeAct 超级工具会吞掉离散工具的调用路径**，工具集重叠时模型走哪条路是不可控的——审计要求高时这是个真问题。

## 7. Chat Interface：把 loop 包成对话

```python
messages = []                                  # 跨轮共享的历史，对话记忆之所在
while (query := input(">:")) != "/exit":       # 海象运算符：读输入直到 /exit
    coding_agent(client, query, system,
                 messages=messages,            # 传同一个 list，多轮对话共用
                 tools=tools, tools_schemas=[...])
```

测试"画一头 ASCII 牛"成功。注意 `messages` 在循环外定义、每轮传入同一个对象——**对话记忆就是这个不断增长的 list**。

## 8. 课程完整版预览：`lib/coding_agent.py` 的进化

Notebook 是教学版；课程仓库 `code/lib/` 里的完整版是后续课程（L4–L6）实际用的，同一个 loop 骨架上叠了四层进化：

| 维度 | Notebook 教学版 | lib 完整版 |
|---|---|---|
| 执行环境 | 本机 `exec()` | **E2B Sandbox**（`sbx.run_code`），所有工具经 `execute_tool(..., sbx=sbx)` 进沙箱 |
| 输出方式 | `print` | **Generator**：每个 part `yield (part, messages, usage)`，UI/logger 流式消费 |
| Context 管理 | 无 | `maybe_compress_messages`：usage 超过 `60_000 × 0.7` 时，把**最旧约 70% 的消息**压缩成 `<state_snapshot>` XML（用 gpt-5-nano 生成，含 overall_goal / key_knowledge / file_system_state / recent_actions / current_plan 五段），切点还要对齐 user 消息边界、并保证 function_call 和它的 output 不被拆开 |
| 工具集 | 3 个 | **8 个**：execute_code / execute_bash / list_directory / read_file / write_file / replace_in_file / search_file_content / glob——检索类工具全部带 `offset`/`limit` 分页，`replace_in_file` 的 description 明确要求"先 read_file 再替换、old_string 要带足上下文" |

`lib/prompts.py` 还给出三个生产级 prompt 范本：**压缩 prompt**（先在 `<scratchpad>` 私下推理，再产出结构化 `<state_snapshot>`——快照将成为 agent 对过去的*唯一*记忆）、**next-speaker 判定 prompt**（判断该轮到 user 还是 assistant 说话，默认 user）、**Web 开发 system prompt**（强制 Reason-then-Act 循环、锁定工作目录、"每次改完必跑 `bunx tsc --noEmit`"、"禁止重启已在 3000 端口运行的 app"——把环境约束全部写死进 prompt）。

> **架构师视角**：对照面试包 `01-agent-run-loop-and-orchestration` 的四相模型（observe → plan → act → verify），本课 loop 的映射关系是：messages 装配 = observe，`response.output` = plan 的产物，`execute_tool` = act，而 **verify 相缺位**——退出仅靠"模型不调工具了"这个自宣告信号，没有独立校验任务真完成了没有（Caesar cipher 里文件是否真写对，是人 `cat` 出来确认的）。这正是教学版与生产版的本质差距之一；另一个差距是退出闸太少：生产 loop 还需要循环检测（同一工具反复失败）和 token 预算闸，lib 版的 compress 机制只是缓解 context 膨胀，并不判停。

## 9. 本课总结

| 要点 | 一句话 |
|---|---|
| 工具三件套 | 真实函数 + JSON Schema（给模型的文档）+ 注册表 dict（名字 → 函数） |
| execute_tool 分发器 | 查表、解析、执行；工具不存在/参数坏/执行失败全部**返回 error 数据** |
| 错误即反馈 | ToolError 短句代替 stack trace，结构化 error 让 agent 自我恢复重试 |
| Context 意识 | read_file 带 limit/offset、write_file 返回值做小——工具输出为 context 而设计 |
| Agent Loop | while + messages 累积（part 与 function_call_output 成对）+ 双退出闸（无工具调用 / max_steps） |
| 对话接口 | 循环外共享同一个 messages list = 多轮记忆 |

> **记忆点（引出 L3）**：本课 agent 的一切能力都建立在一行危险的 `exec(code)` 上——LLM 生成的代码就在 notebook 本机进程里裸跑，能读写你机器上的任何东西。L3 系统回答"这些代码到底该在哪跑"：local、Docker 容器、gVisor、microVM 沙箱的隔离强度谱与选型判据。

## 与我的资产映射

- 行动范式层：`agent/skills/agent-selection/0-action-paradigm.md`（本课 = CodeAct 档最小实现，`exec` 版没有沙箱是教学豁免）
- 面试包：`01-agent-run-loop-and-orchestration`（**直接素材**：本课 loop 是四相模型的手写版，verify 缺位 + 退出闸设计是现成的对比论据）
- 工具层：`agent/skills/agent-selection/4-tools.md`（schema description 质量、分页设计、工具重叠时的路径不可控）
- 安全护栏层：`agent/skills/agent-selection/7-safety-guardrails.md`（裸 exec 的 blast radius → L3 的沙箱谱系）
- [[project_selection_matrix]]
