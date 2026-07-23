"""L6 · 话题护栏 —— **严格照抄课程的 ConstrainTopic validator**(local_config.py)。

真 guardrails 的自定义 Validator,内部用 HuggingFace 的 zero-shot 分类器
`facebook/bart-large-mnli` 判断文本是否命中"禁止话题"。命中即 FailResult。

分类器懒加载(第一次用到才建 pipeline),避免 import 时就下 1.6GB 模型。逻辑与课程
Lesson_6 / local_config.py 完全一致,未做等价替代。
"""

from typing import Optional

from guardrails import Guard, OnFailAction, register_validator
from guardrails.validator_base import (
    FailResult,
    PassResult,
    ValidationResult,
    Validator,
)
from transformers import pipeline

_CLASSIFIER = None


def get_classifier():
    """懒加载 zero-shot 分类器(与课程一致的 model / hypothesis_template / multi_label)。"""
    global _CLASSIFIER
    if _CLASSIFIER is None:
        _CLASSIFIER = pipeline(
            "zero-shot-classification",
            model="facebook/bart-large-mnli",
            hypothesis_template="This sentence above contains discussions of the folllowing topics: {}.",
            multi_label=True,
        )
    return _CLASSIFIER


def detect_topics(text: str, topics: list[str], threshold: float = 0.8) -> list[str]:
    result = get_classifier()(text, topics)
    return [
        topic
        for topic, score in zip(result["labels"], result["scores"])
        if score > threshold
    ]


@register_validator(name="constrain_topic", data_type="string")
class ConstrainTopic(Validator):
    def __init__(
        self,
        banned_topics: Optional[list[str]] = ["politics"],
        threshold: float = 0.8,
        **kwargs,
    ):
        self.topics = banned_topics
        self.threshold = threshold
        super().__init__(**kwargs)

    def _validate(
        self, value: str, metadata: Optional[dict[str, str]] = None
    ) -> ValidationResult:
        detected_topics = detect_topics(value, self.topics, self.threshold)
        if detected_topics:
            return FailResult(
                error_message="The text contains the following banned topics: "
                f"{detected_topics}",
            )
        return PassResult()


def build_topic_guard(banned_topics=None) -> Guard:
    """课程的 topic_guard:禁止 politics / automobiles,命中抛异常。"""
    if banned_topics is None:
        banned_topics = ["politics", "automobiles"]
    return Guard(name="topic_guard").use(
        ConstrainTopic(banned_topics=banned_topics, on_fail=OnFailAction.EXCEPTION)
    )
