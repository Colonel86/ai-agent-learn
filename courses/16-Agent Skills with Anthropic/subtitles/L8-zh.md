# L8 用 Claude Agent SDK 自建研究 Agent

本节用 **Claude Agent SDK**（与 Claude Code 共用同一 harness）从零搭建一个通用研究 agent，组合：**主 agent + 子 agent + Skill + MCP**。

## 我们要造什么

一个研究 agent：

- **主 agent**：编排（orchestrator），整合多源研究并综合摘要
- **三个子 agent**：
  - `docs_researcher`：查官方文档
  - `repo_analyzer`：分析与下载 GitHub 仓库
  - `web_researcher`：搜索网络文章、视频、社区
- **Skill**：`learning-a-tool`——指导主 agent 的研究方法论
- **MCP**：把成果写入 Notion

## 提示词设计概览

### 主 agent prompt（orchestrator）

- 列出可用的三个子 agent 及能力
- **如有 Skill，必须严格遵循其指令**——Skill 可能存在也可能不存在；本例提供
- 派发子 agent 的高层准则
- 拿到子 agent 结果后如何综合

### 子 agent prompt

| 子 agent | 工具 | 内容 |
|---|---|---|
| docs_researcher | WebSearch、WebFetch | 流程、输入格式、准则、输出格式 |
| repo_analyzer | WebSearch、Bash（clone/git）、Read、Glob | 同上 |
| web_researcher | WebSearch、WebFetch | 同上；若主 agent 没给输出格式则走默认 |

## Skill：learning-a-tool

目的：**指导主 agent** 的整体研究方法（子 agent 不直接使用此 Skill）。

`SKILL.md` 关键内容：

- name + description
- **研究阶段（Research Phase）**：分别告诉每个子 agent 该查什么
- **组织为渐进式学习路径**：通过另一份 `progressive-learning.md` 文件渐进披露
  - 层级：概览与动机 → 安装 → 核心概念 → 实用模式 → 下一步
- **结构与输出格式**严格定义：概览、资源、学习路径、代码示例

## 加上 Notion MCP

为了把最终产物落到团队可共享的 Notion 页面，需要接入 **Notion MCP server**。

## 一步步实现

### 1. 初始化项目

```bash
uv init
# 安装依赖
uv add claude-agent-sdk python-dotenv asyncio
```

新建 `agent.py`。

### 2. Boilerplate

```python
import asyncio, os
from dotenv import load_dotenv
from utils import display_message  # 你自己的 helper
```

`display_message` 用于截断、格式化、漂亮展示主 / 子 agent 与工具调用的输出。

### 3. 起步：一个最小 agent

```python
options = ClaudeAgentOptions(
    system_prompt="...",
    allowed_tools=[...],
)
# 进入 loop：接收用户输入 → 调模型 → 展示
```

`uv run agent.py` 跑起来后聊一句"how are you"——能用，但没研究能力。

### 4. 扩展 allowed_tools

只读工具（Read/Grep/Glob）**默认允许**。要写文件、搜网、跑 bash，需要显式加入：

- `Write`
- `Bash`
- `WebSearch`、`WebFetch`

### 5. 接入 Notion MCP

```python
mcp_servers={
    "notion": {
        "command": "...",
        "env": {"NOTION_TOKEN": os.getenv("NOTION_TOKEN")}
    }
}
```

加在 `allowed_tools` 里：`mcp__notion__*`——授权使用 Notion 提供的所有工具。

### 6. 配置子 Agent

```python
from claude_agent_sdk import AgentDefinition

agents = {
    "docs_researcher": AgentDefinition(
        description="...",
        prompt=docs_researcher_prompt,
        tools=["WebSearch", "WebFetch"],
    ),
    "repo_analyzer": AgentDefinition(...),
    "web_researcher": AgentDefinition(...),
}

options = ClaudeAgentOptions(
    system_prompt=main_agent_prompt,
    allowed_tools=[..., "Task"],   # 必须加 Task 工具才能派发子 agent
    mcp_servers={...},
    agents=agents,
)
```

> **重要**：所有子 agent 用到的工具，都必须出现在主 agent 的 `allowed_tools` 里，否则子 agent 也用不了。

### 7. 启用 Skill

只需加一个工具：

- **`Skill`**——让 Claude 能读取并使用 Skill

加上 `setting_sources`：

```python
setting_sources=["user", "project"]
```

声明从 home 目录与 project 目录加载 Skill。Skill 放在 `.claude/skills/<skill-name>/SKILL.md`。

## 跑起来：研究 MinerU

> MinerU：一个开源 PDF 抽取库——Claude 训练数据中不一定熟，正好考验外部研究能力。

提示词："创建 MinerU 的学习指南，先把计划展示给我。"

执行链路：

1. **触发 Skill** `learning-a-tool`
2. 先输出**研究计划**：哪些 phase、哪些子 agent 并行、按 Skill 定义的结构、最终输出
3. 用户确认 → 派发三个子 agent**并行执行**：
   - docs_researcher → 官方文档
   - repo_analyzer → 克隆 GitHub、读文件
   - web_researcher → 搜索文章、YouTube
4. 收齐结果后，按 Skill 指示创建目录结构与文件：
   - `README.md`（学习路径、用法、时长估算）
   - `resources.md`（文档、仓库、PyPI、论文、社区深度报道）
   - `learning-path/`：概览 → 核心概念 → 安装 → 后端对比
   - `code-examples/`：hello-world、概念、实用模式（带 docstring 与详细注释）
5. 最后**校验并生成 summary**

## 把 `resources.md` 写到 Notion

提示词："把 `resources.md` 写到 Notion 的 resources 子页面。"

- 找到 resources 页
- 读 markdown
- 用 Notion MCP 的工具（rich block 写入）
- 批量调用，按 quick start、API 文档、视频、社区等分块

打开 Notion 页面 —— 内容已经从 markdown 同步过来。

## 这个 Agent 用了什么

一个例子里同时演示了：

- **Skill**（learning-a-tool）
- **MCP server**（Notion）
- **主 agent + 三个并行子 agent**
- **Agent SDK 上的同一套 harness**

## 安全与下一步

刚才的 demo 还很粗糙：

- `Write` 与 `Bash` 没有用户确认就执行——**生产场景需要类似 Claude Code 的权限确认 UI**
- 还没有 interrupt（打断）机制
- 可以叠加更多 Skill（比如"工具对比" Skill）、更多子 agent

这套基础已经足够你继续扩展强大的 agentic 应用了。
