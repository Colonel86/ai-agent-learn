你构建的 MCP 服务端可以接入任何兼容 MCP 的应用，无需重写一行服务端代码。本节介绍如何将其接入 Claude Desktop。

---

**配置 Claude Desktop**

在 Claude Desktop 中：设置 → 开发者 → 编辑配置文件（JSON 格式）

将之前的 `server_config.json` 内容粘贴进去，**唯一的区别**是研究服务端需要指定完整的文件路径：

```json
{
  "mcpServers": {
    "research": {
      "command": "uv",
      "args": ["run", "/完整路径/research_server.py"]
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

保存后重启 Claude Desktop，所有之前手写的底层客户端连接代码都被自动处理了——这正是 MCP 标准化的价值所在。

重启后，Claude Desktop 界面中会显示：工具列表（来自三个服务端）、资源 URI、以及提示词模板，UI 呈现方式完全由 Claude Desktop 决定，与我们自己实现的命令行界面不同，但背后的数据和协议完全一致。

---

**演示：三个服务端协同工作**

提示词：  
"用 Fetch 访问 DeepLearning.AI，找一个机器学习相关的有趣主题，用研究服务端搜索几篇论文并总结，最后用 Artifacts 生成一个基于论文关键主题的网页闪卡测验应用。"

执行流程：
1. Fetch 服务端抓取 DeepLearning.AI，发现"多模态 LLM"主题
2. Research 服务端搜索相关论文并提取信息
3. Claude 结合 Artifacts 功能生成交互式闪卡测验应用

MCP 工具提供数据，Artifacts 负责可视化呈现，两者结合大幅扩展了应用边界。

---

**MCP 兼容应用生态**

除 Claude Desktop 外，已有大量应用支持 MCP，涵盖 Web 应用、桌面应用、命令行工具、各类 IDE（Cursor、Windsurf 等）和智能体框架。你之前构建的服务端，无需任何修改，即可接入这些应用。

---

下一节将介绍**远程部署 MCP 服务端**——让你的服务端不再局限于本地运行。我们下节课见。