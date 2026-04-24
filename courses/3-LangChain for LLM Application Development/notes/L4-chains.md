# Lesson 4: Chains（链）

## 核心概念

**Chain** = LLM + Prompt（+ 其他步骤）的组合单元。

链可以单独使用，也可以串联成更复杂的流水线，是 LangChain 最基础的抽象之一。

---

## 三种 Chain 类型

### 1. LLMChain（基础链）

```python
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain

llm = ChatOpenAI(temperature=0.9)
prompt = ChatPromptTemplate.from_template(
    "What is the best name to describe a company that makes {product}?"
)
chain = LLMChain(llm=llm, prompt=prompt)

result = chain.run("Queen Size Sheet Set")
# → "Royal Beddings"
```

**本质**：自动完成 prompt 格式化 → LLM 调用 → 返回结果。

---

### 2. SimpleSequentialChain（简单顺序链）

适用：每个子链**单输入单输出**，前一个的输出自动成为下一个的输入。

```python
from langchain.chains import SimpleSequentialChain

# Chain 1: 产品 → 公司名
chain_one = LLMChain(llm=llm, prompt=prompt_name)

# Chain 2: 公司名 → 公司描述
chain_two = LLMChain(llm=llm, prompt=prompt_desc)

overall_chain = SimpleSequentialChain(
    chains=[chain_one, chain_two],
    verbose=True
)

result = overall_chain.run("Queen Size Sheet Set")
# chain_one: "Royal Beddings"
# chain_two: "Royal Beddings offers premium queen-size bedding..."
```

**数据流**：`产品 → [chain_one] → 公司名 → [chain_two] → 描述`

---

### 3. SequentialChain（顺序链，多输入多输出）

适用：链之间有**多个输入变量**或需要保留**中间输出**。

```python
from langchain.chains import SequentialChain

# Chain 1: 评论 → 英文翻译
chain_one = LLMChain(llm=llm, prompt=prompt_translate,
                     output_key="English_Review")

# Chain 2: 英文评论 → 摘要
chain_two = LLMChain(llm=llm, prompt=prompt_summary,
                     output_key="summary")

# Chain 3: 原始评论 → 语言检测
chain_three = LLMChain(llm=llm, prompt=prompt_detect_lang,
                       output_key="language")

# Chain 4: 摘要 + 语言 → 用原语言写跟进回复
chain_four = LLMChain(llm=llm, prompt=prompt_followup,
                      output_key="followup_message")

overall_chain = SequentialChain(
    chains=[chain_one, chain_two, chain_three, chain_four],
    input_variables=["Review"],
    output_variables=["English_Review", "summary", "followup_message"],
    verbose=True
)
```

**关键注意**：`output_key` 和后续链的输入变量名必须精确匹配，否则报 KeyError。

**数据流**：

```
Review
  ├→ [chain_one] → English_Review
  │     └→ [chain_two] → summary ─────┐
  └→ [chain_three] → language ────────┤
                                       └→ [chain_four] → followup_message
```

---

### 4. Router Chain（路由链）

根据输入内容，**动态选择**最合适的子链。

```python
from langchain.chains.router import MultiPromptChain
from langchain.chains.router.llm_router import LLMRouterChain, RouterOutputParser

# 定义各专业子链
destination_chains = {
    "physics": LLMChain(llm=llm, prompt=physics_prompt),
    "math":    LLMChain(llm=llm, prompt=math_prompt),
    "history": LLMChain(llm=llm, prompt=history_prompt),
    "cs":      LLMChain(llm=llm, prompt=cs_prompt),
}
default_chain = LLMChain(llm=llm, prompt=default_prompt)

# Router 链：用 LLM 自身决定路由到哪个子链
chain = MultiPromptChain(
    router_chain=router_chain,
    destination_chains=destination_chains,
    default_chain=default_chain,
    verbose=True
)

chain.run("What is black body radiation?")  # → 路由到 physics
chain.run("Why does DNA exist in cells?")   # → 路由到 default（未匹配）
```

**路由机制**：

1. 用户输入 → Router LLM → 输出 `{"destination": "physics", "next_inputs": "..."}`
2. `RouterOutputParser` 解析上述 JSON
3. 派发到对应 `destination_chain`

**无法匹配时**：`destination = "DEFAULT"`，使用 `default_chain`。

---

## SimpleSequentialChain vs SequentialChain


|        | SimpleSequentialChain | SequentialChain         |
| ------ | --------------------- | ----------------------- |
| 子链 I/O | 单输入单输出                | 多输入多输出                  |
| 中间结果   | 不保留                   | 可保留（`output_variables`） |
| 灵活性    | 低                     | 高                       |
| 适用     | 线性管道                  | 有分支依赖的流程                |


---

## 关键要点

1. **LLMChain** 是最小单元，所有复杂链都由它组合
2. **变量名对齐**是 SequentialChain 最常见的 bug 来源
3. **Router Chain** 让 LLM 本身做调度决策，是 Agent 的雏形
4. 链可以无限嵌套组合，构建任意复杂的处理管道

