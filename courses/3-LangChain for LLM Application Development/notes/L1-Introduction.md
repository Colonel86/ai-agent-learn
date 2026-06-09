# Introduction - LangChain for LLM Application Development

## 课程背景

通过 prompt LLM，现在可以比以往更快地开发 AI 应用。但实际应用往往需要多次调用 LLM、解析输出，并编写大量"胶水代码"（glue code）。LangChain 正是为了解决这个问题而生。

---

## 什么是 LangChain

**LangChain** 是由 Harrison Chase 创建的开源框架，用于构建 LLM 应用。

- **语言支持**：Python 和 JavaScript 两个版本
- **核心设计理念**：组合性（Composition）和模块化（Modularity）
- **价值主张**：
  - 提供大量可独立使用或组合使用的模块化组件
  - 将组件串联成端到端的使用链（Chains / Agents）

---

## 课程涵盖内容

| 模块 | 说明 |
|------|------|
| **Models** | 封装底层 LLM，统一调用接口 |
| **Prompts** | 如何让模型做有价值的事 |
| **Output Parsers** | 将 LLM 的自由文本输出解析为结构化数据（如 JSON、字段对象），便于下游程序使用 |
| **Indexes** | 数据摄入方式，将私有数据与模型结合 |
| **Chains** | 端到端的使用链，串联多个组件 |
| **Agents** | 用模型作为推理引擎的高级用例 |

---

## 创始团队

- **Harrison Chase** — LangChain 创始人，本课程讲师
- **Ankush Gola** — LangChain 联合创始人，参与课程内容设计
- **Andrew Ng（吴恩达）** — DeepLearning.AI，课程合作方

DeepLearning.AI 制作团队：Geoff Ludwig、Eddy Shyu、Diala Ezzeddine

---

## 学完课程你能做什么

- 快速用 LangChain 构建实用 LLM 应用
- 理解 LangChain 的核心抽象，举一反三
- 有能力为 LangChain 开源社区贡献代码

---

## 课程结构

```
Introduction（本节）
  └── L1: Models, Prompts, and Output Parsers
  └── L2: Memory
  └── L3: Chains
  └── L4: Q&A over Documents
  └── L5: Evaluation
  └── L6: Agents
```
