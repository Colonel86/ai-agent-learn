# Availability & Resilience

**Gate:** G2   **Required tiers:** T2
**Applies when:** the feature has external dependencies (LLM/tools/state) or serves live traffic.

> An agent is only as available as its weakest dependency: the LLM provider, flaky tool
> APIs, and the state backend. Design for graceful degradation, not just uptime.

## Required (the gate)
- LLM provider/region failover; graceful degradation to a smaller model.
- Timeouts, retries (backoff+jitter), circuit breakers, bulkhead isolation on every external call.
- Per-dependency fallback (skip / partial result / cached data — never hard-fail).
- Workflow durability & resumability (checkpointing / durable execution).
- Idempotent side effects (exactly-once for messages, trades, writes).
- Deep health checks (verify dependency connectivity) + a stated availability SLO.

## Patterns
- Failover: gateway (LiteLLM) with health checks + ordered fallback providers/models.
- Resilience: circuit breaker per dependency; bulkheads isolate one failing tool from the rest.
- Durability: LangGraph checkpointer (Postgres/Redis) or Temporal — crashed runs resume from last step.
- Idempotency: idempotency keys + dedup on all side-effecting actions; safe to replay.
- Redundancy: >=2 stateless replicas; any worker resumes any run; state store itself HA.
- Deploy safety: rolling/blue-green/canary + instant rollback; never deploy an agent that fails evals (G6).
- Safe-fail: when uncertain or a check fails, refuse/escalate to human (G4).

## Anti-patterns
- Single LLM provider with no fallback.
- Retrying a side-effecting action without an idempotency key.
- Restarting long runs from scratch after a crash.
- Shallow health checks ("process alive") that miss dependency outages.

## Verification (fitness functions)
- Every external call has explicit timeout + retry + circuit breaker.
- Deployment manifest: replicas >= 2; liveness + readiness probes defined.
- Side-effecting handlers accept an idempotency key; a replay test proves safety.
- A failover/chaos test exists (primary LLM down -> falls back).
- Checkpointer configured; a crash-resume test exists.
