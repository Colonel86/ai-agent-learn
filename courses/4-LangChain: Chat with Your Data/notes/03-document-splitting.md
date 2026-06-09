# LangChain: Chat with Your Data — 第03课：文档分割（Document Splitting）

> 本文档融合**字幕讲解**与**官方代码示例**，旨在帮助你完整且高质量地学习本节课。

---

## 1. 为什么文档分割如此重要？

文档分割发生在**加载数据之后、写入向量库之前**。这一步看似简单——"按字符长度切分一下不就好了？"——但其中的细节会**深刻影响后续检索质量**。

### 1.1 一个直观反例：Toyota Camry

假设有这样一句话：

> "The Toyota Camry has a head-snapping 80 HP and an eight-speed automatic transmission that will lull you to sleep."

如果**简单按长度切分**，可能会把这句话切成两块：

- Chunk A：`"The Toyota Camry has a head-snapping"`
- Chunk B：`"80 HP and an eight-speed automatic..."`

后续如果用户问："**Camry 的规格参数是什么？**"

→ 检索会找到 Chunk B（包含 "80 HP"），但**它不知道这是描述 Camry 的**——因为 "Camry" 这个词在另一个 chunk 里！

> **结论：** 切分必须保持**语义相关的内容在一起**。这就是 LangChain 提供多种文本分割器的原因。

---

## 2. 文本分割器的核心概念

LangChain 中所有文本分割器的基础参数都是 **chunk_size + chunk_overlap**：

| 参数 | 含义 |
|------|------|
| **`chunk_size`** | 每个块的大小。可按字符数（characters）或 token 数衡量；通过传入 `length_function` 来自定义度量 |
| **`chunk_overlap`** | 相邻两个块之间的重叠区域。类似一个**滑动窗口**：上一个块的尾部 = 下一个块的头部，保持上下文连续性 |

### 2.1 通用接口

每个分割器都提供两种方法（底层逻辑相同，仅接口不同）：

| 方法 | 输入 |
|------|------|
| `create_documents` | 一个 **字符串列表** |
| `split_documents` | 一个 **Document 对象列表** |

### 2.2 分割器的差异维度

不同分割器的差异主要体现在：

- **如何切分**：用哪些字符作为分隔点
- **如何度量长度**：字符 vs token
- **是否使用更小的辅助模型**判断句子边界
- **元数据处理**：保留原元数据 + 在合适时**新增元数据**
- **是否针对特定文档类型**（如代码语言：Python、Ruby、C 都有专门的 `LanguageTextSplitter`）

---

## 3. 环境准备

```python
import os
import openai
import sys
sys.path.append('../..')

from dotenv import load_dotenv, find_dotenv
_ = load_dotenv(find_dotenv())
openai.api_key = os.environ['OPENAI_API_KEY']

from langchain.text_splitter import RecursiveCharacterTextSplitter, CharacterTextSplitter
```

**两种最常用的分割器：**

- **`RecursiveCharacterTextSplitter`**：递归字符分割器（**推荐用于通用文本**）
- **`CharacterTextSplitter`**：字符分割器（按单个分隔符切分，默认换行符 `\n`）

---

## 4. 玩具示例：建立直观感受

为了感受这两个分割器的行为，我们设置很小的参数：

```python
chunk_size = 26
chunk_overlap = 4

r_splitter = RecursiveCharacterTextSplitter(
    chunk_size=chunk_size,
    chunk_overlap=chunk_overlap
)
c_splitter = CharacterTextSplitter(
    chunk_size=chunk_size,
    chunk_overlap=chunk_overlap
)
```

### 4.1 示例 1：刚好 26 个字符

```python
text1 = 'abcdefghijklmnopqrstuvwxyz'
r_splitter.split_text(text1)
# 输出：['abcdefghijklmnopqrstuvwxyz']  ← 单个块，因为正好等于 chunk_size
```

### 4.2 示例 2：超过 26 个字符

```python
text2 = 'abcdefghijklmnopqrstuvwxyzabcdefg'
r_splitter.split_text(text2)
# 输出：['abcdefghijklmnopqrstuvwxyz', 'wxyzabcdefg']
#        ↑ 第一块 26 字符（到 z）
#                                       ↑ 第二块以 wxyz 开头（chunk_overlap=4）
```

### 4.3 示例 3：含空格的字符串

