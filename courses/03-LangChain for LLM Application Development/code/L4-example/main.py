"""
LangChain Lesson 4: Q&A over Documents
演示 Embedding + Vector Store + RetrievalQA 文档问答
"""

import os
from dotenv import load_dotenv, find_dotenv
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.document_loaders import CSVLoader
from langchain_community.vectorstores import DocArrayInMemorySearch
from langchain.chains import RetrievalQA

load_dotenv(find_dotenv())
LLM_MODEL = "gpt-3.5-turbo"
CSV_FILE = "products.csv"


# ── 1. 快速方式（一行建索引）────────────────────────────────────────────────

def demo_quick_index():
    print("=" * 60)
    print("1. 快速方式：VectorstoreIndexCreator")
    print("=" * 60)

    from langchain.indexes import VectorstoreIndexCreator

    loader = CSVLoader(file_path=CSV_FILE)
    index = VectorstoreIndexCreator(
        vectorstore_cls=DocArrayInMemorySearch,
        embedding=OpenAIEmbeddings(),
    ).from_loaders([loader])

    query = "List all items with sun protection in a markdown table."
    response = index.query(query, llm=ChatOpenAI(temperature=0, model=LLM_MODEL))
    print(response)


# ── 2. 分步详解 ───────────────────────────────────────────────────────────────

def demo_step_by_step():
    print("\n" + "=" * 60)
    print("2. 分步详解：Loader → Embedding → VectorStore → Retriever → QA")
    print("=" * 60)

    # Step 1: 加载文档
    loader = CSVLoader(file_path=CSV_FILE)
    docs = loader.load()
    print(f"[Step 1] 加载了 {len(docs)} 个文档片段")
    print(f"第一个文档内容预览: {docs[0].page_content[:100]}...")

    # Step 2: 创建 Embedding 模型
    embeddings = OpenAIEmbeddings()

    # Step 3: 演示 embedding 效果
    embed_sample = embeddings.embed_query("Hi my name is Harrison")
    print(f"\n[Step 2] Embedding 维度: {len(embed_sample)}")
    print(f"前 5 个值: {embed_sample[:5]}")

    # Step 4: 存入向量数据库
    db = DocArrayInMemorySearch.from_documents(docs, embeddings)
    print("\n[Step 3] 向量数据库已创建")

    # Step 5: 相似度搜索
    query = "Please suggest an item with sun protection"
    similar_docs = db.similarity_search(query)
    print(f"\n[Step 4] 相似度搜索结果（{len(similar_docs)} 条）:")
    for i, doc in enumerate(similar_docs[:2]):
        print(f"  [{i+1}] {doc.page_content[:80]}...")

    # Step 6: 创建 Retriever
    retriever = db.as_retriever()

    # Step 7: 组装 RetrievalQA Chain
    llm = ChatOpenAI(temperature=0.0, model=LLM_MODEL)
    qa = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        verbose=True
    )

    # Step 8: 提问
    print("\n[Step 5] RetrievalQA 回答:")
    answer = qa.invoke(
        "List all items with sun protection in a markdown table and summarize each one."
    )
    print(answer["result"])


# ── 3. 不同 chain_type 对比 ───────────────────────────────────────────────────

def demo_chain_types():
    print("\n" + "=" * 60)
    print("3. chain_type 选项说明")
    print("=" * 60)

    info = """
    chain_type 选项（处理多文档策略）:

    ┌─────────────┬────────────────────────────┬──────────────┬──────────────┐
    │ 策略         │ 原理                        │ 优点          │ 缺点          │
    ├─────────────┼────────────────────────────┼──────────────┼──────────────┤
    │ stuff       │ 全部塞入一个 prompt           │ 简单/便宜     │ 超长文档受限  │
    │ map_reduce  │ 逐块问答 → 汇总              │ 可处理大文档  │ 多次 LLM 调用 │
    │ refine      │ 逐块迭代累积答案             │ 整合信息好    │ 串行/速度慢   │
    │ map_rerank  │ 逐块答案+置信分 → 取最高     │ 精确事实问答  │ 多次 LLM 调用 │
    └─────────────┴────────────────────────────┴──────────────┴──────────────┘

    推荐：默认 stuff，大文档用 map_reduce
    """
    print(info)


# ── 主入口 ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    demo_quick_index()
    demo_step_by_step()
    demo_chain_types()
