# L8 · MCP 工具 + LangGraph + A2A 三层组装（Healthcare Provider Agent）

> 课程：A2A: The Agent2Agent Protocol（DeepLearning.AI × Google）
> 本课任务：课程开头说过 **A2A 和 MCP 是互补协议**，本课真刀真枪造一个两者都用的 agent——用 FastMCP 写一个提供虚构医生名录的 MCP server，接进 LangGraph agent（OpenAI GPT OSS on Vertex AI），最后再把整个 agent 包成 A2A server 对外服务。

## 0. 本课目标与三层结构

前面 L3-L5 用裸 A2A SDK 跑通了 PolicyAgent（保险问答）闭环，L6-L7 换 Google ADK 走了一遍框架集成。本课引入第三个 agent——**Healthcare Provider Agent**（按地点/专科找医生），它的价值在于一次演示三种技术的正确分层：

```
外部 A2A client（L9 用 Microsoft Agent Framework 来连）
        │  HTTP + A2A 协议
┌───────▼──────────────────────────────────────────┐
│ ③ A2A 层  a2a_provider_agent.py                  │
│    AgentCard/AgentSkill + Starlette + uvicorn    │  ← 对其他 agent 的"名片+门面"
│    ProviderAgentExecutor（懒初始化）              │
│  ┌────────────────────────────────────────────┐  │
│  │ ② 框架层  agents.py :: ProviderAgent       │  │
│  │    LangGraph create_agent + ChatOpenAI     │  │  ← 推理与工具编排
│  │    (gpt-oss-20b-maas @ Vertex AI)          │  │
│  │      │ MCP stdio（子进程 uv run）           │  │
│  │  ┌───▼────────────────────────────────┐    │  │
│  │  │ ① 工具层  mcpserver.py (FastMCP)   │    │  │  ← 数据/工具接入
│  │  │    list_doctors ← doctors.json     │    │  │
│  │  └────────────────────────────────────┘    │  │
│  └────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────┘
```

一句话记：**MCP 面向 LLM 暴露工具，A2A 面向其他 agent 暴露整个 agent**，LangGraph 在中间做编排。

> **对比我的选型矩阵 2-framework/06-protocols.md**：那页给的 2026 参考架构口令是"**MCP 接工具/数据（L1）+ A2A 接 agent（L4）**，两层就够记"——本课就是这句话的**可运行实证**：doctors.json 这份数据走 MCP 进 agent，agent 本身走 A2A 出去给别的 agent 调。两个协议各管一条轴、互不越界，谁也不能替代谁（矩阵里的边界句：协议与各层正交，是加分项不是选型项）。

## 1. 工具层：FastMCP 写 MCP server（mcpserver.py）

用 `%%writefile` 魔法把 MCP server 写成独立文件。数据源是 `code/data/doctors.json`——一份虚构医生名录（demo 数据，每条含 name / specialty / address / 保险 / 教育背景等字段）：

```python
# mcpserver.py（摘录简化）
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("doctorserver")                # 初始化 MCP server，命名 doctorserver
doctors: list = json.loads(Path("../data/doctors.json").read_text())  # 加载虚构医生数据

@mcp.tool()                                  # 装饰器：把普通方法变成 MCP tool
def list_doctors(state: str | None = None, city: str | None = None) -> list[dict]:
    """This tool returns a list of doctors practicing in a specific location...
    Args: state: 两字母州码（如 "CA"）; city: 城市名（如 "Boston"）..."""
    # ↑ docstring 必须写详细——LLM 靠它决定何时调用哪个函数
    if not state and not city:               # 输入校验：至少给州或城市之一
        return [{"error": "Please provide a state or a city."}]
    target_state = state.strip().lower() if state else None   # 归一化 → 大小写不敏感匹配
    target_city = city.strip().lower() if city else None
    return [doc for doc in doctors           # 列表推导式按州/城市过滤
            if (not target_state or doc["address"]["state"].lower() == target_state)
            and (not target_city or doc["address"]["city"].lower() == target_city)]

if __name__ == "__main__":
    mcp.run(transport="stdio")               # 走 stdio 传输 → 本地运行
```

三个要点：

| 要点 | 说明 |
|---|---|
| docstring 即 API 面 | LLM 用它决定"调哪个函数、何时调"，是给模型看的文档，不是给人看的 |
| 返回值自动序列化 | FastMCP 自动把 `list[dict]` 转成 JSON 发给模型，不用手写序列化 |
| stdio 传输 | server 以**宿主脚本的子进程**方式跑在本地，**不是**独立 HTTP server |

> **架构师视角**：`@mcp.tool()` + docstring 这套约定意味着**工具描述就是 prompt 的一部分**——写得含糊，模型就乱调或不调（对应选型矩阵 4-tools.md 的工具描述质量问题）。另外注意 stdio vs HTTP 的取舍：stdio 是"零部署"最轻起步，适合工具与 agent 同机同生命周期；一旦工具要给多个 agent 复用或独立扩缩容，才升级为远端 HTTP MCP server。

## 2. 框架层：LangGraph agent 消费 MCP 工具