```python
text3 = "a b c d e f g h i j k l m n o p q r s t u v w x y z"
r_splitter.split_text(text3)
# 输出 3 个块（因为空格也算长度）：
# ['a b c d e f g h i j k l m', 'l m n o p q r s t u v w x', 'y z']
# overlap 部分（如 "l m"）看似只有 2 字符，但加上前后空格，实际占了 4 个字符
```

### 4.4 示例 4：CharacterTextSplitter 的"陷阱"

```python
c_splitter.split_text(text3)
# 输出：['a b c d e f g h i j k l m n o p q r s t u v w x y z']  ← 没有切！
```

**为什么没切？** `CharacterTextSplitter` **默认按换行符 `\n` 切分**，而 text3 中没有换行符。

**修复方法：显式指定 separator：**

```python
c_splitter = CharacterTextSplitter(
    chunk_size=chunk_size,
    chunk_overlap=chunk_overlap,
    separator=' '   # ← 改为按空格切
)
c_splitter.split_text(text3)
# 现在与 r_splitter 输出一致
```

> **建议：** 此处暂停一下，自己构造几个字符串、调整不同分隔符 / chunk_size / chunk_overlap，建立对底层行为的直觉，对后续真实场景非常有帮助。

---

## 5. 递归分割（Recursive Splitting）的细节

`RecursiveCharacterTextSplitter` 是**通用文本的推荐选择**。它会按一个**有序的分隔符列表**逐层尝试。

### 5.1 真实段落示例

```python
some_text = """When writing documents, writers will use document structure to group content. \
This can convey to the reader, which idea's are related. For example, closely related ideas \
are in sentances. Similar ideas are in paragraphs. Paragraphs form a document. \n\n  \
Paragraphs are often delimited with a carriage return or two carriage returns. \
Carriage returns are the "backslash n" you see embedded in this string. \
Sentences have a period at the end, but also, have a space.\
and words are separated by space."""

len(some_text)   # 约 500
```

注意文本中部有一个 `\n\n`（双换行）——这是段落之间的典型分隔符。

### 5.2 对比两种分割器

```python
# 字符分割器：按空格分
c_splitter = CharacterTextSplitter(
    chunk_size=450,
    chunk_overlap=0,
    separator=' '
)

# 递归分割器：按层级尝试 [双换行 → 单换行 → 空格 → 字符]
r_splitter = RecursiveCharacterTextSplitter(
    chunk_size=450,
    chunk_overlap=0,
    separators=["\n\n", "\n", " ", ""]   # ← 这就是 LangChain 默认的分隔符列表
)
```

**结果对比：**

- `c_splitter`：按空格切分 → 句子可能在中间被切断
- `r_splitter`：先按 `\n\n` 切 → 得到两个完整段落，**即使第一块短于 450 字符也优先按段落切**

### 5.3 递归切分的逻辑

> **优先级从上到下：先尝试用最高级分隔符；如果块仍然太大，再用下一级。**

```
1. \n\n  （段落）
2. \n    （行）
3. " "   （单词）
4. ""    （字符级，兜底）
```

### 5.4 按句号切分

如果想进一步切到**句子级**，加入句号分隔符：

```python
# 错误版本：会把句号切到错误的位置
r_splitter = RecursiveCharacterTextSplitter(
    chunk_size=150,
    chunk_overlap=0,
    separators=["\n\n", "\n", "\. ", " ", ""]
)
```

输出的句号位置不对——这是因为 `"\. "` 这个分隔符本身被消耗掉了（regex 匹配到的内容会被移除）。

**修复：使用 lookbehind 正则**

```python
r_splitter = RecursiveCharacterTextSplitter(
    chunk_size=150,
    chunk_overlap=0,
    separators=["\n\n", "\n", "(?<=\. )", " ", ""]   # ← lookbehind 不消耗匹配
)
```

现在句号会出现在**正确的位置**（前一句的句尾）。

---

## 6. 真实文档分割

### 6.1 PDF 文档

```python
from langchain.document_loaders import PyPDFLoader

loader = PyPDFLoader("docs/cs229_lectures/MachineLearning-Lecture01.pdf")
pages = loader.load()

from langchain.text_splitter import CharacterTextSplitter
text_splitter = CharacterTextSplitter(
    separator="\n",
    chunk_size=1000,
    chunk_overlap=150,
    length_function=len   # ← 默认就是 Python 内置 len，这里显式说明便于理解
)

docs = text_splitter.split_documents(pages)

len(docs)    # 切分后的文档数（远多于原始页数）
len(pages)   # 原始 PDF 页数
```

