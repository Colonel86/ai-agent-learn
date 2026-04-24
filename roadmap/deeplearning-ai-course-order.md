# DeepLearning.AI 课程学习顺序（AI Agent 方向）

> 目标：AI Agent 开发工程师 → AI Agent 开发架构师
> 更新日期：2026-04-24
> **学习理念：T 型学习——主线深挖 LangChain/LangGraph + MCP，其他框架做横向对比**

---

## Phase 1：基础构建

| 序号 | 课程 | 状态 |
|---|---|---|
| 1 | ChatGPT Prompt Engineering for Developers | ✅ 已完成 |
| 2 | Building Systems with the ChatGPT API | ✅ 已完成 |

---

## Phase 2：LLM 应用工程核心

| 序号 | 课程 | 核心内容 |
|---|---|---|
| 3 | LangChain for LLM Application Development | Chain、Memory、RAG 基础 |
| 4 | LangChain: Chat with Your Data | 向量检索、Document Loader |
| 5 | Building and Evaluating Advanced RAG | RAG 评估与优化 |
| 6 | Advanced Retrieval for AI with Chroma | Chroma 向量库、高级检索技巧（query expansion、reranking 等）🆕 |
| 7 | Pydantic for LLM Workflows | 结构化输出、类型安全 Tool Schema、Agent 工作流数据建模 🆕 |

---

## Phase 3：Agent 主线（深度优先，按序完成）

> **目标**：学完这 6 门，能独立用 LangGraph 做一个真实生产项目

| 序号 | 课程 | 核心内容 | 原序号 |
|---|---|---|---|
| 8 | Agentic AI（Andrew Ng） | **概念基石**——框架无关的 Agent 思维（planning / reflection / tool use）⭐ | #8 |
| 9 | Functions, Tools and Agents with LangChain | Tool Use、ReAct、OpenAI Function Calling | #9 |
| 10 | MCP: Build Rich-Context AI Apps with Anthropic | **工具层协议**——2026 事实标准，跨框架通用 ⭐ | #13 |
| 11 | AI Agents in LangGraph | 状态机、多步推理、条件路由、HITL、持久化 ⭐ | #10 |
| 12 | Long-Term Agentic Memory With LangGraph | 语义/情景/程序记忆、邮件助手实战 ⭐ | #17 |

### 💡 主线学习建议
- **#8** 概念奠基，后面所有框架都能对上号
- **#10 MCP** 提前到主线中段——它是协议层，学完 Tool 概念马上接 MCP 效果最佳
- **#12 学完后先做一个真实项目**，再进入 Phase 4

---

## Phase 4：横向扩展（主线学完后按需选学）

> **学习策略**：有了主线参照系，学这些会**快且透**。按兴趣/业务需要选学即可。

### 🅰 多 Agent 协作方向

| 序号 | 课程 | 价值 | 原序号 |
|---|---|---|---|
| 13 | Multi AI Agent Systems with crewAI | 多 Agent 协作**心智模型**（管理者思维、6 要素）⭐ | #11 |
| 14 | AI Agentic Design Patterns with AutoGen | Agent **设计模式**总览 ⭐ | #12 |
| 15 | Practical Multi AI Agents and Advanced Use Cases with crewAI | 生产级 crewAI（只在真用 crewAI 时再看） | #20 |

### 🅱 协议与扩展能力

| 序号 | 课程 | 价值 | 原序号 |
|---|---|---|---|
| 16 | Agent Skills with Anthropic | Skills + MCP + Subagents 组合 ⭐ 2026 新 | #18 |
| 17 | A2A: The Agent2Agent Protocol | 多 Agent 协作协议（Google Cloud + IBM）⭐ 2026 新 | #19 |

### 🅲 专项 RAG Agent（RAG 重业务才学）

| 序号 | 课程 | 价值 | 原序号 |
|---|---|---|---|
| 18 | Building Agentic RAG with LlamaIndex | RAG + Agent 结合 | #14 |
| 19 | Event-Driven Agentic Document Workflows with LlamaIndex | 事件驱动的文档处理 Agent | #15 |

---

## Phase 5：生产化与架构（架构师方向）

| 序号 | 课程 | 核心内容 |
|---|---|---|
| 21 | Evaluating AI Agents | Agent 指标、评测场景、测试方法 ⭐ |
| 22 | LLMOps | 部署、监控、版本管理 |
| 23 | Evaluating and Debugging Generative AI | MLflow 评估体系 |
| 24 | Automated Testing for LLMOps | CI/CD for LLM |
| 25 | Building AI Applications with Haystack | 生产级 RAG 框架 |

---

## Phase 6：前沿方向（按兴趣选修）

| 序号 | 课程 | 方向 |
|---|---|---|
| 26 | Knowledge Graphs for RAG | 结构化知识检索 |
| 27 | Serverless LLM Apps with Amazon Bedrock | 云端部署 |

---

## 学习节奏建议

### 时间投入
- 每门课约 1~2 小时视频 + 1~2 天实践
- **Phase 1~3 是核心主线**，优先完成
- Phase 4~5 根据工作需要按需取用

### 关键节点
- **Pydantic for LLM Workflows（#7）** 建议在 Phase 3 之前掌握，后续 LangChain / LangGraph / crewAI 的 tool schema、state 定义都依赖它
- **Advanced Retrieval for AI with Chroma（#6）** 是深入 RAG 的进阶补充，如果只是搭 Agent 不做深度 RAG 可先跳过
- **Phase 3 主线学完后先做真实项目**——这是从"看过" → "会用"的关键跃迁
- **Evaluating AI Agents（#21）** 建议在开始做第一个真项目之前就过一遍，能少踩很多坑

### Phase 4 选学优先级参考
1. 如果做**企业级 Agent**：先学 🅱 协议与扩展（#16 #17）
2. 如果做**RAG 产品**：先学 🅲 专项 RAG（#18 #19）
3. 如果想拓宽**架构思路**：先学 🅰 多 Agent（#13 #14）
4. #15（crewAI Practical）和 #19（LlamaIndex Event-Driven）都是**业务驱动型**课程——有真实场景再学

---

## 平台对比备注

DataCamp — Associate AI Engineer for Developers Track 更偏向数据科学工程师基础，Agent 系统设计内容较浅。如果时间有限，优先完成 DeepLearning.AI 的 Agent 系列（Phase 3）；如需工程基础补课或认证背书，可并行学习 DataCamp。

---

## 🗺 主线 vs 横向扩展：一图看懂

```
Phase 3 主线（深度）                    Phase 4 横向扩展（广度）
━━━━━━━━━━━━━━━━━━━━━━━━━              ━━━━━━━━━━━━━━━━━━━━━━━━━
#8  Agentic AI（概念）                    🅰 多 Agent 协作
    ↓                                        #13 crewAI 基础
#9  LangChain Tools                         #14 AutoGen
    ↓                                        #15 crewAI Practical
#10 MCP（协议层，跨框架）                  
    ↓                                    🅱 协议与扩展
#11 LangGraph（含 HITL/持久化）             #16 Agent Skills
    ↓                                        #17 A2A
#12 LangGraph 长期记忆                     
                                         🅲 专项 RAG
    ↓                                        #18 LlamaIndex RAG
  真实项目 ← 关键里程碑                      #19 LlamaIndex Event-Driven
```
