# 第 1 课：课程介绍（Introduction）

> 课程：Multi AI Agent Systems with crewAI
> 讲师：João Moura（crewAI 创始人兼 CEO） & Andrew Ng（DeepLearning.AI）
> 原文件：`subtitles/crewai_c1_01.vtt`

---

## 一、课程开场

**Andrew Ng：**

欢迎来到《Multi AI Agent Systems with crewAI》课程。本课程由 DeepLearning.AI 与 crewAI 合作推出，由 crewAI 的创始人兼 CEO **João Moura** 亲自授课。

我认为在不久的将来，**AI Agent 工作流**将成为推动 AI 进步的关键驱动力之一。

---

## 二、什么是多智能体工作流？

**多智能体工作流（Multi-agent workflows）** 允许我们把一个复杂任务拆解为多个子任务，再由各自扮演特定角色的 Agent 分别执行。

### 示例一：撰写研究报告

若目标是"写一份研究报告"，可以设计以下角色：

- **Researcher**（研究员）
- **Writer**（撰稿人）
- **Fact Checker**（事实核查员）

### 示例二：搭建网站

若目标是"搭建一个网站"，角色可以是：

- **Web Designer**（网页设计师）
- **Software Engineer**（软件工程师）
- **Testing Engineer**（测试工程师）

---

## 三、关于讲师 João Moura

Andrew 对 crewAI 的使用体验非常满意，很高兴由其创始人 João 来讲授这门课。

João 最初开发 crewAI，是因为他自己需要一个工具来构建更优秀的 Agent，用于**撰写 LinkedIn 帖子**。他在"为多智能体集合设计工作流"方面拥有丰富的经验。

**João 的回应：**

> 谢谢 Andrew。非常高兴能和你以及你的团队合作，这门课程有潜力帮助工程师们构建出色的应用。

---

## 四、本课程涵盖的核心内容

本课程聚焦于 **Agentic 系统（智能体系统）** 的主要构建模块，重点关注**多智能体系统（Multi-agent systems）**。

### 你将学到的五大核心构建块

1. **Role-playing**（角色扮演）
2. **Tool use**（工具使用）
3. **Memory**（记忆）
4. **Guardrails**（护栏/安全约束）
5. **Collaboration**（协作）

### 你将动手构建的项目

你将使用这些组件搭建一组 Agent，用于完成以下任务：

- 📄 根据岗位描述**定制简历**
- 📊 执行**财务分析**
- 📅 进行**活动策划（Event Planning）**

---

## 五、如何组织 Agent 之间的协作

在组装 Agentic 工作流时，你还需要定义：

- **协作方式**：Agent 之间如何合作
- **委派能力（Delegation）**：哪些 Agent 可以把特定任务（如研究）委派给其他 Agent
- **执行模式**：
  - **并行（Parallel）**
  - **串行（Series）**
  - **层级式（Hierarchical）**——由一个 **Manager Agent** 向多个 **Worker Agent** 分派任务

João 将通过开源库 **crewAI** 来讲解这些概念。

---

## 六、课程目标

João 指出，本课程将帮助工程师理解：

- 如何构建 **AI Agentic 应用**
- 这类应用与我们此前构建的**普通应用**有何不同

学完本课程后，你将掌握构建多智能体系统所需的**全部能力**，并能从中获取相应收益。

---

## 七、核心思维转变：像"管理者"一样思考

João 特别强调了一个重要的心智模型转变：

> **优秀的多智能体系统设计，就像是在当一位管理者。**

你现在被"晋升"为**Agent 的管理者**，你的职责是：

1. 识别**目标（Goals）**
2. 定义不同的**角色（Roles）**，让它们协同完成目标
3. 为"成功"设立**清晰的预期（Clear expectations）**

这与传统工程思维是一次非常有趣的转变。

---

## 八、致谢与下一课预告

**Andrew：**

本课程的制作离不开许多人的努力：

- 感谢整个 **CrewAI 团队**
- 感谢 DeepLearning.AI 的 **Eddy Shyu** 对课程的贡献

### 下一课内容

下一节课（第 1 课正课）将为你讲解：

- **AI Agents 概览**
- **整个课程的结构概览**

让我们进入下一段视频，深入了解 **AI Agent 的关键构建模块**。

---

## 本课要点速记（Cheat Sheet）

| 维度 | 内容 |
|------|------|
| 核心理念 | 把复杂任务拆成子任务，由扮演不同角色的 Agent 分工完成 |
| 五大构建块 | Role-playing / Tool use / Memory / Guardrails / Collaboration |
| 实战项目 | 简历定制、财务分析、活动策划 |
| 协作模式 | 并行 / 串行 / 层级式（Manager-Worker） |
| 心智模型 | 从"工程师"转变为"Agent 管理者" |
| 技术栈 | crewAI 开源库 |
