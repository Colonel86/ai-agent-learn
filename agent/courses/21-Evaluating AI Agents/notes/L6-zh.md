# L6：三种评估器与如何选

埋点之后就可以开始评估。本节介绍三类评估技术，并教你判断什么时候用哪一种。

## 三种评估技术

### 1. 代码评估（Code-based Evals）

最简单、最像传统软件集成测试的一类：用代码对应用输出做检查。常见模式：

- **正则匹配（Regex）**——比如只允许数字、不含字母数字字符
- **JSON 可解析性**
- **关键词检查**——如聊天机器人不能提竞品名称
- **与 Ground Truth 对比**——直接相等比较，或用 **余弦相似度（Cosine Similarity）/ 余弦距离** 做语义匹配

### 2. LLM 作评审（LLM-as-a-judge）

用**另一个 LLM** 来给应用的输出打分。典型流程：

1. 取出一次运行的 input/output（必要时再加点关键上下文）
2. 套到一个**评估专用 Prompt 模板**里，描述要评估的具体维度
3. 把构造好的 prompt 发给**评审 LLM（Judge LLM）**
4. 让它返回一个**离散标签（Label）**

> 例：**RAG 文档相关性评估**——把用户查询和检索到的文档塞进评估模板，问 Judge："这些文档与问题相关吗？" 让它返回 `relevant` / `irrelevant`。

#### 用 LLM-as-a-judge 的几个戒律

- **只有 top-tier 模型才与人类判断对齐**——一般要用 **GPT-4o** 或 **Claude 3.5 Sonnet** 这种水平的 Judge
- **永远不会 100% 准**——LLM 评审总有误差，需要靠**调 Prompt 或调模型**来收敛
- **必须用离散分类标签，不要用连续打分**——`correct`/`incorrect`、`relevant`/`irrelevant` 这种二元（或三元）标签远胜过"打 1-100 分"。LLM 区分不出 83 和 79 的差别，特别是当每个样本独立评分时

### 3. 人工标注（Human Annotations）

可以走两条路：

- **构造标注队列（Annotation Queue）**：Phoenix 等平台把大量 Trace 排成队列，让人工标注员逐条打标
- **从终端用户收集反馈**：经典的"👍/👎"按钮模式

## 怎么选？两个维度

| 维度 | 选择 |
|------|------|
| **指标是定性还是定量？** | 总结质量、分析清晰度等定性指标 → LLM-as-a-judge 或 Human；可代码化的（regex 匹配等）→ Code-based |
| **是否要求 100% 准确？** | 需要 100% → Code-based 或 Human；可接受小误差 → LLM-as-a-judge |

**Human 标注理论上最佳**（既灵活又确定），但**规模化困难**——人工成本高；从用户收集又有选择偏差，不适合作为大规模评估手段。

## 评估智能体的哪些部分？

本节聚焦 **Router** 和 **Skills**，**Path（轨迹）** 留到后续课程。

### 评估 Router 的两个维度

1. **函数调用是否选对（Function Calling Choice）**——是否选了正确的工具？（NLP 分类器路由器也适用这个评估）
2. **参数抽取是否正确（Parameter Extraction）**——选对工具后，从用户输入中抽取的参数对吗？

#### LLM-as-a-judge 评估 Router 的模板要包含

- 给 Judge 的指令
- **占位符**：用户问题、被调用的工具
- **必须输出 `correct` 或 `incorrect` 这种单词**
- 对什么算 correct/incorrect 的详细说明
- **完整的工具定义清单**，让 Judge 知道全部可选项

> 反例：用户问"我的订单 1234 到哪儿了"——智能体先调用 `order_status_check(order_id="1234")`（正确）；用户追问"什么时候到？"，智能体调用 `shipping_status_check(tracking_id="1234")` ——**函数选对了但参数错了**（order_id ≠ tracking_id），这就是参数抽取失败。

### 评估 Skills

技能本身要么是其他 LLM 应用、要么是普通软件代码，因此**所有传统软件/LLM 应用的评估手段都能用**。

- **LLM-as-a-judge** 适合评：相关性、幻觉、问答正确性、生成代码可读性、摘要质量
- **Code-based** 适合评：regex 匹配、JSON 可解析、与 Ground Truth 对比

### 例：给本课程的三个工具配评估

| 工具 | 推荐评估 | 类型 |
|------|---------|------|
| `lookup_sales_data` | SQL 生成是否正确 | LLM-as-a-judge **或** Code-based（对比 Ground Truth SQL/结果） |
| `analyze_sales_data` | 分析的清晰度（clarity）、实体引用正确性（entities correctness） | LLM-as-a-judge |
| `generate_visualization` | 生成的代码是否可运行 | Code-based |

> 评估常常**艺术多于科学**——同一个目标可能有多种合理评估方式，不用纠结唯一正解。

## 小结

本节你掌握了：

- 三大评估技术（Code / LLM-as-a-judge / Human）
- 各自适用场景
- 智能体内 Router 与 Skills 各自该怎么评

下一节进入 Notebook，把 LLM-as-a-judge 和 Code-based 都跑一遍。
