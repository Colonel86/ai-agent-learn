# L2 MCP 架构与核心原语（Architecture & Primitives）

## 架构：Host / Client / Server

MCP 是 **client-server 架构**：

- **Host**：你的 LLM 应用本身（Claude Desktop、Claude AI、Cursor、Windsurf 等都是 host）。
- **Client**：跑在 host 内部；**每个 client 与一个 server 维持 1:1 连接**。
- **Server**：一个轻量程序，按 MCP 协议对外暴露能力。

一个 host 内部可以同时持有多个 client，分别连到不同的 server。

> 你日常用 Claude Desktop 等工具时，背后就是这套架构在跑——本课程会让你**亲手实现底层**，等再用现成工具时心里就有谱了。

## 三个核心原语

### 1. Tools（工具）

- 类似常规的 tool use：可被客户端调用的函数。
- 一般用于**有副作用 / 修改类**操作——更新数据库、发消息、POST 请求语义。

### 2. Resources（资源）

- **只读**数据 / 上下文，类似 GET 请求语义。
- 应用可以选择用或不用，**不强制塞进上下文**。
- 例子：数据库记录、API 返回、文件、PDF。
- 动态：**数据变了，resource 也自动变**。

### 3. Prompt Templates（提示模板）

- 服务端预定义的、**经过打磨**的 prompt。
- 用户只需填一些动态参数，就能用上"专家级 prompt"，不用自己做 prompt engineering。
- **user-controlled**：由用户主动选择是否使用。

### 三者职责分工

| 谁负责 | tools | resources | prompts |
|---|---|---|---|
| Server | 暴露 | 暴露 | 暴露 |
| Client | 发现并请求 | 发现并请求 | 发现并请求 |
| LLM 是否自动调用 | 通常会 | 应用决定 | 由用户触发 |

## 演示：Claude Desktop + SQLite MCP server

讲师连接了 SQLite MCP server 后能直接和数据"对话"：

**Tools 演示**：
- "我有哪些表？每张表多少条记录？" → Claude 调用 `list_tables` 工具。
- Human-in-the-loop UI 让你审批每次调用。
- "基于 products 表生成有意思的可视化" → 调 SQL 工具 + artifacts 画图。

**Prompt 演示**：
- SQLite server 提供 `mcp-demo` prompt 模板——用户只填"用什么数据初始化"（如行星数据），prompt 自动生成完整指令。

**Resource 演示**：
- 一份 `business insight memo` 资源，随着数据变化**动态更新**——无需手写工具去 fetch。

## 用 FastMCP 写各类原语

Python SDK 里用 `FastMCP` 极简：

### 定义 tool

```python
@mcp.tool()
def my_tool(arg: str) -> str:
    """工具说明（自动作为 LLM 看到的 description）"""
    return ...
```

### 定义 resource（静态 URI / 模板 URI）

```python
@mcp.resource("docs://list")
def list_docs() -> str: ...

@mcp.resource("docs://{doc_id}")  # 类似 Python f-string
def get_doc(doc_id: str) -> str: ...
```

UI 一般用 `@` 触发资源（如 Claude Desktop 里 `@folder_name`）。

### 定义 prompt template

```python
@mcp.prompt()
def my_prompt(...) -> str:
    return "..."
```

## 通信流程

1. **初始化握手**：client 打开连接 → 发请求 → server 响应 → 发通知确认。
2. **消息交换**：client/server 双向发请求和通知。
3. **终止连接**。

后续看到代码里出现 `initialize` 等方法时，对应的就是这套流程。

## Transport（传输层）

负责"消息怎么传"，按部署方式选：

| Transport | 场景 | 状态 |
|---|---|---|
| **stdio**（标准输入输出） | 本地运行——client 把 server 作为**子进程**启动 | 本课程本地实验用这个 |
| **HTTP + SSE**（server-sent events） | 远程、**有状态**连接 | 早期远程方案 |
| **Streamable HTTP** | 远程，**同时支持有/无状态** | 新规范推荐，但拍摄时部分 SDK 尚未支持 |

### 有状态 vs 无状态

- **有状态**：连接持续保持，可在多个请求间共享数据/记忆——SSE 适合。
- **无状态**：每次请求独立，更利于横向扩容——Streamable HTTP 才支持。

### Streamable HTTP 工作方式简述

通过 GET / POST 到一个端点（如 `/mcp`）：

- POST → 初始化、请求、响应。
- 可选 GET → "升级"成 SSE 流，双向发通知。

## 本讲收尾

从架构（host / client / server）到原语（tools / resources / prompts）到传输（stdio / SSE / Streamable HTTP），MCP 的全貌已成型。下一讲开始**写代码**：先用普通 tool use 搭一个 chatbot，再一步步改造成 MCP 形态。
