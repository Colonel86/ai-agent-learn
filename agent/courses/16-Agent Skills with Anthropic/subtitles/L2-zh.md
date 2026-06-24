# L2 Skills 是什么 —— 开放标准与底层原理

上一节我们在 Claude 中亲手创建了一个 Skill。本节深入聊聊 Skills 究竟是什么、它的开放标准、以及为什么我们要在搭建 agent 时引入它。

## Skills 是开放标准

类似 MCP（Model Context Protocol），**Skills 也是一个开放标准**：

- 起源于 Anthropic 内部
- 现已有正式的 specification（规范）
- 跨平台使用：Codex、Gemini CLI、Claude Code、Open Code 等都支持

## Skill 能放什么

Skill 文件夹（folder）里不只是 markdown：

- `SKILL.md`（必备）
- 子目录与额外 markdown 文档
- **可执行脚本**（scripts）
- **图标、图片、模板等资源**（assets）

### 例子：PDF Skill

一个处理 PDF 的 Skill 需要执行真实代码：

- PDF 转图片
- 提取表单字段
- 填充 PDF 表单并加批注

这些操作的脚本代码就放在 Skill 内，由 `SKILL.md` 引用，需要时才执行。

> **重要认识**：Skill 不只是引用其他文本文件的文本文件，它能引用脚本，并告诉 agent 这些脚本是干什么的、何时执行。

## 为什么 Agent 时代需要 Skills？

### 旧思路：单一用途 agent

过去构建 agent 围绕"单一用途"展开：

- 编码 agent
- 研究 agent
- 金融 agent
- 营销 agent
- …

每个都有自己的一套工具、上下文、领域知识。

### 新思路：通用骨架 + Skill 注入

实践发现，**底层其实只需要一套简单骨架**——bash 工具 + 文件系统，足够搜寻、编辑、执行各种任务。

这种简化骨架的 agent：

- 更容易评估（evaluate）
- 更容易理解
- 更容易扩展

**但它们缺什么？**——领域专家级的上下文与做事方式。

而这正是 Skills 闪光的地方：

- 用 MCP 注入外部数据
- 用 Skills 注入**程序化知识**（procedural knowledge）和**用户特定上下文**，按需加载

## Skills 解决了哪些核心问题

### 1. 领域专长

Claude 能做数据分析、能做法律审阅。但**你公司、你团队希望按你们的方式做**。Skill 就负责这部分定制。

### 2. 可重复的工作流

LLM 系统是**非确定性**的，每次输出可能不同。Skill 提供清晰的步骤说明，让 agent 执行任务的结果**更可预测**。

### 3. 新能力

agent 开箱不会的事、Claude 完全不知道如何处理的数据，都能通过 Skill 注入——例如生成 PowerPoint、Excel、PDF 报告，按需执行相应脚本。

## Skills 的可移植性（Portability）

写一次 Skill，可在多处使用：

- Claude AI / Claude Desktop
- Claude Code
- Agent SDK
- Anthropic API
- 任何符合 Skills 规范的第三方 agent 平台

**一个生态创建，跨生态复用与扩展。**

## Skills 可组合（Composable）

把自定义 Skill 和内置 Skill 拼起来：

- 自定义"营销活动分析" Skill
- + 内置"PowerPoint 生成" Skill
- + 内置"Excel 生成" Skill

把多个 Skill 串成**复杂但可预测**的工作流。

## 渐进式披露（Progressive Disclosure）

这是 Skills 设计中最重要的概念之一。

### 把上下文窗口当公共资源

> 上下文窗口越多内容 → 越多 token → 越快填满 → 越容易出现**上下文退化**或错误回复。

### 三阶段加载

1. **第一阶段（始终在上下文）**：所有已安装 Skill 的 `name` 和 `description`
2. **第二阶段（触发时加载）**：Claude 判断该 Skill 匹配后，读取 `SKILL.md` 完整内容
3. **第三阶段（按需加载）**：如果还需要其他 reference 文件或脚本，再单独加载——**脚本执行是独立的，不会把脚本代码塞进上下文**

通过 bash + 文件系统，Claude 能精确地"只加载需要的、只执行需要的"，把上下文窗口用在刀刃上。

## 小结

- Skills 是一种**开放标准**，跨平台通用
- 内容可以是 markdown、脚本、资源文件
- 给"通用骨架 agent"提供**领域专长 + 可重复工作流 + 新能力**
- 可移植、可组合
- 通过**渐进式披露**保护上下文窗口

下一节我们将探讨 Skills 与 MCP、工具（Tools）、子 agent 等其他技术如何协同工作。
