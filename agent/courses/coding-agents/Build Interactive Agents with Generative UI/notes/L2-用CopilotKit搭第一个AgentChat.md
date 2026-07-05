# L2 · 用 CopilotKit + AG-UI 搭第一个 Agent Chat（生产级地基）

> 课程：Build Interactive Agents with Generative UI（DeepLearning.AI × CopilotKit）
> 本课任务：搭一个能连**任意 agentic 后端**的生产级 chat 地基——LangChain Deep Agent → AG-UI FastAPI 端点 → CopilotRuntime → React `CopilotChat`；并现场把后端从 LangChain/OpenAI **热切换**到 Google ADK/Gemini 而前端零改动。
> 代码：`code/L2.ipynb`。

## 1. 先谈 chat 的持久价值

在给 agent 加各种花哨 UI 之前，Atai 先为**纯 chat** 正名。LLM 2022 年随 ChatGPT 破圈，很多人预言 chat 只是很快过气的过渡形态、会被更传统的交互取代。但走到 agent 时代，chat 反而**比大家最初给它的信用留存得久得多**。

为什么？CopilotKit 把 chat 理解成"**Slack with an agent**"——chat 是**智能实体间开放式的沟通媒介**，不把你锁死在预设的按钮和菜单里；而且这就是人本来的沟通方式（人与人、甚至人与自己）。所以 chat 会长期陪伴 agentic 革命。但 **chat 不必只有文本**：可被 generative UI 与应用内交互增强，甚至锚定在语音/视频而非文本上。本课搭的地基会随 chat 媒介演化而持续成立。

本课的 chat 与你随手写过的（哪怕只是 debug agent 时的 streamlit）有两点本质不同：① **生产级地基**，可持续往上长 full-stack agent 与 generative UI；② 可配**几乎任意 agentic 后端**（任意语言/任意 LLM provider/任意 agent harness），未来还能换任意前端环境。

## 2. 架构总览

```
┌────────────────────┐   AG-UI    ┌──────────────────┐        ┌─────────────────┐
│ LangChain Deep     │  events    │  CopilotRuntime  │        │  React 前端      │
│ Agent (on LangGraph)│──────────▶│  (Hono TS server │◀──────▶│  <CopilotChat/>  │
│  + CopilotKit MW   │   HTTP     │   :4002)         │  fetch │  provider :3002  │
│  FastAPI :8002     │            │  /api/copilotkit │        │                 │
└────────────────────┘            └──────────────────┘        └─────────────────┘
     后端(Python)                    安全/性能/扩展的桥            用户界面(React)
```

四块拼装：

1. **后端**：LangChain Deep Agent（底层是 LangGraph），部署在 **AG-UI FastAPI 端点**（Python，端口 8002）；
2. **CopilotRuntime**：夹在前端与 agent 之间的后端桥，本课跑在 **Hono**（轻量 TypeScript server）上；
3. **前端**：React，用 CopilotKit 自带的 **`CopilotChat`** 组件（开箱即用的全功能 chat）；
4. **AG-UI 协议**：把三者串起来，让"换后端"变成改配置。

> **架构师视角**：`CopilotRuntime` 技术上**可选**（前端能直连 agent），但生产环境**强烈推荐**——它是为 security / performance / engineering scalability 存在的一道夹层。类比 `10-agent-ux.md`：这就是"呈现层框架"落地时必须补的服务端 glue，别在 demo 里省掉、上线才补。注意每课用不同端口（8002/8003…）避免互相覆盖。

## 3. 后端：AG-UI FastAPI 端点

先起一个标准 FastAPI server，挂一个 **`LangGraphAGUIAgent`**（LangGraph agent 的 AG-UI 兼容端点）：

