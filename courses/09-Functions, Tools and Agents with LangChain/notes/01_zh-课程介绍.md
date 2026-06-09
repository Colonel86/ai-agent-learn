# Functions, Tools and Agents with LangChain — 第 01 课：课程介绍（中文整理）

> 来源：`subtitles/langchain_c3_01_en.vtt`（本节无配套代码）
> 讲师：Andrew Ng（DeepLearning.AI）+ Harrison Chase（LangChain 联合创始人 & CEO）

---

## 一、课程要解决的根本问题

LLM 已经展示了用自然语言与人类交互的惊人能力，打开了很多新应用的大门。但一个更关键的问题是：

> **LLM 怎么和现有的软件基础设施交互？**

例如：
- 让 LLM 自主决定**何时调用另一段程序**去获取更多信息；
- 或者**采取某个动作**（触发 API、写数据库等）。

原本 LLM 是被设计来**为人类生成自然语言**的，而现在 OpenAI 已经把一些最新模型训练为能够**输出结构化数据（如 JSON）**，让 LLM 能以"子程序调用"的方式调度其他代码。

这**极大地扩展了 LLM 可以做什么**，比如从**结构化 / 表格数据**中抽取信息 —— 这正是过去 LLM 容易出错的领域。

---

## 二、OpenAI 的 "Function Calling" 能力

OpenAI 给这项新能力取名为 **Function Calling**。它的核心就是：

- 让模型**知道有哪些可调用的"函数"**；
- 由模型**判断**：此刻要不要调用、调用哪个、传什么参数；
- 模型**并不自己执行函数**，而是把函数名 + 参数作为结构化 JSON 返回；
- 由你的应用去**真正执行**这个函数，然后可以把结果喂回模型，继续生成最终答案。

这是本课程第一个重点概念。

---

## 三、LangChain 此次的两个重要变化

Harrison 指出，LangChain 作为"桥接传统软件和 LLM"的开源框架：
- 支持 500+ 不同语言模型、向量库、工具集成；
- 支持 Memory、Chain、Agent 等概念。

这门课会讲两个**新的重要变化**：

1. **LangChain Expression Language（LCEL）** —— 一种全新的**声明式组合语法**，让构建复杂 chain / agent 更透明、更容易。
2. **Function Calling 的适配** —— LangChain 如何原生地把 OpenAI 的函数调用能力用起来，支撑 **Tagging、Extraction、Tool 使用**等典型任务，并让"构建工具"这件事更简单、更可靠。

---

## 四、课程大纲（8 节预览）

| 课次 | 主题 |
|------|------|
| L1 | 课程介绍（本节） |
| L2 | OpenAI Function Calling —— 直接用 OpenAI SDK 讲清楚原理 |
| L3 | LangChain Expression Language（LCEL）基础 |
| L4 | 用 LCEL 调用 OpenAI Functions + Pydantic |
| L5 | 用 Function Calling 做 **Tagging & Extraction** |
| L6 | 用 Function Calling 做 **Tools & Routing**（含 OpenAPI 规范转工具） |
| L7 | 构建 **Conversational Agent**（对话型 Agent，带 memory） |
| L8 | 结语 |

---

## 五、你会带走什么

- 会直接用 OpenAI SDK 写 function calling；
- 用 Pydantic 干净地声明函数 schema，**不再手搓 JSON**；
- 会用 LCEL 把 prompt、model、output parser、retriever 像管道一样 `|` 起来；
- 会用 function calling 做 tagging（分类打标）与 extraction（结构化抽取）；
- 会自己造工具（tools）、把模型当"路由器"去选工具 / 调工具；
- 最后组装出一个**类 ChatGPT 的会话式 Agent**。

---

## 六、致谢

本课程感谢：

- **LangChain 团队**：Lance Martin、Nuno Kampas
- **DeepLearning.AI 团队**：Jeff Lodwick、Eshmel Gagari

> "Lots of fun things to explore. Let's get started." —— Andrew Ng
