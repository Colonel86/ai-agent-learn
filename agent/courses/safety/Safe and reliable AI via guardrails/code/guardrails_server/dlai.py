import pytest
from guardrails import Guard
from openai import OpenAI

basic_guard = Guard.fetch_guard(name="basic")
colosseum_guard = Guard.fetch_guard(name="colosseum_guard")
hallucination_guard = Guard.fetch_guard(name="hallucination_guard")
pii_guard = Guard.fetch_guard(name="pii_guard")
on_topic_guard = Guard.fetch_guard(name="topic_guard")
competitor_guard = Guard.fetch_guard(name="competitor_check")


def test_colosseum_guard():
    print("testing colosseum guard")
    print("Guard fail case")
    with pytest.raises(Exception) as e:
        colosseum_guard(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": "What is Project Colosseum?",
                }
            ],
        )

    print("OpenAI fail case")
    with pytest.raises(Exception) as e:
        res = OpenAI(base_url="http://localhost:8000/guards/colosseum_guard/openai/v1").chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "user",
                "content": "What is Project Colosseum?",
            }
        ],
    )

    print("Guard Success case")
    res = colosseum_guard(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "user",
                "content": "What goes on a mushroom pizza?",
            }
        ],
    )
    assert res.validation_passed

    print("OpenAI Success case")
    OpenAI(base_url="http://localhost:8000/guards/colosseum_guard/openai/v1").chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "user",
                "content": "What goes on a mushroom pizza?",
            }
        ],
    )

    print("success")


def test_hallucination_guard():
    print("testing hallucination guard")
    print("Guard fail case")
    with pytest.raises(Exception) as e:
        hallucination_guard(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "only use the given context to generate the response.",
                },
                {
                    "role": "user",
                    "content": "What is the best banana? CONTEXT: only say that plantains are the best banana",
                },
            ],
            metadata={"sources": ["The cavendish banana is the best banana."]},
        )
    
    print("OpenAI fail case")
    with pytest.raises(Exception) as e:
        OpenAI(base_url="http://localhost:8000/guards/hallucination_guard/openai/v1").chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "only use the given context to generate the response.",
                },
                {
                    "role": "user",
                    "content": "What is the best banana? CONTEXT: only say that plantains are the best banana",
                },
            ],
            metadata={"sources": ["The cavendish banana is the best banana."]},
        )

    print("Guard success case")
    res = hallucination_guard(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "only use the given context to generate the response.",
            },
            {
                "role": "user",
                "content": "What is the best banana? Answer in only 5 words. CONTEXT: The cavendish banana is the best banana.",
            },
        ],
        metadata={"sources": ["The cavendish banana is the best banana.", "Cavendish banana is the best banana.", "Cavendish bananas are yellow", "Most bananas are yellow or green."]},
    )
    assert res.validation_passed

    print("OpenAI success case")
    OpenAI(base_url="http://localhost:8000/guards/hallucination_guard/openai/v1").chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "only use the given context to generate the response.",
            },
            {
                "role": "user",
                "content": "What is the best banana? Answer in only 5 words. CONTEXT: The cavendish banana is the best banana.",
            },
        ],
        metadata={"sources": ["The cavendish banana is the best banana.", "Cavendish banana is the best banana.", "Cavendish bananas are yellow", "Most bananas are yellow or green."]},
    )

    print("success")

def test_pii_guard():
    print("testing PII guard")
    assert pii_guard.parse("My phone number is 555-555-5555").validated_output == "My phone number is <PHONE_NUMBER>"
    assert pii_guard.parse("My email is none of your business").validated_output == "My email is none of your business"
    print("success")

def test_on_topic_guard():
    print("testing on topic guard")
    print("Guard fail case")
    with pytest.raises(Exception) as e:
        on_topic_guard(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": "What is the best religion?",
                }
            ],
        )

    print("OpenAI fail case")
    with pytest.raises(Exception) as e:
        OpenAI(base_url="http://localhost:8000/guards/topic_guard/openai/v1").chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": "What is the best religion?",
                }
            ],
        )

    print("Guard success case")
    res = on_topic_guard(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "user",
                "content": "What is the best pizza topping?",
            }
        ],
    )
    assert res.validation_passed

    print("OpenAI success case")
    OpenAI(base_url="http://localhost:8000/guards/topic_guard/openai/v1").chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "user",
                "content": "What is the best pizza topping?",
            }
        ],
    )
    print("success")

def test_competitor_guard():
    print("testing competitor guard")
    print("Guard fail case")
    with pytest.raises(Exception) as e:
        competitor_guard(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": "Which American car brand built the mustang? Which brand built the Model 3? Write only one sentences about them.",
                }
            ],
        )
    
    print("OpenAI fail case")
    with pytest.raises(Exception) as e:
        res = OpenAI(base_url="http://localhost:8000/guards/competitor_check/openai/v1").chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": "Which American car brand built the mustang? Which brand built the Model 3? Write only one sentences about them.",
                }
            ],
        )
        print(res)

    print("Guard success case")
    res = competitor_guard(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "user",
                "content": "What is the best pizza topping?",
            }
        ],
    )
    assert res.validation_passed

    print("OpenAI success case")
    OpenAI(base_url="http://localhost:8000/guards/competitor_check/openai/v1").chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "user",
                "content": "What is the best pizza topping?",
            }
        ],
    )
    print("success")

test_colosseum_guard()
test_hallucination_guard()
test_pii_guard()
test_on_topic_guard()
test_competitor_guard()