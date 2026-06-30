# L5 MCP（Model Context Protocol）

## 由来

MCP 是 **Anthropic** 提出的一个标准协议，目的是让 LLM 更方便地接入**更多上下文 / 数据 / 工具**。现在已被很多公司和开发者采纳，生态在快速扩张。

## 它解决的痛点：M × N 的重复劳动

假设你的应用想接入：Slack、Google Drive、GitHub、Postgres……

- 你要为每个数据源/服务写一层封装。
- 旁边另一个团队做不同的应用，但也要接 Slack、Google Drive、GitHub……他们**重新写一遍**封装。
- 全社区有 **M 个应用 × N 个数据源** = M×N 份重复劳动。

MCP 提出的统一标准：

- 数据源/服务方写一次 **MCP server**（暴露工具和资源）。
- 应用方写一次 **MCP client**（消费这些工具和资源）。
- 总工作量从 **M×N 降到 M+N**。

## MCP 的两类对象

- **Resources（资源）**：偏数据获取（fetch data）——这是 MCP 早期设计的重心。
- **Tools（工具）**：更通用的可调用函数。

> 文档里"resources"特指数据型，但日常说"MCP 提供的工具"通常两者都包括。

## 生态：clients 与 servers

- **MCP servers** 越来越多：Slack、GitHub、Google Drive、Postgres……官方和社区都在贡献。
- **MCP clients** 也越来越多：各种 LLM 应用都在接入。
- 你以后开发的应用可能就是一个 MCP client；如果你想把自己的服务/数据开放给其他 LLM 应用，也可以做一个 MCP server。

## 演示：Claude Desktop + GitHub MCP server

讲者演示用 Claude 桌面客户端（一个 MCP client）接了 GitHub 的 MCP server：

**例 1**：用户输入"总结这个 GitHub repo 的 README.md"+ URL（AISuite 仓库）。

1. Claude 通过 GitHub MCP server 请求"读取 AISuite 仓库的 README.md"。
2. MCP server 返回文件内容。
3. 内容进入 LLM 上下文，LLM 生成总结。

**例 2**：用户问"最近的 pull request 有哪些？"

1. Claude 通过 GitHub MCP server 调用另一个工具——"列出 PR"。
2. MCP server 用合适参数（仓库名、排序、数量限制等）返回 PR 列表。
3. LLM 把列表整理成可读的中文摘要。

**重点**：同一个 MCP server 暴露**多个工具**，LLM 自动按问题选合适的那个，不需要你手写每个工具的接入代码。

## 后续学习资源

DeepLearning.ai 有一门**专门讲 MCP 的短课程**，本课程结束后想深入的话可以去看。

## 本模块小结

工具使用是 agentic 应用能力跃升的关键。掌握之后，你能搭出比纯 prompt 工程强大得多的应用。

## 下一模块预告：Evaluations 与 Error Analysis

讲者强调：**这是整门课中他认为最重要的模块**。

观察：能高效落地 agentic 工作流的人/团队，和走得磕磕绊绊的团队，最大区别在于——
**是否有一套有纪律的评测与错误分析流程**。

下一模块会分享 evals 驱动 agentic 应用开发的最佳实践。

## 面试速答总结

**一句话**：MCP 是 Anthropic 提出的工具/数据接入**标准协议**，核心价值是把社区集成成本从 **M×N 降到 M+N**——数据方写一次 server、应用方写一次 client，像"AI 应用的 USB-C / LSP"。

### 面试回答骨架（问"MCP 是什么 / 解决什么问题"）

> 1. **它是什么**：Anthropic 提出的开放标准协议，让 LLM 应用以统一方式接入外部**工具、数据、上下文**；已被广泛采纳，生态快速扩张。
> 2. **解决的痛点（最关键，要会算账）**：没有标准时，**M 个应用 × N 个数据源 = M×N 份重复封装**（每个团队都重写一遍 Slack/GitHub/Drive 接入）；MCP 让**数据源写一次 server、应用写一次 client**，总工作量降到 **M+N**——这是协议类标准的经典价值主张（类比 USB-C、语言服务的 LSP）。
> 3. **两端 + 两类对象**：架构是 **client（应用侧消费）↔ server（数据/服务侧暴露）**；server 暴露两类对象——**Resources**（偏数据获取，早期重心）与 **Tools**（通用可调用函数）。
> 4. **能力**：一个 server 可暴露**多个工具**，LLM 按用户问题**自动选合适的工具**（演示：GitHub MCP server 既能"读 README"又能"列 PR"），开发者无需为每个工具手写接入代码——直接复用上一讲的自动 tool calling。

### 关键判断（加分点）

- **MCP 解决的是"集成标准化"，不是"调用机制"**：底层仍是 L3 的 tool calling（schema + 调用循环），MCP 只是把"工具从哪来、怎么发现、怎么接"标准化了——别把两者混为一谈。
- **取舍：标准化 vs 控制力/安全面**：M+N 的复用很香，但接入第三方 MCP server = 引入**外部可执行能力**，需要关注权限范围、数据出境、server 可信度、工具描述被投毒（prompt injection）等——这点能接上 L4 的安全话题。
- **你会站在哪一端**：自己的应用通常是 **client**；想把自家服务开放给其他 LLM 应用，就做一个 **server**。

### 为什么这是高分答法

- 用 **M×N → M+N** 一句话点穿价值，并给出 USB-C/LSP 类比；
- 分清"集成标准（MCP）"与"调用机制（tool calling）"两层，再补一句安全/可信度取舍，显示有架构判断而非只会背定义。

**一句话收尾**：MCP 把工具接入从"每家各写一遍"变成"server 写一次、client 用一次"，是 agentic 生态的**集成层标准**；用它的同时要管好第三方 server 的权限与可信边界。

> 关联：`L3-现代工具调用语法.md`（底层 tool calling 机制）、`L4-代码执行工具.md`（外部能力的安全边界）、`../../../../roadmap/agent-selection/`（工具/集成选型）。
