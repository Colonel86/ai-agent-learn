"""
LangChain Lesson 5: Evaluation
演示 LLM 应用的评估方法：自动生成测试集 + LLM-as-judge
"""

import os
import langchain
from dotenv import load_dotenv, find_dotenv
from langchain_openai import ChatOpenAI
from langchain.document_loaders import CSVLoader
from langchain.vectorstores import DocArrayInMemorySearch
from langchain_openai import OpenAIEmbeddings
from langchain.indexes import VectorstoreIndexCreator
from langchain.chains import RetrievalQA

load_dotenv(find_dotenv())
LLM_MODEL = "gpt-3.5-turbo"
CSV_FILE = "products.csv"


def build_qa_chain() -> RetrievalQA:
    """构建被评估的 QA 应用。"""
    loader = CSVLoader(file_path=CSV_FILE)
    index = VectorstoreIndexCreator(
        vectorstore_cls=DocArrayInMemorySearch,
        embedding=OpenAIEmbeddings(),
    ).from_loaders([loader])

    llm = ChatOpenAI(temperature=0.0, model=LLM_MODEL)
    qa = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=index.vectorstore.as_retriever(),
        verbose=False,
        chain_type_kwargs={"document_separator": "<<<<>>>>>"}
    )
    return qa


# ── 1. 手动编写测试集 ─────────────────────────────────────────────────────────

def get_manual_examples() -> list:
    return [
        {
            "query": "Does the Sun Shield Shirt have UPF protection?",
            "answer": "Yes, UPF 50+"
        },
        {
            "query": "What is the battery life of the Navigation Watch?",
            "answer": "20 hours"
        },
    ]


# ── 2. LLM 自动生成测试集 ─────────────────────────────────────────────────────

def generate_examples_with_llm(data: list) -> list:
    print("=" * 60)
    print("1. LLM 自动生成测试集（QAGenerateChain）")
    print("=" * 60)

    from langchain.evaluation.qa import QAGenerateChain

    example_gen_chain = QAGenerateChain.from_llm(
        ChatOpenAI(model=LLM_MODEL)
    )
    new_examples = example_gen_chain.apply_and_parse(
        [{"doc": t} for t in data[:3]]
    )

    print(f"生成了 {len(new_examples)} 个测试样本:")
    for i, ex in enumerate(new_examples):
        print(f"  [{i+1}] Q: {ex['qa_pairs']['query']}")
        print(f"       A: {ex['qa_pairs']['answer']}")

    return [ex["qa_pairs"] for ex in new_examples]


# ── 3. Debug 模式查看链内部 ───────────────────────────────────────────────────

def demo_debug(qa: RetrievalQA, query: str):
    print("\n" + "=" * 60)
    print("2. Debug 模式（langchain.debug = True）")
    print("=" * 60)
    print(f"Query: {query}\n")

    langchain.debug = True
    qa.invoke(query)
    langchain.debug = False


# ── 4. LLM 批量评估 ───────────────────────────────────────────────────────────

def evaluate_with_llm(qa: RetrievalQA, examples: list):
    print("\n" + "=" * 60)
    print("3. LLM 辅助评估（QAEvalChain）")
    print("=" * 60)

    from langchain.evaluation.qa import QAEvalChain

    # 批量运行，收集预测
    print("运行 QA chain 收集预测结果...")
    predictions = qa.apply(examples)

    # LLM 评估
    eval_chain = QAEvalChain.from_llm(
        ChatOpenAI(temperature=0, model=LLM_MODEL)
    )
    graded_outputs = eval_chain.evaluate(examples, predictions)

    # 打印结果
    print(f"\n{'─'*60}")
    for i, eg in enumerate(examples):
        grade = graded_outputs[i]["text"].strip()
        print(f"\n[Example {i}]")
        print(f"  Question:  {predictions[i]['query']}")
        print(f"  Reference: {predictions[i]['answer']}")
        print(f"  Predicted: {predictions[i]['result'][:100]}...")
        print(f"  Grade:     {grade}")

    # 统计
    correct = sum(
        1 for g in graded_outputs if "CORRECT" in g["text"].upper()
    )
    print(f"\n{'─'*60}")
    print(f"正确率: {correct}/{len(examples)} = {correct/len(examples)*100:.0f}%")


# ── 主入口 ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("构建 QA 应用...")
    qa = build_qa_chain()

    # 准备数据（用于生成测试集）
    loader = CSVLoader(file_path=CSV_FILE)
    data = loader.load()

    # 1. 手动测试集
    manual_examples = get_manual_examples()

    # 2. LLM 生成测试集
    try:
        generated_examples = generate_examples_with_llm(data)
        all_examples = manual_examples + generated_examples
    except Exception as e:
        print(f"LLM 生成失败，仅使用手动测试集: {e}")
        all_examples = manual_examples

    # 3. Debug 模式
    demo_debug(qa, all_examples[0]["query"])

    # 4. LLM 评估
    evaluate_with_llm(qa, all_examples[:4])
