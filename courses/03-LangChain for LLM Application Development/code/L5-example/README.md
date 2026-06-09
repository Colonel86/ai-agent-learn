# L5 - Evaluation（评估）

## 本节主题

如何系统评估 LLM 应用质量？核心挑战：LLM 输出是自由文本，无单一标准答案。

```
传统方式：字符串匹配 → 失败（"Yes" ≠ "Yes, it has side pockets"）
LLM 评估：理解语义等价 → 正确 ✓
```

## 评估流程

```
1. 构建 QA 应用
2. 准备测试集（手动 + LLM 自动生成）
3. 运行应用，收集预测
4. LLM-as-judge 评分
5. 查看正确率
```

## 快速开始

```bash
pip install -r requirements.txt
```

创建 `.env` 文件：

```
OPENAI_API_KEY=sk-...
```

将 L4 的 `products.csv` 复制到本目录，然后运行：

```bash
cp ../L4-example/products.csv .
python main.py
```

## 核心 API

```python
from langchain.evaluation.qa import QAGenerateChain, QAEvalChain

# 自动生成测试集
gen_chain = QAGenerateChain.from_llm(llm)
examples = gen_chain.apply_and_parse([{"doc": doc} for doc in docs])

# LLM 评估
eval_chain = QAEvalChain.from_llm(llm)
graded = eval_chain.evaluate(examples, predictions)

# Debug 模式
import langchain
langchain.debug = True
```

## 关键工具

| 工具 | 用途 |
|------|------|
| `QAGenerateChain` | 从文档自动生成 Q&A 测试对 |
| `langchain.debug` | 查看链内部完整执行过程 |
| `QAEvalChain` | 用 LLM 评判预测是否正确 |
