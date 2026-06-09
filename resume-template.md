# AI Agent 工程师 / 架构师 简历模板

> 使用说明
> - `[方括号]` 是占位符，按你的真实情况替换
> - `<!-- ... -->` 是写作指导，最终交付时删除
> - 目标长度：**1 页**（最多 1.5 页）。砍掉不能体现 AI Agent 能力的内容。
> - 顺序原则：HR 看 30 秒就要看到你最强的点 → 项目经验放靠前

---

# [姓名]

[手机] · [邮箱] · GitHub: [github.com/Colonel86] · 博客: [可选]

[城市] · [N] 年工作经验

---

## 求职意向

**AI Agent 开发工程师 / AI 应用架构师**

<!-- 一行话定位。不要写"AI 工程师 / 后端开发 / 架构师"这种发散的多目标——投不同岗位就改这一行。 -->

---

## 核心技能

**Agent 编排框架** · LangGraph（主，状态机/HITL/持久化）· crewAI（多角色协作）· LlamaIndex Workflows（事件驱动）

**RAG 技术栈** · LlamaIndex（Agentic RAG）· Haystack（Pipeline 架构）· Chroma 高级检索（query expansion / reranking）· RAGAS 评估

**协议与扩展** · MCP（Model Context Protocol，含自建 server）· Agent Skills（自研 3 个 Skill）· Function Calling

**长期记忆** · LangGraph Memory（语义 / 情景 / 程序记忆三分）

**LLM 工程** · OpenAI / Anthropic Claude · Pydantic 结构化输出 · Prompt 工程 · Chain-of-Thought / Reflection

**评测与生产化** · Agent 端到端 + 组件级评测 · LLMOps CI（CircleCI）· 幻觉检测 · 延迟/成本优化

**Agentic Coding 工作流** · Claude Code（Plan 模式 / Subagent / Worktree / Hooks）· Spec-Driven Development

**通用工程** · Python · TypeScript · [你原本会的：Java / Go / SQL / Docker / K8s 等]

<!--
反面教材：堆 30 个框架名 → HR 觉得你什么都"略懂"
本模板做法：分组 + 给取舍判断的暗示词（如"主"、"自建"、"含 ...")
-->

---

## 项目经验

### 项目一 · [项目名，例：企业文档智能问答 Agent]
**个人 / 团队项目** · `2026.06 – 2026.07`
[Demo 链接] · [GitHub 链接]

**背景**：[一句话讲解决了什么真实问题。例：解决企业内部文档检索准确率低、缺少多轮上下文与引用溯源的问题。]

**技术架构**：
- **编排层**：LangGraph 状态机驱动 ReAct 循环，支持 HITL 审核中断 + 断点恢复
- **检索层**：LlamaIndex Agentic RAG，Agent 自主决定 retrieve / re-query / answer 路径
- **上下文层**：LangGraph 长期记忆，区分语义记忆（用户偏好）与情景记忆（历史会话）
- **协议层**：自研 MCP server 暴露检索能力，可被 Claude Desktop / Cursor 等外部 Agent 复用
- **评测层**：RAGAS（faithfulness / context precision）+ 自定义业务指标，CI 自动跑回归

**关键产出**：
- 检索 Hit@5 从 baseline **62% → 84%**（通过 query expansion + reranking）
- 端到端响应延迟 **P95 从 8s 降到 3.2s**（流式输出 + 检索并发）
- 单次问答 token 成本控制在 **¥0.04 以内**（Sonnet + 缓存策略）
- 引用溯源准确率 **97%**（PromptBuilder 强制带 url meta）

**架构取舍记录**：
- LangGraph vs crewAI：选 LangGraph，因为业务流程强控制、需要 HITL，crewAI 在状态恢复上较弱
- LlamaIndex vs LangChain RAG：选 LlamaIndex，文档结构与 Agentic 检索的抽象更深

<!--
关键三条铁律：
1. 必须有量化指标（哪怕是 baseline 对比、哪怕是估算值）
2. 必须有架构取舍——这是中级 vs 高级的分水岭
3. 用粗体把数字 highlight 出来，HR 扫一眼就能看到
-->

---

### 项目二 · [项目名，例：MCP 工具服务器生态] *（可选第二项目）*
**个人开源项目** · `2026.06 起持续维护`
[GitHub 链接]

**简介**：基于 MCP 协议构建的 [领域，例：知识管理 / 代码 review / 数据查询] 工具服务器集合，已接入 [Claude Code / Cursor / Zed]。

**技术亮点**：
- 实现 MCP 三大原语：Tools（执行）/ Resources（数据）/ Prompts（模板）
- 支持本地 stdio + 远程 SSE 两种部署模式
- 完整测试覆盖（pytest），CI 自动发布到 [npm / PyPI]

**社区数据**：
- GitHub Star [N] · npm 周下载 [N] · 已有 [N] 个外部贡献者
<!-- 没数据就先不写这块，等真有 star 再加 -->

