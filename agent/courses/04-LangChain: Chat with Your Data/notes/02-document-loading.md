# LangChain: Chat with Your Data — 第02课：文档加载（Document Loading）

> 本文档融合**字幕讲解**与**官方代码示例**，旨在帮助你完整且高质量地学习本节课。

---

## 1. 课程概述

要构建一个"与你的数据对话"的应用，**第一步**就是把数据加载成一种可以处理的格式——这正是 **LangChain 文档加载器（Document Loaders）** 的使命。

LangChain 提供了 **80+ 种不同类型**的文档加载器。本节课将覆盖其中最核心的几种，帮助你建立对这一概念的整体认识。

### 1.1 检索增强生成（RAG）背景

在 **RAG（Retrieval Augmented Generation）** 中，LLM 在执行过程中会从外部数据集中检索相关的上下文文档。

**适用场景：** 当我们想要针对特定文档（如自己的 PDF、一组视频等）提问时，RAG 非常有用。

---

## 2. 文档加载器的核心思想

文档加载器的职责是处理"**从各种来源、各种格式访问并转换数据**"的细节，最终把它们统一成**标准化的 Document 对象**。

### 2.1 数据来源（Sources）

| 维度 | 示例 |
|------|------|
| **网站** | 任意 URL、GitHub 页面 |
| **数据库** | Airbyte、Stripe、Airtable |
| **媒体平台** | YouTube、Twitter、Hacker News |
| **协作工具** | Figma、Notion |

### 2.2 数据类型（Formats）

- PDF
- HTML
- JSON
- 纯文本
- 音频（需配合语音转文字模型）

### 2.3 标准化的 Document 对象

无论来源和格式如何，加载器最终都返回 `Document` 对象，它包含：

- **`page_content`**：文档的内容（文本）
- **`metadata`**：与文档相关的元数据（来源、页码等）

### 2.4 80+ 加载器的大致分类

| 类别 | 说明 | 示例数据源 |
|------|------|-----------|
| **非结构化 + 公开** | 加载公开来源的非结构化数据 | YouTube、Twitter、Hacker News |
| **非结构化 + 私有** | 加载企业或个人的专有非结构化数据 | Figma、Notion |
| **结构化数据** | 表格型数据，可能某些单元格含有文本，仍可做问答或语义搜索 | Airbyte、Stripe、Airtable |

---

## 3. 环境准备

```python
import os
import openai
import sys
sys.path.append('../..')

from dotenv import load_dotenv, find_dotenv
_ = load_dotenv(find_dotenv())  # 读取本地 .env 文件

openai.api_key = os.environ['OPENAI_API_KEY']
```

> **学生提示：** 在高负载时段，notebook 可能无响应。它看起来在执行（左侧 `[#]` 编号会更新），但单元格实际并未运行——尤其在 `print` 时没有任何输出。如果遇到此情况，请通过 Kernel 菜单**重启内核**。

---

## 4. PDF 加载

我们将加载 **Andrew Ng 的 CS229 课程讲义 PDF**（机器学习经典课程）。这些文档是自动转录的，所以单词和句子有时会被意外切分。

### 4.1 安装依赖

```bash
pip install pypdf
```

### 4.2 加载 PDF

```python
from langchain.document_loaders import PyPDFLoader

loader = PyPDFLoader("docs/cs229_lectures/MachineLearning-Lecture01.pdf")
pages = loader.load()
```

### 4.3 检查加载结果

```python
len(pages)
# 输出：22  ← 该 PDF 共 22 页，每页都是一个独立的 Document
```

每一页（page）都是一个 `Document` 对象，包含 `page_content`（文本内容）和 `metadata`（元数据）。

```python
page = pages[0]

# 内容可能很长，这里只打印前 500 个字符
print(page.page_content[0:500])
```

### 4.4 查看元数据

```python
page.metadata
# 输出示例：
# {
#   'source': 'docs/cs229_lectures/MachineLearning-Lecture01.pdf',
#   'page': 0
# }
```

**两个关键字段：**

| 字段 | 含义 |
|------|------|
| `source` | 加载该文档的源文件名 |
| `page` | 在 PDF 中的页码 |

---

## 5. YouTube 视频加载

YouTube 上有大量精彩内容，很多人想"和自己最喜欢的视频或讲座对话"——这正是 YouTube 加载器的用武之地。

### 5.1 核心组件

| 组件 | 作用 |
|------|------|
| **`YoutubeAudioLoader`** | 从 YouTube 视频下载音频文件 |
| **`OpenAIWhisperParser`** | 调用 OpenAI 的 **Whisper** 语音识别模型，将音频转换为文本 |
| **`GenericLoader`** | 将音频加载器与解析器组合，形成一个完整的"加载 + 解析"管道 |

### 5.2 安装依赖

```bash
pip install yt_dlp
pip install pydub
```

### 5.3 完整代码

```python
from langchain.document_loaders.generic import GenericLoader, FileSystemBlobLoader
from langchain.document_loaders.parsers import OpenAIWhisperParser
from langchain.document_loaders.blob_loaders.youtube_audio import YoutubeAudioLoader

url = "https://www.youtube.com/watch?v=jGwO_UgTS7I"
save_dir = "docs/youtube/"

loader = GenericLoader(
    # YoutubeAudioLoader([url], save_dir),    # 方案A：从 YouTube 下载
    FileSystemBlobLoader(save_dir, glob="*.m4a"),  # 方案B：使用本地已有 m4a 音频
    OpenAIWhisperParser()
)

docs = loader.load()
```

