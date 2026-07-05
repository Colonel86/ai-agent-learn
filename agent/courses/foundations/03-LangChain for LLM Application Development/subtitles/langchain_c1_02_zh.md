# LangChain for LLM Application Development — 第02课：模型、提示词与解析器（中文字幕）

---

在第一课中，我们将介绍**模型（Models）**、**提示词（Prompts）**和**解析器（Parsers）**。

- **模型**：指底层的语言模型
- **提示词**：指创建输入并传递给模型的方式
- **解析器**：位于流程的另一端，负责获取模型的输出并将其解析为更结构化的格式，以便在下游处理中使用

当你使用 LLM 构建应用时，通常会有可复用的模型——反复提示模型、解析输出。LangChain 为此类操作提供了一套简洁的抽象。

---

## 入门代码

首先，导入 `os` 和 `openai`，并加载 OpenAI 密钥。如果你在本地运行且尚未安装 OpenAI，可以运行 `pip install openai`。

以下是一个辅助函数示例，与 ChatGPT 提示工程课程中的函数类似。使用 `get_completion("1加1是多少")`，即可调用 GPT-3.5 Turbo 获取答案。

---

## 使用 LangChain 的动机示例

假设你收到一封用"海盗英语"写的客户邮件：

> "我的搅拌机盖子飞出来，把我的厨房墙壁都溅上了冰沙，我气得不行。更糟糕的是，保修不包含清理厨房的费用。伙计，我现在急需你的帮助。"

我们希望将其翻译为"平静、礼貌的美式英语"。

用 f-string 构建提示词，指定将三重反引号内的文本转换为目标风格。这样可以生成提示词，驱动 LLM 输出翻译结果。

---

## 使用 LangChain 的 ChatOpenAI

```python
from langchain.chat_models import ChatOpenAI
chat = ChatOpenAI(temperature=0.0)
```

`temperature=0` 表示输出更确定性、减少随机性（默认值为 0.7）。

---

## Prompt Templates（提示词模板）

```python
from langchain.prompts import ChatPromptTemplate

template_string = """将三重反引号内的文本翻译为 {style} 风格：
\`\`\`{text}\`\`\`"""

prompt_template = ChatPromptTemplate.from_template(template_string)
```

从模板中可以提取原始提示词，LangChain 能自动识别其中的输入变量（如 `style` 和 `text`，用花括号标注）。

**为什么用模板而不是 f-string？**

随着应用变得复杂，提示词会越来越长、越来越详细。模板是一种有用的抽象，让你可以复用优质提示词。

LangChain 还为常见操作提供内置提示词，例如：摘要生成、问答、连接 SQL 数据库、调用各类 API——使用这些内置提示词，可以跳过自己写提示词的环节。

---

## Output Parsers（输出解析器）

构建复杂 LLM 应用时，通常需要指示 LLM 按特定格式（如特定关键词）输出结果。

**示例：ReAct 框架中的链式推理**

- `Thought`（想法）：给 LLM 留出思考空间，往往能得到更准确的结论
- `Action`（行动）：执行具体操作
- `Observation`（观察）：记录从行动中学到的内容

如果提示词中包含这些关键词，就可以配合解析器从输出中提取对应文本，形成从输入到结构化输出的完整抽象。

---

## 实战示例：从产品评论中提取 JSON

**目标输出格式（Python 字典）：**
```python
{
    "gift": False,
    "delivery_days": 5,
    "price_value": "pretty affordable"
}
```

**客户评论示例：**

> 这款叶片鼓风机真了不起，有四档设置：蜡烛风、微风、城市风和龙卷风。两天就到货，正好赶上我妻子的周年纪念日礼物…

**使用步骤：**

1. 使用 `ResponseSchema` 和 `StructuredOutputParser` 定义 schema
2. 通过 `output_parser.get_format_instructions()` 获取格式指令
3. 将格式指令嵌入提示词，发送给 LLM
4. 用 `output_parser.parse()` 将返回字符串解析为 Python 字典

这样就能直接通过 `output_dict["gift"]` 等方式访问数据，而不是操作一个大字符串。

---

## 本课小结

- **Prompt Templates**：方便复用和共享提示词，也可配合 LangChain 内置模板
- **Output Parsers**：将 LLM 输出解析为 Python 字典或其他数据结构，便于下游处理

下一课将学习 LangChain 如何通过更好地管理对话记忆来构建更有效的聊天机器人。
