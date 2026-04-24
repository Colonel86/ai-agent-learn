# Functions, Tools and Agents with LangChain — 第 08 课：课程结语（中文整理）

> 来源：`subtitles/langchain_c3_08_en.vtt`（本节无配套代码）

---

## 一、课程回顾

这门课围绕**两个核心新能力**展开：

1. **OpenAI Function Calling** —— 让 LLM 输出结构化的"函数名 + 参数"，从而能调用外部代码；
2. **LangChain Expression Language（LCEL）** —— 用 `|` 管道符把组件拼成 chain，享受 invoke / batch / stream / async / fallback / 并行等统一接口。

在这两个能力之上，课程展示了三类典型应用：

| 应用 | 关键思路 |
|------|----------|
| **Structured Data Extraction** | 用 Pydantic 描述你想要的结构 → 强制 LLM 按结构输出（Tagging / Extraction） |
| **Tool Usage** | 用 `@tool` 装饰器造工具 → `format_tool_to_openai_function` 转 OpenAI function → 模型选工具 → 代码执行工具 |
| **Tool Selection / Routing** | 绑定多个 function → `OpenAIFunctionsAgentOutputParser` 得到 `AgentAction` / `AgentFinish` → 用 route 函数分流 |

最后把上面所有东西组合起来，搭出了一个**会话式 Agent**：

- 有 **memory**（能记住"我叫 Bob"）；
- 会 **自主选择 & 调用工具**（天气、Wikipedia、自定义工具）；
- 行为上已经很接近 **ChatGPT 的 Code Interpreter / Plugin 调度**。

---

## 二、8 节课脉络串起来

| 课次 | 主题 | 带走什么 |
|------|------|-----------|
| **L1** | 课程介绍 | 明白为什么 LLM 需要 function calling，以及这门课会教什么 |
| **L2** | OpenAI Function Calling（纯 SDK） | 懂 functions / function_call 参数，以及 role=function 的回传机制 |
| **L3** | LCEL 基础 | 会用 `\|` 拼 chain、RunnableMap、`.bind`、`with_fallbacks`、invoke / batch / stream / async |
| **L4** | Pydantic + LCEL + Functions | 用 Pydantic 干净地声明函数 schema；模型在多 function 间自主选择 |
| **L5** | Tagging & Extraction | 用 JsonOutputFunctionsParser / JsonKeyOutputFunctionsParser；长文 splitter + map + flatten |
| **L6** | Tools & Routing + OpenAPI | `@tool` 造工具、OpenAPI spec 批量导入、`OpenAIFunctionsAgentOutputParser` 得到 AgentAction/Finish |
| **L7** | Conversational Agent | agent_scratchpad 循环 / RunnablePassthrough.assign / AgentExecutor / ConversationBufferMemory |
| **L8** | 结语（本节） | 回顾 + 鼓励在实际业务中落地 |

---

## 三、讲师寄语

> "With all these learnings under your belt, the only thing left to do is go out into the real world and apply them to your use cases."
> —— 掌握了这些技术之后，剩下的事就是**回到真实业务里去用它**。

---

## 四、接下来可以怎么做（落地路线图）

1. **选一个痛点业务场景**：先挑一个"LLM + 外部系统"的小问题，例如：
   - 客服场景下自动查订单状态、退款记录；
   - 研发内部工具里让 LLM 查 PR / 部署 / 日志；
   - 财务流程里结构化抽取发票/合同字段。
2. **先写 1 个工具**：用 `@tool` 包起来，确保单独能 run。
3. **让 LLM 选它**：绑上 function + 最小 prompt，观察模型调用是否稳定。
4. **扩成 Agent 循环**：加 `AgentExecutor` + `ConversationBufferMemory`，让它可以多轮、可以组合工具。
5. **评估 & 迭代**：给一批典型问题，看看工具选错率、参数错误率；必要时修 description / schema。
6. **上线观察**：加日志、加 fallback、设最大循环步数。

---

## 五、几条来自本课的"最佳实践"沉淀

- **Function / Tool 的 description 本质就是 prompt**，写得越清晰选得越准。
- **Pydantic class 的 docstring 必填**（LangChain 强制）——因为这是 description 的来源。
- **对"结构化输出"场景，`temperature=0`**，避免模型发挥。
- **Tagging / Extraction 要明确告诉模型"没有就返回空"**，避免幻觉填充。
- **长文本要 splitter + map + flatten**，不要一把梭把超过 token 上限的内容塞过去。
- **多步 Agent** 要记得：循环 + scratchpad + 停止条件（模型自主 or 最大步数硬限）。
- **记忆不是魔法**：`memory_key` 必须和 prompt 里 `MessagesPlaceholder` 的变量名对齐。

---

## 六、写在最后

这门课把 "**如何用 LLM 去驱动实际软件系统**" 这件事拆到了一个相对清晰的方法论层：

- 结构化输入输出靠 **Function Calling + Pydantic**；
- 编排组合靠 **LCEL**；
- 把"智能决策"和"真实执行"解耦的最小抽象是 **Tool + Routing**；
- 把它做成有状态的助手就是 **Agent + Memory**。

这些组件在 2026 年的今天仍在快速演进（工具调用的原生模型、LangGraph 风格的显式状态机等），但**L2 ~ L7 打下的概念模型**仍然是理解更复杂框架的基础。
