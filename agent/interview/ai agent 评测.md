# AI Agent 评测 · 面试口述整理
### 主题:如何测试 AI Agent 回答精准度

---

## 怎么用这份文档

这是一条完整的面试 **drill-down**:`Q0` 是开场题,后面 `Q1→Q9` 是面试官几乎一定会顺着挖的追问,顺序就是真实面试的推进节奏。

- 引用块 `>` 里是**脱稿口述版**,练到能用自己的话讲出来。
- `要点` 是讲的时候要点到的关键词 / 强 senior 信号。
- 时间不够就只背 Q0 的电梯版 + 文末「一页速记」,够撑住开场和大部分追问。

---

## Q0(开场)· 如何测试 AI Agent 回答精准度?

**核心 reframe:精准度不是一个数。** 它是多维的、要测过程不只测结果、而且非确定性。

> 「测 Agent 精准度和测分类器完全不同,因为输出是开放式生成、是多步带工具调用的、而且非确定性——同样输入跑两次结果可能不一样。所以我会先把精准度拆成三层:最终答案质量、执行轨迹、检索质量;作为 Agent,我不只测最终答案,还要测它走的路。测的时候能用确定性断言的优先断言,主观维度才上 LLM-as-judge,但 judge 必须先用人工标注校准;评测集分层、混真实日志和对抗样本、严防污染;最后做成 CI 回归门禁加线上采样,失败回流形成飞轮。因为非确定性,所有指标我都跑多次看均值和方差。」

`要点`:三层 / 测 trajectory 不只 final answer / judge 要校准 / CI 门禁 + 线上 + 飞轮 / 跑多次看方差。

**三层分解(精准度 = 三个可测量的层面):**

| 层面 | 测什么 | 为什么 |
|---|---|---|
| 最终答案质量 | 正确性、忠实度/无幻觉、相关性、完整性、格式 | 它本身就多维,"正确但不忠实"(蒙对却编出处)要分开测 |
| **执行轨迹** | 工具选对没、参数对没、步数/冗余、路径对没 | **Agent 特有考点**——答案对但用错工具/绕路也是缺陷 |
| 检索质量(RAG) | 上下文精确率、召回率、利用率 | 答案差是"没召回到"还是"召回了没用好",归因不同、修法不同 |

> 主动说「我会测 trajectory 而不只是 final answer」「检索质量和生成质量要分开测」——立刻显出做过 Agent 而非只调过 API。

---

## Q1 · 具体每一层怎么测?(四种方法,从便宜到贵)

> 「我有一个优先级:能用确定性断言的绝不动用 LLM。第一档是 programmatic 断言——JSON schema、正则、关键字段精确匹配、工具调用序列对比期望、数值区间,又快又稳又免费,适合格式、结构化输出、工具调用。第二档是参考答案对比,有 golden answer 时用语义等价判断,别用 exact match 或 BLEU 这种字面指标。第三档是 LLM-as-judge,按 rubric 打分,测忠实度、相关性这些主观维度的主力,但它有偏差、必须校准。第四档是人工评估,不规模化,用来校准 judge、定基线、抓系统性问题。先把能断言的都断言掉,剩下的才交给贵的方法——这是成本意识。」

`要点`:断言优先 / 开放式别用字面指标 / judge 是主力但要校准 / 人工用来校准而非规模化。

---

## Q2 · 评测集怎么来?(真正的瓶颈)

> 「模型和指标都好搞,评测集质量决定一切。我用三个来源混合:生产日志采样保证测试分布等于线上分布,这是最有价值的;合成生成补覆盖率;对抗和边界样本——故意造难的、模糊的、易触发幻觉的,这些才能暴露问题。然后按能力维度和难度分层分桶,这样能看到在哪类问题上掉链子,而不是只有一个笼统总分。两条纪律:防污染,评测集绝不能进 prompt 的 few-shot 例子或微调数据,否则刷分自欺;保持新鲜,线上分布会漂,要持续从新日志补。」