```python
from fastapi import FastAPI
from ag_ui_langgraph import add_langgraph_fastapi_endpoint
from copilotkit import LangGraphAGUIAgent
from langchain.agents import create_agent
from helper import start_server

app = FastAPI()
graph = create_agent("openai:gpt-4.1")          # 先占位一个 graph
agent = LangGraphAGUIAgent(
    name="lesson2_agent",
    description="Lesson 2 chart agent",
    graph=graph,
)
add_langgraph_fastapi_endpoint(app=app, agent=agent, path="/")  # 挂到根路径
start_server(app, port=8002)                    # 端口 8002
```

> LangGraph 是 LangChain 所有 agentic 方案的底层框架——用的是 Deep Agent，但因其建在 LangGraph 上，所以走 `LangGraphAGUIAgent`。

再定义**真正的 agent**，全程标准 LangChain，**唯一要划重点的是注入 CopilotKit 的 middleware**：

```python
from copilotkit import CopilotKitMiddleware
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver

graph = create_agent(
    model=ChatOpenAI(model="gpt-4.1"),
    tools=[],
    middleware=[CopilotKitMiddleware()],        # ★ 把 LangChain agent 接到 AG-UI 的一切
    checkpointer=MemorySaver(),                 # 记忆
    system_prompt="You are a helpful assistant",
)
agent.graph = graph        # 热重载：更新 graph 而不重启 server
```

`CopilotKitMiddleware()` 是**连接点**——它让模型能发现并调用**前端定义的工具**（L3 的 controlled UI 全靠它）。没有它，agent 只看得见后端工具。middleware 是 LangChain 世界的标准概念，此处零侵入接入。

## 4. CopilotRuntime：前端与 agent 之间的桥（server.ts）

用 `%%writefile` 直接写盘（跑着的 app 会自动热更）。从 `@ag-ui/langgraph` 引入 **`LangGraphHttpAgent`** 指向 8002，注册进 `CopilotRuntime` 的 agent 字典，暴露 `/api/copilotkit`，用 Hono serve：

```ts
import { serve } from "@hono/node-server";
import { LangGraphHttpAgent } from "@ag-ui/langgraph";
import { CopilotRuntime, createCopilotEndpoint } from "@copilotkit/runtime/v2";

const langGraphAgent = new LangGraphHttpAgent({
  url: process.env.LANGGRAPH_DEPLOYMENT_URL || "http://localhost:8002",
});

const runtime = new CopilotRuntime({
  agents: { default: langGraphAgent },   // agentId → 端点 的映射；未指定则用 default
});

const app = createCopilotEndpoint({ runtime, basePath: "/api/copilotkit" });
serve({ fetch: app.fetch, port: 4002 });
```

要点：CopilotRuntime 持有一个 **`{ agentId: 端点 }` 字典**——前端可指定跟哪个 agent 说话，不指定就用 `default`。`/v2` 导入路径给的是最新 hooks/组件，全课用 v2。

## 5. 前端：Provider + CopilotChat

**任何要跟 agent 对话的部分都必须被 `CopilotKit` provider 包住**。通常在 `main.tsx` 里一次性包整个应用，`runtimeUrl` 指向上一步的 `/api/copilotkit`：

```tsx
// main.tsx
import { CopilotKit } from "@copilotkit/react-core/v2";
import "@copilotkit/react-core/v2/styles.css";

createRoot(document.getElementById("root")!).render(
  <CopilotKit runtimeUrl="/api/copilotkit" useSingleEndpoint={false}>
    <App />
  </CopilotKit>
);
```

再放 **`CopilotChat`**——开箱全功能 chat，指向 `default` agent：

```tsx
// App.tsx
import { CopilotChat } from "@copilotkit/react-core/v2";
const agentId = "default";
export default function App() {
  return <CopilotChat agentId={agentId} />;
}
```

`CopilotChat` 可用自定义 CSS / 子组件深度改造（本课不展开）；若想从零手搓 chat，可用 headless 的 **`useAgent`** hook。至此，一个连着真实 LangChain agent 的 chat 就跑起来了。