### 2.1 连接 MCP：MultiServerMCPClient

先认证 Google Cloud、拼出 Vertex AI 的 OpenAI 兼容端点（LangChain 的 OpenAI connector 要用 Vertex AI，必须覆写默认 base_url），并用 `nest_asyncio` 让异步代码能跑在 Jupyter 里：

```python
credentials, project_id = authenticate()     # Google Cloud 认证（helpers.py）
base_url = f"{os.getenv('GOOGLE_VERTEX_BASE_URL')}/v1/projects/{project_id}/locations/us-central1/endpoints/openapi"
# ↑ 覆写默认 URL：让 LangChain 的 OpenAI 连接器指向 Vertex AI 的 OpenAI 兼容端点

mcp_client = MultiServerMCPClient({          # LangGraph 侧的 MCP 客户端（可挂多个 server）
    "find_healthcare_providers": StdioConnection(
        transport="stdio",
        command="uv", args=["run", "mcpserver.py"],  # 以子进程方式拉起 MCP server
    )
})
tools = asyncio.run(mcp_client.get_tools())  # 关键一步：MCP tools → LangChain/LangGraph tools
```

`get_tools()` 是两个生态的**转换器**：MCP 侧的工具 schema 被翻译成 LangChain tool 对象，此后 LangGraph 完全不感知 MCP 的存在。

### 2.2 创建 agent：create_agent + 反幻觉 system_prompt

```python
agent = create_agent(
    ChatOpenAI(
        model="openai/gpt-oss-20b-maas",     # OpenAI GPT OSS 20B，Vertex AI 上的 model-as-a-service
        openai_api_key=credentials.token,    # 用 Google Cloud 凭证 token 充当 API key
        openai_api_base=base_url,            # 指向 Vertex AI 端点
    ),
    tools,                                   # 上一步转换来的 MCP 工具
    name="HealthcareProviderAgent",
    system_prompt="""Your task is to find and list healthcare providers
    using the find_healthcare_providers MCP Tool based on the users query.
    Only use providers based on the response from the tool.""",
    # ↑ 最后一句是实测补的：这个模型爱"自作主张"编入真实世界的医生，
    #   必须显式约束只允许使用工具返回的（虚构）provider
)
```

测试："I'm based in Austin, TX. Are there any Psychiatrists near me?" → agent 调用 MCP 工具，返回 Austin 的精神科医生 Dr. Coffey。**LangGraph agent 通了**。

> **架构师视角**：讲师那句"in my experimentation, this model likes to try and include real doctors"值得存档——**模型参数知识会污染工具结果**是工具型 agent 的通病，医疗场景里编一个真实医生就是事故。防线两道：prompt 显式声明"only use providers from the tool"（本课做法），更严的场景在输出侧再加校验（返回的 provider 必须能在工具结果里 join 到）。

### 2.3 封装成 ProviderAgent 类（追加到 agents.py）

为了给 A2A 层一个干净接口，把上述逻辑收进容器类。注意是 `%%writefile -a` **追加**——agents.py 里已经有 L3 的 PolicyAgent（Claude 读保险 PDF 那个）：

```python
# agents.py（追加部分，摘录简化）
class ProviderAgent:
    def __init__(self) -> None:
        # 同步部分：认证、拼 base_url、构造 MultiServerMCPClient
        self.agent = None                     # agent 留空，等 initialize()

    async def initialize(self):
        """异步初始化：MCP 客户端连接是 async 的，不能塞进 __init__，
        单独一个 initialize() 避免初始化竞态（race condition）"""
        tools = await self.mcp_client.get_tools()
        self.agent = create_agent(...)        # 同 2.2；system_prompt 多加了一句
        return self                           # "Output the information in a table"

    async def answer_query(self, prompt: str) -> str:
        # 所有 agent 通信逻辑收口在这：prompt 进、字符串出
        response = await self.agent.ainvoke({"messages": [{"role": "user", "content": prompt}]})
        return response["messages"][-1].content
```

用 `await ProviderAgent().initialize()` 再跑一次 Austin 精神科的查询验证——类工作正常。

## 3. A2A 层：包成 A2A server（a2a_provider_agent.py）

一个插曲：LangGraph 的官方 serving 方案（LangSmith）**有内建 A2A 集成**，但它的工作方式与本课其他集成差异很大。为保持一致性，讲师选择沿用 L3 裸 A2A SDK 的包装流程——**这也正是任何"还没有 A2A 集成"的框架的通用接入姿势**。

### 3.1 Executor：懒初始化是关键

```python
# a2a_provider_agent.py（摘录简化）
class ProviderAgentExecutor(AgentExecutor):
    def __init__(self) -> None:
        self.agent = None                     # __init__ 不是 async，不能 await → 先占位

    async def _ensure_initialized(self) -> None:
        """懒初始化：第一次请求到达时才真正建 agent + MCP 连接"""
        if self.agent is None:
            self.agent = await ProviderAgent().initialize()

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        await self._ensure_initialized()      # 确保就绪
        prompt = context.get_user_input()     # 从 A2A 请求上下文取用户输入（同 L3）
        response = await self.agent.answer_query(prompt)
        await event_queue.enqueue_event(new_agent_text_message(response))  # 结果入事件队列

    async def cancel(self, context, event_queue) -> None:
        pass                                  # 与 L3 一样，cancel 直接放过
```