`要点`:日志+合成+对抗 / 分层分桶 / 防污染 / 保持新鲜。

---

## Q3 · 上线后怎么持续保证?(FDE 最看重)

> 「我把评测当成系统而不是跑一次。Eval-driven development——把 eval 当单元测试写,改 prompt、换模型前先有评测集兜底;CI 回归门禁,每次变更自动跑、指标跌破阈值就拦合并。非确定性我同一条 case 跑 N 次,报均值和方差、看 pass@k,一个平均分高但方差大的 Agent 是不可靠的。离线在 golden set 上跑回归,在线对生产流量采样、用 judge 实时评、收用户显式反馈(赞踩)和隐式信号(重问、人工接管)。线上发现的失败 case 回流进评测集形成数据飞轮。评测集、prompt、模型版本全部版本化保证可复现。」

`要点`:eval 当测试 / CI 门禁 / 跑多次看方差 pass@k / 离线+在线 / 失败回流飞轮 / 版本化。

---

## Q4 · 你用 LLM-as-judge,凭什么信它?

**核心心法(说出来就赢):judge 是一台测量仪器,我在用"人类判断"这把基准尺去验证并对齐它。我优化的不是 judge 的分数,而是它和人类判断的一致性;而且这个一致性的天花板是人和人之间本身的一致性,不是 100%。**

> 「judge 本身是把没校准过的尺子,有已知偏差:位置偏差偏好排前面的、啰嗦偏差偏好更长的、自我偏好偏袒自家风格、还普遍手软。所以我不会盲信,会把它当一个待验证的分类器:先建人工标注金集,验证 judge 和人类的一致性达到可接受水平,再让它上岗。对策上 pairwise 比 pointwise 稳、rubric 要可操作、关键场景换不同模型当 judge,最重要是用人工标注校准。」

`要点`:judge=仪器、人=基准尺 / 目标是 judge-human 一致率追平 human-human / 已知偏差要逐个量化缓解。

---

## Q5 · 怎么验证 judge 靠不靠谱?(五步)

> 「第一步,建人工金集,每条让多名标注员独立打,先算人际一致性——它定义了 judge 能达到的上限。如果人和人只有 75% 一致,就别指望 judge 95%,那是任务定义模糊、该先修 rubric。第二步,用对的指标:别用裸准确率,标签不平衡时一个全打 pass 的废 judge 准确率也很高;二元/类别用 Cohen's κ,多人用 Fleiss' κ,打分用 weighted κ 或 Spearman/Kendall。第三步,专门探测偏差:位置偏差就把 A/B 对调再判、统计翻转率;长度偏差在'人判等价'的样本上看是否偏好更长的;还要看区分度——能不能真把好坏分开,可以算 judge 分对人类标签的 AUC,因为'一致率高'和'有区分度'是两回事。第四步,混淆分析,把 judge≠人 的样本分桶找固定 pattern,直接指导 rubric 怎么改。第五步,改 rubric 留 held-out 别过拟合,上线后定期重标复验,因为 judge 和数据都会漂。」

`要点`:多人金集→人际一致性=上限 / κ 而非准确率 / 量化位置&长度偏差&区分度 / 混淆分桶 / held-out + 定期重标。

**判读标准:judge-human 一致率 ≈ human-human 一致率,就够了——目标是"和人一样不完美",不是完美。**

---

## Q6 · κ 是什么?(面试官追问统计细节时)

**κ = Cohen's kappa,扣掉"瞎蒙也会蒙对"那部分之后,剩下的真实一致 —— chance-corrected agreement。**

> 「直接用一致率会被骗。举个真实例子:judge 和人各打 100 条 pass/fail,大部分都 pass。裸一致率 85% 看着很好,但既然双方都倾向打 pass,他们纯靠运气也会经常同时打 pass——算出来这个'巧合一致'有 78%。所以 85% 里真有信号的没多少。κ 就是把实际一致减掉巧合一致再归一化。」

公式与那个例子(我跑过验证):

