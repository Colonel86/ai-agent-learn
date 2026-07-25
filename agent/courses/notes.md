**一句话**：Prompt Engineering 优化的是"你写的那段话"，Context Engineering 优化的是"模型每次调用时看到的全部输入的构成"。前者是后者的子集，这个词的兴起（2025 年，Karpathy 带火）本质是承认了一件事：agent 时代，prompt 里大部分内容不是人写的，是**系统装配**的。

| 维度 | Prompt Engineering | Context Engineering |
|---|---|---|
| 优化对象 | 指令文本本身（措辞、结构、few-shot 怎么写） | 整个上下文窗口的**内容构成**：放什么、放哪个区、放多少、何时换出 |
| 典型动作 | "改写这句指令让分类更准"、加 CoT、调 XML 标签 | 检索注入、分区、压实/换页、工具定义按需加载、token 预算分配 |
| 静态/动态 | 基本静态：写好一段好 prompt | **动态系统**：每轮调用现场装配，内容随状态变化 |
| 关注的失效模式 | 模型不听话、输出格式错 | 上下文膨胀、lost-in-the-middle、信噪比下降、缓存击穿 |
| 角色类比 | 文案 | **内存管理器 / 操作系统** |

用已经写过的代码来定位这条线，其实每一课都能拆成两层：

- `triage_system_prompt` 里那句 "Follow these examples more than any instructions above"——这是 **prompt engineering**（一句措辞改变优先级）
- 但"检索哪几条案例、注入到 examples 槽"——这是 **context engineering**（L4 的向量检索 + 动态装配）
- L2 的 `system(重建) + history(追加)` 公式、12a 的五段分区 + 80% 压实 + toolbox top-k 检索、12b 的 memory statistics（"不给内容只给存在性信号"）——全是 context engineering，跟任何一句 prompt 怎么写无关
- 12a 那条共识"上下文要分区，且要告诉 LLM 分区的语义"恰好是两者的**交界处**：分区本身是 context engineering，"告诉 LLM 分区语义"的那段说明文字是 prompt engineering

**为什么这个区分在面试里值钱**：它对应能力边界的判断。prompt 调优的收益天花板很快就到（模型越强，措辞敏感度越低）；而 agent 的失败大多发生在 context 层——该在的信息不在（检索没命中）、不该在的信息挤占窗口（没压实）、信息在但被淹没（lost-in-the-middle）。所以 Anthropic 官方那篇 context engineering 文章的立场就是：**把上下文当稀缺资源做预算管理**，这正是 12a 整门课的立足点——"Compaction ≠ Summarization"、"Toolbox = 程序性记忆"、"元认知分水岭"，全是这个学科的具体技术。

还有一层递进关系可以在面试里用：**prompt engineering → context engineering → memory engineering**。记忆系统本质上是 context engineering 的时间维度扩展——单轮内管好窗口是 context engineering，跨轮/跨会话决定"什么值得进未来的窗口"就是记忆系统了。三门记忆课其实都是在教"如何持续地喂好那个窗口"。