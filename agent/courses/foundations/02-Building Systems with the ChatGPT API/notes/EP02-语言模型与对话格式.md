# EP02: Language Models, the Chat Format and Tokens（语言模型、对话格式与 Token）

> 学习日期：2026-04-16
> 所属阶段：Phase 1 · 基石构建
> 课程来源：DeepLearning.AI × OpenAI · Building Systems with the ChatGPT API（Andrew Ng + Isa Fulford）

---

## 本课概览

| 主题 | 核心内容 | 重要程度 |
|---|---|---|
| LLM 工作原理 | 监督学习 → 反复预测下一个词 | ⭐⭐⭐ |
| 基础 LLM vs 指令微调 LLM | Base LLM 只会续写；Instruction Tuned LLM 会遵循指令 | ⭐⭐⭐ |
| RLHF 训练流程 | 人类反馈 → 强化学习 → 提高输出质量 | ⭐⭐⭐ |
| Token 与分词器 | LLM 预测的是 Token 而非单词；分词方式影响任务表现 | ⭐⭐⭐ |
| Chat Format（对话格式）| system / user / assistant 三种消息角色 | ⭐⭐⭐ |
| Token 计数与限制 | GPT-3.5-turbo 约 4000 token 上限 | ⭐⭐ |
| API 密钥安全 | 使用 dotenv 而非明文写入 notebook | ⭐⭐ |

> **关键洞察**：提示工程（Prompting）正在革命性地改变 AI 应用开发——过去需要数月的工作，现在可能只需数分钟到数小时。

---

## 一、LLM 的工作原理

### 1.1 监督学习：核心构建模块

LLM 训练的主要方法是**监督学习**——计算机通过有标签的训练数据学习输入到输出（X → Y）的映射关系。

**传统例子：** 情感分类
- "The pastrami sandwich is great!" → 正面
- "Service was slow, the food was so-so." → 负面

**LLM 的做法：** 反复预测下一个词

给定训练句子 "My favorite food is a bagel with cream cheese and lox."：
- 输入 "My favorite food is a" → 预测 "bagel"
- 输入 "My favorite food is a bagel" → 预测 "with"
- 以此类推……

在数千亿词的训练集上重复此过程，就构建了大语言模型。

### 1.2 基础 LLM vs 指令微调 LLM

| | 基础 LLM（Base LLM） | 指令微调 LLM（Instruction Tuned LLM） |
|---|---|---|
| 行为 | 根据训练数据续写文本 | 尝试遵循指令回答问题 |
| 示例输入 | "What is the capital of France?" | "What is the capital of France?" |
| 典型输出 | "What is France's largest city? What is France's population?" | "The capital of France is Paris." |
| 代表模型 | GPT-3 基座模型 | ChatGPT、GPT-4 |

**问题根源：** 基础 LLM 在互联网上学到的是"问题后面通常跟着更多问题"，而不是"问题后面应该跟着答案"。

### 1.3 训练指令微调 LLM 的流程（如 ChatGPT）

1. **训练基础模型** — 在数千亿词上训练，需要数月时间和大型超级计算系统
2. **指令微调** — 在较小的"指令-回应"示例集上微调模型
3. **人类评级** — 让人类对多个 LLM 输出按照"有帮助、诚实、无害"等标准评分
4. **RLHF（基于人类反馈的强化学习）** — 进一步微调模型，提高生成高评分输出的概率

> **时间对比：** 训练基础模型需要数月；从基础模型到指令微调模型只需数天，所需数据和计算资源也小得多。

---

## 二、代码设置

### 2.1 加载 API 密钥

使用 `dotenv` 库从本地 `.env` 文件中安全加载密钥，**不要**在 notebook 中明文写入：

```python
import os
import openai
import tiktoken
from dotenv import load_dotenv, find_dotenv
_ = load_dotenv(find_dotenv())  # 读取本地 .env 文件

openai.api_key = os.environ['OPENAI_API_KEY']
```

### 2.2 辅助函数：get_completion

接收一个 prompt，返回模型的补全结果。

**OpenAI 库 v0.27.0 版本：**

```python
def get_completion(prompt, model="gpt-3.5-turbo"):
    messages = [{"role": "user", "content": prompt}]
    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        temperature=0,  # temperature 为 0 表示输出确定性最高
    )
    return response.choices[0].message["content"]
```

**OpenAI 库 v1.0.0+ 版本：**

```python
client = openai.OpenAI()

def get_completion(prompt, model="gpt-3.5-turbo"):
    messages = [{"role": "user", "content": prompt}]
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0,
    )
    return response.choices[0].message.content
```

### 2.3 基本调用

```python
response = get_completion("What is the capital of France?")
print(response)
# 输出：The capital of France is Paris.
```

---

## 三、Token 与分词器

### 3.1 核心概念：LLM 预测的是 Token，不是单词

LLM 将输入的字符序列分组成 **Token（词元）**，每个 Token 是一组常见的字符组合。

| 输入文本 | Token 划分 | 说明 |
|---|---|---|
| "Learning new things is fun!" | [Learning] [new] [things] [is] [fun] [!] | 常见词 → 每个词一个 Token |
| "Prompting" | [prom] [pt] [ing] | 不常见词 → 被拆成多个 Token |
| "lollipop" | [l] [oll] [ipop] | 被拆成 3 个 Token，模型看不到单个字母 |

### 3.2 Lollipop 问题

因为 "lollipop" 被分词为 `[l][oll][ipop]`，模型无法看到单个字母，所以**无法正确反转字母**：