```
κ = (Po − Pe) / (1 − Pe)
  Po = 实际一致率 = 0.85
  Pe = 巧合一致率 = 0.85×0.90 + 0.15×0.10 = 0.78
κ = (0.85 − 0.78) / (1 − 0.78) = 0.07 / 0.22 ≈ 0.318
```

→ **裸一致率 85%,κ 只有 0.32**,一下打回"一般"。这就是为什么不平衡时只能看 κ。

怎么读 / 区别:
- κ=1 完美;κ=0 等于瞎蒙;κ<0 比瞎蒙还差(系统性对着干)。
- 档位:0.2–0.4 一般 / 0.4–0.6 中等 / **0.6–0.8 substantial(可接受)** / 0.8+ 接近完美。judge 校准一般要 **κ>0.6**。
- **Cohen's κ** = 正好两个标注者;**Fleiss' κ** = 三个及以上(算人际上限用它)。
- 打分(1–5)别用普通 κ,因为它把类别当无序——"判1 vs 判2"和"判1 vs 判5"罚得一样重。要用 **weighted κ**(按差距加权)或排序相关。

---

## Q7 · rubric 怎么写?

> 「六条原则。一,分解,别问'整体好不好',拆成可独立判定的维度——忠实度、相关性、完整性,一维一判。二,尽量二元或低基数,二元 pass/fail 远比 1–10 稳;非要打分就小刻度并给每档锚定定义,写清 3 分和 4 分的区别,锚定才让分数可复现。三,把 rubric 当'给人的标注指南'写——具体、可操作、带边界规则,然后同一份指南既发给人类标注员、也发给 judge,这个双用设计让两者天然对齐。四,先推理后结构化裁决,让它先列证据再输出 JSON。五,关键场景给一个临界 pass、一个临界 fail 的边界 few-shot。六,有 golden 就 reference-guided、测忠实度就把检索上下文喂给它去比对,比凭空判断可靠得多。」

`要点`:分解 / 二元锚定 / rubric=人和 judge 共用的标注指南 / 先推理后 JSON / 边界 few-shot / reference-guided。

---

## Q8 · 比较两个模型 / prompt 用什么?(pairwise)

> 「绝对打分会漂、会全挤在 3–4 分,人和模型对'相对比较'都远比'绝对打分'可靠,所以选型我用 pairwise。最关键一条纪律:双向跑消位置偏差——同一对永远跑 (A,B) 和 (B,A) 两遍,只有两个顺序结论一致才算一方赢,翻转就判 tie。要允许 tie,对势均力敌强行二选一是在注入噪声。聚合上,两个系统直接看 win rate;N 个系统 round-robin 两两比、用 Elo 或 Bradley-Terry 聚合成全局分,这就是 Chatbot Arena 的做法;想要跨时间稳定的绝对指标就 reference-anchored,每个候选都和一个固定参考比、看对参考的胜率。分工上 CI 门禁用 pointwise 二元卡绝对阈值,选型用 pairwise 比谁更好。最后统计上要严谨:win rate 比小差异别过度解读,要有足够样本量、看 bootstrap 置信区间;同时比很多 variant 还有多重检验问题,不控制就会把噪声当成'找到更好的 prompt 了'。」

`要点`:pairwise>pointwise / **双向跑消位置偏差** / 允许 tie / Elo/Bradley-Terry 聚合 / reference-anchored 做监控 / 门禁 pointwise·选型 pairwise / 置信区间 + 多重检验。

---

## Q9 · 代码里 κ 怎么算?

三个库函数,这几行基本够用(都已实测可跑):

```python
from sklearn.metrics import cohen_kappa_score           # κ 主力
from statsmodels.stats.inter_rater import fleiss_kappa   # 多人上限
from scipy.stats import spearmanr                        # 打分排序相关

k = cohen_kappa_score(human, judge, labels=["pass","fail"])      # 二元/类别
k = cohen_kappa_score(human, judge, weights="quadratic")          # 1–5 分必须加
```

