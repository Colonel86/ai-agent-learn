# L8 在 Claude Desktop 中使用 MCP（Using MCP in Claude Desktop）

之前所有 host / client / session / cleanup 的底层代码，**Claude Desktop 都替你抽象掉了**。只需要写一个配置文件，它就能拉起多个 server 并提供漂亮的 UI。

本讲没有对应的 notebook。

## 准备 server

讲师先在桌面建了一个 `MCP project` 文件夹，把 L7 的 `research_server.py` 放进去，然后准备好环境：

```bash
cd ~/Desktop/MCP\ project
uv init
uv venv
source .venv/bin/activate
uv add arxiv mcp
```

**注意**：不需要在这里手动启动 server——交给 Claude Desktop 拉起。

## 配置 Claude Desktop

Settings → Developer → Edit Config（会打开一个 JSON 文件），写入：

```json
{
  "mcpServers": {
    "research": {
      "command": "uv",
      "args": [
        "--directory",
        "/绝对路径/MCP project",
        "run",
        "research_server.py"
      ]
    },
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/some/path"]
    },
    "fetch": {
      "command": "uvx",
      "args": ["mcp-server-fetch"]
    }
  }
}
```

关键差异（与 L6 课程内的配置相比）：

- 这里要写**绝对路径**——Claude Desktop 不知道你在哪个目录运行。
- 改完配置后**关闭并重启** Claude Desktop 才生效。

## 重启后的体验

Claude Desktop 自动：

- 把每个 server 作为子进程拉起。
- 抽象掉所有底层 stdio 通信、session 管理、错误处理。
- 在 UI 中暴露：tools / resources / prompts。

界面上能看到：

- 本地 research server 的工具与 prompt 模板
- fetch / filesystem 的工具
- 资源以可选附件形式（具体 UI 由 host 决定）

## 多 server 协作演示

输入一条复合 prompt：

> "用 fetch 访问 DeepLearning.AI，找一个关于 machine learning 的有意思的话题。然后用 research server 搜几篇相关论文并总结。最后用 artifacts 生成一个带 flashcard 的网页 quiz。"

执行链：

1. `fetch` → 拉 DeepLearning.AI 内容，找到"multi-modal LLM"等话题。
2. `search_papers` → 从 arXiv 搜两三篇相关论文。
3. Artifacts（Claude Desktop 内建能力）→ 渲染出一个交互式 flashcard 网页。

> 这就是"成熟 host + 多个 MCP server"的威力——开发者只写 server，UI 与协调由 host 包办。

## 生态：还能跟谁集成？

`modelcontextprotocol.io` 的文档维护了**支持 MCP 的应用列表**，覆盖：

- IDE：Cursor、Windsurf 等
- 桌面应用：Claude Desktop 等
- Web 应用 / agentic 产品
- 命令行工具

每个 host 自行决定要支持哪些原语——除了已经学的 tools / resources / prompts，还会逐步引入 **sampling / roots** 等更高级的客户端原语（Conclusion 那讲会讲）。

## 关键认知

- **一份 MCP server，处处复用**：自己 chatbot、Claude Desktop、Cursor……同一个 server 都能接。
- **UI 是 host 的事，协议是 MCP 的事**：MCP 不规定展现，只规定数据/能力的传递格式。
- 学完前几讲后，你**已经理解 Claude Desktop 底下在干嘛**——它只是把"L5/L6 你手写的循环"产品化了。

## 下一讲

到目前为止 server 都在本机（stdio）。下一讲讲**远程 MCP server**：怎么改 transport、怎么测试、怎么部署到云端。
