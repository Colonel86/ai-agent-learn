# LangChain for LLM Application Development — 第06课：评估（Evaluation）（中文字幕）

---

构建复杂 LLM 应用时，一个重要但有时棘手的步骤是：**如何评估你的应用表现如何？**

- 它是否满足某种准确率标准？
- 当你更换 LLM、调整向量数据库检索策略或修改其他系统参数时，如何判断改进了还是退步了？

本课将介绍评估 LLM 应用的框架和工具，包括一个非常有趣的思路：**用语言模型来评估其他语言模型**。

---

## 准备工作

使用上一课的文档问答链：

```python
# 加载数据、创建索引、创建检索 QA 链
index = VectorStoreIndexCreator(
    vectorstore_cls=DocArrayInMemorySearch
).from_loaders([loader])

qa = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=index.vectorstore.as_retriever(),
    verbose=True
)
```

---

## 创建评估数据集

### 方法一：手动创建

查看文档，手动编写"问题-答案"对：

```python
examples = [
    {
        "query": "Cozy Comfort Pullover Set 有侧袋吗？",
        "answer": "有"
    },
    {
        "query": "这件夹克属于哪个系列？",
        "answer": "DownTek 系列"
    }
]
```

缺点：耗时，不易规模化扩展。

### 方法二：用 LLM 自动生成

```python
from langchain.evaluation.qa import QAGenerationChain

qa_gen_chain = QAGenerationChain.from_llm(ChatOpenAI())

# 对每个文档自动生成问答对（返回字典格式）
new_examples = qa_gen_chain.apply_and_parse(
    [{"doc": doc} for doc in docs[:5]]
)
```

LLM 读取整篇文档，生成高质量的问题和参考答案，省去大量人工工作。

将自动生成的示例合并到手动创建的示例中，最终得到约 7 个评估示例。

---

## 调试：langchain.debug

只看最终答案不够——需要了解链内部发生了什么：

```python
import langchain
langchain.debug = True

qa.run(examples[0]["query"])
```

开启 debug 后，可以看到：
1. **RetrievalQA 链** 进入
2. **Stuff Documents 链** 进入
3. **LLM Chain** 进入，显示完整输入：
   - 原始问题
   - 检索到的上下文（多个文档片段）
4. **ChatOpenAI** 接收的完整提示词：
   > "请使用以下上下文片段来回答用户的问题。如果你不知道答案，直接说不知道，不要编造答案。"
5. 模型返回结果，还包含 `token_usage`（prompt_tokens、completion_tokens、total_tokens）和 `model_name`

**调试技巧：** 问答出错时，通常不是 LLM 本身的问题，而是**检索步骤**出了问题。仔细对比问题和检索到的上下文，有助于定位根因。

---

## 批量评估：用 LLM 自动打分

```python
from langchain.evaluation.qa import QAEvalChain

# 关闭 debug 模式
langchain.debug = False

# 批量运行所有示例，获取预测结果
predictions = qa.apply(examples)

# 创建评估链（用 LLM 来判断对错）
eval_chain = QAEvalChain.from_llm(llm)
graded_outputs = eval_chain.evaluate(examples, predictions)

# 打印每个示例的详情
for i, eg in enumerate(examples):
    print(f"示例 {i}：")
    print(f"问题：{eg['query']}")
    print(f"真实答案：{eg['answer']}")
    print(f"预测答案：{predictions[i]['result']}")
    print(f"评分：{graded_outputs[i]['text']}")
```

---

## 为什么需要 LLM 来评估？

以第一个示例为例：

- **真实答案**："有"
- **预测答案**："Cozy Comfort Pullover Set，Stripe 款确实有侧袋"

这两个字符串**完全不同**——一个极短，一个很长，"有"这个词甚至不出现在预测答案中。

用**字符串匹配、精确匹配或正则表达式**根本无法判断这两个答案是否等价。

这就是 LLM 评估的价值：它们是**开放性文本生成任务**，不存在唯一正确的字符串答案，只要语义等价就应被判为正确。**LLM 能够理解语义**，因此能做出人类级别的判断。

这是当前 LLM 应用评估中**最有趣、最流行**的方法——用语言模型来评估语言模型的输出。

---

## LangChain Evaluation Platform（可视化平台）

除了代码中的 debug 输出，LangChain 还提供可视化 UI：

```python
# 在 notebook 中设置 session 名称，运行结束后自动持久化
```

平台功能：
- 以 UI 形式展示 debug 模式的所有信息
- 追踪每次运行的输入/输出
- 在每个链层级逐级查看详情（RetrievalQA → Stuff Chain → LLM Chain → ChatOpenAI）
- 查看系统消息、人类问题、模型回复、输出元数据
- **将运行结果添加到数据集**：点击按钮即可将某次运行的输入输出加入评估数据集

这形成了一个**评估飞轮**：不断积累评估示例 → 持续测试系统改进效果。

---

## 本课小结

| 环节 | 方法 |
|------|------|
| 创建评估数据集 | 手动编写 或 QAGenerationChain 自动生成 |
| 单次调试 | `langchain.debug = True` |
| 批量评估 | QAEvalChain（用 LLM 打分） |
| 可视化追踪 | LangChain Evaluation Platform |

下一课将介绍 LangChain 中最令人兴奋的组件——**智能体（Agents）**。
