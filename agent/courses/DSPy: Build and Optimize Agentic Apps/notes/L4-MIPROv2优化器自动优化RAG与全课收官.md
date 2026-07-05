# L4 · 用 DSPy Optimizer（MIPROv2）自动优化 Agentic RAG + 全课收官

> 课程：DSPy: Build and Optimize Agentic Apps（DeepLearning.AI × Databricks）
> 本课任务：用 **MIPROv2 optimizer** 自动优化一个以 Wikipedia 为数据源的 agentic RAG——只提供 metric 函数和小数据集，不改一行 prompt，评估分从 **31 → 54**；并用 MLflow 追踪整个优化过程。（含课程 Conclusion）

## 0. 本课目标与路线

L3 用 tracing 解决了"看见问题"；本课解决"自动改进"。路线：**① GenAI 优化的三种含义 → ② optimizer 使用范式（metric + 数据集）→ ③ MIPROv2 内部机制 → ④ 实战：优化 Wikipedia agentic RAG → ⑤ MLflow 追踪优化过程**。

## 1. GenAI 应用的"优化"指什么

三件事，DSPy 全部支持：

| 优化对象 | 归类 |
|---|---|
| 优化 prompt template（instruction） | prompt optimization / prompt engineering |
| 构建高质量 few-shot examples | prompt optimization / prompt engineering |
| 微调 LM 权重（fine-tuning） | weight optimization |

本课聚焦前两者（prompt 侧），用 MIPROv2 演示；fine-tuning 及其他 optimizer 见 dspy.ai 文档与 tutorials。

## 2. Optimizer 使用范式：让它知道"什么是好程序"

使用步骤：

1. **挑 optimizer**（选型指南见 dspy.ai 文档；MIPROv2 擅长 prompt template 优化 + few-shot 构建）；
2. 提供**用户定义的 metric 函数** + **训练/验证数据集**。

核心思想：**optimizer 必须能区分好程序和坏程序**——metric 定义"好"，数据集提供样本。与传统 ML 不同，**数据集可以小到 20 条**；不给 valset 时 optimizer 会自动从数据里切一部分做验证。

> **架构师视角**：`metric + 小数据集` 本质上是把"质量"从一种口头感觉变成**可执行的定义**——这正是课程 21 讲的 eval 驱动开发，只是 DSPy 更进一步：**同一个 metric 既是验收标准又是优化目标**，eval 循环被内嵌进了"编译"过程。反过来的约束也很清楚：写不出 metric 的任务（开放式创作、主观语气）就吃不到 optimizer 的红利——这是判断"要不要上 DSPy"的第一道门。

## 3. MIPROv2 内部机制

高层流程：

```
trainset ──① bootstrapping──▶ few-shot examples 候选集 ─┐
                                                        ├─ ③ 组合采样 → 候选程序
程序代码+描述+few-shot+tips ──② Proposer(LLM)──▶ instruction 候选集 ─┘        │
                                                                            ▼
              持续保留最高分候选 ◀── ④ 在 valset 上评估：metric 对比 golden label，取平均分
              （循环 N 个 trials，N 由用户指定）
```

**① Bootstrapping 生成 few-shot 候选**：从 trainset 取数据喂给 DSPy 程序（单模块或多模块）跑一遍；若 metric 得分超过用户设定的阈值，就**裁剪该次 trace**（每个 module 的输入输出）作为该 module 的 few-shot example 候选。因为调用带非零 temperature 的随机性，**一条数据可以产出多条不同 trace**。

**② Proposer 生成 instruction 候选**：把程序代码和描述、few-shot examples、再加一些任意的 tips（如"要全面"、"要简洁"）一起送进 LLM（DSPy Proposer），批量生成 instruction 候选——对类式 signature 来说，instruction 就是那个 docstring。

**③④ 组合采样与评估**：从两个候选集里各取其一组合成候选程序 → 在 valset 上跑，用 metric 对比程序输出与 golden label，平均分即程序得分。关键：**既不做 grid search 也不穷举所有组合**，而是用统计方法（贝叶斯式采样）**智能地朝最优组合方向采样**。

