# 可观测性 + Eval 选型方案对比

> **用途**:为 Agent 选可观测性平台(tracing/监控)与评估方案(eval 框架+方法)。
> **适用**:Spec-Kit `/plan`;或由 `stack-selector` skill 路由进来。
> **最后核对:2026-06**。结论分级 ✅稳定 / ⚠️快照 / ❓待验证。
> **层定位**:这是**横切层**——和编排框架、模型、检索都正交,任何 Agent 上生产前都要做。

---

## 一、何时需要这层选型

- 任何要上生产/要持续迭代的 Agent(不能只靠 print 调试)。
- prompt/模型一改就怕回归,需要可重复的 eval。
- RAG 答非所问、agent 乱调工具,需要定位是哪一步出错。

> 👉 两个独立子决策:**① 可观测平台**(看运行时发生了什么)+ **② Eval 方案**(系统化判好坏)。常配套用,但分开选。

---

## 二、子决策 1:可观测性平台

| 平台 | 形态 | 特点 | 适合 |
|---|---|---|---|
| **LangSmith** ⭐ | 付费 SaaS | LangChain/LangGraph 原生,trace+dataset+eval+监控一体 | 用 LangChain 系、要省心 |
| **Langfuse** ⭐ | 开源(可自托管) | LangSmith 的 OSS 替代,功能全 | 要自托管/控成本/不锁定 |
| **Arize Phoenix** ⭐ | 开源 | OpenTelemetry 标准,框架中立 | 多框架、要标准化 trace |
| **Braintrust** | SaaS | eval-first,带版本控制 | 以 eval 为中心的团队 |
| **Galileo / Patronus / Honeyhive** | 企业 | 合规/护栏/企业治理 | 大企业、合规要求 |

```
用 LangChain/LangGraph → LangSmith(原生最顺)
要开源/自托管/不锁定 → Langfuse 或 Phoenix
要框架中立 + OpenTelemetry → Phoenix
以 eval 为核心 → Braintrust
企业合规 → Galileo / Patronus / Honeyhive
```

## 三、子决策 2:Eval 框架/库

| 库 | 风格 | 强项 | 适合 |
|---|---|---|---|
| **Ragas** ⭐ | RAG 专用 | faithfulness/answer relevance/context precision | RAG 系统(标准选择) |
| **DeepEval** ⭐ | pytest 式 | G-Eval rubric,接 CI 顺 | 想把 eval 当单元测试跑 |
| **pydantic-evals** | 类型安全 | PydanticAI 原生 | 用 Pydantic AI 栈 |
| **OpenAI Evals** | rubric | 基础 A-E 评分 | OpenAI 生态、轻量 |
| **Inspect AI** | agent+安全 | 英国 AISI,能力+安全评测 | agent 能力/安全评测 |
| **Promptfoo** | YAML/CLI | prompt 对比 | 快速横比多 prompt/模型 |
| **TruLens** | feedback functions | RAG Triad 实现 | 反馈函数式评估 |

---

## 四、Eval 方法论(课程 21/24)

### 两种 eval 类型 + 两种节奏
| 类型 | 怎么判 | 速度/成本 | 节奏 |
|---|---|---|---|
| **Rule-based** | 正则/字符串/schema 校验 | 快、便宜 | **每次 commit**(CI gate) |
| **Model-graded(LLM-as-Judge)** | 另一个 LLM 评质量 | 慢、贵 | **发布前**(pre-release) |

### 4 层评估(从小到大)
1. **Component**:单次 LLM 调用/工具(准确率、JSON 合法性)
2. **Retrieval**:recall@k、faithfulness(RAG,见 `retrieval-stack-selection.md` 的 RAG Triad)
3. **Trajectory**:agent 步骤是否正确、路径是否最优、工具选对没——**agent 特有,组件级测不出**
4. **Task**:端到端目标完成率、满意度、成本/延迟

### LLM-as-Judge 要点
- **评委用更强的模型**(强评弱);**pairwise 对比比绝对打分更可靠**;带 CoT reasons 便于 debug。
- **offline + online 双轨**:dev 集做 CI gate,生产抽样做线上监控。
- eval 数据集**当代码管**(版本化),每次 prompt 变更跑回归;关键路径人工抽检(LLM eval 与人约 70-85% 一致)。

---

## 五、组合决策树

```
可观测:用 LangChain 系→LangSmith;要 OSS→Langfuse/Phoenix;企业合规→Galileo 类
Eval 库:RAG→Ragas;想进 CI→DeepEval;PydanticAI→pydantic-evals;agent 轨迹→Inspect/trajectory eval
Eval 节奏:每 commit 跑 rule-based;发布前跑 model-graded
Agent 系统:别只测最终输出,必须加 trajectory 级(路由/工具/路径)
```

---

## 六、场景推荐

| 场景 | 可观测 | Eval |
|---|---|---|
| LangGraph 生产 agent | LangSmith | DeepEval(CI)+ trajectory eval(发布前) |
| 开源/自托管栈 | Langfuse 或 Phoenix | Ragas(RAG)/ DeepEval |
| RAG 系统 | Phoenix/Langfuse | Ragas + RAG Triad |
| PydanticAI 栈 | Phoenix(OTel) | pydantic-evals |
| 快速横比 prompt/模型 | — | Promptfoo |

---

## 七、接入 Spec-Kit(可复制 prompt 块)

```
请用 roadmap/agent-selection/5-observability-eval.md 为本 Agent 选可观测平台 + eval 方案。
- 现有栈:<LangChain/LlamaIndex/PydanticAI/裸SDK…>
- 是否要自托管/OSS:<…>  是否 RAG:<…>  是否多步 agent(需轨迹评估):<…>  合规要求:<…>
请分别给:① 可观测平台 推荐+备选+理由；② eval 库+方法(类型/节奏/层级)推荐+备选+理由+代价。
```

---

## 八、课程回溯 + 相关资产

- 回溯:`courses/21-Evaluating AI Agents/notes/`、`courses/24-Automated Testing for LLMOps/notes/{L03-规则评估, L04-模型评分评估, L05-综合测试与幻觉检测}.md`、`courses/05`(RAG Triad)、`courses/eval/agent-eval-landscape.md`。
- 相关层:`roadmap/agent-selection/3-retrieval.md`(RAG Triad)、`roadmap/agent-selection/2-framework/`(评分卡里 D5/D6 即观测/eval 维度)。
- 总览:`roadmap/agent-selection/README.md`。沉淀:`skills/adr-writer`。