切分后会得到**比原始页数更多**的 Document 对象。

### 6.2 Notion 文档

```python
from langchain.document_loaders import NotionDirectoryLoader

loader = NotionDirectoryLoader("docs/Notion_DB")
notion_db = loader.load()

docs = text_splitter.split_documents(notion_db)

len(notion_db)   # 原始 Notion 文档数
len(docs)        # 切分后的文档数
```

---

## 7. 按 Token 切分

除了按字符切分，还可以**按 token 切分**——这非常重要，因为 **LLM 的上下文窗口通常以 token 计量**。

### 7.1 字符 vs Token

> 经验值：1 token ≈ 4 个字符（英文）

按 token 切分能更准确地反映 LLM "看到" 的内容。

### 7.2 TokenTextSplitter 示例

```python
from langchain.text_splitter import TokenTextSplitter

# chunk_size=1, chunk_overlap=0：把文本切成单个 token 列表
text_splitter = TokenTextSplitter(chunk_size=1, chunk_overlap=0)

text1 = "foo bar bazzyfoo"
text_splitter.split_text(text1)
# 输出类似：['foo', ' bar', ' b', 'az', 'zy', 'foo']
# ← 注意每个 token 长度不一，且 'bazzyfoo' 被切成了多个 token
```

### 7.3 应用到真实文档

```python
text_splitter = TokenTextSplitter(chunk_size=10, chunk_overlap=0)
docs = text_splitter.split_documents(pages)

docs[0]
# Document(page_content='MachineLearning-Lecture01\n', metadata={...})

pages[0].metadata
# 验证元数据从原始 page 正确传递到了切分后的 chunk
```

> **关键观察：** `metadata` 中的 `source` 和 `page` **完整保留**到了每个切分块中。

---

## 8. 上下文感知分割（Context-aware Splitting）

切分的目的是让"语义相关"的内容保持在一起。许多文档（如 **Markdown**）本身就有显式的结构（标题、子标题），可以直接利用。

### 8.1 MarkdownHeaderTextSplitter

它会：

1. 按标题层级（`#`、`##`、`###` ...）切分 Markdown 文档
2. **将标题文本作为元数据**附加到对应的块上
3. 后续 chunk 自动继承所属标题层级信息

### 8.2 玩具示例

```python
from langchain.text_splitter import MarkdownHeaderTextSplitter

markdown_document = """# Title\n\n \
## Chapter 1\n\n \
Hi this is Jim\n\n Hi this is Joe\n\n \
### Section \n\n \
Hi this is Lance \n\n 
## Chapter 2\n\n \
Hi this is Molly"""

# 定义要按哪些标题层级切分
headers_to_split_on = [
    ("#", "Header 1"),
    ("##", "Header 2"),
    ("###", "Header 3"),
]

markdown_splitter = MarkdownHeaderTextSplitter(
    headers_to_split_on=headers_to_split_on
)
md_header_splits = markdown_splitter.split_text(markdown_document)
```

### 8.3 查看切分结果

```python
md_header_splits[0]
# Document(
#   page_content='Hi this is Jim  \nHi this is Joe',
#   metadata={'Header 1': 'Title', 'Header 2': 'Chapter 1'}
# )

md_header_splits[1]
# Document(
#   page_content='Hi this is Lance',
#   metadata={'Header 1': 'Title', 'Header 2': 'Chapter 1', 'Header 3': 'Section'}
# )
```

> **关键效果：** 每个 chunk 的 metadata 自动记录了它所属的标题层级路径——后续检索时可以利用这些信息提供更好的上下文。

### 8.4 应用到真实 Notion 文档

```python
from langchain.document_loaders import NotionDirectoryLoader

loader = NotionDirectoryLoader("docs/Notion_DB")
docs = loader.load()
txt = ' '.join([d.page_content for d in docs])

headers_to_split_on = [
    ("#", "Header 1"),
    ("##", "Header 2"),
]
markdown_splitter = MarkdownHeaderTextSplitter(
    headers_to_split_on=headers_to_split_on
)

md_header_splits = markdown_splitter.split_text(txt)
md_header_splits[0]
# 例如：metadata 中 Header 1 = "Blendle's Employee Handbook"
```

---

## 9. 元数据：为什么要扩充