实验表明 MIPROv2 在多个任务上大幅超过原始 prompt；细节见论文 *Optimizing Instructions and Demonstrations for Multi-stage Language Model Programs*。

> **对比课程 12 LangMem 的 prompt optimizer**：两者都"让 LLM 改 prompt"，但机制两个世界——LangMem 是**运行期在线**优化：从对话反馈里总结教训、增量改写单条 system prompt，没有系统性打分；MIPROv2 是**编译期离线**搜索：候选集 × 统计采样 × valset 评分，多模块联合优化，产物可版本化、可回归测试。前者适合"随用户反馈缓慢进化"的长活 agent，后者适合"上线前把质量分推到最高"的 pipeline。谁更工程化一目了然：MIPROv2 的每一步都有 metric 兜底，LangMem 的改写质量只能靠人抽查。

## 4. 实战：优化 Wikipedia Agentic RAG

**Agentic RAG** = 让 LLM 自己决定"要不要再检索一轮"才给最终答案（区别于固定单轮检索的普通 RAG）。程序本体极简：

```python
def search_wikipedia(query: str) -> list[str]:
    # ColBERTv2 公共检索接口（Wikipedia 2017 abstracts），取 top-3 文本 chunk
    results = dspy.ColBERTv2(url="http://20.102.90.50:2017/wiki17_abstracts")(query, k=3)
    return [x["text"] for x in results]

react = dspy.ReAct("question -> answer", tools=[search_wikipedia])
#                  ↑ 字符串式 signature：只有 question/answer，无任何 instruction
```

数据集是 **HotPotQA 子集**（基于 Wikipedia 的多跳问答），每条只有 question + answer：

```python
trainset.append(dspy.Example(**json.loads(line)).with_inputs("question"))
# with_inputs 声明哪个字段是输入，其余字段（answer）即 golden label
```

创建 optimizer 并"编译"：

```python
tp = dspy.MIPROv2(
    metric=dspy.evaluate.answer_exact_match,  # metric：答案精确匹配（本任务答案短，适用）
    auto="light",                             # 推荐用 auto 档位：light / medium / heavy，已调好
    num_threads=16,
)

optimized_react = tp.compile(                 # 优化 = compile：送入程序 + 两个数据集
    react, trainset=trainset, valset=valset,
    requires_permission_to_run=False,
)
# 注：优化很耗时，lab 预录了 LLM 调用缓存（dspy.cache.load_memory_cache）；生产直接真调
```

优化日志里可见：不断生成候选程序 → 评估 → 最终挑出最高分的程序。**优化前后对比**：

```python
optimized_react.react.signature  # 原本无 instruction 的 react 子模块，被填充了一段非常详尽的指令
optimized_react.react.demos      # 且内置了一组 few-shot examples（demos 属性里的列表）
```

## 5. 评估：31 → 54

```python
evaluator = dspy.Evaluate(
    metric=dspy.evaluate.answer_exact_match,  # 与优化时同一个 metric
    devset=valset,
    display_table=True, display_progress=True, num_threads=24,
)
evaluator(react)            # 原始程序：31 分
evaluator(optimized_react)  # 优化后：54 分
```

**没有任何人工介入**，只是套上 optimizer，分数从 31 提到 54——这就是 DSPy optimizer 的威力。

## 6. 用 MLflow 追踪优化过程

比 L3 多开三个 flag，优化过程本身也被记录：

```python
mlflow.dspy.autolog(
    log_evals=True,                  # 记录评估运行
    log_compiles=True,               # 记录 compile（优化）过程
    log_traces_from_compile=True,    # 记录优化期间每个候选程序的 trace
)
```

MLflow UI 里：优化 run 显示为一个父 run，**每个 child run 对应一次候选程序的评估**，点进去能看到该候选的 instruction、few-shot examples 等 attributes 和评估分——整个搜索过程全程留痕、可复盘。

