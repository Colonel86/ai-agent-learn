# L12（加餐）：评估你的 LLM 评审本身

LLM-as-a-judge 永远不会 100% 准——所以 **Judge 本身也要被评估**。本节是一节加餐课，告诉你怎么用同一套 Experiment 机制来"审判审判官"。

## 为什么需要

回想之前 Router 评估的例子，你同时使用了：

- **Code-based** 比对 ground truth 工具名（100% 准）
- **LLM-as-a-judge**（不到 100% 准）

> 既然 Code-based 已经 100% 准了，为什么还要 LLM-as-a-judge？

因为 Code-based **依赖 ground truth**，规模化困难；而 LLM-as-a-judge **能横扫所有生产 Trace**。问题变成：**LLM Judge 与"地面真值"对齐到什么程度？** 这个对齐度就是要测的。

## 套路：用 Experiment 评估 Judge

把"被评估对象"从**智能体**换成**LLM Judge Prompt**——其余流程不变：

```
Dataset (judge 的 input + 期望 judge 标签)
  -> Task (跑 judge prompt)
  -> Evaluator (对比 judge 输出 vs 期望标签)
```

### 例 1：评估 Function Calling Judge

测试用例形如：

```
input:
  question: "Which stores have the best sales performance in 2021?"
  tool_call: database_lookup
expected_output: "correct"
```

> 红色的部分（**question + tool_call**）才是给 Judge 的输入；`expected_output` 是**ground truth 标签**。

实验维度：

- **改 Judge Prompt 措辞**
- **加 Few-shot 示例**——把一些既往被判定正确的例子塞进 Prompt，提升对齐度

评估器：Code-based 比对 `correct/incorrect` 标签。

### 例 2：评估 Analysis Clarity Judge

这个 Judge 不只输出标签，还输出**一段解释**，比如"分析清晰，因为 x、y、z"。

测试用例：

```
input: "In 2021 the best performing stores ..."
expected_output: "The analysis is clearer because of X, Y, and Z."
```

实验维度：换不同的 Judge **模型**或不同 Prompt。

**这次怎么评？** 不能字符串严格相等——Judge 可能写成"The analysis is easy to understand because of X, Y, Z."，意思一样。

> 解法：**语义相似度（Semantic Similarity）**——用 embedding 比对两段文本的含义。

## 小结

本节核心一句话：

> 用同一套 Experiment 工具去 evaluate your evaluators。

下一节也是最后一节，进入生产环节的话题。
