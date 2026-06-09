# L13 跨 Agent 标准：MCP / AGENTS.md / Skills / ACP

> 原始字幕：`subtitles/L13-eng.vtt`

---

## 一、问题：不要把工作流锁死在某一个 Agent

> "Agents and models progress so fast, you don't want your workflow tied to just one choice."

SDD 的核心资产是 **spec + skill + 流程**——这些应**与具体 Agent 解耦**。

---

## 二、四个互补的开放标准

| 标准 | 角色 | 类比 |
|---|---|---|
| **MCP** (Model Context Protocol) | Agent ↔ 外部工具/数据 | Agent 的"USB 总线" |
| **AGENTS.md** | 项目级规则的标准文件名 | "README.md for agents" |
| **Agent Skills** | 可重用的工作流 + context 包 | npm 包之于 Node |
| **ACP** (Agent Client Protocol) | Agent ↔ 编辑器/客户端 | 类似 LSP 之于 IDE |

---

## 三、ACP：把 Agent 和编辑器解耦

### 3.1 思路类比 LSP

> "The protocol matches what's used in LSP."

LSP 让任意 IDE 接任意语言；ACP 让任意 IDE 接任意 Agent。

### 3.2 ACP Registry：自动化匹配

- JetBrains IDE 的 AI Chat 窗口 → 调起 ACP Registry
- 列出所有兼容 Agent（如 OpenCode）
- 一键 install + 集成

### 3.3 ACP 覆盖范围超出预期

不只是"换 Agent"，还包括：
- **Next Edit Suggestion**（编辑器内联建议）
- **Plan mode** 等高级交互

---

## 四、Skills 的可移植性

例：在 Claude Code 写的 feature spec skill → 复制到 Codex（OpenAI 的 Agent） → 它存在不同路径 → 简单调整后**照常工作**。

> **本课最重要的演示之一**：你为 SDD 写的 Skill 不会绑死在一个 Agent 上。

---

## 五、AGENTS.md：项目级规则的事实标准

逐步形成的"所有 Agent 都会读 `AGENTS.md`"——
- 当下尚未完全统一（有的 Agent 读 `CLAUDE.md`、有的读 `agents.md`）
- 但方向是清晰的：**一个 markdown 文件让所有 Agent 都能用**

> SDD 视角：Constitution 已经是结构化、agent-agnostic 的 spec；`AGENTS.md` 可作为它的"指针入口"。

---

## 六、如何挑 Agent

短期看 benchmark leaderboard，但要点：
- **benchmarks 变化很快**，月度刷新
- **依据你关心的维度**选（代码质量？速度？成本？工具集成？）
- 重要的是**你的工作流不被锁死**，所以哪个 Agent 都能试

---

## 七、架构师视角

- **SDD 的真正护城河 = spec + skill + 流程**，不是某个 Agent。
- 拥抱**开放标准**（MCP / AGENTS.md / Skills / ACP）= 你的资产具备时间复利。
- 反之，把所有 know-how 绑在某一个 Agent 的私有特性上 = 自己挖坑。

---

## 八、要点速记

- 四个标准对应四种解耦：工具（MCP）/ 规则（AGENTS.md）/ 工作流（Skills）/ 客户端（ACP）
- Skill 跨 Agent 可移植，已在 Codex 实测
- ACP ≈ LSP for Agents，Registry 让安装自动化
- 选 Agent 看 benchmark，但更要确保**可换**
