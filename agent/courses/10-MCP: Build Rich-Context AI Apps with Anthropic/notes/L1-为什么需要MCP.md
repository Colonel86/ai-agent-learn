# L1 为什么需要 MCP（Why MCP）

## 核心论断

> **模型再聪明，也只能用它能拿到的上下文来工作。**

前沿大模型再强，如果不能连接到外部世界获取数据，能力会被大幅压缩。MCP 解决的正是这件事：**标准化 LLM 与工具、数据源的连接方式**。

## 类比：REST 之于 Web

Web 应用通过 **REST** 标准化了前后端通信。MCP 的目标对 AI 应用是同样的——**让任意 LLM 与任意数据源能讲同一种"接入语言"**。

> MCP 能做的事其实没有 MCP 也能做。但当世界上有 N 个模型 × M 个数据源时，没有标准就要做 N×M 份重复集成。MCP 把它降到 N+M。

## 思想来源：LSP

MCP 借鉴了 **Language Server Protocol（LSP，Microsoft 2016）**——一个让 IDE 和语言工具解耦的协议。MCP 在精神上一脉相承：**标准化"应用 ↔ 外部能力"的边界**。

## 一个真实演示

讲师在 Claude Desktop 里同时接了两个 MCP server：

- **GitHub MCP server**：读取仓库 issue。
- **Asana MCP server**（项目管理工具）：创建任务、分派负责人。

用自然语言："从这个仓库读取 issue → 分类 → 在 Asana 里创建任务 → 分派人。"

- 一边读 GitHub，一边写 Asana。
- UI 里有 human-in-the-loop 让你确认每一步动作。
- 用极少代码就完成了跨系统的工作流。

## 解决的工程痛点

没有 MCP 时，每个 AI 应用都得自己维护：

- 工具定义
- 自定义 prompt
- 数据访问层
- 鉴权逻辑

不同团队对同一个数据源（如 GitHub）反复重写一遍。MCP 把这些**外部化到 server**：

- 工具与数据连接由开源社区或你自己提供。
- 应用只要"MCP 兼容"就能即插即用。

## 不同角色的收益

| 角色 | 收益 |
|---|---|
| 应用开发者 | 极小工作量就能接入一个 MCP server |
| API / 数据源开发者 | 写一次 server，被所有 MCP 应用复用 |
| 终端用户 | 给应用一个 server URL，就获得新能力 |
| 企业 | 关注点分离，跨团队复用集成 |

## 常见问题答疑

**Q：MCP server 是谁写的？**
A：任何人都可以——你自己写、用社区写好的、或者公司官方维护的。

**Q：MCP server 和 API 有什么区别？**
A：可以理解为"**API 之上的网关/封装**"。你不想直接调用 API 时，让 MCP server 用自然语言去帮你调用。

**Q：MCP 就等于 tool use 吗？**
A：tool use 只是 MCP 能做的事之一。MCP 还提供 resources、prompt templates 等其它原语——下一讲展开。

## 下一讲

深入 MCP 架构底层：**hosts / clients / servers**，以及核心原语 **tools / resources / prompts**。
