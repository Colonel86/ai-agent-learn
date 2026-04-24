# EP06: Transforming（格式转换）

> 学习日期：2026-04-15
> 所属阶段：Phase 1 · 基石构建
> 课程来源：DeepLearning.AI × OpenAI（Andrew Ng + Isa Fulford）

---

LLM 擅长将一种形式的文本转换为另一种形式。

## 翻译（Translation）

LLM 在大量多语言互联网文本上训练，具备很强的翻译能力，支持数百种语言。

**基础翻译：**
```python
prompt = "将以下英文翻译成西班牙语：'Hi, I would like to order a blender'"
# 输出：Hola, me gustaría ordenar una licuadora
```

**语言检测：**
```python
prompt = f"告诉我这是什么语言：{text}"
# 输出：This is French
```

**多语言同时翻译：**
```python
prompt = "将以下文本翻译成法语、西班牙语和英语海盗腔：'I want to order a basketball'"
```

**正式/非正式语气：**
```python
prompt = "将以下文本翻译成西班牙语的正式和非正式两种形式：'Would you like to order a pillow?'"
```

**通用翻译器（批量处理多语言）：**
```python
user_messages = [
    "La performance du système est plus lente que d'habitude.",  # 法语
    "Mi monitor tiene píxeles que no se iluminan.",              # 西班牙语
    "My keyboard has a key that doesn't work",                   # 英语
]

for msg in user_messages:
    lang = get_completion(f"告诉我这是什么语言：{msg}")
    translation = get_completion(f"将以下文本翻译成英语和韩语：{msg}")
    print(f"原始消息({lang})：{msg}\n{translation}\n")
```

---

## 语气转换（Tone Transformation）

```python
prompt = """
将以下俚语翻译成商务信函风格：
"Dude, this is Joe, check out this spec on the standing lamp."
"""
# 输出：专业的站立台灯规格说明商务提案
```

---

## 格式转换（Format Conversion）

```python
data_json = {
    "restaurant employees": [
        {"name": "Shyam", "email": "shyam@example.com"},
        {"name": "Bob", "email": "bob@example.com"},
    ]
}

prompt = f"""
将以下 Python 字典从 JSON 转换为 HTML 表格，包含列标题和标题。
{data_json}
"""
# 输出：格式完整的 HTML 表格，可直接显示
```

---

## 拼写和语法检查（Spell/Grammar Check）

```python
text_with_errors = [
    "The girl with the black and white puppies have a ball.",
    "Yolanda has her notebook.",
    "Its going to be a long day.",
]

for text in text_with_errors:
    prompt = f"""
    校对并更正以下文本。
    如果没有错误，直接回复"未发现错误"。
    ```{text}```
    """
    response = get_completion(prompt)
    print(response)
```

**进阶技巧：用 redlines 库可视化差异**

```python
from redlines import Redlines

diff = Redlines(original_text, corrected_text)
display(Markdown(diff.output_markdown))
# 红色标记被删除/修改的部分，直观展示校对效果
```

**更高级的改写：** 还可以同时要求改善语气、符合 APA 格式、面向特定读者群：

```python
prompt = f"""
校对并更正以下评论，同时使其更具说服力，确保符合 APA 风格，
并面向高级读者，以 Markdown 格式输出。
评论：{review}
"""
```
