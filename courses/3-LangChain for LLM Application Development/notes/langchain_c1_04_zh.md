# LangChain for LLM Application Development — 第04课：链（Chains）（中文字幕）

---

本课 Harrison 将介绍 LangChain 最重要的核心构建块——**链（Chain）**。

链通常将一个 LLM 与一个提示词结合在一起。有了这个构建块，你还可以将多个链组合在一起，对文本或其他数据执行一系列操作。

---

## 准备工作

加载环境变量，并加载一个 pandas DataFrame（包含产品列和评论列的数据集），用于演示链如何批量处理多条输入。

---

## LLM Chain（基础链）

这是最基础也最常用的链类型：

```python
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain

llm = ChatOpenAI(temperature=0.9)
prompt = ChatPromptTemplate.from_template(
    "描述一家生产 {product} 的公司，最适合的公司名称是什么？"
)
chain = LLMChain(llm=llm, prompt=prompt)
chain.run("Queen Size Sheet Set")  # 输出：Royal Bettings
```

---

## Sequential Chains（顺序链）

顺序链将多条链依次运行，前一条链的输出作为下一条链的输入。

### Simple Sequential Chain（简单顺序链）

适用于每个子链**只有单一输入和单一输出**的场景：

```python
from langchain.chains import SimpleSequentialChain

# Chain 1：根据产品生成公司名
chain_one = LLMChain(llm=llm, prompt=prompt_one)

# Chain 2：根据公司名生成20字描述
chain_two = LLMChain(llm=llm, prompt=prompt_two)

overall_chain = SimpleSequentialChain(chains=[chain_one, chain_two])
overall_chain.run("Queen Size Sheet Set")
# 先输出 "Royal Bettings"，再输出该公司的描述
```

### Sequential Chain（普通顺序链）

适用于有**多个输入或多个输出**的场景：

```python
from langchain.chains import SequentialChain

# Chain 1：将评论翻译成英文（输入: review → 输出: english_review）
# Chain 2：生成一句话摘要（输入: english_review → 输出: summary）
# Chain 3：检测评论的原始语言（输入: review → 输出: language）
# Chain 4：用原始语言写后续回复（输入: summary + language → 输出: followup_message）

overall_chain = SequentialChain(
    chains=[chain_one, chain_two, chain_three, chain_four],
    input_variables=["review"],
    output_variables=["english_review", "summary", "followup_message"]
)
```

**注意：** 变量名必须精确对应，输入键和输出键要完全匹配，否则会出现 KeyError。

**可视化对比：**
- 简单顺序链：每个链只有单一输入 → 单一输出，依次传递
- 普通顺序链：任意步骤可接受多个输入变量，适合更复杂的下游链

---

## Router Chain（路由链）

更复杂的用例：**根据输入内容，动态决定将其路由到哪条子链**。

**场景示例：** 根据问题的学科，路由到不同的专业提示词链：

```python
physics_template = "你是一位物理学老师，专门回答物理问题..."
math_template = "你是一位数学老师，专门回答数学问题..."
history_template = "你是一位历史老师，专门回答历史问题..."
cs_template = "你是一位计算机科学老师..."
```

**实现步骤：**

1. **定义目标链（Destination Chains）：** 每条子链本身是一个 LLM Chain
2. **定义默认链（Default Chain）：** 当路由器无法决定使用哪条子链时调用（如生物学问题不属于任何已定义学科）
3. **创建路由模板：** 包含任务说明和格式要求，传递给 LLM 来决策路由
4. **组合路由链：**

```python
from langchain.chains.router import MultiPromptChain
from langchain.chains.router.llm_router import LLMRouterChain, RouterOutputParser

# RouterOutputParser 将 LLM 输出解析为字典，确定路由目标和输入
router_chain = LLMRouterChain.from_llm(llm, router_prompt)

overall_chain = MultiPromptChain(
    router_chain=router_chain,
    destination_chains=destination_chains,
    default_chain=default_chain
)
```

**测试：**
- 提问物理问题 → 自动路由到物理链，给出详细物理学解答
- 提问数学问题 → 路由到数学链
- 提问生物学问题 → 路由器返回 `None`，转入默认链（通用 LLM 调用）

---

## 本课小结

| 链类型 | 特点 |
|--------|------|
| **LLM Chain** | 最基础的链，组合 LLM + 提示词 |
| **Simple Sequential Chain** | 单输入单输出，依次串联 |
| **Sequential Chain** | 支持多输入多输出，变量名需精确匹配 |
| **Router Chain** | 根据输入内容动态选择子链，适合多场景分流 |

下一节将介绍如何利用这些构建块，创建能够对文档进行**问答**的链。
