# L1 · 第一个 AI Agent：知识定制路线与 Azure OpenAI + LangChain 三步连通

> 课程：Building Your Own Database Agent（DeepLearning.AI × Microsoft）· Lesson 1
> 本课任务：先讲清 LLM 的知识定制（customization）有哪些层级、为什么选 RAG，再用三步把 Azure OpenAI 通过 LangChain 连通，跑出第一个"Hello World"级 Agent（一句翻译）。

## 1. 为什么先讲 Foundation Model

讲师给 GenAI 下定义时只抓一个词：**foundation model（基础模型）**。因为一个基础模型能"一次配置、多任务复用"——同一个模型，既能连数据库、又能处理文档、又能搭各种应用。对企业而言这是巨大优势：部署一个模型扛下不同任务，极其高效。

三个关键差异化能力（后面所有课都建立在这上面）：

| 能力 | 含义 | 对本课的意义 |
|---|---|---|
| 单模型多任务 | 一次 setup 干多种活 | 同一个 GPT-4 连 CSV / SQL / 文档 |
| 多模态 | 文本/图像/视频/音频 | 数据源可混合 |
| 自然语言接口 | 用户用母语交互，不写代码 | database agent 的立身之本——用户不必会 SQL |

> **架构师视角**：讲师把"自然语言接口"单列为核心能力，点破了 database agent 的商业价值所在——它把系统的受众从"会 SQL 的技术用户"扩展到"所有业务用户"。这不是技术炫技，而是**改变了谁能用这个系统**。做架构选型时，"用户是谁、他们用什么语言表达需求"应当先于"用哪个框架"来定。

## 2. 知识定制的两条路：RAG vs Fine-tuning

"定制"指的是把企业自己的知识（数据库、PDF、data lake、私有信息）灌进像 GPT-4 这样的模型。两个选项：

| | RAG（检索增强） | Fine-tuning（微调） |
|---|---|---|
| 做法 | 用编排工具把模型连到数据源，**不重训** | 在特定数据集上重训 + 重新部署 |
| 成本 | 低，高效实用，无训练开销 | 高，资源密集、运维复杂 |
| 换模型 | 无缝，同一套连接机制 | 要重训重部署 |
| 采用度 | 本课全程采用 | 少见（仅个别公司为造 IP 尝试） |

RAG 的首要优势是 **flexibility**：未来模型升级或替换，用同样的连接机制接入即可。这正是本课的实现路线。

> **对比 3-retrieval.md 的 RAG 谱系**：选型矩阵里 RAG 通常指"向量检索非结构化文本"。本课的 RAG 是一个**特例——结构化数据 RAG**：数据源是 CSV/SQL 这类有 schema 的表格，"检索"动作不是向量相似度匹配，而是 LLM 生成一段 pandas/SQL 查询去精确取数。判断标准：数据本身有结构就走"生成查询"式 RAG（确定、可解释），只有自由文本才动用向量检索。

## 3. 环境准备与 Azure OpenAI 的连接变量

本地跑要用 `requirements.txt` 装依赖（含 pandas 等），DeepLearning.AI 平台的 notebook 已配好 key。Azure OpenAI 与原生 OpenAI API 相似但有差异，关键连接变量：

```python
# Azure OpenAI 的四要素（与原生 OpenAI 的主要区别在 endpoint / deployment / api_version）
openai_api_version = "2023-05-15"          # API 版本，会随预览版更新，可在官方参考里换日期
azure_deployment  = "gpt-4-1106"           # 部署名：你在 Azure 上给这个模型实例起的名字
azure_endpoint    = "https://testadri.openai.azure.com"  # 预建的云资源端点
# API key 通过环境变量注入，教学 key 仅供教学用
```

要点：**Azure 是"部署（deployment）"而非直接调模型名**——你先在 Azure 上把某个模型部署成一个命名实例（讲师叫 `testadri`），代码里引用的是这个部署名。生产中部署名应更贴合用途。

## 4. 三步连通：LangChain → Azure OpenAI

讲师把连通拆成"极简三步、直击要点"：

```python
# 步骤 1：导入 LangChain 的消息类型与 Azure 聊天封装
from langchain.schema import HumanMessage        # 人类角色的消息（你发给系统的 prompt）
from langchain_openai import AzureChatOpenAI      # LangChain 连 Azure OpenAI 的对象（区别于原生 OpenAI）

# 步骤 2：建立连接实例——把 Azure 的三要素喂进去
model = AzureChatOpenAI(
    openai_api_version="2024-04-01-preview",
    azure_deployment="gpt-4-1106",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
)

# 步骤 3：准备 prompt（用 HumanMessage 包住，让系统识别这是"人类"发的消息）
message = HumanMessage(
    content="Translate this sentence from English to French and Spanish. "
            "I like red cars and blue houses, but my dog is yellow."
)
```

发送就一个动作——`invoke`（这个函数后面每一课都复用）：

```python
model.invoke([message])   # 触发调用，返回一个 AIMessage
```

## 5. 角色模型：human / AI / administrator

跑完能看到输入是 `HumanMessage`、返回是 `AIMessage`。讲师借此点出与模型交互的**角色（role）**概念——human、agent(AI)、administrator 等不同角色；本课聚焦 human↔AI 这一对。翻译结果同时给出法语和西语（讲师本人会这两种语言，确认翻译正确），证明链路通了。

这个"一句无意义句子的翻译"看似 trivial，作用是**验证管道**：环境 → endpoint → LangChain 连接 → invoke，四段全通，才有资格往上加数据源。

## 本课总结

| 要点 | 一句话 |
|---|---|
| Foundation model | 单模型多任务 + 多模态 + 自然语言接口，是 database agent 的地基 |
| RAG vs Fine-tuning | 本课选 RAG——不重训、换模型无痛、高效实用 |
| Azure 连接三要素 | api_version / deployment / endpoint，调的是"部署名"不是模型名 |
| 三步连通 | 导入 → `AzureChatOpenAI` 建实例 → `HumanMessage` + `invoke` |
| invoke | 贯穿全课的统一调用入口 |

> **记忆点（引出 L2）**：L1 的 `model` 只会"凭自己的知识"回答（翻译靠模型自带能力），还没连任何私有数据。L2 给它接上第一个数据源——一个 CSV 文件，用 LangChain 的 **pandas DataFrame agent** 把"问数据"变成"问自然语言"，`invoke` 依旧是同一个入口，但 Agent 开始会自己写 pandas 代码、思考、取数。

## 与我的资产映射

- 检索层：`agent/skills/agent-selection/3-retrieval.md`（结构化数据 RAG = "生成查询"式检索，区别于向量检索）
- 模型层：Azure OpenAI 部署模型的连接范式（deployment 而非模型名），可沉淀为选型清单里的"托管模型接入"条目
- [[project_selection_matrix]]
