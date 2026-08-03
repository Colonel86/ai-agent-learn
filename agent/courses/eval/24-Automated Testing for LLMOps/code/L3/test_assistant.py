"""L2 · per-commit 评估: 硬规则断言 (关键词出现 / 拒答语出现)。

本地化说明: 课程原版 evaluate_refusal 调 assistant_chain 时把
human_template 和 system_message 传反了(位置参数顺序 bug), 这里已修正。
"""

from app import assistant_chain, system_message


def eval_expected_words(system_message, question, expected_words):
    assistant = assistant_chain(system_message)
    answer = assistant.invoke({"question": question})
    print(answer)
    assert any(word in answer.lower() for word in expected_words), (
        f"Expected the assistant questions to include '{expected_words}', but it did not"
    )


def evaluate_refusal(system_message, question, decline_response):
    assistant = assistant_chain(system_message)
    answer = assistant.invoke({"question": question})
    print(answer)
    assert decline_response.lower() in answer.lower(), (
        f"Expected the bot to decline with '{decline_response}' got {answer}"
    )


def test_science_quiz():
    question = "Generate a quiz about science."
    expected_subjects = ["davinci", "telescope", "physics", "curie"]
    eval_expected_words(system_message, question, expected_subjects)


def test_geography_quiz():
    question = "Generate a quiz about geography."
    expected_subjects = ["paris", "france", "louvre"]
    eval_expected_words(system_message, question, expected_subjects)


def test_refusal_rome():
    question = "Help me create a quiz about Rome"
    decline_response = "I'm sorry"
    evaluate_refusal(system_message, question, decline_response)
