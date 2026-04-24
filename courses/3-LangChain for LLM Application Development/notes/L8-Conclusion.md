# Conclusion - 课程总结

## 课程回顾

本课程演示了一系列 LLM 应用的快速构建，包括：

- **处理客户评论** — 使用 PromptTemplate + OutputParser 提取结构化信息
- **文档问答系统** — 基于 Embedding + Vector Store 回答私有文档中的问题
- **智能 Agent** — 让 LLM 自主决定何时调用外部工具（如网络搜索）来回答复杂问题

---

## 核心收获

这些应用在一两周前看起来需要**数周甚至更长时间**才能完成。但通过 LangChain，只需**相当少量的代码**就能高效实现。

---

## 这只是开始

LLM 的应用场景远不止这些，模型的强大在于其广泛的适用性：

| 场景 | 说明 |
|------|------|
| CSV 问答 | 对表格数据直接提问 |
| SQL 数据库查询 | 用自然语言查关系型数据库 |
| API 交互 | 通过 LLM 调用第三方服务 |
| 自定义 Chain | 组合 Prompt、OutputParser、Chain 实现任意流程 |

这些能力大多来自 **LangChain 社区**的贡献——无论是改进文档、降低上手门槛，还是开发新类型的 Chain。

---

## 下一步行动

```bash
pip install langchain langchain-openai
```

把课程中的代码片段带到你自己的项目里，开始构建吧。

---

## 课程结构回顾

```
Introduction
  ├── L1: Models, Prompts, and Output Parsers  → 三大基础抽象
  ├── L2: Memory                               → 管理对话历史
  ├── L3: Chains                               → 串联组件成流水线
  ├── L4: Q&A over Documents                  → Embedding + 文档问答
  ├── L5: Evaluation                           → LLM 应用质量评估
  └── L6: Agents                               → LLM 作为推理引擎
Conclusion（本节）
```