## 6. 换后端：一行配置切到 Google ADK / Gemini

AG-UI 的意义就在这。**同一套前端**接到 Google ADK agent，只改两处、UI 零改写。

**① 起一个 ADK agent（端口 8009）**：

```python
from ag_ui_adk import ADKAgent, add_adk_fastapi_endpoint
from google.adk.agents import LlmAgent

gemini_agent = LlmAgent(name="assistant", model="gemini-2.5-flash",
                        instruction="Be helpful and fun!")
adk_agent = ADKAgent(adk_agent=gemini_agent, app_name="demo_app",
                     user_id="demo_user", use_in_memory_services=True)
app_adk = FastAPI()
add_adk_fastapi_endpoint(app_adk, adk_agent, path="/")
start_server(app_adk, port=8009)
```

**② CopilotRuntime 里多注册一个 agent**（`HttpAgent` 指向 8009，键名 `gemini`——键名随意）：

```ts
const adkAgent = new HttpAgent({ url: "http://localhost:8009" });
const runtime = new CopilotRuntime({
  agents: { default: langGraphAgent, gemini: adkAgent },  // ★ 新增一行
});
```

**③ 前端改 `agentId`**：`"default"`→LangChain/OpenAI，`"gemini"`→ADK/Gemini。问它"你是什么模型"，答"Google 训练的大模型"——切换成功。

> 因为在 Jupyter 里写 TypeScript，改动只能**整文件覆盖**（`%%writefile`），不能局部改。这是 notebook 的限制，不是 CopilotKit 的。

## 7. 什么是 AG-UI（本课回扣）

**AG-UI（Agent-User Interaction）= 开放、轻量、基于事件的协议**，标准化 chat 消息、tool call、state 更新、流式 token 如何走 HTTP。运行时：AG-UI 兼容 agent 边跑边 emit **output events**，并接受前端因用户交互 emit 的 **input events**。它诞生于 CopilotKit 与 LangChain、CrewAI 的合作。刚才亲眼看到的三个收益：

- CopilotKit 能跟**任何实现了 AG-UI 的后端**对话；
- 一个配置改动就从 LangChain/OpenAI 切到 ADK/Gemini，**无 UI 重写**；
- 流式与工具行为**跨框架一致**。

## 本课总结

| 要点 | 一句话 |
|---|---|
| 四块地基 | LangChain Deep Agent(FastAPI) → CopilotRuntime(Hono) → React CopilotKit provider → CopilotChat |
| 唯一非标准点 | 后端注入 `CopilotKitMiddleware()`，让 agent 能看见前端工具 |
| CopilotRuntime | 可选但生产强推的安全/性能/扩展夹层；持 `{agentId:端点}` 字典 |
| 换后端 | AG-UI 让"换 agent"退化成改配置：ADK/Gemini 三处改动、UI 零改写 |
| 热重载 | `agent.graph = ...` 不重启换 graph；TS 文件在 notebook 里靠整文件覆盖 |

> **记忆点（引出 L3）**：L2 的 agent 只能回**纯文本**。L3 迈出文本——用 **Controlled Generative UI**（generative UI 的劳模）：靠 `useComponent()` 把 React 组件（showMyName / pieChart / flightCard）注册成**前端定义的工具**，agent 自己决定何时调、填什么数据来渲染。底层正是 L2 那个 `CopilotKitMiddleware` 把这些前端工具暴露给模型的。

## 与我的资产映射

- 呈现层选型：`agent/skills/agent-selection/10-agent-ux.md`（AG-UI/CopilotKit 候选行的落地实操；CopilotRuntime = 呈现层框架必补的服务端 glue，对应"选了 AG-UI 会反向约束后端框架有适配"）
- 协议层：`agent/skills/agent-selection/2-framework/06-protocols.md`（AG-UI output/input 事件模型）
- [[project_selection_matrix]]