与 L3 的 Executor 骨架完全同构，唯一新增的复杂度是**异步初始化**：MCP 客户端连接是 async 的，而 `__init__` 不能 `await`，所以用 `_ensure_initialized()` 把初始化推迟到首个 `execute` 调用。

### 3.2 main：AgentSkill / AgentCard / Starlette

```python
def main():
    HOST = os.environ.get("AGENT_HOST", "localhost")
    PORT = int(os.environ.get("PROVIDER_AGENT_PORT", 9997))

    skill = AgentSkill(                       # Skill 基本上就是在"描述那个 MCP 工具"
        id="find_healthcare_providers",
        name="Find Healthcare Providers",
        description="Finds and lists healthcare providers based on user's location and specialty.",
        tags=["healthcare", "providers", "doctor", "psychiatrist"],
        examples=["Are there any Psychiatrists near me in Boston, MA?", ...],
    )
    agent_card = AgentCard(                   # 名片：名称/描述/URL/输入输出模态/能力/skills
        name="HealthcareProviderAgent",
        url=f"http://{HOST}:{PORT}/",
        capabilities=AgentCapabilities(streaming=False),  # 本 agent 不做流式
        skills=[skill], ...
    )
    request_handler = DefaultRequestHandler(  # 请求处理器 + 内存任务存储（同 L3）
        agent_executor=ProviderAgentExecutor(),
        task_store=InMemoryTaskStore(),
    )
    server = A2AStarletteApplication(agent_card=agent_card, http_handler=request_handler)
    uvicorn.run(server.build(), host=HOST, port=PORT)     # uvicorn 拉起
```

在 Terminal 3 里 `uv run a2a_provider_agent.py` 启动——server 就绪，等 L9 的客户端来连。

> **架构师视角**：注意同一个能力在两层被描述了两次——MCP 侧的 `list_doctors` docstring 写给**本 agent 的 LLM** 看（函数粒度：参数、返回值），A2A 侧的 `AgentSkill` 写给**外部 agent/编排者**看（能力粒度：examples、tags）。这不是重复，是**抽象级别的语义提升**：外部调用者不需要知道背后是一个 MCP 工具还是十个。发布 agent 时两份"文档"都要认真写，它们分别决定内部工具命中率和外部被发现/被委派的概率。

## 4. 汇总：本课用到的三次"协议翻译"

| 边界 | 翻译动作 | 谁做的 |
|---|---|---|
| MCP tool → LangChain tool | `mcp_client.get_tools()` | langchain-mcp-adapters |
| LangGraph agent → Python 类 | `ProviderAgent.answer_query()` 收口 | 手写容器类 |
| Python 类 → A2A agent | Executor + AgentCard + Starlette | 手写（裸 A2A SDK 模式，同 L3） |

## 5. 本课总结

| 要点 | 一句话 |
|---|---|
| MCP × A2A 互补实证 | 数据走 MCP 进 agent（工具轴），agent 走 A2A 对外（协作轴），两协议正交叠加 |
| FastMCP 极简工具 | `@mcp.tool()` + 详细 docstring + stdio 子进程运行，返回值自动 JSON 化 |
| MCP → LangGraph 桥 | `MultiServerMCPClient(StdioConnection).get_tools()` 一步转成 LangChain tools |
| Vertex AI 曲线接入 | ChatOpenAI 覆写 base_url 指向 Vertex 的 OpenAI 兼容端点，GCP token 当 API key |
| 反幻觉约束 | system_prompt 显式要求"只用工具返回的 provider"，防模型编真实医生 |
| 异步懒初始化 | MCP 连接是 async、`__init__` 不能 await → `initialize()` + `_ensure_initialized()` |
| 通用 A2A 包装 | 框架没有 A2A 集成时，裸 SDK 的 Executor/AgentCard 流程就是标准姿势 |

> **记忆点（引出 L9）**：Provider Agent 现在跑在 Terminal 3，说的是 A2A 这门"世界语"——下一课用 **Microsoft Agent Framework** 内建的 A2A client 去连它：Google 栈上的 LangGraph agent 被微软框架当成自家 agent 用，跨框架互操作才是 A2A 的存在意义。

## 与我的资产映射

- 协议层：`agent/skills/agent-selection/2-framework/06-protocols.md`——"MCP 接工具 + A2A 接 agent"两层参考架构，本课是完整可运行样例
- 框架档案：`agent/skills/agent-selection/2-framework/03-framework-profiles.md`——LangGraph 条目（可控性卖点；此处只用了 `create_agent` 浅层能力）
- 工具层：`agent/skills/agent-selection/4-tools.md`——工具描述质量（docstring 即 prompt）、模型知识污染工具结果的防线
- 课程横向：课程 10-MCP（本课把 MCP 从"独立主题"落成 A2A agent 的内脏）
- [[project_selection_matrix]]
