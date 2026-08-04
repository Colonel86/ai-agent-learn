"""TruLens 评估定义 (课程 helper.py 评估段的本地化版, provider 指向 DeepSeek)。

- RAG Triad: groundedness / answer relevance / context relevance
  (selector 挂在 RETRIEVAL span 的 QUERY_TEXT / RETRIEVED_CONTEXTS 上)
- GPA (Goal-Plan-Act): logical consistency / execution efficiency /
  plan adherence / plan quality (selector 挂 trace 级)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
from trulens.core import Feedback
from trulens.core.feedback.selector import Selector
from trulens.otel.semconv.trace import SpanAttributes

from local_stack import make_tru_provider

provider = make_tru_provider()
gpa_eval_provider = make_tru_provider()

f_groundedness = (
    Feedback(provider.groundedness_measure_with_cot_reasons, name="Groundedness")
    .on(
        {
            "source": Selector(
                span_type=SpanAttributes.SpanType.RETRIEVAL,
                span_attribute=SpanAttributes.RETRIEVAL.RETRIEVED_CONTEXTS,
                collect_list=True,
            )
        }
    )
    .on_output()
)

f_answer_relevance = (
    Feedback(provider.relevance_with_cot_reasons, name="Answer Relevance")
    .on_input()
    .on_output()
)

f_context_relevance = (
    Feedback(provider.context_relevance_with_cot_reasons, name="Context Relevance")
    .on(
        {
            "question": Selector(
                span_type=SpanAttributes.SpanType.RETRIEVAL,
                span_attribute=SpanAttributes.RETRIEVAL.QUERY_TEXT,
            )
        }
    )
    .on(
        {
            "context": Selector(
                span_type=SpanAttributes.SpanType.RETRIEVAL,
                span_attribute=SpanAttributes.RETRIEVAL.RETRIEVED_CONTEXTS,
                collect_list=False,
            )
        }
    )
    .aggregate(np.mean)
)

RAG_TRIAD = [f_groundedness, f_answer_relevance, f_context_relevance]

f_logical_consistency = Feedback(
    gpa_eval_provider.logical_consistency_with_cot_reasons, name="Logical Consistency"
).on({"trace": Selector(trace_level=True)})

f_execution_efficiency = Feedback(
    gpa_eval_provider.execution_efficiency_with_cot_reasons, name="Execution Efficiency"
).on({"trace": Selector(trace_level=True)})

f_plan_adherence = Feedback(
    gpa_eval_provider.plan_adherence_with_cot_reasons, name="Plan Adherence"
).on({"trace": Selector(trace_level=True)})

f_plan_quality = Feedback(
    gpa_eval_provider.plan_quality_with_cot_reasons, name="Plan Quality"
).on({"trace": Selector(trace_level=True)})

GPA = [f_logical_consistency, f_execution_efficiency, f_plan_adherence, f_plan_quality]
