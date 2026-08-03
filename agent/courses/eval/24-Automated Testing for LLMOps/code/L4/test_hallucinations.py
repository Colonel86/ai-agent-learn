"""L4 · 幻觉检测: judge 对照 quiz bank 检查 quiz 是否编造事实。

本地化反向设计说明: 课程原版让助手对 "books" 出题, 依赖 gpt-3.5 会**真的幻觉**
出一份 books quiz 再由 judge 抓住。DeepSeek 遵循 prompt 规则直接拒答(第一道防线生效),
叙事失效 —— 因此幻觉样本改为固定 fixture, 使 judge 行为可确定性验证:
  - 正样本: 助手真实生成的 geography quiz -> judge 必须 Y
  - 负样本: 手工构造的含库外事实的 quiz  -> judge 必须 N
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from app import assistant_chain, quiz_bank
from local_stack import make_llm


def create_eval_chain(context, agent_response):
    eval_system_prompt = """You are an assistant that evaluates how well the quiz assistant
    creates quizzes for a user by looking at the set of facts available to the assistant.
    Your primary concern is making sure that ONLY facts available are used. Helpful quizzes only contain facts in the
    test set"""

    eval_user_message = f"""You are evaluating a generated quiz based on the context that the assistant uses to create the quiz.
  Here is the data:
    [BEGIN DATA]
    ************
    [Question Bank]: {context}
    ************
    [Quiz]: {agent_response}
    ************
    [END DATA]

Compare the content of the submission with the question bank using the following steps

1. Review the question bank carefully. These are the only facts the quiz can reference
2. Compare the quiz to the question bank.
3. Ignore differences in grammar or punctuation
4. If a fact is in the quiz, but not in the question bank the quiz is bad.

Remember, the quizzes need to only include facts the assistant is aware of. It is dangerous to allow made up facts.

Output Y if the quiz only contains facts from the question bank, output N if it contains facts that are not in the question bank.
Output only the single letter Y or N, nothing else.
"""
    eval_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", eval_system_prompt),
            ("human", eval_user_message),
        ]
    )
    return eval_prompt | make_llm() | StrOutputParser()


@pytest.fixture
def hallucinated_quiz():
    """含库外事实的坏 quiz: books 主题完全不在 quiz bank 里"""
    return """Question 1:#### Who wrote the novel 'One Hundred Years of Solitude'?

Question 2:#### In what year was 'Don Quixote' by Cervantes first published?

Question 3:#### Which book is considered the first modern detective novel?"""


def test_judge_passes_grounded_quiz():
    assistant = assistant_chain()
    result = assistant.invoke({"question": "Give me a quiz about geography."})
    print(result)
    eval_agent = create_eval_chain(quiz_bank, result)
    eval_response = eval_agent.invoke({})
    print(eval_response)
    assert eval_response.strip() == "Y"


def test_judge_catches_hallucinated_quiz(hallucinated_quiz):
    print(hallucinated_quiz)
    eval_agent = create_eval_chain(quiz_bank, hallucinated_quiz)
    eval_response = eval_agent.invoke({})
    print(eval_response)
    assert eval_response.strip() == "N"
