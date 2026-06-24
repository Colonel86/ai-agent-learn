# Observability

**Gate:** G3   **Required tiers:** T1, T2
**Applies when:** any Agent code reaches production.

## Required (the gate)
- Distributed tracing across agent / LLM / tool spans (trace id propagated through sub-agents).
- Structured logging with correlation/trace IDs.
- Four golden signals (latency, traffic, errors, saturation) + token/cost metrics.
- Online quality evaluation — distinguish "failed" (error) from "answered, low quality".
- Alerting tied to SLO breaches.

## Patterns
- Tracing/eval: LangSmith / Phoenix; offline scoring: RAGAS / DeepEval.
- One root trace per request with a child span for every LLM and tool call.
- Sample a fraction of prod traffic for online quality scoring.

## Anti-patterns
- Logging only at the top level (no per-step spans) — impossible to localize failures.
- Treating a low-quality-but-successful response as a success with no signal.

## Verification (fitness functions)
- Each request emits a root trace; every LLM/tool call has a child span.
- Logs carry a correlation/trace id.
- Dashboards/metrics exist for p50/p99 latency, error rate, token cost.
- >=1 online quality metric is published per sampled request.
- Alert rules exist and reference the SLO.
