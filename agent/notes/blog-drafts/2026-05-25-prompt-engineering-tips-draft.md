# 从 Prompt Engineering 到实战——我整理的 Prompt 实践清单

> 状态：初稿骨架（待填充）· 目标字数 ≥ 1200 字
> 选题来源：课程 1《ChatGPT Prompt Engineering for Developers》+ 课程 2《Building Systems with the ChatGPT API》
> 计划首发渠道：掘金 / 个人博客
> 骨架由学习助手于 2026-05-23 生成——下面每个「✍️ 待填」就是你今天要做的事

---

## 开头（约 150 字）

✍️ 待填：用 2-3 句话讲清楚——你为什么写这篇？
建议钩子：「我刷完了 21 门 AI Agent 课程，但回头看，真正每天都在用的，还是最基础的 Prompt 技巧。这篇把它们整理成一份能直接抄的清单。」

---

## 一、为什么 Prompt 工程依然重要（约 150 字）

✍️ 待填：简述——再强的模型，输入质量决定输出质量；Agent 时代 Prompt 是 Agent 行为的「源代码」。

---

## 二、实践清单（核心部分，6-8 条，每条用「反例 → 正例 → 原理」三段式）

> 写法提示：每条 150~250 字。先给一个差的 Prompt，再给改进版，再用一句话讲原理。素材去 `courses/1-*/notes/ep01~ep03` 和 `courses/2-*/notes/` 里翻。

### 1. 写清晰、具体的指令（而非简短的指令）
✍️ 待填：反例 / 正例 / 原理

### 2. 用分隔符圈定输入边界（```、<tag> 等）
✍️ 待填：反例 / 正例 / 原理

### 3. 要求结构化输出（JSON / 指定字段）
✍️ 待填：反例 / 正例 / 原理

### 4. 让模型先检查前提条件再作答
✍️ 待填：反例 / 正例 / 原理

### 5. Few-Shot：给少量示范胜过长篇解释
✍️ 待填：反例 / 正例 / 原理

### 6. 给模型「思考时间」——Chain-of-Thought / 分步骤
✍️ 待填：反例 / 正例 / 原理

### 7. 迭代式开发：Prompt 不是一次写成的
✍️ 待填：反例 / 正例 / 原理

### 8.（可选）输出校验：用 Moderation / 规则兜底
✍️ 待填：反例 / 正例 / 原理

---

## 三、把清单用进 Agent / 系统里（约 200 字）

✍️ 待填：从「单条 Prompt」到「系统」的过渡——提示链（chained prompts）、输入分类、输出审核，呼应课程 2 的端到端例子。

---

## 结尾（约 100 字）

✍️ 待填：一句收束 + 一个行动号召。
建议：「这份清单我会随着实战继续更新。如果你也在学 AI Agent，欢迎交流。」

---

## 配图 / 资源备选

- 课程 1 的「迭代式 Prompt 开发循环」示意图：`courses/1-ChatGPT Prompt Engineering for Developers/notes/images/ep03-iterative-loop.png`
- Anthropic Prompt Engineering 文档：https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering
- Anthropic Prompt Library：https://docs.anthropic.com/en/prompt-library/library

---

## 完成后清单

- [ ] 正文 ≥ 1200 字
- [ ] 至少完成 6 条清单
- [ ] 在 `AI-Agent-学习追踪表.xlsx` 的「博客追踪」Sheet 第 1 行填标题、状态改「初稿中」
- [ ] `git add -A && git commit`