---

### 项目三 · [若有：在职项目的 AI 改造，可写脱敏版] *（可选）*

<!-- 如果你当前公司允许，把工作中和 AI 相关的事写一条——价值密度更高 -->

---

## 工作经历

### [公司名] · [职位，例：高级软件工程师] · `2023.XX – 至今`

<!--
重点：把工作经历里"和 AI / 架构 / 工程方法"沾边的事抠出来，往 AI Agent 方向靠
即使原岗位不是 AI，也能挖出：
- "主导服务架构重构" → 体现架构能力
- "引入 X 自动化" → 体现工程方法
- "技术选型决策" → 体现取舍判断
-->

- 主导 [模块/系统] 的架构设计与重构，[量化结果，如 "QPS 提升 N 倍 / 响应延迟降低 N%"]
- [若有 AI 相关] 引入 AI 辅助 [代码 review / 文档生成 / 日志分析]，团队效率提升 [N%]
- 推动团队采用 [工程实践，例：Spec-Driven Development / Code Review 标准化]
- 担任 [N] 人小组技术 lead，负责技术方案评审与 mentorship

### [上一家公司] · [职位] · `YYYY.XX – YYYY.XX`

<!-- 越往前越简——只列最有代表性的 1-2 条 -->

---

## 技术输出

<!-- 这一段是体现"持续学习 + 公开影响力"的关键，比"完成了 20 门课"管用 10 倍 -->

- **开源**：[github.com/Colonel86] · 维护 [N] 个 AI Agent 相关项目，累计 Star [N]
- **自研 Skill**：开源 3 个 Agent Skill（`adr-writer` 架构决策记录 · `pydantic-ai-agent` AI 应用脚手架 · `study-session` 学习辅助），地址 [...]
- **技术文章**：在 [知乎 / 公众号 / 个人博客] 发表 AI Agent 架构系列 [N] 篇，代表作：
  - 《LangGraph vs crewAI vs LlamaIndex Workflows：三种 Agent 编排范式的实战取舍》
  - 《从 MCP 到 CLI + Skill：2026 Agent 工具协议的演化判断》
  - 《Spec-Driven Development 在遗留代码上的落地实践》
  <!-- 如果还没写，先把 GitHub repo 链接挂上，"持续输出中"也比"看了 20 门课"强 -->
- **系统化学习**：完整学习 DeepLearning.AI AI Agent 路线 20+ 门（Andrew Ng Agentic AI · Anthropic MCP · LangGraph · LlamaIndex 等），技术笔记 200+ 篇开源于 [GitHub repo 链接]

---

## 教育背景

[最高学历，学校 · 专业 · 学位] · `YYYY – YYYY`

<!-- 应届放最上面，工作多年的放最后 -->

---

# 简历定制速查表

> 投不同岗位前，对照这张表调整：

| 岗位类型 | 重点突出 | 弱化/砍掉 |
|---|---|---|
| **AI Agent 工程师**（中级） | 框架熟练度、能跑通项目、code 质量 | 架构取舍可少写、不必强调 MCP 协议级 |
| **AI 应用架构师** | 取舍判断、协议层（MCP）、跨框架对比、技术文章 | 单一框架的 API 细节砍掉 |
| **创业/小公司 AI Lead** | 端到端交付、量化效果、成本控制 | 砍掉理论描述，全部换成业绩 |
| **大厂 AI 平台/基础设施** | 工程化（CI/CD、评测、监控）、MCP server、Skill 复用 | 砍掉业务向 demo 描述 |

---

# 投递前 checklist

- [ ] 简历 1-1.5 页，**没有任何"参加了 / 学习了"这种弱动词**
- [ ] 每个项目至少 **2 个量化指标**
- [ ] 至少 **1 个 GitHub 项目链接** + **1 个 Demo 链接**
- [ ] 技能 section 没有堆 30 个名词，分组 + 标注主次
- [ ] 用 Adobe / 网页转 PDF 时检查中英文标点、链接可点击
- [ ] 文件名：`[姓名]-AI Agent工程师-[N]年.pdf`
- [ ] 求职意向那一行**和投递岗位 JD 标题一致**

---

# 你目前的关键缺口（按优先级）

1. **🔴 没有可演示的项目** — 模板里的"项目一"占整张简历 40% 篇幅，必须先建一个。建议 4-6 周做出企业知识库 Agent 或自动化调研 Agent。
2. **🟡 GitHub repo 公开露出** — 把 205 篇笔记 + 3 个 Skill 先开源，今天就能做。
3. **🟡 技术文章** — 3 篇硬文足够支撑"持续输出"标签，每篇 2000 字、周末 1 天能写一篇。
4. **🟢 工作经历里的 AI 含量** — 如果当前岗位允许，找一个小切入点（如内部 Bug 分析用 Claude Code、文档生成自动化）做出来写进简历。
