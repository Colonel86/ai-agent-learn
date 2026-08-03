"""L4 · 数据集回归: 覆盖不同问法与支持/不支持的类目。"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import assistant_chain

dataset = [
    {
        "input": "I'm trying to learn about science, can you give me a quiz to test my knowledge",
        "response": "science",
        "subjects": ["davinci", "telescope", "physics", "curie"],
    },
    {
        "input": "I'm an geography expert, give a quiz to prove it?",
        "response": "geography",
        "subjects": ["paris", "france", "louvre"],
    },
    {
        "input": "Quiz me about Italy",
        "response": "geography",
        "subjects": ["rome", "alps", "sicily"],
    },
]


def test_on_dataset():
    assistant = assistant_chain()
    for row in dataset:
        user_input = row["input"]
        expected_category = row["response"]
        expected_subjects = row.get("subjects", None)
        answer = assistant.invoke({"question": user_input})
        assert expected_category.lower() in answer.lower(), (
            f"expected: {expected_category}, got {answer}"
        )
        if expected_subjects:
            assert any(s.lower() in answer.lower() for s in expected_subjects), (
                f"Expected the assistant questions to include '{expected_subjects}', but got {answer}"
            )
