# EP03: Classification（输入分类 — 评估用户查询的第一步）

> 学习日期：2026-04-17
> 所属阶段：Phase 1 · 基石构建
> 课程来源：DeepLearning.AI × OpenAI · Building Systems with the ChatGPT API（Isa Fulford）

---

## 本课概览

| 主题 | 核心内容 | 重要程度 |
|---|---|---|
| 为什么要分类 | 面向多场景的系统，用分类决定"用哪套指令" | ⭐⭐⭐ |
| 一级 / 二级类别 | 先粗分大类，再细分子类，层层收敛 | ⭐⭐⭐ |
| 分隔符（Delimiter）| 用 `####` 隔离 system / user 内容，防止提示注入 | ⭐⭐⭐ |
| 结构化输出（JSON）| 键固定 → 易解析、可驱动下游逻辑 | ⭐⭐⭐ |
| 为下一步路由提供输入 | 分类结果用于挑选后续的专用指令集 | ⭐⭐ |
| 客户服务场景 | 计费 / 技术支持 / 账户管理 / 一般咨询 | ⭐⭐ |

> **关键洞察**：当一个系统要处理多种独立任务时，与其在一个"万能 Prompt"里塞下所有规则，不如先**分类**，再根据分类**路由**到各自的专用指令——这是构建复杂 LLM 系统的基础模式。

---

## 一、为什么要先分类

### 1.1 问题背景

一个真实的 LLM 应用（如客服助手）通常要面对**多种独立的用户意图**：

- 有人想关闭账户
- 有人询问某款产品
- 有人反馈技术故障
- 有人问一般性问题

如果把所有处理逻辑都塞进一个巨型 system message，会导致：
- Prompt 越来越长、越来越难维护
- 模型容易混淆不同场景下的规则
- Token 开销大

### 1.2 解决思路：分类 + 路由

**两步走**：
1. **分类（Classify）**：先识别用户查询属于哪个类别
2. **路由（Route）**：根据类别，加载专门为这类任务写好的指令

> 这其实就是软件工程里的 `switch/case` 思想——只不过每个 `case` 里装的是一段"硬编码"的 Prompt 片段。

---

## 二、分隔符（Delimiter）

### 2.1 为什么需要分隔符

System message 里既要描述"规则"，又要插入"用户消息"。模型怎么知道哪段是指令、哪段是用户内容？——用**分隔符**明确分界。

### 2.2 为什么选 `####`（四个井号）

| 分隔符 | 优点 | 缺点 |
|---|---|---|
| `####` | **在 tokenizer 中被表示为 1 个 Token**，省开销 | 美观度一般 |
| `"""` | 可读性好 | 可能占多个 Token |
| `<xml>` | 结构化 | 啰嗦 |
| 换行 | 自然 | 模型可能混淆边界 |

### 2.3 附加好处：防提示注入

用分隔符把用户输入包起来，相当于给模型一个明确信号："这之间的内容是**数据**，不是**指令**"。

---

## 三、System Message 的写法

### 3.1 完整示例

```text
You will be provided with customer service queries.
The customer service query will be delimited with #### characters.

Classify each query into a primary category and a secondary category.
Provide your output in JSON format with the keys: primary and secondary.

Primary categories:
  - Billing
  - Technical Support
  - Account Management
  - General Inquiry

Billing secondary categories:
  - Unsubscribe or upgrade
  - Add a payment method
  - Explanation for charge
  - Dispute a charge

Account Management secondary categories:
  - Password reset
  - Update personal information
  - Close account
  - Account security

...（其他类别省略）
```

### 3.2 三个关键设计

1. **告知输入格式**：明确说 query 会被 `####` 包围
2. **要求结构化输出**：指定 JSON schema（`primary` / `secondary`）
3. **枚举所有合法类别**：杜绝模型自己发明新类别

---

## 四、Python 代码实现

### 4.1 构造 messages

```python
delimiter = "####"
system_message = f"""
You will be provided with customer service queries.
The customer service query will be delimited with {delimiter} characters.
Classify each query into a primary category and a secondary category.
Provide your output in json format with the keys: primary and secondary.

Primary categories: Billing, Technical Support, Account Management, or General Inquiry.

Billing secondary categories:
Unsubscribe or upgrade
Add a payment method
Explanation for charge
Dispute a charge

Technical Support secondary categories:
General troubleshooting
Device compatibility
Software updates

Account Management secondary categories:
Password reset
Update personal information
Close account
Account security

General Inquiry secondary categories:
Product information
Pricing
Feedback
Speak to a human
"""
```