四个真正绊人的坑:

1. **数据按题对齐 + 显式传 `labels=`**:两数组同 index 一一对应;显式给 labels 既定 weighted κ 的"顺序",又避免某类缺失时乱序/报错。
2. **打分不加 `weights="quadratic"` 是错的**:实测同一份数据,普通 κ=0.367、weighted κ=0.855,差距巨大——普通 κ 把"差1档"和"差4档"当成一样的错。
3. **Fleiss 数据格式坑**:`fleiss_kappa` 要的是"每题×每类别的票数表",中间必须过 `aggregate_raters` 转换,直接喂标签会报错。
4. **judge-κ 贴着 human ceiling 读,>100% 是红灯**:达成率远超 100% 不代表 judge 超神,而是人类标注分歧太大、金标准本身不可靠,该回去修 rubric。

接流程:离线在金集上跑;CI 设门槛(如 judge-κ≥0.6 且达成率落在合理区间才允许 judge 上岗);分布漂了重标复验。本质是"先验尺子,再用尺子量"。

---

## 一页速记

**四条主线(任何追问往这四条回扣):**
1. **测什么** → 最终答案 / 执行轨迹 / 检索质量;测过程不只测结果。
2. **怎么测** → 断言优先,主观才上 LLM-judge,judge 必须校准,人工用来校准。
3. **评测集** → 日志+合成+对抗,分层,防污染,保持新鲜。
4. **做成系统** → CI 回归门禁 + 跑多次看方差 + 离线+线上 + 失败回流飞轮。

**judge 校准一句话总纲:** 「把 judge 当待验证的分类器——多人标注金集、用 κ 而非裸准确率衡量一致性、目标是 judge-human 追平 human-human;rubric 分解成二元锚定、人和 judge 共用;比较用双向 pairwise 消位置偏差、Elo 聚合,门禁用 pointwise,并对版本比较做置信区间和多重检验控制。」

**术语中英对照:**

| 中文 | 英文 | 一句话 |
|---|---|---|
| 机会校正一致性 | chance-corrected agreement | κ 的本质,扣掉巧合一致 |
| 科恩 / 弗莱斯 卡帕 | Cohen's / Fleiss' κ | 两人 / 多人一致性 |
| 加权卡帕 | weighted κ (quadratic) | 打分场景,按差距罚 |
| 人际一致性 | inter-annotator agreement | judge 能达到的上限 |
| 位置/啰嗦/自我偏差 | position / verbosity / self bias | judge 的已知偏差 |
| 忠实度 | faithfulness / groundedness | 有无幻觉、有无出处支撑 |
| 执行轨迹 | trajectory | Agent 特有考点 |
| 上下文精确率/召回率 | context precision / recall | RAG 检索质量(RAGAS) |
| 冠军挑战者 | champion / challenger | 新旧版本同期对照 |
| 通过率@k | pass@k | 非确定性下的一致性 |
| 数据飞轮 | data flywheel | 失败 case 回流评测集 |

**工具栈:** RAGAS(RAG 四件套)· TruLens(RAG triad)· DeepEval(pytest 断言/G-Eval)· LangSmith(数据集+评估器+trace+CI,原生 pairwise)· Phoenix/Arize(trace+线上漂移)。




# LLM 评估与可观测工具 — 面试速查

覆盖：**DeepEval、RAGAS、Phoenix、Langfuse、LangSmith**
适用场景：被问到评估 / 可观测栈如何选型、各工具区别、如何组合时的标准答案。

---

## 0. 先抛心智模型（开场就给框架，体现结构化思维）

整个评估栈有**两个正交的槽**，先把工具按槽归位，再谈区别：

- **槽 A — CI/CD 门禁框架**：离线、上线前、代码优先、在 PR 时跑、回归就 fail 掉 deploy。
  → **DeepEval / RAGAS / Promptfoo**（本质是「库」）
