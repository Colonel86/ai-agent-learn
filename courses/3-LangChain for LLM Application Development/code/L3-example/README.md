# L3 - Chains（链）

## 本节主题

Chain 是 LangChain 最核心的抽象，将 LLM + Prompt 组合并串联成复杂流程。

| Chain 类型 | 适用场景 |
|-----------|---------|
| `LLMChain` | 基础单元：prompt → LLM → 输出 |
| `SimpleSequentialChain` | 多步骤线性管道（单输入单输出） |
| `SequentialChain` | 多步骤管道（支持多输入多输出） |
| `Router Chain` | 根据输入内容动态选择子链 |

## 快速开始

```bash
pip install -r requirements.txt
```

创建 `.env` 文件：

```
OPENAI_API_KEY=sk-...
```

运行：

```bash
python main.py
```

## 核心 API

```python
from langchain.chains import LLMChain, SimpleSequentialChain, SequentialChain

# 基础链
chain = LLMChain(llm=llm, prompt=prompt)

# 顺序链（多输入多输出）
overall = SequentialChain(
    chains=[chain_one, chain_two, chain_three],
    input_variables=["Review"],
    output_variables=["English_Review", "summary", "followup_message"]
)
```

## 关键注意

- `SequentialChain` 中 `output_key` 与下游链输入变量名必须**精确匹配**
- Router Chain 使用 LLM 自身做路由决策，是 Agent 的雏形
