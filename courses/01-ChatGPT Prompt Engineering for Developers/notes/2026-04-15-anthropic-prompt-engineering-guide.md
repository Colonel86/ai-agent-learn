# Anthropic Prompt Engineering Guide 学习笔记

> 学习日期：2026-04-15
> 所属阶段：Phase 1 · 第 1-4 周
> 资料来源：Anthropic 官方文档 + 互动教程（GitHub）
> 预计耗时：4-6h

---

## 背景：为什么学 Anthropic 的 Prompt Engineering？

已完成 DeepLearning.AI 的 "ChatGPT Prompt Engineering for Developers"（OpenAI 视角）。  
Anthropic 这套指南是 **Claude 专属** 的，有一些重要差异：

| 维度 | OpenAI 课程 | Anthropic 指南 |
|------|------------|----------------|
| 模型背景 | GPT 系列 | Claude 系列 |
| XML 标签 | 不强调 | ⭐ **核心技巧**（Claude 专门训练了 XML 识别） |
| 系统提示 | system message | system prompt（概念一致，但用法更丰富） |
| 幻觉防止 | 少量提及 | 有专章（Chapter 8） |
| 互动教程 | Jupyter 课程为主 | 9章 Notebook + Google Sheets 版本 |

---

## 核心概念

### 概念 1：Claude 的工作原理（Before You Prompt）

- **定义**：Claude 是一个文字接龙预测器（token predictor），通过人类反馈微调（RLHF）后具备了遵循指令、有帮助、无害的特性
- **为什么重要**：理解"它在预测下一个 token"有助于你设计更好的提示——给它好的开头，它就会续写好的内容
- **关键要点**：
  - Claude 没有内置记忆，每次对话都是全新的
  - Claude 4 系列（Opus 4.6 / Sonnet 4.6 / Haiku 4.5）更精确地遵循字面指令，"超出期望"的行为减少了
  - Claude 被专门训练来识别 XML 标签的层级结构

---

### 概念 2：提示的基础结构

Claude 的提示有两个主要位置：

```
System Prompt（系统提示）
  └─ 角色设定、背景规则、输出格式要求、固定上下文

Human Turn（用户轮次）
  └─ 具体任务、数据、当前问题
```

**与 OpenAI 对比**：
- OpenAI：`system` / `user` / `assistant` 三个角色
- Anthropic：`system` + `user`/`assistant` 交替，概念一致但 system prompt 功能更强大

**最佳实践**：
- 规则、角色、格式 → 放 System Prompt
- 任务数据、当前问题 → 放 Human Turn
- 用 XML 标签区分两者：`<instructions>`, `<context>`, `<task>`

---

### 概念 3：清晰直接（Be Clear and Direct）

Claude 的 Prompt Engineering 第一原则：**直接告诉它你要什么**。

❌ 模糊："写点关于气候变化的东西"  
✅ 清晰："用 3 段话向高中生解释气候变化的主要原因，每段不超过 50 字，语气友好"

**Claude 4 特别注意**：新版 Claude 会**字面执行**你的指令，不会自动"超出期望"。如果你想要更详尽的分析，要明确要求。

---

### 概念 4：XML 标签（Claude 独有的超强技巧）⭐

Claude 被专门训练来理解 XML 层级结构，这是它与 GPT 最大的提示差异。

**基础用法**：
```xml
<instructions>
  你是一位专业的产品经理，用简洁、结构化的语言回答问题。
</instructions>

<context>
  我们正在开发一款面向个人用户的任务管理 App。
</context>

<task>
  列出 5 个核心功能，每个功能附上一句话说明。
</task>
```

**进阶用法 - 与 Chain of Thought 结合**：
```xml
<thinking>
  [让 Claude 在这里思考，不显示给用户]
</thinking>

<answer>
  [最终答案]
</answer>
```

**常用标签对照表**：

| 标签 | 用途 |
|------|------|
| `<instructions>` | 任务指令 |
| `<context>` | 背景上下文 |
| `<examples>` | 示例（配合 multishot） |
| `<task>` | 当前具体任务 |
| `<thinking>` | 推理过程（CoT scratchpad） |
| `<answer>` | 最终输出 |
| `<document>` | 传入文档内容 |
| `<formatting>` | 输出格式要求 |

---

