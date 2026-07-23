"""L7 · PII 护栏 —— **严格照课程**:Microsoft Presidio + 自定义 PIIDetector(真 guardrails)。

Presidio 是本地开源的 PII 引擎(不需要任何 key):
  - AnalyzerEngine    识别文本里的 PII 实体(PERSON / PHONE_NUMBER / EMAIL_ADDRESS ...)
  - AnonymizerEngine  把识别到的 PII 打码

`detect_pii` / `PIIDetector` 逐字照课程 Lesson_7。额外补了 `anonymize_pii` + 让 PIIDetector 在
命中时带上 `fix_value`(打码后的文本),这样 on_fail=FIX 能像课程 hub DetectPII 那样"脱敏"输出
——用的仍是课程自己引入的 Presidio anonymizer,不是另造轮子。

引擎懒加载(第一次用到才建,避免 import 就加载 spacy 模型)。
"""

from typing import Any, Dict, Optional

from guardrails import Guard, OnFailAction, register_validator
from guardrails.validator_base import (
    FailResult,
    PassResult,
    ValidationResult,
    Validator,
)

_ANALYZER = None
_ANONYMIZER = None


def _engines():
    global _ANALYZER, _ANONYMIZER
    if _ANALYZER is None:
        from presidio_analyzer import AnalyzerEngine
        from presidio_anonymizer import AnonymizerEngine
        _ANALYZER = AnalyzerEngine()
        _ANONYMIZER = AnonymizerEngine()
    return _ANALYZER, _ANONYMIZER


def detect_pii(text: str, entities=("PERSON", "PHONE_NUMBER")) -> list[str]:
    """返回文本里命中的 PII 实体类型列表(逐字照课程)。"""
    analyzer, _ = _engines()
    result = analyzer.analyze(text, language="en", entities=list(entities))
    return [entity.entity_type for entity in result]


def anonymize_pii(text: str, entities=("PERSON", "PHONE_NUMBER", "EMAIL_ADDRESS")) -> str:
    """用 Presidio anonymizer 把 PII 打码后返回(供 on_fail=FIX 用)。"""
    analyzer, anonymizer = _engines()
    analysis = analyzer.analyze(text, language="en", entities=list(entities))
    return anonymizer.anonymize(text=text, analyzer_results=analysis).text


@register_validator(name="pii_detector", data_type="string")
class PIIDetector(Validator):
    """命中 PII 即 Fail;fix_value 为打码后的文本(支持 EXCEPTION / REFRAIN / FIX)。"""

    def __init__(self, entities=("PERSON", "PHONE_NUMBER"), **kwargs):
        self.entities = tuple(entities)
        super().__init__(**kwargs)

    def _validate(self, value: Any, metadata: Dict[str, Any] = {}) -> ValidationResult:
        detected_pii = detect_pii(value, self.entities)
        if detected_pii:
            return FailResult(
                error_message=f"PII detected: {', '.join(detected_pii)}",
                metadata={"detected_pii": detected_pii},
                fix_value=anonymize_pii(value),
            )
        return PassResult(message="No PII detected")


def build_pii_guard(on_fail=OnFailAction.EXCEPTION,
                    entities=("PERSON", "PHONE_NUMBER")) -> Guard:
    return Guard(name="pii_guard").use(PIIDetector(entities=entities, on_fail=on_fail))
