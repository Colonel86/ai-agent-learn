服务端已就绪，现在构建 MCP 客户端，让聊天机器人通过 MCP 协议与服务端通信。

---

**架构变化**

之前的聊天机器人直接在代码中定义工具；现在，工具定义全部在服务端，客户端负责从服务端获取工具列表并传给模型。

---

**构建 MCP 客户端的核心步骤**

**1. 建立连接**

使用 `StdioServerParameters` 指定如何启动服务端（即 `uv run research_server.py`），再通过 `stdio_client` 上下文管理器将服务端作为子进程启动，获取读写流。

**2. 创建 ClientSession**

将读写流传入 `ClientSession`，得到高层会话对象，提供 `initialize()`、`list_tools()`、`call_tool()` 等方法。

**3. 初始化与获取工具**

```python
await session.initialize()          # 握手
tools_result = await session.list_tools()  # 获取工具列表
```

将工具列表格式化后传给 Claude，后续模型可以请求调用这些工具。

**4. 执行工具调用**

当模型请求调用工具时，不再调用本地函数，而是通过会话转发给服务端：

```python
result = await session.call_tool(tool_name, tool_input)
```

服务端执行函数并返回结果，客户端再将结果追加到消息历史。

---

**完整文件：`mcp_chatbot.py`**

```python
# 关键依赖
import asyncio
import nest_asyncio
from anthropic import Anthropic
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

nest_asyncio.apply()

class MCPChatbot:
    def __init__(self):
        self.session = None
        self.tools = []
        self.client = Anthropic()

    async def connect_to_server_and_run(self):
        server_params = StdioServerParameters(
            command="uv",
            args=["run", "research_server.py"]
        )
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                self.session = session
                await session.initialize()
                tools_result = await session.list_tools()
                self.tools = [...]  # 格式化工具列表
                await self.chat_loop()
```

---

**安装额外依赖**

```bash
uv add anthropic python-dotenv nest-asyncio
```

**运行聊天机器人**

```bash
uv run mcp_chatbot.py
```

启动后可以看到：客户端发出 `list_tools` 请求 → 服务端返回工具列表 → 开始对话。

**演示效果**：输入"搜索两篇物理学论文"，客户端通过 `call_tool` 请求发给服务端，服务端调用函数返回结果，Claude 结合结果给出摘要回复。

---

下一节将扩展支持**多个 MCP 服务端**的同时连接，并添加资源（Resources）和提示词模板（Prompts）等更多原语。我们下节课见。