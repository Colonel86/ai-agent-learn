# L0 课程介绍：Anthropic 的 Agent Skills

欢迎来到《Agent Skills with Anthropic》课程，本课程由 DeepLearning.AI 与 Anthropic 合作推出，主讲人是 Anthropic 技术教育负责人 Elie Schoppik。

## 什么是 Skills（技能）？

**Skills 是一组指令文件夹，能为 Claude Code 和其他智能体（agent）扩展专业知识与新能力。**

简而言之，Skills 让你把"重复让 agent 执行的工作流"打包成一个可复用、可共享的资产。任何符合规范的 agent 都能加载并执行它。

## Skills 是开放标准

这是 Skills 最令人兴奋的一点——它们现在是**开放标准（open standard）**：

- 统一的格式规范
- 可以在任何兼容 Skills 的 agent 上运行
- **一次构建，多处部署**：写一次 Skill，可以在多个 agent 产品中使用（Claude Code、Codex、Gemini CLI、Open Code 等）

## Skill 的基本结构

每个 Skill 必须包含一个 `SKILL.md` markdown 文件，内含：

- **name**（名称）
- **description**（描述）
- **主指令内容**

主指令可以引用其他文件，例如：

- 脚本（scripts）
- 额外的 markdown 文件
- 资源文件（assets），如模板、图片等

## 渐进式披露（Progressive Disclosure）

Skills 采用**渐进式披露**机制加载到 agent 上下文中：

1. **始终在上下文中**：只有 Skill 的 `name` 和 `description`
2. **匹配时加载**：当用户请求与 Skill 描述匹配时，agent 才加载 `SKILL.md` 的完整指令
3. **按需加载**：如有需要，agent 再加载引用的 reference 文件和资源

这样做的好处是**保护上下文窗口**，避免无关信息污染。

## Skill 运行所需的工具

要使用 Skill，agent 至少需要一组基础工具：

- **文件系统访问**：读写文件
- **bash 工具**：执行代码

有了这些工具，agent 就能执行任意 Skill 所需的命令。

## Skills 与 MCP、子 Agent 协同

Skills 可以与 **MCP**（模型上下文协议）和**子 agent（sub-agent）**结合，构建强大的 agentic 工作流：

- 用 **MCP** 从外部数据源拿数据
- 用 **Skill** 教 agent 如何处理这些数据、或如何高效检索
- 用 **子 agent** 在隔离的上下文中并行执行任务，子 agent 内部也可以使用 Skill

## 本课程将带你完成

讲师 Elie Schoppik 会带你从浅到深掌握 Skills：

1. **Claude AI**：为营销活动创建一个 Skill，并与内置的 Excel、PowerPoint Skill 组合使用
2. **Claude API**：构建两个 Skill（内容生成与数据分析工作流），通过 API 调用
3. **Claude Code**：用 Skill 进行代码审查与测试
4. **Claude Agent SDK**：搭建一个研究型 agent，使用 Skill 来综合研究结果

特别感谢 DeepLearning.AI 的 Hawraa Salami 对本课程的贡献。

## 什么时候该用 Skill？

> 如果你发现自己**反复让 agent 执行同一个工作流**，就该把它打包成 Skill。

与其每次都重复解释流程，不如让 agent 一看到匹配的请求就自动知道该怎么做。

下一节，Elie 会带你在 Claude AI 中亲手创建第一个 Skill。
