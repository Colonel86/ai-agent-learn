# L3 · 用 Claude on Vertex AI 构建保险问答 Agent（协议接入前的"裸 Agent"）

> 课程：A2A: The Agent2Agent Protocol（DeepLearning.AI × Google）
> 本课任务：用 Claude Haiku 4.5（经 Vertex AI）构建一个回答**健康保险政策**问题的 QA Agent，并重构成 `PolicyAgent` 类——它是接下来七课多 Agent 系统的第一块砖，**此刻还没有一行 A2A 代码**。

## 0. 本课目标与七课路线

从本课起，L3–L9 会逐步搭出一个**医疗健康行业的多 Agent 系统**：先做单个 Agent，再不断加新 Agent、用 A2A 把它们连起来，且刻意混用**多种框架和模型**（裸 SDK + Claude、ADK + Gemini、LangGraph……）——这正是 A2A 要解决的异构互操作场景。

模型统一走 **Vertex AI Model Garden** 获取（讲师原话：方便、安全、可扩展地访问多种模型），但 **A2A 本身不绑云**——任何云甚至 on-prem 都能跑。本课的推进节奏：

```
L3: PolicyAgent（普通 Python 类，会答保险问题）
L4: 包成 A2A Server（AgentExecutor + AgentCard）
L5: 写 A2A Client 去发现并调用它
```

## 1. 认证与客户端：AnthropicVertex

课程环境用 helper 函数 `authenticate()` 完成 Google Cloud 认证，值得拆开看一眼（`helpers.py`）——它不是简单读个 API key：

```python
def authenticate():
    # ① 从 GOOGLE_APPLICATION_CREDENTIALS 找 service account 的 JSON key
    source_credentials = service_account.Credentials.from_service_account_file(
        key_path, scopes=["https://www.googleapis.com/auth/cloud-platform"])
    source_credentials.refresh(request)          # ② 换 1 小时短期 token
    credentials = impersonated_credentials.Credentials(
        source_credentials=source_credentials,
        target_principal=...,                    # ③ 自我模拟(impersonate)
        lifetime=7200)                           #    换成 2 小时 token(够上一节课)
    credentials.refresh(request)
    return credentials, project_id
```

然后创建 Anthropic 官方 SDK 提供的 **`AnthropicVertex`** 客户端——接口和直连 Anthropic API 的 `Anthropic` 客户端一致，但鉴权走 GCP：

```python
client = AnthropicVertex(
    project_id=project_id,        # GCP 项目,计费/配额归属
    region="global",              # Vertex 区域
    access_token=credentials.token,  # 用 GCP token,不是 Anthropic API key
)
```

> **对比 1-model.md 的供应形态**：这是"**第三方模型经云厂商托管**"的典型形态——Claude 不从 Anthropic API 直连，而是从 Vertex AI Model Garden 取。换到的东西：统一 GCP IAM 鉴权（上面那串 impersonated credentials 就是代价的具象）、统一计费、数据边界留在自家云内、与 Gemini 等同一入口横评（Q4"是否接受绑定单一厂商"在这里变成绑云而非绑模型厂商）；付出的代价：模型 ID 要带日期钉版本（`claude-haiku-4-5@20251001`）、新模型/新区域上架可能滞后、鉴权比一个 API key 复杂得多。AWS Bedrock 上的 Claude 同理。

## 2. 上下文注入：整份 PDF 塞进 Prompt

Claude 自己不知道任何保险政策，需要把政策文档喂给它。做法是把 PDF 读出来 base64 编码，作为 **document block** 放进消息：

```python
with Path("../data/2026AnthemgHIPSBC.pdf").open("rb") as file:
    pdf_data = base64.standard_b64encode(file.read()).decode("utf-8")
```

讲师明确说这是"**RAG 的相似模式，但不做 chunking 和 retrieval**"——整份文档直接进 prompt。对一份几十页的保单文档 + 长上下文模型，这是最省事的做法。

> **架构师视角**：全文档注入 vs 建 RAG 管线，是 3-retrieval 层最常被跳过的第一问——**文档总量塞得进上下文窗口且查询频次不高时，检索层整层可以不建**。代价是每次请求都重复付整份 PDF 的输入 token（可用 prompt caching 缓解）；等文档从 1 份变 100 份，再升级到 chunking + 检索也不迟。先用最轻方案打通端到端，是这门课整体的搭建哲学。

