# L2 · Lab 1：用 pytesseract + ReAct 搭第一个文档 Agent

> 课程：Document AI: From OCR to Agentic Doc Extraction（DeepLearning.AI × LandingAI）· Lesson 1 Lab（讲师 David Park）
> 本课任务：动手把 L1 的概念接成代码——OCR 封成 `@tool`、LangChain 搭 ReAct agent，先演示 **regex 在噪声 OCR 上脆断**，再用 LLM agent 在无规则下抽对字段；然后用表格 / 手写 / 收据三个「不友好」样本，逼出 OCR 的边界。
> 目标不是造完美生产系统，而是**看清 OCR + 规则 + LLM 推理三者如何咬合**。

## 1. 技术栈与 OCR 工具化

```python
from PIL import Image                       # 载图
import pytesseract                          # OCR 引擎（Tesseract v5）
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI     # LLM=脑
```

把 OCR 封成 agent 能按名调用的**工具**——`@tool` 装饰器是关键：

```python
from langchain.tools import tool

@tool
def ocr_read_document(image_path: str) -> str:
    """Reads an image from the given path and returns extracted text using OCR."""
    try:
        text = pytesseract.image_to_string(Image.open(image_path))  # 图 → 文字
        return text
    except Exception as e:
        return f"Error reading image: {e}"
```

agent 循环里 LLM 会自己判断「我得先读文档」→ 调 `ocr_read_document` → 拿到文字 → 继续推理。**注意：agent 的推理再强，也只和它拿到的输入一样好**（garbage in, garbage out）——这是本 lab 反复验证的主线。

## 2. 理想样本：干净数字发票

第一张 `invoice.png` 是干净数字发票：完美光照、清晰字体、无手写无阴影——**传统 OCR 的高光时刻**。先跑原始 OCR 看输出：

```python
ocr_text = ocr_read_document.run("invoice.png")
print("Raw OCR Output:\n", ocr_text)
```

拿到的是 raw text——无结构、无含义、无理解。正因如此，下游一切（regex / ML / 抽取）都很**脆（brittle）**。

## 3. Regex 的脆断：不是 bug，是根本缺陷

用简单正则抽 tax 和 total：

```python
import re
tax_match   = re.search(r'Tax\s*\$?([0-9.,]+)',   ocr_text)
total_match = re.search(r'Total\s*\$?([0-9.,]+)', ocr_text)
```

结果**两处都错**：

| 失败 | 原因 |
|---|---|
| 完全漏掉 tax 行 | OCR 把 `Tax` 读成了 `Tax @`（多了 @ 符号），正则匹配不上 |
| 抓成 subtotal 而非 total | `total` 在文档里出现多次（sub**total** / **total**），正则贪婪匹配到**先出现**的 subtotal |

这不是正则写得烂，而是**规则 × 噪声 OCR 的根本缺陷**：regex ≠ understanding，它不知道 `tax` 指的是税行、`subtotal` 不是 `total`。放到每年处理数十亿张不同供应商、不同结构发票的场景，regex 会**在生产里静默失败（fail silently）**——这正是传统 IDP 系统的通病。

> **对比 OCR vs agentic extraction 范式**：这一节是全课「感知 vs 认知」分界线的实证。regex 把「结构假设」硬编码进模式串，OCR 输出一抖动（多个 @、多个 total）就崩；下一节的 LLM agent 不写任何模式，靠**语义理解**判断「哪个才是最终总额」。同一份噪声输入，脆断 vs 稳健的差别不在 OCR，而在其上那层是规则还是认知。

## 4. 换成 LLM Agent：无规则也能抽对

三大部件（对应 L1 的 Brain/Eyes/Hands）：

```python
tools = [ocr_read_document]                          # Hands：工具
llm = ChatOpenAI(model="gpt-5-mini", temperature=1)  # Brain：LLM

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant designed to extract information "
               "from documents. You have access to this tool: "
               "OCR tool to extract raw text from images"),
    ("user", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),  # ReAct 的思考草稿区
])

agent = create_tool_calling_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
```

`agent_scratchpad` 就是 ReAct 循环的载体，`AgentExecutor` 跑起 tool-enabled loop。下任务：

```python
task = """Please process the document at 'invoice.png' using the OCR tool
and extract the following information in JSON format:
- tax
- total"""
response = agent_executor.invoke({"input": task})
```

「magical」发生：agent 识别到需要 OCR → 调工具 → **语义地**读文本 → 返回结构化 JSON。**没有 regex、没有规则、没有模板**，却抽对了 tax，且拿到的是真正的 total 而非 subtotal。这就是 agentic 系统正在取代静态 IDP 流水线的原因。

