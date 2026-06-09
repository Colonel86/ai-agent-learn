"""
LangChain Lesson 3: Chains
演示 LLMChain / SimpleSequentialChain / SequentialChain / Router Chain
"""

import os
from dotenv import load_dotenv, find_dotenv
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, PromptTemplate
from langchain.chains import LLMChain, SimpleSequentialChain, SequentialChain
from langchain.chains.router import MultiPromptChain
from langchain.chains.router.llm_router import LLMRouterChain, RouterOutputParser

load_dotenv(find_dotenv())
LLM_MODEL = "gpt-3.5-turbo"


# ── 1. LLMChain ───────────────────────────────────────────────────────────────

def demo_llm_chain():
    print("=" * 60)
    print("1. LLMChain（基础链）")
    print("=" * 60)

    llm = ChatOpenAI(temperature=0.9, model=LLM_MODEL)
    prompt = ChatPromptTemplate.from_template(
        "What is the best name to describe a company that makes {product}?"
    )
    chain = LLMChain(llm=llm, prompt=prompt)

    result = chain.invoke({"product": "Queen Size Sheet Set"})
    print(f"公司名建议: {result['text']}")


# ── 2. SimpleSequentialChain ──────────────────────────────────────────────────

def demo_simple_sequential():
    print("\n" + "=" * 60)
    print("2. SimpleSequentialChain（单输入单输出顺序链）")
    print("=" * 60)

    llm = ChatOpenAI(temperature=0.9, model=LLM_MODEL)

    chain_one = LLMChain(
        llm=llm,
        prompt=ChatPromptTemplate.from_template(
            "What is the best name to describe a company that makes {product}?"
        )
    )
    chain_two = LLMChain(
        llm=llm,
        prompt=ChatPromptTemplate.from_template(
            "Write a 20-word description for the following company: {company_name}"
        )
    )

    overall_chain = SimpleSequentialChain(
        chains=[chain_one, chain_two],
        verbose=True
    )

    result = overall_chain.invoke({"input": "Queen Size Sheet Set"})
    print(f"\n最终输出: {result['output']}")


# ── 3. SequentialChain（多输入多输出）────────────────────────────────────────

def demo_sequential_chain():
    print("\n" + "=" * 60)
    print("3. SequentialChain（多输入多输出）")
    print("=" * 60)

    llm = ChatOpenAI(temperature=0.0, model=LLM_MODEL)

    # Chain 1: 评论 → 英文翻译
    chain_one = LLMChain(
        llm=llm,
        prompt=ChatPromptTemplate.from_template(
            "Translate the following review to English:\n\n{Review}"
        ),
        output_key="English_Review"
    )

    # Chain 2: 英文评论 → 一句话摘要
    chain_two = LLMChain(
        llm=llm,
        prompt=ChatPromptTemplate.from_template(
            "Summarize the following review in 1 sentence:\n\n{English_Review}"
        ),
        output_key="summary"
    )

    # Chain 3: 检测原始评论语言
    chain_three = LLMChain(
        llm=llm,
        prompt=ChatPromptTemplate.from_template(
            "What language is the following review written in?\n\n{Review}"
        ),
        output_key="language"
    )

    # Chain 4: 用原语言写跟进回复
    chain_four = LLMChain(
        llm=llm,
        prompt=ChatPromptTemplate.from_template(
            "Write a follow-up response to the summary in the specified language.\n"
            "Summary: {summary}\nLanguage: {language}"
        ),
        output_key="followup_message"
    )

    overall_chain = SequentialChain(
        chains=[chain_one, chain_two, chain_three, chain_four],
        input_variables=["Review"],
        output_variables=["English_Review", "summary", "followup_message"],
        verbose=True
    )

    review = "Je suis très satisfait de ce produit. La qualité est excellente!"
    result = overall_chain.invoke({"Review": review})
    print(f"\n英文翻译: {result['English_Review']}")
    print(f"摘要: {result['summary']}")
    print(f"跟进回复: {result['followup_message']}")


# ── 4. Router Chain ───────────────────────────────────────────────────────────

def demo_router_chain():
    print("\n" + "=" * 60)
    print("4. Router Chain（路由到专业子链）")
    print("=" * 60)

    llm = ChatOpenAI(temperature=0, model=LLM_MODEL)

    # 各学科专家 prompt
    prompt_infos = [
        {
            "name": "physics",
            "description": "Good for answering questions about physics",
            "prompt_template": "You are an expert physics professor.\n\nQuestion: {input}"
        },
        {
            "name": "math",
            "description": "Good for answering math questions",
            "prompt_template": "You are an expert mathematician.\n\nQuestion: {input}"
        },
        {
            "name": "history",
            "description": "Good for answering history questions",
            "prompt_template": "You are an expert historian.\n\nQuestion: {input}"
        },
        {
            "name": "computer science",
            "description": "Good for answering computer science questions",
            "prompt_template": "You are an expert computer scientist.\n\nQuestion: {input}"
        },
    ]

    destination_chains = {}
    for p in prompt_infos:
        prompt = ChatPromptTemplate.from_template(p["prompt_template"])
        destination_chains[p["name"]] = LLMChain(llm=llm, prompt=prompt)

    default_chain = LLMChain(
        llm=llm,
        prompt=ChatPromptTemplate.from_template("{input}")
    )

    destinations_str = "\n".join(
        [f"{p['name']}: {p['description']}" for p in prompt_infos]
    )

    ROUTER_TEMPLATE = """Given a raw text input, select the model prompt best suited for it.
Available prompts:
{destinations}

Return a markdown JSON block:
```json
{{{{
    "destination": string \\ one of {{{destinations_names}}} or "DEFAULT"
    "next_inputs": string \\ the original or revised input
}}}}
```

Input: {{input}}
Output (include ```json):"""

    router_template = ROUTER_TEMPLATE.format(
        destinations=destinations_str,
        destinations_names=", ".join([p["name"] for p in prompt_infos])
    )

    router_prompt = PromptTemplate(
        template=router_template,
        input_variables=["input"],
        output_parser=RouterOutputParser(),
    )
    router_chain = LLMRouterChain.from_llm(llm, router_prompt)

    chain = MultiPromptChain(
        router_chain=router_chain,
        destination_chains=destination_chains,
        default_chain=default_chain,
        verbose=True
    )

    questions = [
        "What is black body radiation?",
        "What is 2 + 2?",
        "Why does every cell in our body contain DNA?",
    ]
    for q in questions:
        print(f"\n问题: {q}")
        result = chain.invoke({"input": q})
        print(f"回答: {result['text'][:200]}...")


# ── 主入口 ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    demo_llm_chain()
    demo_simple_sequential()
    demo_sequential_chain()
    demo_router_chain()