```python
response = get_completion("Take the letters in lollipop \
and reverse them")
print(response)
# 输出错误！不是 "popillol"
```

### 3.3 解决技巧：加分隔符

在字母之间加连字符，让每个字符成为独立 Token：

```python
response = get_completion("""Take the letters in \
l-o-l-l-i-p-o-p and reverse them""")
print(response)
# 现在正确输出：p-o-p-i-l-l-o-l
```

> **实用技巧：** 如果用 ChatGPT 玩 Wordle、Scrabble 等文字游戏，用这个方法帮助模型识别单个字母。

### 3.4 Token 限制

- 英语中 1 个 Token ≈ 4 个字符 ≈ 0.75 个单词
- 输入称为 **context（上下文）**，输出称为 **completion（补全）**
- GPT-3.5-turbo：输入 + 输出合计约 **4,000 Token** 上限
- 超出限制会抛出异常/报错

---

## 四、对话格式（Chat Format）

### 4.1 三种消息角色

| 角色 | 作用 | 示例 |
|---|---|---|
| **system** | 设定助手的整体行为和语气 | "You are an assistant who responds in the style of Dr Seuss." |
| **user** | 用户的具体指令或问题 | "write me a very short poem about a happy carrot" |
| **assistant** | 模型之前的回复（用于多轮对话） | 上一轮模型输出的内容 |

### 4.2 辅助函数：get_completion_from_messages

```python
def get_completion_from_messages(messages,
                                 model="gpt-3.5-turbo",
                                 temperature=0,
                                 max_tokens=500):
    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        temperature=temperature,  # 随机性程度
        max_tokens=max_tokens,    # 最大输出 token 数
    )
    return response.choices[0].message["content"]
```

### 4.3 示例：Dr. Seuss 风格

```python
messages = [
    {'role': 'system',
     'content': 'You are an assistant who responds in the style of Dr Seuss.'},
    {'role': 'user',
     'content': 'write me a very short poem about a happy carrot'},
]
response = get_completion_from_messages(messages, temperature=1)
print(response)
# 输出：一首苏斯博士风格的快乐胡萝卜诗歌
```

### 4.4 控制输出长度

```python
messages = [
    {'role': 'system',
     'content': 'All your responses must be one sentence long.'},
    {'role': 'user',
     'content': 'write me a story about a happy carrot'},
]
response = get_completion_from_messages(messages, temperature=1)
print(response)
# 输出：只有一个句子的故事
```

### 4.5 组合风格和长度

```python
messages = [
    {'role': 'system',
     'content': """You are an assistant who responds in the style of Dr Seuss. \
All your responses must be one sentence long."""},
    {'role': 'user',
     'content': 'write me a story about a happy carrot'},
]
response = get_completion_from_messages(messages, temperature=1)
print(response)
# 输出：一句话的苏斯博士风格诗句
```

---

## 五、Token 计数

### 5.1 辅助函数：get_completion_and_token_count

同时返回回复内容和 Token 使用量：

```python
def get_completion_and_token_count(messages,
                                   model="gpt-3.5-turbo",
                                   temperature=0,
                                   max_tokens=500):

    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )

    content = response.choices[0].message["content"]

    token_dict = {
        'prompt_tokens': response['usage']['prompt_tokens'],
        'completion_tokens': response['usage']['completion_tokens'],
        'total_tokens': response['usage']['total_tokens'],
    }

    return content, token_dict
```

### 5.2 使用示例

```python
messages = [
    {'role': 'system',
     'content': 'You are an assistant who responds in the style of Dr Seuss.'},
    {'role': 'user',
     'content': 'write me a very short poem about a happy carrot'},
]
response, token_dict = get_completion_and_token_count(messages)
print(response)
print(token_dict)
# 示例输出：prompt_tokens=37, completion_tokens=55, total_tokens=92
```

> **实践建议：** 大多数情况下不需要太担心 Token 数量。唯一需要关注的场景是当用户输入可能超过 4000 Token 限制时，此时应检查并截断输入。

---

## 六、API 密钥安全

**❌ 错误做法 — 明文写入 notebook：**
```python
openai.api_key = "sk-..."  # 千万不要这样做！
```

**✅ 正确做法 — 使用 dotenv：**
```python
# 1. 创建本地 .env 文件（不要提交到 Git）：
#    OPENAI_API_KEY=sk-...

# 2. 在 notebook 中加载：
from dotenv import load_dotenv, find_dotenv
_ = load_dotenv(find_dotenv())
openai.api_key = os.environ['OPENAI_API_KEY']
```

**原因：** Notebook 太容易被分享到 GitHub 或发给他人，导致 API 密钥泄露。`dotenv` 方法可以安全地从本地文件加载密钥，适用于管理任何在线服务的 API 密钥。

---

## 七、Prompting vs 传统机器学习

| 步骤 | 传统监督学习 | 基于 Prompting |
|---|---|---|
| 数据收集 | 数周 ~ 数月 | 不需要 |
| 模型训练 | 数天 ~ 数月 | 数分钟（编写 prompt） |
| 部署上线 | 数天 ~ 数周 | 数小时（API 调用） |
| **总计** | **数月** | **数分钟 ~ 数小时** |

**适用范围：** 非结构化数据应用（尤其是文本），以及越来越多的视觉应用。**不适用于**结构化表格数据（如 Excel 中的数值数据）。

> **与 AI Agent 的关联：** 这种快速构建 AI 应用的能力，是 AI Agent 能够实用化的重要基础——Agent 的每个模块都可以用 Prompt 快速搭建和迭代。