- **槽 B — 可观测 + 监控平台**：在线、上线后、有 UI/dashboard、抓 trace、采样打分。
  → **Phoenix / Langfuse / LangSmith**（本质是「平台」）

一句话类比：**DeepEval ≈ 单元测试，RAGAS ≈ 生产监控采样，可观测平台 ≈ trace 质量的 single source of truth。**

第二条轴是**「离线评估 vs 在线可观测」**，和上面的库/平台轴基本重合：库偏离线、平台偏在线（但平台也都含离线评估能力）。

---

## 1. 每个工具的一句话定位（用于快速口头作答）

- **RAGAS**：RAG 专用的**纯评估指标库**。2023 年开创 reference-free（无需 ground-truth 标注）评估，核心四指标 context precision / context recall / faithfulness / answer relevancy。无 UI、无 tracing，最轻。
- **DeepEval**：**pytest 原生的评估测试框架**（Confident AI）。50+ 指标，把评估当单元测试写，天然做 CI 门禁。范围比 RAGAS 广（含 agentic、multi-turn、safety）。
- **Phoenix（Arize）**：**开源可观测 + 评估平台**，OpenTelemetry / OpenInference 原生。独有杀手锏是 embedding 2D/3D 可视化看检索漂移。最易自托管（单容器）。
- **Langfuse**：**开源 LLMOps 全栈平台**（MIT，ClickHouse 旗下）。tracing + 最强的 prompt 版本治理 + eval + dataset + 实验，采用最广，为生产规模自托管设计。
- **LangSmith**：**LangChain 第一方的闭源 SaaS 平台**。对 LangChain/LangGraph 整合最深（LangGraph Studio、zero-config tracing），自托管仅 Enterprise，per-trace 计费规模化偏贵。

---

## 2. 常见追问 + 标准答案

### Q1：这几个工具是干嘛的？有什么区别和共同点？

**答**：可以分两类。RAGAS 和 DeepEval 是**评估库**，跑在开发/CI 里，吃 input/output/context 吐分数；Phoenix、Langfuse、LangSmith 是**可观测平台**，先抓生产 trace，再在其上叠加评估、看板、存储。

**共同点**：
1. 都做 LLM-as-a-Judge（解决「输出非确定、无标准答案」）；
2. 评估库（RAGAS/DeepEval）和开源平台（Phoenix/Langfuse）都可自托管；
3. **不互斥、可叠加** —— Phoenix 能把 RAGAS、DeepEval 当 evaluator 接进来；
4. 可观测平台都建在 OpenTelemetry 上（对应 span/trace/metric 三支柱）。

**结论**：实战是分层组合，不是二选一。

---

### Q2：用了 DeepEval 或 Phoenix，还需要 RAGAS 吗？

**答**：要分两种情况，因为 DeepEval 和 RAGAS 是同类（指标库），Phoenix 和 RAGAS 不是同类（平台 vs 库）。

- **DeepEval 侧**：指标高度重叠，两者都算 faithfulness / answer relevancy / context precision / recall，DeepEval 甚至有个直接叫 `RAGAS` 的复合指标，所以大多数场景可以不另装 RAGAS。**但有三个保留 RAGAS 的理由**：
  1. RAGAS 的 RAG 指标库更深（8 个，含 noise sensitivity、context utilization），每个有论文，**强监管行业需要可辩护方法论**时更稳；
  2. **关键陷阱**：DeepEval 的 `ContextualPrecision` / `ContextualRecall` 是 **reference-based**（需要 expected_output / ground-truth context）。没有 ground-truth context 时它会**静默退化成「让 LLM 猜应该检索到什么」**，结果不可靠 —— 这种情况要用 RAGAS 的 context precision。DeepEval 真正 referenceless 的只有 answer relevancy / faithfulness / contextual relevancy 这套 RAG triad。
- **Phoenix 侧**：层级错配。Phoenix 是平台，RAGAS 是指标库；Phoenix 替掉的是「另搭一个跑指标的地方」，而 Phoenix 里跑的指标既能用自带 evaluator，也能 import RAGAS。所以用了 Phoenix，RAGAS 仍可能作为它的一个 evaluator 来源存在。

