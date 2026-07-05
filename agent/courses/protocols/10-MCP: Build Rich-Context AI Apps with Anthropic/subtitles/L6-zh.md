本节将聊天机器人升级为可同时连接多个 MCP 服务端。

---

**引入两个参考服务端**

**Fetch 服务端**（Python，由 Anthropic 维护）：抓取网页内容并转为 Markdown，方便 LLM 消费。运行命令：`uvx mcp-server-fetch`

**File System 服务端**（TypeScript）：提供文件读写、搜索、获取元数据等功能。运行命令：`npx -y @modelcontextprotocol/server-filesystem .`（`.` 表示限制在当前目录）

---

**用 JSON 配置文件管理多服务端**

将服务端连接参数从代码中抽离，存入 `server_config.json`：

```json
{
  "mcpServers": {
    "research": {
      "command": "uv",
      "args": ["run", "research_server.py"]
    },
    "fetch": {
      "command": "uvx",
      "args": ["mcp-server-fetch"]
    },
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "."]
    }
  }
}
```

新增任何服务端只需在此文件添加一条配置。

---

**代码升级要点**

聊天机器人类中新增：
- `self.sessions`：维护所有已建立的会话列表
- `self.tools`：记录每个工具及其对应的会话

由于需要同时管理多个异步上下文管理器，使用 `AsyncExitStack` 统一管理连接的生命周期。启动时循环读取配置文件，依次连接每个服务端并聚合所有工具。工具调用时，根据工具名找到对应会话，转发给正确的服务端执行。

---

**演示效果**

启动后显示已连接三个服务端及各自的工具列表。

**示例一**（两个服务端协作）：  
"抓取 MCP 官网内容，保存为 `mcp_summary.md`，并生成可视化图表"  
→ Fetch 服务端抓取网页 → File System 服务端写入文件 → Claude 生成 Markdown 图表

**示例二**（三个服务端协作）：  
"访问 DeepLearning.AI，找一个有趣的术语，搜索相关论文，总结后写入 `results.txt`"  
→ Fetch 抓取网站 → Research 服务端搜索论文 → File System 写入结果

（演示中模型将 MCP 搜索成"Multi-Concept Pre-training"——提示词工程的重要性由此可见）

---

下一节将为服务端添加**资源（Resources）**和**提示词模板（Prompts）**，进一步丰富 MCP 的能力。我们下节课见。