本节将上一节的工具函数改造为 MCP 服务端，并用 MCP Inspector 进行测试。

---

**核心改动：三步构建 MCP 服务端**

**第一步：引入 FastMCP 并初始化服务端**

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("research")
```

**第二步：用装饰器将函数声明为 MCP 工具**

```python
@mcp.tool()
def search_papers(topic: str, max_results: int = 5):
    ...

@mcp.tool()
def extract_info(paper_id: str):
    ...
```

FastMCP 会自动读取函数的文档字符串和类型注解，生成工具的 Schema 描述，无需手动编写 JSON 格式的工具定义。

**第三步：启动服务端**

```python
if __name__ == "__main__":
    mcp.run(transport="stdio")
```

本地运行使用标准 IO 传输，远程部署时切换为 HTTP + SSE 或 Streamable HTTP。

以上所有代码写入 `research_server.py` 文件。

---

**用 MCP Inspector 测试服务端**

**环境配置**（使用 uv 包管理器）：

```bash
uv init          # 初始化项目
uv venv          # 创建虚拟环境
source .venv/bin/activate  # 激活虚拟环境
uv add mcp arxiv  # 安装依赖
```

**启动 Inspector**：

```bash
npx @modelcontextprotocol/inspector uv run research_server.py
```

Inspector 提供浏览器界面，无需构建任何 MCP 客户端或宿主，就能直接：
- 查看服务端暴露的所有工具（`list tools`）
- 测试调用工具并查看返回结果
- 观察初始化握手过程

**测试演示**：在 Inspector 中搜索 `chemistry`，返回论文 ID；再用该 ID 调用 `extract_info`，成功获取论文详情。Inspector 对于开发和调试 MCP 服务端非常实用，也适合探索他人构建的服务端。

退出服务端：`Ctrl+C`

---

下一节将构建 MCP 客户端和宿主，把这个服务端与聊天机器人集成起来，实现完整的 MCP 通信链路。我们下节课见。