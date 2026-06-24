# Plan: Real-Time Smart-Money Signal (Mentis Skill)

> A worked example showing the NFR gates filled out with **evidence linkage** for a **T2**
> (production, user-facing) feature. Use as the reference for what "good" looks like.

## Feature

A Mentis Skill `smart_money_signal` that, given a token, pulls large perp/on-chain
positions from market-data providers, runs an LLM-assisted synthesis, and streams a
**structured signal + market-structure read** back to the user in chat. Read-only with
respect to funds (no trades); it persists a prediction record for later tracking.

## Non-Functional Context  *(from spec)*

- **Criticality tier:** T2 (user-facing, financial output) → gates G1–G7 all required.
- **Expected load:** ~5 RPS peak; bursty; long-tail per request (multi-provider fan-out + LLM).
- **Availability SLO:** 99.5% (best-effort during third-party data-provider outages).
- **Latency:** TTFT < 2s; end-to-end p99 < 8s.
- **Data sensitivity:** public market data + the user's queried token; no PII; user wallet must not leave the system.
- **Cost budget:** ≤ $0.04 / request.
- **Trust boundary:** provider responses (token names/metadata) are untrusted; the only side effect is a prediction-log write.

## Technical Approach

LangGraph subgraph with 5 nodes: resolve token → fetch positions (parallel, multi-provider)
→ fetch price/market-structure → LLM synthesis (structured output) → stream. Data providers
sit behind a `MarketDataProvider` abstraction; LLM calls go through the existing gateway.
The skill is registered via config — no core orchestration changes.

## Constitution Check — NFR Gates  *(tier T2 → all required)*

| Gate | Status | Evidence (task / test / manifest) — or N/A reason |
|------|--------|----------------------------------------------------|
| **G1 Performance** | Addressed | SLO TTFT<2s / p99<8s asserted by `tests/perf/test_signal_latency.py::test_p99`. Streaming `T010`; parallel provider fetch via `asyncio.gather` `T011`; prefix-cache on synthesis system prompt `T012`. |
| **G2 Availability** | Addressed | timeout+retry+circuit-breaker wrapper `core/resilience.py` `T020`; provider failover in `MarketDataProvider` `T021` (`tests/resilience/test_provider_failover.py`); cached-data fallback on total outage `T021`. Manifest `deploy/mentis-skill.yaml`: replicas 3, liveness+readiness probes. Side-effect (prediction-log write) is idempotent `T022` (`test_prediction_log_idempotent`). |
| **G3 Observability** | Addressed | LangSmith root trace + child spans per provider fetch & LLM call `T030`; online signal-quality metric `T031`; SLO alert rules in `deploy/alerts.yaml`. Logs carry `trace_id`. |
| **G4 Security** | Addressed | Provider text (token names/metadata) sanitized + delimited before prompt assembly `T040` (`test_prompt_injection_resistance`); output guardrail enforces disclaimer + no-personalized-advice `T041` (`test_output_guardrail`); secret scan in CI `T042`; user wallet never sent to providers (egress allow-list) `T040`. |
| **G5 Cost** | Addressed | Per-request token ceiling + abort `T050` (`test_token_budget`); prefix/semantic cache `T012`/`T051`; routing table — small model for parse/extract, large only for final synthesis `T052`; per-request cost metric published (G3). Measured p50 $0.021, p99 $0.038 < $0.04. |
| **G6 Evaluation** | Addressed | Walk-forward backtest harness, **no look-ahead** `T060`; versioned golden set `eval/golden/smart_money/*.json` `T061`; CI regression gate `ci/eval_gate.py` blocks on signal-precision drop > 3pp; quality SLO = 7d precision ≥ 80%. |
| **G7 Maintainability** | Addressed | Skill registered via `skills/smart_money_signal.yaml` — **zero core-file edits** (diff check in `ci/no_core_change.py`) `T070`; provider behind `MarketDataProvider`, no vendor SDK in skill code `T071`; synthesis prompt versioned in prompt registry `T072`; complexity + coverage gates in CI. |

### NFR Trade-offs  *(deliberate, accepted — not violations)*

- **Availability vs cost/complexity:** one primary data provider + one fallback (not three).
  Accept slightly lower availability to control cost and code surface; revisit if the
  provider's SLA proves insufficient. (G2)
- **Cost vs quality:** final synthesis uses the larger model to meet the 80% precision SLO;
  offset by routing parse/extraction to the small model, keeping p99 cost under budget. (G5/G6)
- **Latency ceiling:** p99 of 8s is loose because deep analysis fans out to multiple providers;
  mitigated by streaming so perceived latency (TTFT < 2s) stays good. (G1)

## Task Breakdown  *(IDs referenced as evidence above)*

- `T001` Resolve-token node; `T002` provider fetch nodes; `T003` price/structure node; `T004` LLM synthesis (structured output); `T005` streaming output node.
- **G1:** `T010` token streaming · `T011` parallel provider fetch · `T012` prefix cache.
- **G2:** `T020` resilience wrapper · `T021` provider failover + cached fallback · `T022` idempotent prediction-log write.
- **G3:** `T030` tracing instrumentation · `T031` online quality metric · alerts.
- **G4:** `T040` sanitize/delimit + egress allow-list · `T041` output guardrail · `T042` CI secret scan.
- **G5:** `T050` token budget + abort · `T051` semantic cache · `T052` model routing table.
- **G6:** `T060` walk-forward backtest (no look-ahead) · `T061` golden set + CI regression gate.
- **G7:** `T070` config-driven skill registration · `T071` provider abstraction · `T072` prompt versioning.

## Complexity Tracking

None. The capability is added via a config file with zero core-orchestration changes
(satisfies Principle IV and G7); no constitutional violations to justify.
