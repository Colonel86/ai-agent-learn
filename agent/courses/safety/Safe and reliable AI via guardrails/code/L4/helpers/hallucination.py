"""L4 · 用 NLI 检测幻觉 —— **严格照抄课程的 HallucinationValidation validator**。

这是真 guardrails 的自定义 Validator,内部用:
  - SentenceTransformer('all-MiniLM-L6-v2')  对句子/来源做 embedding,挑相关来源(cos>0.8)
  - HuggingFace NLI 模型 'GuardrailsAI/finetuned_nli_provenance'  判断"句子是否被来源蕴含"
  - nltk.sent_tokenize  把回答拆成句子,逐句判定

只要有一句不被任何相关来源蕴含,就判为幻觉(FailResult)。逻辑与课程 Lesson_4 完全一致,
未做任何等价替代。本课不需要 guardrails 服务器,validator 在进程内直接跑。

首次运行会从 HuggingFace 下载 NLI 模型与 all-MiniLM(约几十 MB~百 MB),并确保 nltk 的
punkt_tab 分句数据就绪(nltk.download)。国内可 export HF_ENDPOINT=https://hf-mirror.com。
"""

import os
from typing import Dict, List, Optional

import numpy as np
import nltk
from sentence_transformers import SentenceTransformer
from transformers import pipeline

from guardrails.validator_base import (
    FailResult,
    PassResult,
    ValidationResult,
    Validator,
    register_validator,
)


def ensure_punkt() -> None:
    """确保 nltk 分句数据可用(课程假设 notebook 环境已装;这里主动补一次)。"""
    # nltk>=3.9 只需 punkt_tab;旧 punkt 在本机网络下必下载失败,不再尝试
    for pkg in ("punkt_tab",):
        try:
            nltk.data.find(f"tokenizers/{pkg}")
            return
        except LookupError:
            try:
                nltk.download(pkg, quiet=True)
                nltk.data.find(f"tokenizers/{pkg}")
                return
            except Exception:
                continue


@register_validator(name="hallucination_detector", data_type="string")
class HallucinationValidation(Validator):
    """与课程 Lesson_4 逐字一致的幻觉校验器。"""

    def __init__(
        self,
        embedding_model: Optional[str] = None,
        entailment_model: Optional[str] = None,
        sources: Optional[List[str]] = None,
        **kwargs,
    ):
        if embedding_model is None:
            embedding_model = "all-MiniLM-L6-v2"
        self.embedding_model = SentenceTransformer(embedding_model)

        self.sources = sources

        if entailment_model is None:
            entailment_model = "GuardrailsAI/finetuned_nli_provenance"
        self.nli_pipeline = pipeline("text-classification", model=entailment_model)

        super().__init__(**kwargs)

    def validate(
        self, value: str, metadata: Optional[Dict[str, str]] = None
    ) -> ValidationResult:
        # Split the text into sentences
        sentences = self.split_sentences(value)

        # Find the relevant sources for each sentence
        relevant_sources = self.find_relevant_sources(sentences, self.sources)

        entailed_sentences = []
        hallucinated_sentences = []
        for sentence in sentences:
            # Check if the sentence is entailed by the sources
            is_entailed = self.check_entailment(sentence, relevant_sources)
            if not is_entailed:
                hallucinated_sentences.append(sentence)
            else:
                entailed_sentences.append(sentence)

        if len(hallucinated_sentences) > 0:
            return FailResult(
                error_message=f"The following sentences are hallucinated: {hallucinated_sentences}",
            )

        return PassResult()

    def split_sentences(self, text: str) -> List[str]:
        if nltk is None:
            raise ImportError(
                "This validator requires the `nltk` package. "
                "Install it with `pip install nltk`, and try again."
            )
        return nltk.sent_tokenize(text)

    def find_relevant_sources(self, sentences: List[str], sources: List[str]) -> List[str]:
        source_embeds = self.embedding_model.encode(sources)
        sentence_embeds = self.embedding_model.encode(sentences)

        relevant_sources = []

        for sentence_idx in range(len(sentences)):
            # Find the cosine similarity between the sentence and the sources
            sentence_embed = sentence_embeds[sentence_idx, :].reshape(1, -1)
            cos_similarities = np.sum(np.multiply(source_embeds, sentence_embed), axis=1)
            # Find the top 5 sources that are most relevant to the sentence that
            # have a cosine similarity greater than 0.8
            top_sources = np.argsort(cos_similarities)[::-1][:5]
            top_sources = [i for i in top_sources if cos_similarities[i] > 0.8]

            # Return the sources that are most relevant to the sentence
            relevant_sources.extend([sources[i] for i in top_sources])

        return relevant_sources

    def check_entailment(self, sentence: str, sources: List[str]) -> bool:
        for source in sources:
            output = self.nli_pipeline({"text": source, "text_pair": sentence})
            if output["label"] == "entailment":
                return True
        return False


def make_nli_pipeline(entailment_model: str = "GuardrailsAI/finetuned_nli_provenance"):
    """课程里单独演示 NLI pipeline 用;与 validator 内部同一个模型。"""
    return pipeline("text-classification", model=entailment_model)