### 概念 5：Multishot Prompting（多样本提示）

提供 3-5 个示例，让 Claude 学习你期望的输出格式和风格。

```xml
<examples>
  <example>
    <input>用户输入：苹果手机太贵了</input>
    <output>情感：负面 | 主题：价格 | 实体：苹果手机</output>
  </example>
  <example>
    <input>用户输入：这个 App 好用极了</input>
    <output>情感：正面 | 主题：体验 | 实体：App</output>
  </example>
</examples>
```

**与 OpenAI 课程的关联**：这等同于课程里的 "few-shot learning"，但 Anthropic 建议用 XML 标签包裹示例，结构更清晰。

---

### 概念 6：逐步思考（Chain of Thought / Precognition）

让 Claude 在回答前先推理，显著提升复杂任务准确率。

**三种深度**：

```
# 基础版（一句话触发）
"请一步一步思考，然后给出答案。"

# 引导版（给出思考框架）
"先分析问题，再考虑可能的解决方案，最后给出建议。"

# 结构版（XML 分离推理和答案）
<thinking>
  Claude 在这里推理...
</thinking>
<answer>
  最终答案...
</answer>
```

**Precognition（预认知）的特殊用法**：在判断题或有争议的问题中，先让 Claude 考虑双方论点，再得出结论——避免"锚定效应"（回答过早被第一印象锁定）。

---

### 概念 7：避免幻觉

**核心方法**：让 Claude 先提取证据，再基于证据回答。

```
你的任务是回答关于文档的问题。
步骤：
1. 先从文档中找到所有相关引用，列在 <quotes> 标签中
2. 检查这些引用是否足以回答问题
3. 如果不足，说明"文档中没有相关信息"
4. 如果足够，基于引用给出答案

<document>
  [文档内容]
</document>

问题：[问题]
```

---

### 概念 8：角色扮演（Role Prompting）

通过 system prompt 给 Claude 一个角色，将其从通用助手变成领域专家。

```python
system_prompt = """
You are Dr. Chen, a senior data scientist at a fintech company.
You have 10+ years of experience in machine learning and risk modeling.
When answering, think like a practitioner who has shipped production ML systems.
"""
```

**关键技巧**：给角色具体的背景（行业、经验、思维方式），比简单说"你是专家"效果好得多。

---

## 9 章课程大纲（互动教程）

| 章节 | 主题 | 难度 | 核心技能 |
|------|------|------|----------|
| Ch 1 | Basic Prompt Structure | ⭐ | system/human 结构 |
| Ch 2 | Being Clear and Direct | ⭐ | 清晰指令 |
| Ch 3 | Assigning Roles | ⭐ | 角色扮演 |
| Ch 4 | Separating Data from Instructions | ⭐⭐ | 数据与指令分离 |
| Ch 5 | Formatting Output | ⭐⭐ | 输出格式控制 |
| Ch 6 | Precognition (Thinking Step by Step) | ⭐⭐ | CoT + XML 推理 |
| Ch 7 | Using Examples (Multishot) | ⭐⭐ | Few-shot learning |
| Ch 8 | Avoiding Hallucinations | ⭐⭐⭐ | 先提取证据再回答 |
| Ch 9 | Complex Prompts (Industry Cases) | ⭐⭐⭐ | 综合实战 |
| Appendix | Advanced Methods | ⭐⭐⭐⭐ | 更多高级技巧 |

---

## 学习资源

