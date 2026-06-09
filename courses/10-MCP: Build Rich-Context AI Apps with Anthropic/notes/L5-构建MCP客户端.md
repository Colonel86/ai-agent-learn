# L5 构建 MCP 客户端（Creating an MCP Client）

把 chatbot 改造为"通过 MCP client 连接 L4 server"。

> 对应代码：`code/L5.ipynb` → 写出 `mcp_project/mcp_chatbot.py`

## 总体变化

**之前**（L3 chatbot）：tools 定义和执行都在 chatbot 进程里。
**之后**：tools 定义/执行**搬到 MCP server**；chatbot 通过 client 拉取工具列表、转发调用。

`process_query` / `chat_loop` 主体逻辑基本不变，关键差异在**工具调用那一步换成 session.call_tool(...)**。

## MCP 客户端的基本结构（参考代码）

```python
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

server_params = StdioServerParameters(
    command="uv",
    args=["run", "research_server.py"],
    env=None,
)

async def run():
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()           # 握手
            tools = await session.list_tools()   # 拉工具清单
            # ... chat loop
            result = await session.call_tool("tool-name", arguments={...})

asyncio.run(run())
```

要点：

- `StdioServerParameters` 告诉 client 怎么把 server 作为子进程启动。
- `stdio_client(...)` 拉起 server 子进程，返回 **read / write 流**。
- `ClientSession(read, write)` 是高层封装，提供 `initialize / list_tools / call_tool` 等方法。
- 全程 `async / await`，所以最外层用 `asyncio.run(...)`。

## chatbot 完整重构：`MCP_ChatBot` 类

```python
class MCP_ChatBot:
    def __init__(self):
        self.session: ClientSession = None
        self.anthropic = Anthropic()
        self.available_tools: List[dict] = []

    async def process_query(self, query):
        messages = [{'role': 'user', 'content': query}]
        response = self.anthropic.messages.create(
            max_tokens=2024,
            model='claude-sonnet-4-6',
            tools=self.available_tools,
            messages=messages,
        )
        # ... 与 L3 几乎一样，唯一差别在 tool_use 分支：
        # result = await self.session.call_tool(tool_name, arguments=tool_args)
        # messages.append({"role": "user", "content": [{
        #     "type": "tool_result", "tool_use_id": tool_id,
        #     "content": result.content,
        # }]})

    async def chat_loop(self):
        while True:
            query = input("\nQuery: ").strip()
            if query.lower() == 'quit':
                break
            await self.process_query(query)

    async def connect_to_server_and_run(self):
        server_params = StdioServerParameters(
            command="uv",
            args=["run", "research_server.py"],
            env=None,
        )
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                self.session = session
                await session.initialize()

                response = await session.list_tools()
                tools = response.tools
                print("\nConnected to server with tools:",
                      [tool.name for tool in tools])

                self.available_tools = [{
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.inputSchema,
                } for tool in tools]

                await self.chat_loop()

async def main():
    chatbot = MCP_ChatBot()
    await chatbot.connect_to_server_and_run()

if __name__ == "__main__":
    asyncio.run(main())
```

### 几个细节

- `nest_asyncio.apply()`：在 Jupyter / 某些操作系统下让 asyncio 事件循环嵌套友好。
- **工具发现**：`session.list_tools()` 拿到的工具结构里包含 `name / description / inputSchema`，正好就是 Anthropic API 要的格式。
- **工具调用**：原来 `execute_tool(...)` 在本地跑函数；现在 `await self.session.call_tool(name, arguments=...)` 把调用请求发到 server，由 server 执行后回传结果。

## 整体流程

1. chatbot 启动 → 通过 stdio 把 `research_server.py` 拉起来当子进程。
2. session 初始化（握手）。
3. 拉 tool list → 灌给 Claude。
4. 用户 query → Claude 想用工具 → chatbot 把请求经 session 发到 server → server 真正执行 → 返回值回到 chatbot → 再交给 Claude 综合回复。
5. 退出时 `with` 自动清理 session 和子进程。

## 命令行运行

```bash
cd L5/mcp_project
source .venv/bin/activate
uv add anthropic python-dotenv nest_asyncio
uv run mcp_chatbot.py
```

试一下：

- `Hi` —— 简单确认通信。
- `search for 2 papers on physics` —— 看到 `list_tools_request` / `call_tool_request` 在 stdio 上来回传。

## 这一讲打下的基础

至此你已经手写过一次"client 是怎么连 server 的"。之后用 Claude Desktop / Cursor 等成品 host 时，背后的事就是这套。下一讲扩展到**连接多个 server**。
