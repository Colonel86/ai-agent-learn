# AI Agent Eval：业界方法与好用的库

> 整理日期：2026-05-27
> 视角：AI Agent 架构师
> 关联课程：Course 2 EP09/EP10、Course 5 (Building and Evaluating Advanced RAG)、Course 21 (Evaluating AI Agents)

---

业界目前没有"一统天下"的方案，比较成熟的是按**评估对象**分层选工具。

## 一、评估的 4 个层次（先想清楚要评什么）

| 层次 | 评估对象 | 典型指标 |
|---|---|---|
| **组件级** | 单个 LLM 调用 / 单个工具 | 准确率、JSON 合法性、引用一致性 |
| **RAG 检索** | 检索质量 + 生成忠实度 | recall@k、faithfulness、answer relevance |
| **轨迹级（Trajectory）** | Agent 走的步骤是否合理 | 工具选择正确率、步数、是否绕路 |
| **任务级（End-to-end）** | 用户目标是否达成 | 任务成功率、用户满意度、成本/延迟 |

> 很多团队踩的坑：只做组件级评估，结果上线后整体表现差——**轨迹级 + 任务级**才是 Agent 区别于普通 LLM 应用的关键。

---

## 二、主流库 / 平台分类

### 1. 一站式平台（追踪 + 数据集 + 评估 + 监控）
- **LangSmith**：LangChain 生态，trace 体验最好，付费；和 LangGraph 无缝衔接
- **Langfuse**：开源自托管 LangSmith 替代品，国内团队用得多
- **Arize Phoenix**：开源，OpenTelemetry 标准，跨框架兼容性最好
- **Braintrust**：eval-first 设计，数据集版本控制做得好，适合"把评估当 CI 跑"
- **商业**：Galileo、Patronus AI、Honeyhive——更偏企业合规

### 2. 评估指标库（嵌入到代码里跑）
- **Ragas**：RAG 评估事实标准，faithfulness / answer relevance / context precision
- **DeepEval**：pytest 风格，G-Eval（用 LLM 按 rubric 打分）实现得不错
- **pydantic-evals**：PydanticAI 团队出品，类型安全、轻量，适合 Pydantic 栈
- **OpenAI Evals**：祖宗级框架，A~E rubric 来源；现在更多作参考

### 3. Agent 专项 / 安全评估
- **Inspect AI**（UK AISI）：英国 AI 安全研究所开源，agent 能力 + 安全评测的事实标准
- **AgentBench / τ-bench / SWE-bench / WebArena**：公开 benchmark，对自研 Agent 做能力定位时用

### 4. Prompt 对比 / 回归
- **Promptfoo**：YAML 配置、CLI 友好，适合"换模型/换 prompt 看效果"
- **TruLens**：feedback function 思路，已经有点边缘化

---

## 三、目前业界的几个最佳实践

1. **LLM-as-Judge 是默认方案**，但要做两件事：① 用更强的模型当裁判（GPT-4 级评 GPT-3.5 输出）；② 用 pairwise 比较而不是绝对打分，置信度更高。
2. **离线 + 在线双轨**：离线跑 dev set 做 CI 门禁，在线对真实流量采样跑 eval（Langfuse / Phoenix 都支持）。
3. **数据集版本化**：把 dev set 当代码管，每次 prompt 变更都跑回归——Braintrust / LangSmith 都把这点做成了一等公民。
4. **轨迹评估**用 LLM 裁判看完整 trace，问"这条路径是否最优"，比单纯看终态更有信息量。
5. **人类标注还是不可省**：纯 LLM 评估在主观任务上和人类一致性约 70-85%，关键场景要有人类抽检。

---

## 四、个人学习路线建议（对应 24 周路线图）

1. **现在（Course 2 EP09/10 阶段）**：先用 pydantic-evals 或 DeepEval 把"代码里写 eval"的肌肉记忆建立起来
2. **进 LangGraph 课时（Course 11）**：直接接 LangSmith 或 Langfuse，体验"trace → 标注 → 数据集 → 回归"完整闭环
3. **做 RAG 项目时（Course 5 / 6）**：必上 Ragas，它的几个指标几乎是 RAG 圈的通用语
4. **进阶（Course 21 Evaluating AI Agents）**：读 Inspect AI 的设计，它对"agent capability eval"的抽象比商业平台更清晰

---

## 五、速查：选型决策树

```
要评什么？
├── 单条 prompt 改了想看回归  → Promptfoo / Braintrust
├── RAG 系统                  → Ragas + Langfuse trace
├── LangGraph Agent           → LangSmith（首选）/ Langfuse
├── 跨框架 / 想自托管         → Phoenix + OpenTelemetry
├── Pydantic 栈轻量需求       → pydantic-evals
├── Agent 能力 benchmark      → Inspect AI + 公开 bench
└── 企业合规 / SLA            → Galileo / Patronus
```
