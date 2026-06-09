# 17 · Agentic Coding 工作流实战

> 一门由两门 DeepLearning.AI 短课合并构成的主题课程，主线是：**怎么把 AI 编码 Agent 用成一套可复用、可沉淀、工具无关的工程方法。**

## 为什么把这两门合并

| 模块 | 课程 | 合作方 | 在主线中的角色 |
|---|---|---|---|
| Module 1 | Claude Code: A Highly Agentic Coding Assistant | Anthropic | **工具深度** — 把日常在用的 Agent CLI 吃透 |
| Module 2 | Spec-Driven Development with Coding Agents | JetBrains | **方法论** — Constitution / Spec / Plan-Implement-Verify |

两门课的顺序刻意安排：先深用一个工具（Module 1），再从中抽象出与工具无关的方法论（Module 2）。

## 与课程 16（Agent Skills）的衔接

- 16 教 **Skill 是什么、怎么写**
- 17 教 **用 Skill 承载工程方法、跨工具复用**

`synthesis.md` 会把 16 的 Skill 概念和这里的 SDD 方法论合并讨论。

## 学习路径

```
Module 1 (Claude Code)  →  Module 2 (SDD)  →  synthesis.md
        深度用                  抽方法              架构师视角总结
```

每个 module 下：
- `subtitles/` — 英文字幕 + 中文笔记
- `notes/` — 实操记录、代码片段、个人反思

## 架构师视角的判断题（学完后要能回答）

1. **何时该用 Agent 编码、何时不该用？** 给一个新项目，你的判断依据是什么？
2. **如何把工作流沉淀为团队资产**，而不是依赖个人手感？Skill / Spec / Constitution 各自承担什么角色？
3. **工具的抽象边界在哪里？** Claude Code、Cursor 这类 Agent 工具，换掉的代价有多大？哪些是可迁移的，哪些是绑死的？

答案写在 `synthesis.md`，学完两个模块后回过来填。

## 状态

- [ ] Module 1 — Claude Code
- [ ] Module 2 — Spec-Driven Development
- [ ] synthesis.md — 两课横向对比与架构判断