---

### Q3：用了 Phoenix，还需要 DeepEval 吗？

**答**：不能简单替代，因为它俩占不同的槽。Phoenix 填的是**可观测平台槽（槽 B）**，DeepEval 填的是 **CI 门禁槽（槽 A）**。

- Phoenix 的评估是**实验/看板导向**（跑数据集、UI 里比 prompt 版本）；DeepEval 是 **pytest 单元测试导向**（`assert_test()`、回归就挡 PR）。
- Phoenix 没复刻 DeepEval 的几样东西：
  1. pytest 原生 CI 门禁惯用法；
  2. **DAG 指标**（决策树式确定性打分，避开 LLM-judge 非确定性）；
  3. 多轮对话模拟 + red teaming（DeepTeam）。
- 反过来，**用了 Phoenix 反而可能还在用 DeepEval**：Phoenix 支持把 DeepEval 当第三方 evaluator 接进来。

**业界常见做法**：DeepEval 占 CI 门禁（PR 时挡回归）+ 可观测平台占在线观测，两个都跑。

---

### Q4：Phoenix 和 Langfuse 可互换吗？

**答**：槽位上是替代关系（二选一占可观测平台位置），但不是无差别可互换。

- **真正「可互换」的那一层是 OTel 埋点**：OpenInference 是一套 OpenTelemetry 语义约定，任何 OTel-native 后端都能经 OTLP 吃。所以**可以保留埋点、只换后端，甚至同时往多个 OTLP endpoint fan-out**。但**平台侧累积的数据（历史 trace、prompt 版本、dataset、看板、标注队列）不会自动迁移**。
- **重心不同**（决定选哪个）：
  - **Phoenix**：偏 ML / research / OTel，notebook 友好，强在离线评估、实验对比、RAG 检索 introspection、embedding 可视化。
  - **Langfuse**：偏 product / ops，强在生产监控、prompt 版本治理、sessions/users。
- **自托管权衡**：Phoenix 起步最简单（单容器 / 单 pip），但 OSS 是单节点 / PostgreSQL，定位本地测试，高吞吐生产要上商业版 Arize AX；Langfuse 自托管要 ClickHouse + Redis + S3，部件多，但为生产规模设计。
- **License**：Phoenix 是 ELv2（限制做托管服务），Langfuse 是 MIT（更宽松）。
- 因为重心互补，**很多团队两个都跑**：Langfuse 接 live traffic，Phoenix 对采样 trace 做离线评估。

---

### Q5：LangSmith 呢？和它们什么关系，怎么选？

**答**：LangSmith 也在可观测平台槽里，和 Phoenix/Langfuse 是**三选一**。但有两个根本不同点：

1. **闭源 + LangChain/LangGraph 第一方原生**（Phoenix/Langfuse 都开源）。它对 LangGraph 整合最深：zero-config tracing、**LangGraph Studio**（可视化 graph、设断点、运行中改 state、从 checkpoint 恢复重跑 —— 本质是 Pregel 执行模型 + checkpointer 的可视化）、一键部署（LangSmith Deployment / 前 LangGraph Platform）、Prompt Hub、规模化标注队列。
2. **主权/成本反着戳偏好**：闭源 SaaS，自托管仅 Enterprise；per-trace 计费规模化贵（1M events 约 \$2,514/月，对比 Langfuse Core 约 \$101/月）。

**OTel 现状**：2026 年 LangSmith 加了 OTel 支持（`LANGSMITH_OTEL_ENABLED`，可经 Collector fan-out 多后端），但**不是 OTel-first**，重心仍是 LangChain-native。lock-in 现在不主要在埋点（OTel 降低了），而在 Prompt Hub + 原生 LangGraph tracing 这些深度功能。

