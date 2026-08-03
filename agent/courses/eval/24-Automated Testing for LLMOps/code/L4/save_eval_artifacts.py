"""L4 · 评估报告工件: 数据集逐条过 judge(决策+解释), 产出 HTML 报告。

课程原版在 CircleCI 上用 store_artifacts 保存报告; 本地直接落盘
quiz_eval_report.html, 概念一致 —— 评估不只出 pass/fail, 还要出可读工件。
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from app import assistant_chain, quiz_bank
from local_stack import make_llm

LESSON_DIR = Path(__file__).resolve().parent

eval_system_prompt = """You are an assistant that evaluates how well the quiz assistant
    creates quizzes for a user by looking at the set of facts available to the assistant.
    Your primary concern is making sure that ONLY facts available are used. Helpful quizzes only contain facts in the
    test set"""

eval_user_message = """You are evaluating a generated quiz based on the question bank that the assistant uses to create the quiz.
  Here is the data:
    [BEGIN DATA]
    ************
    [Question Bank]: {context}
    ************
    [Quiz]: {agent_response}
    ************
    [END DATA]

## Steps to make a decision
1. Review the question bank carefully. These are the only facts the quiz can reference
2. Compare the information in the quiz to the question bank.
3. Ignore differences in grammar or punctuation

## Additional rules
- Output an explanation of whether the quiz only references information in the context.
- Make the explanation brief only include a summary of your reasoning for the decision.
- Include a clear "Yes" or "No" as the first paragraph.
- Reference facts from the quiz bank if the answer is yes

Separate the decision and the explanation. For example:

************
Decision: <Y>
************
Explanation: <Explanation>
************
"""

dataset = [
    {"input": "I'm trying to learn about science, can you give me a quiz to test my knowledge"},
    {"input": "I'm an geography expert, give a quiz to prove it?"},
    {"input": "Quiz me about Italy"},
]


def create_eval_chain():
    eval_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", eval_system_prompt),
            ("human", eval_user_message),
        ]
    )
    return eval_prompt | make_llm() | StrOutputParser()


def main():
    assistant = assistant_chain()
    judge = create_eval_chain()
    rows = []
    for row in dataset:
        question = row["input"]
        answer = assistant.invoke({"question": question})
        verdict = judge.invoke({"context": quiz_bank, "agent_response": answer})
        rows.append({"input": question, "quiz": answer, "judge": verdict})
        decision = next((l for l in verdict.splitlines() if "Decision" in l), verdict.strip().splitlines()[0])
        print(f"  [{question[:40]}...] {decision.strip()[:60]}")

    df = pd.DataFrame(rows)
    report = LESSON_DIR / "quiz_eval_report.html"
    table = df.to_html(escape=True)
    report.write_text(
        "<meta charset='utf-8'><style>td{text-align:left;white-space:pre-wrap;"
        "vertical-align:top;font-family:monospace;font-size:13px}</style>" + table
    )
    print(f"\n  [报告工件已保存: {report}]")
    return report


if __name__ == "__main__":
    main()
