# L1 · DSPy 是什么：两大痛点与三个特别之处

> 课程：DSPy: Build and Optimize Agentic Apps（DeepLearning.AI × Databricks）
> 本课任务：回答"DSPy 是什么、特别在哪、为什么不是重复造轮子"。纯理论课，无代码。

## 0. 本课目标与路线

开场直面用户最自然的质疑：**"我们已经有这么多选择了，DSPy 是在重复造轮子吗？"** 讲师的答案是 No，但论证方式不是直接吹产品，而是先把"我们到底在被什么问题折磨"讲清楚：**① compound AI system 的兴起 → ② 痛点一：prompt engineering → ③ 痛点二：框架本身 → ④ DSPy 的定义与三个特别之处**。

## 1. 背景：compound AI system 的兴起

2022 年底以来，随着 GenAI 模型的成功，**compound AI system（复合 AI 系统）**兴起——课程给的两个例子是问答系统（RAG）和代码生成器。

- Compound AI system = 由**多个 module** 组成的系统；
- 每个 module 处理一个子任务——可以是 LLM 调用，也可以是普通的 tool calling；
- 把这些 module 组合起来，形成能处理复杂任务（retrieval augmented generation、code generation……）的大系统。

```
输入 ──▶ [module 1: LLM 调用] ──▶ [module 2: 工具调用] ──▶ [module 3: LLM 调用] ──▶ 输出
         └── 每个 module 一个子任务，组合成 compound AI system ──┘
```

而只要在构建 compound AI system，就绕不开两个问题。

## 2. 痛点一：prompt engineering——又脆弱又耗时

我们做 prompt engineering 的原因很朴素：prompt 更好 → 模型结果更好。但过程非常 messy：

- 本质上是在**拧字符串**（tweaking the strings），而且**不知道哪个改动真正起了作用**；
- 实践中往往要迭代 **50、100 个甚至更多**的 prompt，每个 prompt 可能长达**数万词**；
- 更糟的是：prompt engineering **严重偏向（biased towards）特定语言模型**——一换模型，全部推倒重来。

讲师的总结：**prompt engineering is both brittle and time-consuming**（既脆弱又耗时）。

> **对比 01《ChatGPT Prompt Engineering for Developers》**：那门课教的正是这里被诊断为"痛点"的手工流程——写清晰指令、给 few-shot 示例、迭代调优，全靠人肉试错，且成果绑定在当时的 GPT-3.5 上。两门课隔着一条方法论分水岭：01 教你**当一个好的 prompt 工程师**，DSPy 教你**把 prompt 工程师自动化**。手工调 prompt 的直觉仍然有用——它变成了你给 optimizer 定义 signature 描述和 metric 时的领域知识。

## 3. 痛点二：框架税——contract 学习成本与迁移锁定

框架本身也在成为问题。框架的价值是**简化并标准化**构建 agent / RAG 等系统的体验，但抱怨越来越多——"我看到的麻烦比价值多"：

1. **被迫学习框架的 contract**：这些概念常常是不必要的开销，让人无法专注在业务逻辑上；
2. **迁移锁定**：一旦决定换框架，存量代码**很难迁出**。

## 4. DSPy 的正式定义

针对这两个痛点，DSPy 的完整定义：

> DSPy 是一个**灵活、轻量**的框架：**简化与 LM 的交互**，并通过 DSPy optimizer 提供**自动程序优化**——包括 prompt optimization 和 LM weights finetuning；同时提供**无缝生产化**支持（streaming、async 等）。

关键姿态：DSPy 提供 AI 应用的 building blocks，但**不限制你构建应用的方式**——**易迁入，也易迁出**（easy to migrate to DSPy and migrate off DSPy）。这是对痛点二的直接回应。

## 5. 三个特别之处

### 5.1 LM-agnostic programming（而非 LM-biased prompting）

不做 prompt engineering，而是通过定义 **input fields 和 output fields** 与 LLM 交互。课程给的心智模型：

```
传统 RESTful API：   输入/输出格式由【服务端】定义，客户端照办
DSPy 眼中的 LLM：    一个工程良好的 API 端点，但输入/输出格式由【客户端】定义（signature）
```

即：把 LLM 看作一个行为良好的 RESTful API，只是数据契约写在调用方——这就是 L2 要展开的 signature（本课点到为止）。

### 5.2 无缝生产化：原生特性 + MLflow 集成

- **原生**：streaming、cache 等；
- **MLflow**：ML/AI ops 工具，覆盖 AI 应用端到端开发——**MLflow tracing** 调试 AI 程序、**MLflow experiments** 追踪开发过程、**MLflow deployments** 部署应用（L3 展开）。

### 5.3 自动程序优化

创建一个 DSPy optimizer，应用到你的 program 上，**自动获得质量提升**（L4 展开）。

最后的信任背书：DSPy 已被业界大量采用，企业用户案例见 `dspy.ai/community/use-cases`。

> **架构师视角**：三个特别之处对应三种不同的"税"——LM-agnostic 免的是**换模型税**，易迁入迁出免的是**框架锁定税**，optimizer 免的是**人肉调优税**。对照 `2-framework/03-framework-profiles.md` 的画像维度，DSPy 的定位很独特：它不和 LangGraph 争"编排图怎么画"，而是垂直切入"**LLM 调用这一层怎么写、怎么优化**"——所以它可以和编排框架共存（L2 会明说 forward 里可以调 LangChain/LlamaIndex）。选型时它不是"替代谁"，而是"叠在谁上面"。

## 6. 本课总结

| 要点 | 一句话 |
|---|---|
| Compound AI system | 多 module 组合的系统，每个 module 一个子任务（LLM 调用或工具调用） |
| 痛点一 | 手工 prompt engineering 脆弱（换模型作废）且耗时（50-100+ 个数万词的 prompt） |
| 痛点二 | 框架 contract 学习成本 + 迁移锁定 |
| DSPy 定义 | 灵活轻量框架：简化 LM 交互 + optimizer 自动优化（prompt / 权重）+ 生产化支持 |
| 三个特别之处 | LM-agnostic programming、无缝生产化（原生 + MLflow）、自动程序优化 |

> **记忆点（引出 L2）**：本课反复出现但刻意不展开的词是 **signature**——"输入输出由客户端定义"到底怎么写？L2 进入代码：用 signature + module 两个抽象搭出情感分类器，再自定义 module 做一个猜名人游戏 agent，并回答那个所有人都会问的问题——"**我的 prompt 到底在哪？**"

## 与我的资产映射

- 框架层：`agent/skills/agent-selection/2-framework/03-framework-profiles.md`——DSPy 画像的核心素材：轻量、LM-agnostic、易迁出（反锁定）、与编排框架正交
- 观测/评估层：`agent/skills/agent-selection/5-observability-eval.md`（MLflow tracing/experiments/deployments 三件套的定位）
- [[project_selection_matrix]]——roadmap 标注的"选型矩阵真缺口"，本课给出 DSPy 的官方自我定位，可直接入矩阵