## 3. 查询模型：system 定人设，messages 带文档

```python
response = client.messages.create(
    model="claude-haiku-4-5@20251001",   # 钉死日期的版本号(Vertex 惯例)
    max_tokens=1024,
    system="You are an expert insurance agent ... "
           "If the information is not available in the documents, "
           "respond with 'I don't know'",   # 人设 + 任务 + 兜底护栏
    messages=[MessageParam(role="user", content=[
        DocumentBlockParam(                 # PDF 作为 document block
            type="document",
            source=Base64PDFSourceParam(
                type="base64",
                media_type="application/pdf",
                data=pdf_data)),
        TextBlockParam(type="text",
            text="How much would I pay for mental health therapy?"),
    ])],
)
```

三个要点：

| 要素 | 作用 |
|---|---|
| system prompt | 定义 persona（专家保险顾问）+ 任务边界 + **"文档里没有就答 I don't know"** 的反幻觉护栏 |
| DocumentBlockParam | PDF 原生进 prompt，模型自己读版面（不需要先转文本） |
| `$` 转义 | `response.content[0].text.replace("$", r"\\$")`——纯粹是 Jupyter 渲染 Markdown 时 `$` 会触发数学公式，与 Agent 逻辑无关 |

运行结果：心理健康治疗费用为 **In-Network 10% / Out-of-Network 30%（满足 $1,700 免赔额之后）**。讲师翻开 PDF 核对，答案正确。

## 4. 重构为 PolicyAgent 类

为了下一课好包装，把上述逻辑收进一个类，用 Jupyter magic `%%writefile agents.py` 落盘（**Agent 的实际行为零变化**，只是换了组织形式）：

```python
# %%writefile agents.py
class PolicyAgent:
    def __init__(self) -> None:
        load_dotenv()
        credentials, project_id = authenticate()
        self.client = AnthropicVertex(...)          # 客户端建一次
        self.pdf_data = base64...(file.read())...   # PDF 读一次,缓存在实例上

    def answer_query(self, prompt: str) -> str:     # 唯一对外接口:文本进,文本出
        response = self.client.messages.create(
            model="claude-haiku-4-5@20251001",
            system="You are an expert insurance agent ...",
            messages=[...文档 + prompt...])
        return response.content[0].text.replace("$", r"\\$")
```

测试：`PolicyAgent().answer_query(prompt)` 得到与之前相同的答案。

> **架构师视角**：`answer_query(str) -> str` 这个签名是刻意设计的**协议中立接口**——`PolicyAgent` 里没有任何 A2A/HTTP/框架的痕迹，全部是纯业务逻辑（模型 + 文档 + prompt）。L4 的 A2A 包装因此可以做到对这个类**零侵入**。这就是"业务 Agent 与协议适配器分层"：明天想把它挂到 MCP、挂到 REST API 或换一个协议，`agents.py` 一行不用改。反例是把 HTTP 处理和 LLM 调用写在一起——那样每换一次暴露方式都要动核心逻辑。

## 5. 本课总结

| 要点 | 一句话 |
|---|---|
| 供应形态 | Claude 经 Vertex AI Model Garden 接入，GCP token 鉴权、模型 ID 钉日期 |
| 上下文策略 | 整份 PDF base64 → DocumentBlockParam 进 prompt，不建检索层 |
| 护栏 | system prompt 里"文档没有就答 I don't know" |
| 重构 | 逻辑收进 `PolicyAgent.answer_query(str)->str`，协议中立、为 L4 铺路 |

> **记忆点（引出 L4）**：此刻的 `PolicyAgent` 只是**本进程里的一个 Python 类**——别的进程、别的团队、别的框架写的 Agent 既发现不了它，也调用不了它。L4 用 A2A Python SDK 给它套上 AgentExecutor、写好 AgentCard，把它变成网络上一个**可发现、可调用的 A2A Server**。

## 与我的资产映射

- 模型层选型：`agent/skills/agent-selection/1-model.md`（供应形态：API 直连 vs 云托管 Model Garden/Bedrock——本课是后者的活例子）
- 检索层：`agent/skills/agent-selection/3-retrieval.md`（全文档注入是"检索层先不建"的最轻起步）
- 协议层：`agent/skills/agent-selection/2-framework/06-protocols.md`（本课正处于升级路径第一级："单 agent + 好工具"，还没到需要协议的边界）
- [[project_selection_matrix]]
