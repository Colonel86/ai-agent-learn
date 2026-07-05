# EP01: Introduction

> 学习日期：2026-04-15
> 所属阶段：Phase 1 · 基石构建
> 课程来源：DeepLearning.AI × OpenAI（Andrew Ng + Isa Fulford）

---

## 核心结论

**这门课的重点不是"怎么跟 ChatGPT 聊天"，而是"怎么用 LLM API 构建产品"。**

网上大量 Prompt 技巧文章（比如"30 个必知 Prompt"）主要针对 ChatGPT 网页界面的一次性任务。但作为开发者，真正的价值在于通过 API 调用 LLM 快速构建软件应用——这一点目前还被严重低估。

---

## 知识点 1：Base LLM vs Instruction-tuned LLM


|           | **Base LLM**                                                                                              | **Instruction Tuned LLM**                        |
| --------- | --------------------------------------------------------------------------------------------------------- | ------------------------------------------------ |
| **核心行为**  | Predicts next word, based on text training data                                                           | Tries to follow instructions                     |
| **训练方式**  | 海量文本预训练                                                                                                   |                                                  |
| **关键技术**  | —                                                                                                         | RLHF: Reinforcement Learning with Human Feedback |
| **设计目标**  | —                                                                                                         | Helpful, Honest, Harmless                        |
| **输入示例**  | "Once upon a time, there was a unicorn"                                                                   | "What is the capital of France?"                 |
| **输出示例**  | "that lived in a magical forest with all her unicorn friends"（续写故事）                                       | "The capital of France is Paris."（直接回答）          |
| **另一个输入** | "What is the capital of France?"                                                                          | —                                                |
| **另一个输出** | "What is France's largest city? / What is France's population? / What is the currency of France?"（生成相关问题） | —                                                |
| **推荐程度**  | 不推荐直接用于产品                                                                                                 | ✅ 推荐，本课程重点                                       |


**RLHF**（Reinforcement Learning from Human Feedback）= 人类反馈强化学习，是让模型更"听话"的关键技术。

---

## 知识点 2：如何跟 Instruction-tuned LLM 沟通

把它想象成**一个聪明但不了解你具体任务的新同事**：

- ❌ "帮我写点关于图灵的东西"
- ✅ "用专业记者的风格，写一篇 500 字关于图灵在计算机科学史上贡献的文章，重点在他的学术成就，不涉及个人生活"

越清晰的指令 → 越好的输出。

---

## 本课程覆盖内容（预告）

1. Prompting 最佳实践（软件开发视角）
2. 常见使用场景：
  - 总结（Summarizing）
  - 推理（Inferring）
  - 转换（Transforming）
  - 扩写（Expanding）
3. 用 LLM 构建一个 Chatbot