## 7. 全课收官

### 7.1 Conclusion 要点

- DSPy 是**轻量、灵活的 GenAI authoring 框架**：简化与 LLM 的交互和 agent 开发；
- 通过 **DSPy optimizer 提供自动程序优化**；**原生集成 MLflow tracing** 方便开发调试；
- 核心用法回顾：`dspy.Signature` 定义输入输出契约，`dspy.Module` 包装自定义逻辑；准备**小数据集 + metric 函数**即可用 optimizer 提升程序质量；`mlflow.dspy.autolog()` 一行接入 tracing。

### 7.2 L1-L4 全课回顾

| 课 | 一句话 |
|---|---|
| L1 | DSPy 定位：写"AI 程序"而非写 prompt——轻量 GenAI authoring 框架，prompt 成为可自动优化的中间产物 |
| L2 | 两大抽象落地：signature（输入输出契约）+ module（LLM 交互逻辑），内置模块做情感分析、自定义 agent 做"猜名人"游戏 |
| L3 | `mlflow.dspy.autolog()` 一行接入 tracing，逐层看清 ReAct 航司客服 agent 的多跳调用（module/adapter/LM/tool 四层） |
| L4 | MIPROv2：metric + 几十条数据，自动搜索 instruction 与 few-shot 组合，RAG 从 31 → 54 分 |

> **架构师的裁决**：什么时候用 DSPy 这类"编程化 + 自动优化 prompt"的框架？三个条件同时满足才值得：**① 任务有可写的 metric**（答案可判对错/可打分），**② 有几十条以上带 golden label 的数据**，**③ pipeline 是多模块的且会随模型/需求持续迭代**（每次换底座模型重新 compile 即可，prompt 不用手工重调——这是 DSPy 最锋利的卖点）。反之，单条 prompt、任务主观、无数据可标，手工 prompt + 少量人评就是正解，引入 DSPy 只会白付抽象成本。与 LangMem prompt optimizer 的分工：LangMem 解决"上线后随用户反馈**在线**微调人格与偏好"，DSPy 解决"上线前把可度量任务的质量**离线**压榨到位"——两者不互斥，一个管运行期、一个管编译期。

## 8. 本课总结

| 要点 | 一句话 |
|---|---|
| 优化三含义 | prompt template、few-shot examples（合称 prompt optimization）、fine-tune 权重，DSPy 全支持 |
| 使用范式 | 挑 optimizer + metric 函数 + 小数据集（20 条起），让 optimizer 知道什么是"好程序" |
| Bootstrapping | trainset 跑程序，metric 超阈值就裁 trace 当 few-shot 候选；非零 temperature 让一条数据出多条 trace |
| Proposer | 程序代码+描述+few-shot+tips 喂给 LLM，批量生成 instruction 候选 |
| 智能搜索 | 不 grid search 不穷举，统计采样朝最优 instruction × few-shot 组合逼近，valset 均分定胜负 |
| 实测效果 | Wikipedia agentic RAG（HotPotQA），零人工干预 31 → 54 |
| 优化可观测 | autolog 加三个 flag，每个候选程序的评估在 MLflow 里一个 child run，全程留痕 |

## 与我的资产映射

- Eval 层：`agent/skills/agent-selection/5-observability-eval.md`（metric+数据集驱动的优化 = eval 驱动开发的"自动化终态"；MLflow 补充进 eval 框架/后端两格）
- 框架层：`agent/skills/agent-selection/2-framework`（DSPy 作为"编程化 prompt + 编译期优化"路线的代表，选型条件即上面裁决块的三条）
- 记忆层：课程 12 LangMem prompt optimizer（运行期在线优化）与 MIPROv2（编译期离线优化）的对照，可补入 `6-memory.md` 相关小节
- 课程 21 Evaluating AI Agents：experiment/judge 方法论与本课 metric/Evaluate 相互印证
- [[project_selection_matrix]]
