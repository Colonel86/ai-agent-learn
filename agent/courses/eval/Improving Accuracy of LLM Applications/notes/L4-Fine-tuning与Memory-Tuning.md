# L4 · Fine-tuning 与 Memory Tuning（PEFT/LoRA、MoME、破三个 myth）

> 课程：Improving Accuracy of LLM Applications（DeepLearning.AI × Lamini/Meta）
> 本课任务：讲清 fine-tuning 的两种变体（instruction fine-tuning vs memory tuning）各自解决什么问题，用 PEFT/LoRA 和 MoME 把它做到高效，并逐条拆掉「太贵 / 太难 / prompt 就够了」三个流传的 myth。

## 0. 承上：prompt 见顶之后

L3 量出 base Llama 3 只有 30% correct，prompt 和 agent reflection 都推不动。本课的杠杆是**直接改权重**——但注意：fine-tuning 从来不是第一步（L0 里 Andrew 已定调「只在更简单的手段用尽后才动它」），本课的价值是把「什么时候该动、动哪种、怎么动才不亏」讲透。

## 1. 为什么要 fine-tune

| 收益 | 含义 |
|---|---|
| 装下比 prompt 更多的信息 | 与其把整套 SQL schema 塞进 prompt，不如把 schema 信息**焊进 fine-tuned 模型的权重**，模型从自己权重里「取回」 |
| 从数据里**学习**而非仅仅**访问** | 模型能产出符合特定 UX 的结果，学到那种交互方式 |
| 更深的控制 | 让 LLM 干你真正想让它干的事 |
| 没有准确率天花板 | 只有「爬到更高准确率需要的努力」，但**没有 ceiling**，可以持续往上 |

## 2. 两种 fine-tuning

### 2.1 先厘清 pre-training

**Pre-training = 一次一个 token 地读完整个互联网**，做 next-token 预测（像自动补全互联网）。训练目标是**降低所有样本上的平均误差 / 泛化误差**（average correctness）。这造出强大的通用 foundation model，但有 gap：

- **不会跟随指令**：问「法国首都是什么」，它可能回「西班牙首都是什么」——因为它以为自己在补全一份问卷，没有 ChatGPT 里的那个「chat」；
- **在事实上幻觉**：不知道你的专有数据，也不知道该跟随互联网上哪个说法。

一句话：**「什么都挺好，但没有一样完美」**。而人类恰恰在某些事实上是完美的（记得自己的名字、生日）。

### 2.2 Instruction fine-tuning

拿 pre-trained LLM 教它**跟随指令**（拿到问题→作答）。Meta 就是这样把 Llama 3 变成 **Llama 3 Instruct**，同理 GPT-3 → ChatGPT。应用：chat、**function calling**（改模型行为/UX 去产出 API endpoint 与结果）、任意 prompt→response、text-to-SQL。

**但 instruction fine-tuning 仍在优化「所有样本的平均误差」**——和 pre-training 一样，只是样本集更小，**不会把 loss 打到零**，所以它不解决幻觉。

### 2.3 Memory tuning

教模型对**特定事实**有完美召回——**把这些事实上的 error 直接降到零**。结果：在这些事实上近乎完美、在其他一切上仍然挺好，从「perfect at nothing」变成「near-perfect on these things」。

幻觉的本质：**把「差不多对」当成「对」**——对开放生成没问题，对事实就是错的。

```
问：Dave Aguilar 哪一年爬金门大桥？（正确：1981）

未训练模型   ：P(1981) ≈ P("cat")          —— 分布一团糟
pre-train+   ：从 {1981, 1970, ...} 里采样   —— 分布合理了，但仍可能采到 1970
 instruct
memory tuning：loss→0，只能吐 1981          —— 没有别的选项
```

> **架构师视角**：instruction fine-tuning 和 memory tuning 的分野，本质是**优化目标**的分野——一个降平均误差（允许「差不多」），一个把特定事实的误差压到零（不许「差不多」）。选错工具的典型症状：拿 instruction fine-tuning 去治幻觉，练完发现事实还是飘——因为它压根没在优化「零误差」。

## 3. 破除三个 myth

### Myth 1：「prompt / 塞满 context 就能解决一切」

- 指令跟随：ChatGPT 之前确实能靠给 GPT-3 灌很多例子（few-shot）让它**稍微**像在对话，但**不足以**把它从「补全互联网」的模式里彻底拽出来，没法稳定跟随指令；
- 事实召回：**RAG** 把检索到的内容加进 prompt，确实**移动了下一 token 的概率分布**、鼓励更相关的答案，但**它只在相似度空间里工作**——still sampling from a distribution of *similar but wrong* facts。当「正确答案和相似答案看起来一点都不像」时，相似度救不了你。