> **注意：** 加载和转录可能需要数分钟。课程示例已修改为优先使用本地音频以加速实验。

### 5.4 查看转录结果

```python
docs[0].page_content[0:500]
```

输出即为 YouTube 视频的**转录文本**前 500 个字符。

> 这是一个很好的暂停点——挑选你最喜欢的 YouTube 视频，试试这个流程是否对你有效！

---

## 6. URL 网页加载

互联网上有海量的优秀教育内容。LangChain 的 **`WebBaseLoader`** 让你能直接"和这些网页内容对话"。

### 6.1 加载示例

```python
from langchain.document_loaders import WebBaseLoader

loader = WebBaseLoader(
    "https://github.com/basecamp/handbook/blob/master/titles-for-programmers.md"
)
docs = loader.load()
```

> **说明：** 此处 URL 与视频中所示略有不同，因为该资源在 2024 年有更新。

### 6.2 查看内容并意识到"后处理"的必要性

```python
print(docs[0].page_content[:500])
```

你会观察到：
- 开头有**大量空白**
- 紧接着是初始文本
- 然后才是更多内容

> **关键启示：** 这是一个非常典型的例子，说明你**几乎总是需要对加载后的内容做后处理（post-processing）**，才能将其转化为可用的格式。下一节"文档分割"中会涉及更多此类处理。

---

## 7. Notion 加载

Notion 是非常流行的个人/企业知识库，许多人构建了"和自己的 Notion 数据库对话"的聊天机器人。

### 7.1 数据导出步骤

按照[官方文档](https://python.langchain.com/docs/modules/data_connection/document_loaders/integrations/notion)的说明，例如以 [Blendle Employee Handbook](https://yolospace.notion.site/Blendle-s-Employee-Handbook-e31bff7da17346ee99f531087d8b133f) 为例：

1. **复制（Duplicate）** 该页面到你自己的 Notion 工作空间
2. 选择 **Markdown / CSV** 格式**导出**
3. **解压**得到一个文件夹（包含该 Notion 页面的 markdown 文件）

### 7.2 加载到 LangChain

```python
from langchain.document_loaders import NotionDirectoryLoader

loader = NotionDirectoryLoader("docs/Notion_DB")
docs = loader.load()
```

### 7.3 查看内容与元数据

```python
print(docs[0].page_content[0:200])
docs[0].metadata
```

加载结果是**Markdown 格式**的文本——这是 Blendle 员工手册的内容。

> **行动建议：** 如果你正在使用 Notion，并且希望和自己的数据库对话，这是一个绝佳的练习机会——导出数据，引入 LangChain，立即开始构建。

---

## 8. 本课小结

### 8.1 我们学到了什么

- 文档加载器把**多源、多格式**的数据，统一加载到**标准化的 `Document` 接口**
- 每个 `Document` 包含 `page_content` 和 `metadata`
- 学习了 **4 种代表性加载器**：

| 加载器 | 数据源 | 关键依赖 |
|--------|--------|----------|
| **`PyPDFLoader`** | PDF 文件 | `pypdf` |
| **`GenericLoader` + `OpenAIWhisperParser`** | YouTube 视频 | `yt_dlp`、`pydub`、Whisper |
| **`WebBaseLoader`** | 任意网页 URL | （无） |
| **`NotionDirectoryLoader`** | 导出的 Notion Markdown | （无） |

### 8.2 下一步：为什么需要"切分文档"

这些加载到的文档**仍然偏大**。在 RAG 中，我们只想检索**最相关的片段**——而不是整篇文档。

例如，对于一个具体问题，你只需要传给 LLM **某一段或某几句最切题的内容**，而不是整本书的内容。

> 因此，**下一节将介绍如何把这些大文档切分成更小的语义块（Chunks）**，这看似简单的预处理步骤其实有很多细节和讲究。

### 8.3 鼓励与拓展

如果你想到某个数据源 LangChain **目前还没有对应的加载器**，但你又很想用——

> **谁知道呢？也许你可以给 LangChain 提一个 PR，把它贡献到开源社区中！**

---

## 附录：完整代码速查

```python
# === 通用准备 ===
import os, openai, sys
sys.path.append('../..')
from dotenv import load_dotenv, find_dotenv
_ = load_dotenv(find_dotenv())
openai.api_key = os.environ['OPENAI_API_KEY']

# === 1. PDF ===
from langchain.document_loaders import PyPDFLoader
pages = PyPDFLoader("docs/cs229_lectures/MachineLearning-Lecture01.pdf").load()
print(len(pages))                # 22
print(pages[0].page_content[:500])
print(pages[0].metadata)         # {'source': '...', 'page': 0}

# === 2. YouTube ===
from langchain.document_loaders.generic import GenericLoader, FileSystemBlobLoader
from langchain.document_loaders.parsers import OpenAIWhisperParser
from langchain.document_loaders.blob_loaders.youtube_audio import YoutubeAudioLoader

loader = GenericLoader(
    FileSystemBlobLoader("docs/youtube/", glob="*.m4a"),
    OpenAIWhisperParser()
)
docs = loader.load()
print(docs[0].page_content[:500])

# === 3. URL ===
from langchain.document_loaders import WebBaseLoader
docs = WebBaseLoader(
    "https://github.com/basecamp/handbook/blob/master/titles-for-programmers.md"
).load()
print(docs[0].page_content[:500])

# === 4. Notion ===
from langchain.document_loaders import NotionDirectoryLoader
docs = NotionDirectoryLoader("docs/Notion_DB").load()
print(docs[0].page_content[:200])
print(docs[0].metadata)
```