每个 chunk 都需要保留**原始元数据**，但有时也需要**新增元数据**，例如：

- chunk 在文档中的位置
- chunk 与其他章节/概念的关系
- chunk 来自哪个标题层级

> **作用：** 这些信息在后续问答中可以提供**更精确的上下文**，让 LLM 知道"这段话来自哪儿"。

---

## 10. 本课小结

### 10.1 核心收获

| 主题 | 要点 |
|------|------|
| **为什么需要好的切分** | 否则会把同一句话切到不同 chunk，导致检索失败 |
| **基础参数** | `chunk_size` + `chunk_overlap`（滑动窗口保持连续性） |
| **接口** | `create_documents`（输入字符串列表） / `split_documents`（输入 Document 列表） |

### 10.2 分割器对照

| 分割器 | 适用场景 | 关键说明 |
|--------|----------|----------|
| **`CharacterTextSplitter`** | 单一分隔符场景 | 默认按 `\n` 切；可设 `separator=' '` 等 |
| **`RecursiveCharacterTextSplitter`** | **通用推荐** | 按 `["\n\n", "\n", " ", ""]` 层级递归切分 |
| **`TokenTextSplitter`** | 严格匹配 LLM 上下文窗口 | 按 token 数计量，更贴近 LLM 视角 |
| **`MarkdownHeaderTextSplitter`** | Markdown / Notion 等结构化文档 | **保留并扩充标题元数据** |

### 10.3 下一步

我们已经获得了**带语义相关性 + 合适元数据的文本块**。

> **下一节：** 把这些 chunks 写入**向量库（Vector Store）**，开启检索之旅。

---

## 附录：完整代码速查

```python
# === 通用准备 ===
import os, openai, sys
sys.path.append('../..')
from dotenv import load_dotenv, find_dotenv
_ = load_dotenv(find_dotenv())
openai.api_key = os.environ['OPENAI_API_KEY']

# === 1. 玩具示例（chunk_size=26, chunk_overlap=4） ===
from langchain.text_splitter import RecursiveCharacterTextSplitter, CharacterTextSplitter

r_splitter = RecursiveCharacterTextSplitter(chunk_size=26, chunk_overlap=4)
c_splitter = CharacterTextSplitter(chunk_size=26, chunk_overlap=4, separator=' ')

text1 = 'abcdefghijklmnopqrstuvwxyz'
text2 = 'abcdefghijklmnopqrstuvwxyzabcdefg'
text3 = "a b c d e f g h i j k l m n o p q r s t u v w x y z"

r_splitter.split_text(text1)
r_splitter.split_text(text2)
r_splitter.split_text(text3)
c_splitter.split_text(text3)

# === 2. 段落级递归切分（lookbehind regex） ===
some_text = """..."""  # 长段落
r_splitter = RecursiveCharacterTextSplitter(
    chunk_size=150, chunk_overlap=0,
    separators=["\n\n", "\n", "(?<=\. )", " ", ""]
)
r_splitter.split_text(some_text)

# === 3. 真实 PDF 切分 ===
from langchain.document_loaders import PyPDFLoader
pages = PyPDFLoader("docs/cs229_lectures/MachineLearning-Lecture01.pdf").load()

text_splitter = CharacterTextSplitter(
    separator="\n", chunk_size=1000, chunk_overlap=150, length_function=len
)
docs = text_splitter.split_documents(pages)
print(len(docs), len(pages))

# === 4. Notion 切分 ===
from langchain.document_loaders import NotionDirectoryLoader
notion_db = NotionDirectoryLoader("docs/Notion_DB").load()
docs = text_splitter.split_documents(notion_db)

# === 5. Token 分割 ===
from langchain.text_splitter import TokenTextSplitter
TokenTextSplitter(chunk_size=1, chunk_overlap=0).split_text("foo bar bazzyfoo")
docs = TokenTextSplitter(chunk_size=10, chunk_overlap=0).split_documents(pages)

# === 6. Markdown 标题感知切分 ===
from langchain.text_splitter import MarkdownHeaderTextSplitter

markdown_document = """# Title\n\n## Chapter 1\n\nHi this is Jim..."""

headers_to_split_on = [("#", "Header 1"), ("##", "Header 2"), ("###", "Header 3")]
md_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
md_header_splits = md_splitter.split_text(markdown_document)
print(md_header_splits[0].metadata)   # 标题层级被自动写入 metadata
```
