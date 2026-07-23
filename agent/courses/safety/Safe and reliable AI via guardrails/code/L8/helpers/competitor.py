"""L8 · 竞品检测 —— **严格照抄课程的 CheckCompetitorMentions validator**。

真 guardrails 的自定义 Validator,三层查竞品(逐字照课程 Lesson_8):
  1. 精确匹配:整词命中竞品名(regex \b...\b)
  2. NER 抽实体:用 dslim/bert-base-NER 抽出文本里的命名实体
  3. 向量相似:实体 embedding 与竞品 embedding 余弦相似度 ≥ 0.6 也算命中
只要任一层命中即 FailResult。

模型懒加载(第一次用到才建),避免 import 就下 NER/all-MiniLM。
"""

import re
from typing import List, Optional

import numpy as np
from guardrails import Guard, OnFailAction, register_validator
from guardrails.validator_base import (
    FailResult,
    PassResult,
    ValidationResult,
    Validator,
)


@register_validator(name="check_competitor_mentions", data_type="string")
class CheckCompetitorMentions(Validator):
    def __init__(self, competitors: List[str], **kwargs):
        self.competitors = competitors
        self.competitors_lower = [comp.lower() for comp in competitors]

        # 懒加载:NER pipeline + SentenceTransformer(第一次 validate 时才真正建)
        self._ner = None
        self._sentence_model = None
        self._competitor_embeddings = None

        self.similarity_threshold = 0.6
        super().__init__(**kwargs)

    # -- 懒加载模型 --
    def _ensure_models(self):
        if self._ner is None:
            from transformers import (
                AutoModelForTokenClassification,
                AutoTokenizer,
                pipeline,
            )
            tokenizer = AutoTokenizer.from_pretrained("dslim/bert-base-NER")
            model = AutoModelForTokenClassification.from_pretrained("dslim/bert-base-NER")
            self._ner = pipeline("ner", model=model, tokenizer=tokenizer)
        if self._sentence_model is None:
            from sentence_transformers import SentenceTransformer
            self._sentence_model = SentenceTransformer("all-MiniLM-L6-v2")
            self._competitor_embeddings = self._sentence_model.encode(self.competitors)

    def exact_match(self, text: str) -> List[str]:
        text_lower = text.lower()
        matches = []
        for comp, comp_lower in zip(self.competitors, self.competitors_lower):
            if comp_lower in text_lower:
                if re.search(r"\b" + re.escape(comp_lower) + r"\b", text_lower):
                    matches.append(comp)
        return matches

    def extract_entities(self, text: str) -> List[str]:
        ner_results = self._ner(text)
        entities = []
        current_entity = ""
        for item in ner_results:
            if item["entity"].startswith("B-"):
                if current_entity:
                    entities.append(current_entity.strip())
                current_entity = item["word"]
            elif item["entity"].startswith("I-"):
                current_entity += " " + item["word"]
        if current_entity:
            entities.append(current_entity.strip())
        return entities

    def vector_similarity_match(self, entities: List[str]) -> List[str]:
        if not entities:
            return []
        from sklearn.metrics.pairwise import cosine_similarity
        entity_embeddings = self._sentence_model.encode(entities)
        similarities = cosine_similarity(entity_embeddings, self._competitor_embeddings)
        matches = []
        for i, _entity in enumerate(entities):
            max_similarity = np.max(similarities[i])
            if max_similarity >= self.similarity_threshold:
                most_similar_competitor = self.competitors[np.argmax(similarities[i])]
                matches.append(most_similar_competitor)
        return matches

    def validate(self, value: str, metadata: Optional[dict] = None) -> ValidationResult:
        self._ensure_models()

        # 1) 精确匹配
        exact_matches = self.exact_match(value)
        if exact_matches:
            return FailResult(
                error_message=f"Your response directly mentions competitors: "
                f"{', '.join(exact_matches)}"
            )

        # 2) NER 抽实体
        entities = self.extract_entities(value)

        # 3) 向量相似
        similarity_matches = self.vector_similarity_match(entities)

        # 4) 汇总
        all_matches = list(set(exact_matches + similarity_matches))
        if all_matches:
            return FailResult(
                error_message=f"Your response mentions competitors: {', '.join(all_matches)}"
            )
        return PassResult()

    # guardrails 0.5.x 自定义 validator 用 _validate 或 validate 皆可;这里用 validate(照课程)


def build_competitor_guard(competitors=None,
                           on_fail=OnFailAction.EXCEPTION) -> Guard:
    if competitors is None:
        competitors = ["Pizza by Alfredo"]
    return Guard(name="competitor_check").use(
        CheckCompetitorMentions(competitors=competitors, on_fail=on_fail)
    )