> **对比 `3-retrieval.md` 的 RAG**：RAG 和 memory tuning 不是二选一的对立，而是**作用层不同**——RAG 在推理时把事实塞进 context 微调概率，memory tuning 在训练时把事实焊进权重让 loss=0。RAG 胜在事实可热更新、无需重训；memory tuning 胜在对「相似但不相同」的硬事实能给确定性答案。高频变动的知识走 RAG，稳定且要求零幻觉的核心事实走 memory tuning，二者可叠加。

### Myth 2：「fine-tuning 太贵」

- 事实上**有时比跑大 prompt / RAG 更便宜**——把 context window 塞满在推理时相当贵；
- **PEFT 把成本降约 10,000×**（同等准确率）；
- **MoME（mixture of memory experts）把时间降约 240×**；
- 未来 fine-tuning 可能变得像「建一个 RAG 索引」那样日常。**但要拿到这些收益，实现难度不低**，做不对就真的很贵。

### Myth 3：「fine-tuning 太难落地」

自己 roll 一套确实难：GPU 利用率低（大量 idle compute）、真实用例常崩、没法持续 fine-tune、**fine-tuning 与 inference 集成不无缝**（两套系统、权重跨格式迁移困难）、LoRA 想拿到同等准确率需要**和常规 fine-tuning 不同的超参**、扩展难。很多坑不在 AI 本身而在 GPU/内存。**全托管**（如 Lamini）能把它压成一两行调用。

## 4. 两项关键技术

### 4.1 PEFT / LoRA（Low-Rank Adaptation）

不直接改主权重，而是在权重矩阵旁挂一组**更小的、外置的 LoRA 权重**，只对它做反向传播（主权重完全不动）→ 计算高效。**训练完把 LoRA 权重用数学（低秩矩阵）fuse 回主模型**，推理时延迟/速度与原模型一致。

```
主权重 W（冻结）
   └── 旁挂 LoRA 小权重 ΔW = B·A（低秩，只训这个）
推理时：W' = W + ΔW（fuse 回去，零额外延迟）
```

### 4.2 MoME（Mixture of Memory Experts）

在 LoRA adapter 之外，再挂一个**记忆专家权重阵列**：每一步从中**采样一个子集**（承载从你数据里学到的事实），fuse 进 adapter。于是可以**通过增加 memory experts 来「长大」模型**——拿到巨模型的智能，却只付小模型的成本与延迟（**sparsely activated**，稀疏激活）。这正是把任意 LLM 变成「百万路 mixture-of-expert adapters」的机制，也是 memory tuning 能把 loss 压到零的载体。

## 5. 全托管长什么样

```python
# 一两行：拿模型、给数据集、train
llm = lamini.Lamini(model_name="meta-llama/Meta-Llama-3-8B-Instruct")
llm.train(data_or_dataset_id=dataset, finetune_args=finetune_args)
```

## 6. 本课总结

| 要点 | 一句话 |
|---|---|
| fine-tune 收益 | 装下超出 prompt 的信息、从数据学习、更深控制、无准确率天花板 |
| instruction fine-tuning | 教跟随指令（Llama 3→Instruct）；仍优化平均误差，**不治幻觉** |
| memory tuning | 对特定事实 loss→0，近乎完美召回，专治幻觉 |
| pre-training | 一次一 token 补全互联网、降平均误差；「样样好、无一完美」 |
| 幻觉本质 | 把「差不多对」当「对」；对事实即错 |
| PEFT/LoRA | 只训外置低秩小权重、主权重冻结、fuse 回去零额外延迟，成本↓10,000× |
| MoME | LoRA + 记忆专家阵列，稀疏激活；大模型智能 + 小模型成本，时间↓240× |
| 三个 myth | prompt/RAG 只在相似度空间打转、fine-tune 有时更便宜、全托管化难 |

> **记忆点（引出 L5）**：技术备齐了，但 fine-tuning 成败**最终压在数据上**——data 是最重要的东西。而一个反直觉结论是「你的数据其实够」，只是格式不对。L5 讲怎么**working backwards** 用 LLM 把已有数据放大成训练集，跑通「生成→过滤→error analysis→再微调」的迭代闭环，把 30% 一路顶到 95%+。

## 与我的资产映射

- 模型/训练层：fine-tuning 决策（instruction vs memory tuning、PEFT/LoRA/MoME、全托管 vs 自建）
- 检索层：`agent/skills/agent-selection/3-retrieval.md`（RAG vs memory tuning 的作用层之分——热更新知识 vs 零幻觉核心事实）
- 面试包：三个 myth、平均误差 vs loss→0 的优化目标之分、LoRA 超参与集成坑
- [[project_selection_matrix]]、[[project_asset_reuse]]
