# L4 构建第一个 MCP 服务器（Creating an MCP Server）

把上一讲 chatbot 里的两个工具函数**抽离到 MCP server**，用 `FastMCP` 高层封装暴露，再用 **MCP Inspector** 在浏览器里测试。

## 目标产物：`research_server.py`

完整骨架：

```python
import arxiv
import json
import os
from typing import List
from mcp.server.fastmcp import FastMCP

PAPER_DIR = "papers"

# 初始化 server
mcp = FastMCP("research")

@mcp.tool()
def search_papers(topic: str, max_results: int = 5) -> List[str]:
    """..."""  # 上一讲的实现完全照搬
    ...

@mcp.tool()
def extract_info(paper_id: str) -> str:
    """..."""
    ...

if __name__ == "__main__":
    mcp.run(transport='stdio')
```

### 关键点

- **`@mcp.tool()` 装饰器**：函数自动变成 MCP 工具；
  - 函数名 → 工具名
  - **docstring** → 工具描述
  - 类型注解 + 参数 → 自动生成 JSON Schema
- **`transport='stdio'`**：本地运行，client 把 server 作为子进程拉起；远程才会换成 SSE / Streamable HTTP。
- **`if __name__ == "__main__"`**：保证仅在直接运行时启动，被 import 时不会自动跑。

## 项目环境：用 `uv` 管理依赖

讲师推荐用 [`uv`](https://github.com/astral-sh/uv) 代替 `pip`——更快、依赖管理体验更好。

```bash
cd mcp_project
uv init                 # 初始化项目
uv venv                 # 创建虚拟环境
source .venv/bin/activate
uv add mcp arxiv        # 安装依赖
```

## 用 MCP Inspector 测试

不写任何 client / host 代码，先用官方 Inspector 在浏览器里玩。

```bash
npx @modelcontextprotocol/inspector uv run research_server.py
```

- `npx ...`：临时拉起 Inspector 工具。
- `uv run research_server.py`：Inspector 用这个命令把 server 拉起。

### Inspector UI 要点

- **Transport Type**：保持 `stdio`（本地默认）。
- **Command**：`uv run research_server.py`。
- 课程环境下还要填 **Inspector Proxy Address**（本地运行不需要）。
- 点 Connect → 初始化握手成功。

### 能做什么

| 操作 | 含义 |
|---|---|
| **List Tools** | 让 server 把工具清单发回来 |
| 直接调用工具 | 在 UI 里填参数运行，立刻看返回值 |
| 查看自动生成的 description / schema | 来自 docstring 和函数签名 |

讲师演示：搜 "chemistry"，max_results=1 → 看到 server 返回的 paper ID 列表；用该 ID 调 `extract_info` → 看到完整信息。

## 这个流程的价值

- **完全独立于任何 LLM**——server 是纯协议层的能力暴露。
- 在接入 chatbot 之前先用 Inspector 验证 server 是不是健康。
- 别人写好的 server 你拿来用之前也可以先这样"沙箱体验"。

## 退出

`Ctrl+C` 终止 Inspector 进程。再次启动按上箭头复用历史命令。

## 下一讲

构建 host + MCP client，让 chatbot 不再硬编码工具，而是从 MCP server **动态发现**。