### 4.2 第一个用户消息：关闭账户

```python
user_message = f"""\
I want you to delete my profile and all of my user data"""

messages = [
    {'role': 'system', 'content': system_message},
    {'role': 'user',   'content': f"{delimiter}{user_message}{delimiter}"},
]

response = get_completion_from_messages(messages)
print(response)
```

**期望输出**：

```json
{
  "primary": "Account Management",
  "secondary": "Close account"
}
```

### 4.3 第二个用户消息：询问产品

```python
user_message = f"""\
Tell me more about your flat screen tvs"""

messages = [
    {'role': 'system', 'content': system_message},
    {'role': 'user',   'content': f"{delimiter}{user_message}{delimiter}"},
]

response = get_completion_from_messages(messages)
print(response)
```

**期望输出**：

```json
{
  "primary": "General Inquiry",
  "secondary": "Product information"
}
```

---

## 五、为什么要 JSON 格式输出

### 5.1 下游可编程

```python
import json

result = json.loads(response)
primary = result["primary"]         # "Account Management"
secondary = result["secondary"]     # "Close account"

# 用分类结果驱动路由
if primary == "Account Management" and secondary == "Close account":
    next_instructions = ACCOUNT_CLOSURE_PROMPT
elif primary == "General Inquiry" and secondary == "Product information":
    next_instructions = PRODUCT_INFO_PROMPT
# ...
```

### 5.2 结构化的三点好处

1. **易解析**：直接 `json.loads`，不用写正则
2. **可验证**：能 schema 检验，错了可以重试
3. **跨语言**：Python 读成 dict，JS 读成 object，通用性强

---

## 六、分类 → 路由的整体架构

```
┌──────────────┐      ┌──────────┐      ┌─────────────────────────┐
│ 用户查询      │ ───▶ │ 分类模型  │ ───▶│ primary + secondary     │
└──────────────┘      └──────────┘      └─────────────┬───────────┘
                                                       │
                    ┌──────────────────────────────────┴─┐
                    │                                    │
                    ▼                                    ▼
        ┌──────────────────┐                ┌──────────────────┐
        │ 账户管理专用指令   │                │ 产品咨询专用指令   │
        │ （含关闭链接等） │                │ （含产品信息等）   │
        └──────────────────┘                └──────────────────┘
                    │                                    │
                    ▼                                    ▼
              最终回复                             最终回复
```

---

## 七、实践要点

### 7.1 何时适用分类

- ✅ 场景差异大、规则各自独立（客服、工单系统、智能助理）
- ✅ 需要针对不同意图加载不同工具 / 知识
- ❌ 单一任务（例如"翻译英文到中文"）——不需要分类

### 7.2 设计类别时的坑

| 坑 | 表现 | 解决 |
|---|---|---|
| 类别重叠 | 模型在两个类别之间反复横跳 | 类别定义要互斥（MECE 原则） |
| 类别过细 | 分类错误率高 | 先粗分再细分，两级足矣 |
| 遗漏兜底 | 奇怪的查询无处归类 | 必带 "General Inquiry / 其他" |

### 7.3 可观测性

- 记录每次分类结果，定期检查 **置信度分布**
- 用小样本人工校验分类准确率
- 当某类二级分类频繁被选到时，考虑提升为一级

---

## 八、与 AI Agent 的关联

> 本课的"分类 → 路由"模式，其实就是 Agent 中 **Router / Dispatcher** 模块的雏形。

在后面的 Agent 架构里会看到更复杂的版本：
- Router 不仅分类，还决定调用哪个工具 / 哪个子 Agent
- 分类结果变成 **Tool Call** 的参数
- 配合 Function Calling / Structured Output 更严格地约束模型

**本课的分类**，是**无工具调用版本**的 Router——理解了这个，就理解了 Agent 路由的骨架。

---

## 九、预告：下一节

下一节将讨论**另一种评估输入的方式**——如何确保用户以**负责任**的方式使用系统（防止滥用、攻击、越狱等），也就是 Moderation API 和 Prompt Injection 防护。
