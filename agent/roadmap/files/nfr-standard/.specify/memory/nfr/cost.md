# Cost & Efficiency

**Gate:** G5   **Required tiers:** T2 (recommended: T1)
**Applies when:** the feature makes LLM calls.

## Required (the gate)
- Token/cost budget per request and per loop iteration.
- Prompt/prefix caching and semantic caching where applicable.
- Model right-sizing & routing (cheap model for routing/classification; big model only for hard steps).
- Batching for non-realtime workloads.
- Cost monitoring and alerting.

## Patterns
- Cap loop iterations; fail/escalate past a budget ceiling.
- Route classify/route subtasks to small models via a routing table.
- Cache static system prompts and tool defs (prompt/prefix caching).
- Batch API for non-realtime jobs.

## Anti-patterns
- Using the largest model for routing/classification.
- Unbounded agent loops with no cost ceiling.

## Verification (fitness functions)
- A per-request token ceiling is enforced (truncate/abort + alert past it).
- Static prompts/tool defs use prompt/prefix caching.
- A model-routing table maps task class -> model.
- Cost metric per request is published; a budget alert is configured.