**选型一句话**：「数据必须留在自己基础设施」→ Langfuse；「全押 LangChain、不想运维服务器」→ LangSmith。Langfuse 朝可移植性，LangSmith 朝整合度。

**两全解法**（加分）：开发期用 LangGraph Studio + LangSmith 调试（享受原生体验），生产期用 OTel fan-out 同时写到自托管的 Langfuse/Phoenix 保数据主权和低成本存储 —— 一份埋点、多后端各取所长。

---

## 3. 能体现资深度的加分细节（被深挖时抛出）

- **reference-based 退化陷阱**：DeepEval 的 ContextualPrecision/Recall 没有 ground-truth context 会静默退化，结果不可信。区分 referenceless 与 reference-based 指标是基本功。
- **确定性评分**：DeepEval 的 DAG metric 用决策树规避 LLM-as-judge 的非确定性 —— 评估器本身也会抖动，这是评估的元问题。
- **OTel/OpenInference 是抗锁定的关键**：埋点一次、后端可换、可 fan-out。选型时优先「埋点标准化」而非「绑某个平台」。
- **可观测测机制、不测语义**：trace 是绿的（200、正常延迟、正常 token），产品可能是坏的（答错、用户在生气、agent 在死循环）。这些是**语义失败**，得在每轮内容上加分类器（is_user_frustrated、stuck-in-loop、jailbreak…），LLM-as-judge eval 是其近似。
- **License 三档**：MIT（Langfuse，最宽松）/ ELv2（Phoenix，限制托管服务）/ 闭源（LangSmith）。数据主权敏感时这是硬约束。
- **成本模型**：per-trace（LangSmith）规模化后成本曲线陡；unit/event（Langfuse）和自托管（Phoenix）便宜。agent trace 嵌套多、payload 大，per-trace/unit 计费更快触顶。
- **长 agent run 的 trace UX**：Langfuse 的 observation-first 数据模型适合 prompt 为中心的应用，读 30 分钟、多子 agent 的长链路会变慢 —— 这是专门的 agent 可观测（如 Laminar）的切入点。

---

## 4. 对比速查表

### 评估库（槽 A）

| 维度 | RAGAS | DeepEval |
|---|---|---|
| 定位 | RAG 专用指标库 | pytest 评估框架 |
| 范围 | 最窄（RAG） | 广（RAG + agentic + multi-turn + safety） |
| 工作流 | dataset + evaluate() | pytest assert + CI gate |
| 独特点 | reference-free，RAG 指标事实标准 | DAG 确定性、多轮模拟、red teaming |
| 陷阱 | — | ContextualPrecision 需 ground-truth，否则退化 |
| License | Apache-2.0 | Apache-2.0 |

### 可观测平台（槽 B）

| 轴 | Phoenix | Langfuse | LangSmith |
|---|---|---|---|
| 开源 | ✅ ELv2 | ✅ MIT | ❌ 闭源 |
| 自托管 | 单容器；OSS 单节点 | ClickHouse，生产规模 | 仅 Enterprise |
| OTel | OTel-first（OpenInference） | OTel-first | 后加，非原生 |
| 重心 | 评估/实验/research | 生产监控/prompt 治理 | LangChain/LangGraph 最深 |
| 独特点 | embedding 2D/3D 漂移可视化 | prompt 版本治理、采用最广 | LangGraph Studio、一键部署 |
| 成本规模化 | 免费自托管 | 低（约 \$101/1M） | 高（约 \$2,514/1M） |

---

## 5. 选型一句话决策树

- 要 **RAG 指标 / 监管可辩护** → RAGAS
- 要 **CI 门禁 / 代码优先回归测试** → DeepEval
- 要 **最易自托管 + embedding 检索调试 + ML/research 风格** → Phoenix
- 要 **数据主权 + 生产规模自托管 + prompt 治理** → Langfuse
- **全押 LangChain/LangGraph + 不想运维 + 要 Studio/一键部署** → LangSmith
- **抗锁定的底层原则**：先用 OpenTelemetry 标准化埋点，后端保持可换。