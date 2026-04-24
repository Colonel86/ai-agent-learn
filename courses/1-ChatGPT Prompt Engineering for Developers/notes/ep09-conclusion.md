# EP09: Conclusion（课程总结）

> 学习日期：2026-04-15
> 所属阶段：Phase 1 · 基石构建
> 课程来源：DeepLearning.AI × OpenAI（Andrew Ng + Isa Fulford）

---

## 课程回顾

本课程覆盖的核心内容：

1. **两大 Prompting 原则**：清晰具体的指令 + 给模型时间思考
2. **迭代开发流程**：没有完美的第一次 Prompt，关键是迭代过程
3. **四大 LLM 能力**：
   - Summarizing（摘要）
   - Inferring（推理/提取）
   - Transforming（格式转换）
   - Expanding（扩写）
4. **构建 Chatbot**：system/user/assistant 角色、上下文管理

---

## 行动建议

从 Andrew Ng 和 Isa Fulford 的建议中提炼：

- **从小项目开始**，不需要很有用，有趣就好
- **用第一个项目的经验**构建更好的第二个项目
- **负责任地使用**：LLM 影响力大，只构建对人有正向影响的东西
- **LLM 应用开发是正在爆发的领域**，现在掌握这些技能的人非常稀缺

---

## 核心知识点总结

| 主题 | 关键要点 |
|---|---|
| LLM 类型 | Instruction-tuned LLM（RLHF微调）是开发产品的首选 |
| 原则一 | 清晰具体：分隔符 / 结构化输出 / 条件检查 / Few-shot |
| 原则二 | 时间思考：指定步骤 / 指定输出格式 / 先自行推理再对比 |
| 模型局限 | 幻觉（Hallucinations）：会编造看似合理的假信息，用"先找引用再回答"缓解 |
| 迭代开发 | 无完美 Prompt，关键是开发过程（Idea→Prompt→Result→Refine） |
| 摘要 | 定向摘要 vs 精准提取（Summarize vs Extract）|
| 推理 | 情感/情绪/话题提取、Zero-Shot 分类 |
| 转换 | 翻译、语气调整、格式转换、语法校对 |
| 扩写 | Temperature 控制随机性（0=可预测, 高=创意）|
| Chatbot | system/user/assistant 三角色、上下文必须手动维护 |

---

## 个人反思与延伸问题

- [ ] 在 AI Agent 框架中，system prompt 就是 agent 的"人格设定"，和这节课的 system message 是同一概念
- [ ] Temperature 在 Agent 工具调用场景中应该用多少？（猜测：工具调用 0，生成摘要 0，创意回复可以稍高）
- [ ] Few-shot prompting 和 RAG 的关系：Few-shot 是"硬编码示例"，RAG 是"动态检索相关内容" → 下一阶段会深入
- [ ] 下一步：LangChain 如何封装这些 Prompt 模板？（Phase 1 Week 2 的学习内容）