## 5. 压力测试：表格 / 手写 / 收据

理想发票之所以顺，是因为布局干净、文字质量高。真实文档没那么友好。三个样本逐步把 OCR 推过断点：

### 5.1 表格（Attention is all you need 论文的表）

表格对 OCR 出了名地难：需要空间对齐 + 列重建，而 Tesseract 从未为此设计；这张表还**没有分隔线**、有**空单元格**和**科学计数法数字**。

```python
task = """Extract the Training Cost (FLOPs) for EN-DE for ALL methods
from the table.png using the OCR tool.
Return as a list with model name and its training cost."""
ocr_output = ocr_read_document.run("table.png")   # 先看原始 OCR
response = agent_executor.invoke({"input": task}) # 再看 agent
```

原始 OCR **一片混乱**：指数变成撇号、小数点变成感叹号、列错位；`1.0×10²⁰` 被读成 `1.0 −107°`。但 agent 仍做「尽力解读」：

| agent 表现 | 结果 |
|---|---|
| ByteNet 那格 | 正确判断**为空**（即便 OCR 没保住表结构，也懂这里没值）|
| 第二行本应为空 | ❌ 从别的列**串了个错值**进来 |
| 数值本身 | ❌ 因 OCR 读错，值随之错 |

**LLM 擅长在输入退化时揣摩意图**，但揣摩不能凭空造出 OCR 丢掉的信息。

### 5.2 手写（学生填空练习）

学生 John Smith 的填空作业，含语法错误答案（如 "They **is** dancing"）。任务：抽 student name + 十道题答案为 JSON。

- 原始 OCR：**没认出学生名**，填空答案全错（`am`→`Aum`，数字被认成字母，第 9 题 "They is dancing" 被读成 "1%"）。
- LLM 结果：靠推理**猜对了部分**答案；但第 9 题学生原答案是 `is`，LLM **过度纠正（overcorrected）**成了 `are`——这恰恰不是我们要的（作业要保留学生原始错误）。

> 教训：LLM 的「脑补」是双刃剑——退化输入下能救场，也能**擅自改写**该保真的内容。

### 5.3 收据（餐厅照片）

收据极其杂乱：低分辨率、热敏打印、文字错位、阴影。任务：核验总额是否正确。

- 第一个食品行实际 `$7.95`，OCR 误读成 `$7.99` → 冲乱总额。
- LLM 结果：逐行读、甚至指出某些行「有点不清」，认真做加法、和标注总额比对，**推理链完全站得住**，但结论**错**——因为 OCR 没把数字读准。

一句话：**The reasoning is solid, but the answer is incorrect**——错在 OCR 那层，不在 agent。

## 本课总结

| 要点 | 一句话 |
|---|---|
| OCR 工具化 | `@tool` 把 pytesseract 封成 agent 可按名调用的 Hands |
| Regex 脆断 | 规则 × 噪声 OCR = 静默失败，非 bug 而是根本缺陷 |
| LLM Agent | 无规则/模板即抽对 tax 和 total（非 subtotal），语义理解补上认知层 |
| OCR 擅读不擅懂 | 干净印刷体优秀，表格/手写/科学计数崩坏 |
| 联动真相 | agent 推理再强，OCR 输错则结论错（garbage in, garbage out）|
| 完整理解需要 | OCR + layout detection + VLM + agentic workflow + grounding/validation |

> **记忆点（引出 L3）**：本 lab 用的 Tesseract 是**传统过程式 OCR**，在表格/手写/低质照片上系统性崩坏——问题的根子在 OCR 引擎本身。L3（Lesson 2「Four decades of OCR evolution」，讲师换 Andrea）拉远视角看 OCR 四十年演进：从手工工程的 **Tesseract** 到深度学习端到端的 **PaddleOCR**，并讲清「什么场景该用哪一个」，为 L4 换引擎重跑这三个样本做铺垫。

## 与我的资产映射

- **检索层上游**：本 lab 证明 RAG 的解析质量天花板取决于 OCR——`agent/skills/agent-selection/3-retrieval.md` 数据摄取环节若用错 OCR，后面向量检索再好也救不回丢失的数字/结构。
- **工具化范式**：`@tool` + ReAct + AgentExecutor 是可复用的 agent 骨架，任何「外部能力→agent 工具」都套这个模子。
- **同族课程**：`Preprocessing Unstructured Data for LLM Applications`（解析质量决定下游一切）。
- 选型沉淀：「感知层 vs 认知层」「规则 vs LLM 抽取」的取舍 → [[project_selection_matrix]]。