| 资源 | 类型 | 链接 | 状态 |
|------|------|------|------|
| Anthropic Prompt Engineering 概览 | 官方文档 | [链接](https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/overview) | ✅ 已读 |
| Claude 4 最佳实践 | 官方文档 | [链接](https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/claude-4-best-practices) | 待读 |
| 互动教程（GitHub Jupyter Notebooks）| 实践课程 | [链接](https://github.com/anthropics/prompt-eng-interactive-tutorial) | 🔲 未开始 |
| XML 标签使用指南 | 官方文档 | [链接](https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/use-xml-tags) | 🔲 未开始 |
| Multishot Prompting 指南 | 官方文档 | [链接](https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/multishot-prompting) | 🔲 未开始 |
| Long Context Prompting Tips | 官方文档 | [链接](https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/long-context-tips) | 🔲 未开始 |
| Prompt Generator（自动生成提示）| 工具 | [链接](https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/prompt-generator) | 🔲 未开始 |
| Prompt Library（提示词库）| 参考库 | [链接](https://docs.anthropic.com/en/prompt-library/library) | 🔲 未开始 |

---

## Anthropic vs OpenAI Prompt Engineering 对比总结

| 技巧 | OpenAI 课程 | Anthropic 指南 | 备注 |
|------|------------|----------------|------|
| 清晰直接 | ✅ 强调 | ✅ 强调 | 共同基础 |
| 系统提示 | ✅ system message | ✅ system prompt | 概念一致 |
| 角色扮演 | ✅ 有示例 | ✅ 有专章（Ch 3） | Anthropic 更详细 |
| Few-shot | ✅ 有示例 | ✅ Multishot（Ch 7）| Anthropic 推荐 XML 包裹 |
| Chain of Thought | ✅ 一句话触发 | ✅ 三种深度 + Precognition | Anthropic 更系统 |
| XML 标签 | ❌ 未提及 | ⭐ **核心特性** | Anthropic 独有 |
| 幻觉防止 | ⚠️ 简单提及 | ✅ 有专章（Ch 8） | Anthropic 更详细 |
| 温度（Temperature）| ✅ EP07 专门讲解 | ⚠️ 简单提及 | OpenAI 课程更系统 |
| 消息历史管理 | ✅ EP08 详细讲解 | ⚠️ 简单提及 | OpenAI 课程更系统 |
| Prompt 自动生成 | ❌ | ✅ Console 工具 | Anthropic 特有工具 |

---

## 关键代码示例

### 最佳实践：完整结构化 Prompt

```python
import anthropic

client = anthropic.Anthropic()

system_prompt = """
<role>
你是一位资深的 Python 代码审查员，专注于代码质量、性能和安全性。
</role>

<instructions>
审查用户提交的代码时：
1. 首先识别潜在的 bug 和安全漏洞
2. 然后评估代码风格和可读性
3. 最后给出改进建议，并提供修改后的代码示例
</instructions>

<output_format>
请用以下格式输出：
- 问题列表（按严重程度排序）
- 改进建议
- 修改后的代码
</output_format>
"""

message = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    system=system_prompt,
    messages=[
        {
            "role": "user",
            "content": """
<task>请审查以下代码：</task>

<code>
def get_user(user_id):
    query = "SELECT * FROM users WHERE id = " + user_id
    return db.execute(query)
</code>
"""
        }
    ]
)

print(message.content[0].text)
```

### Chain of Thought + XML 分离推理

```python
message = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=2048,
    messages=[
        {
            "role": "user",
            "content": """
分析这个商业决策，先在 <thinking> 里思考，再在 <answer> 里给出建议。

场景：一家 SaaS 公司考虑将月订阅价格从 $29 提高到 $39，当前有 1000 名用户，月流失率 5%。

<thinking>
请在这里分析：
- 价格提升对收入的影响
- 可能引起的用户流失
- 综合 ROI 计算
</thinking>

<answer>
请在这里给出最终建议。
</answer>
"""
        }
    ]
)
```

---

## 互动教程学习计划

建议按以下顺序完成 GitHub 上的 Jupyter Notebook 教程：

**第一天（1-2h）**：Ch 1-3（基础结构 + 清晰指令 + 角色）
**第二天（1-2h）**：Ch 4-5（数据隔离 + 格式控制）
**第三天（1-2h）**：Ch 6-7（CoT + Multishot）
**第四天（1-2h）**：Ch 8-9 + Appendix（幻觉防止 + 综合实战）

---

## 思考与总结

（学完互动教程后填写）

- 最大的收获：
- 与 OpenAI 课程最大的差异：
- 在项目中如何应用 XML 标签：
- 还有什么不清楚的：

---

## 下一步

1. **立即**：完成 GitHub 互动教程的 9 章 Notebooks（克隆到本地运行）
2. **本周**：阅读 [Claude 4 最佳实践](https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/claude-4-best-practices) 官方文档
3. **实战**：用 Anthropic SDK 重写 EP08 的 OrderBot，加入 XML 标签
4. **Phase 1 收尾**：完成多模型 CLI 工具（支持 GPT-4 + Claude 切换）
