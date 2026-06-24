#!/usr/bin/env bash
# setup-nfr-library.sh  (v2)
# Scaffolds the NFR (non-functional requirement) module library for an AI-agent
# project using spec-kit. Idempotent and non-destructive: never overwrites an
# existing file. Run from your repo root.
set -euo pipefail

NFR=".specify/memory/nfr"
TPL=".specify/templates"
SKILL=".claude/skills/nfr-architect"
mkdir -p "$NFR" "$TPL" "$SKILL"

# write_file <path> : writes stdin to <path> only if it does not already exist;
# consumes stdin either way so heredocs stay balanced.
write_file() {
  if [ -f "$1" ]; then echo "skip (exists): $1"; cat >/dev/null; else cat > "$1"; echo "created: $1"; fi
}

# --- gitignore safety check (team-sharing depends on these being committed) ---
if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  for p in .specify .claude; do
    if git check-ignore -q "$p" 2>/dev/null; then
      echo "WARNING: '$p' is gitignored — NFR files will NOT be shared with your team."
      echo "         Remove it from .gitignore (or add '!$p/**') before committing."
    fi
  done
fi

# ============================ README ============================
write_file "$NFR/README.md" << 'EOF'
# NFR Module Library

A reusable library of non-functional / cross-cutting architecture concerns for
AI-agent systems. Each concern is a module with four parts:

1. **A constitution gate** (`../constitution.md`) — the "must consider" rule, applied
   by criticality tier and checked during the Constitution Check in `/plan`.
2. **A playbook** (this folder) — the "how to do it" depth, loaded on demand.
3. **Template hooks** — spec-template elicits NFR inputs, plan-template gates them
   (with evidence linkage), tasks-template derives NFR tasks.
4. **CI enforcement** — `/speckit.analyze` + MR auto-review hard-block violations.

This is architecture **fitness functions**: the gates are the architectural
characteristics; the Verification section of each playbook is what CI checks.

## Modules
performance · availability · observability · security · cost · maintainability · evaluation

## Reference artifacts
- **Worked example plan** — `EXAMPLE-plan.md`: a real T2 feature with all 7 gates filled out + evidence. Shows what "good" looks like.
- **MR auto-review rule** — `mr-review-prompt.md`: checks a PR diff against each playbook's Verification (fitness functions). Wire it into your CI MR-review step.

## Adding a module
1. `cp _TEMPLATE.md <concern>.md` and fill it in (especially Verification).
2. Add a `G#` gate to `../constitution.md` with tier applicability.
3. Add the line to all three template snippets in this folder, then merge them.
One concern per module. Keep playbooks lean; push long code to companion files.
EOF

# ============================ TEMPLATE ============================
write_file "$NFR/_TEMPLATE.md" << 'EOF'
# <Concern Name>

**Gate:** G#   **Required tiers:** <T0/T1/T2>
**Applies when:** <when this concern is in scope>

## Required (the gate — every applicable plan must address these)
- <item>

## Patterns
<concrete patterns, decision rules, code snippets>

## Anti-patterns
<what NOT to do>

## Verification (fitness functions — what CI / review mechanically checks)
- <automatable assertion: lint/AST rule, manifest assertion, CI step, test presence>
EOF

# ============================ performance ============================
write_file "$NFR/performance.md" << 'EOF'
# Performance & Scalability

**Gate:** G1   **Required tiers:** T2
**Applies when:** the feature makes LLM/Agent calls, serves concurrent load, or has a user-facing latency expectation.

> Two distinct concerns: **latency** (how fast one request feels) and **throughput/scalability**
> (how many at once). Agent latency is dominated by sequential LLM calls; throughput by the
> LLM tier (GPU-bound self-hosted, or RPM/TPM-limited via API). (Resilience details: see G2.)

## Required (the gate)
- A latency SLO: time-to-first-token and end-to-end p99.
- Identify the bottleneck tier (orchestration / inference / tools) and optimize that.
- Fully async, non-blocking orchestration.
- Inference throughput (self-hosted) OR API rate-limit handling (TPM/RPM).
- Externalize agent state (stateless workers + checkpointer) for scale-out.
- Queue-based execution + backpressure for long-running tasks.

## Patterns
- Latency: stream tokens (cut perceived latency); prefix caching (cuts latency AND cost); parallelize independent sub-agent/tool calls (`asyncio.gather`) to cut end-to-end; speculative decoding (self-hosted); trim agent-loop iterations.
- Throughput/scale: vLLM/SGLang continuous batching; quantization; LiteLLM multi-key/region/provider; token-bucket limiter + queue; model routing; Batch API.
- Long tasks: accept -> enqueue (Celery/Temporal/SQS) -> worker pool -> stream back (SSE/WS).
- Per-dependency semaphores capping concurrent LLM/tool calls.

## Anti-patterns
- Optimizing throughput while ignoring p99 latency on a user-facing path.
- Sequential sub-agent calls when they are independent (a latency tax).
- Scaling only with LB + replicas when the limit is the LLM tier.
- Holding agent state in process memory; session affinity.

## Verification (fitness functions)
- A latency SLO (TTFT, p99) is defined and a perf test asserts it.
- AST/lint: no synchronous blocking LLM/HTTP client on an async code path.
- Independent sub-calls are parallelized (not awaited sequentially).
- Every LLM/tool call site is wrapped by a rate-limiter or semaphore.
- Autoscaling policy keys on queue depth / in-flight count (not CPU%).
EOF

# ============================ availability ============================
write_file "$NFR/availability.md" << 'EOF'
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
EOF

# ============================ observability ============================
write_file "$NFR/observability.md" << 'EOF'
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
EOF

# ============================ security ============================
write_file "$NFR/security.md" << 'EOF'
# Security & Safety

**Gate:** G4   **Required tiers:** T0, T1, T2  (first-order for agents)
**Applies when:** the feature handles untrusted input, uses side-effecting tools, or touches sensitive data.

> For agents, prompt injection and over-broad tool permissions are the dominant risks.
> Treat everything the model reads from tools, retrieval, or users as DATA, never commands.

## Required (the gate)
- Prompt-injection defense: tool outputs / retrieved docs / user files are data, not instructions;
  delimit and label untrusted content; never let it alter control flow.
- Tool & permission boundaries: per-agent allow-list; least privilege; irreversible/high-impact
  actions (payments, deletes, external sends, infra changes) require gating or human confirmation;
  validate tool inputs.
- Secrets: never in prompts, logs, traces, or persisted state; pulled from a secret manager at runtime.
- Data privacy: classify data; enforce egress boundaries (don't send sensitive data to unapproved
  model/tool endpoints); minimize/redact PII.
- Output guardrails + safe-fail: validate/scan outputs; refuse or escalate when uncertain or a guardrail trips.
- Supply chain: pin dependencies; vet MCP servers and their scopes; verify model sources.

## Patterns
- Structural separation of "instruction" vs "data" context; spotlighting/delimiting of untrusted text.
- Capability-scoped tool registry; confirmation gates on side effects.
- Egress allow-list: what data may leave, to which endpoints.

## Anti-patterns
- Concatenating raw web/tool/user content straight into the system prompt.
- Broad tool permissions "for convenience."
- Logging full prompts/responses containing secrets or PII.

## Verification (fitness functions)
- Secret-scanner in CI finds no secrets in code, logs, or traces.
- Tool registry enforces an allow-list; side-effecting tools flagged as requiring confirmation.
- Untrusted content passes a sanitize/delimit step before prompt assembly.
- Dependencies pinned; MCP server scopes reviewed; SCA scan runs in CI.
EOF

# ============================ cost ============================
write_file "$NFR/cost.md" << 'EOF'
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
EOF

# ============================ evaluation ============================
write_file "$NFR/evaluation.md" << 'EOF'
# Evaluation & Quality

**Gate:** G6   **Required tiers:** T1, T2
**Applies when:** the change affects agent behavior, prompts, tools, or models.

## Required (the gate)
- Offline evaluation baseline established before tuning.
- Golden test set + regression gate before merge/deploy.
- Runtime guardrails for output quality/safety.
- A quality SLO and how regressions are detected.

## Patterns
- Baseline first, then tune (metrics-driven).
- Block deploy on eval regression (ties to G2 deploy safety).
- Curate versioned golden sets per critical scenario.

## Anti-patterns
- Shipping a prompt/model change with no eval (vibe-based tuning).
- Golden sets that are never updated as the product evolves.

## Verification (fitness functions)
- Eval suite runs in CI on every change to prompts/tools/models.
- A regression gate fails the pipeline if a key metric drops beyond threshold.
- A versioned golden set exists and is referenced by the suite.
- An online quality metric is tracked against the SLO.
EOF

# ============================ maintainability ============================
write_file "$NFR/maintainability.md" << 'EOF'
# Maintainability & Evolvability

**Gate:** G7   **Required tiers:** T1, T2
**Applies when:** any code intended to live beyond a spike.

> For agents, evolvability is dominated by how cheaply you add a capability and how safely
> you change a prompt/model. Single-vendor lock-in is an evolvability risk (and a G2 risk).

## Required (the gate)
- Add a capability via config/plugin, not a core rewrite (new skill/tool = add config, zero core changes).
- Version prompts / tools / models / datasets; changes traceable and rollback-able.
- Modular decoupling: clear boundaries between orchestration / tools / prompts / memory.
- Dependency hygiene: pin, minimize, SCA.
- Code & test quality: complexity thresholds, coverage gate, documentation.
- Model/provider portability: LLM access behind an abstraction; no single-vendor lock-in.

## Patterns
- Config/registry-driven skills & tools so a new capability is a new config file.
- Prompt/tool/model registry with versions + changelog; pin dated model snapshots.
- Provider abstraction (or a gateway like LiteLLM) so swapping vendors is a config change — also enables G2 failover.
- Keep prompts/tool-defs as versioned assets, not inline literals scattered across code.

## Anti-patterns
- Adding a capability requires editing core orchestration files.
- Hardcoding one vendor's SDK calls throughout the codebase.
- Unversioned prompts changed in place with no rollback path.

## Verification (fitness functions)
- Adding a representative capability touches no core files (diff check).
- Prompts/tools/models carry version identifiers; a rollback path exists.
- Cyclomatic complexity / lint thresholds enforced in CI; coverage gate present.
- grep finds no scattered vendor SDK calls — LLM access goes through one abstraction.
- Dependencies pinned; SCA scan runs in CI.
EOF

# ============================ skill (robust outside spec-kit) ============================
write_file "$SKILL/SKILL.md" << 'EOF'
---
name: nfr-architect
description: Use when designing, implementing, or reviewing any non-functional / cross-cutting concern of an AI-agent system — concurrency, availability/resilience, observability, security, cost, or evaluation/quality. Trigger on throughput, scaling, 429s, failover, retries, uptime, SLO, tracing, prompt injection, secrets, token cost, eval/regression, "扛并发", "高可用".
---

# NFR Architect

When this applies, do NOT give generic web-scaling/SRE advice. Instead:

1. Identify which NFR concern(s) the task touches (often more than one; they trade off).
2. If `.specify/memory/nfr/` exists, read the matching playbook(s)
   (performance / availability / observability / security / cost / maintainability / evaluation)
   and apply their gate items, patterns, and Verification checks. If that folder is absent
   (non spec-kit repo), apply the same concerns from the summaries below.
3. Flag the real bottleneck or risk FIRST, then propose the specific layer(s) that fit.
4. Name the trade-offs you are making (e.g., cost vs availability).

In a spec-kit flow, ensure the plan addresses each gate required by the feature's tier,
with evidence linkage, or marks it N/A with reason.

## Concern summaries (fallback when playbooks are absent)
- Performance: latency SLO (TTFT, p99) — stream, prefix-cache, parallelize sub-calls; bottleneck tier; async; inference throughput / rate-limit handling; state externalization; queues + backpressure.
- Availability: provider failover; timeout/retry/circuit-breaker; per-dependency fallback; durable resumable workflows; idempotent side effects; health checks + SLO.
- Observability: tracing spans; structured logs w/ correlation id; golden signals + token cost; online quality eval; SLO alerts.
- Security: injection defense (data != instructions); tool allow-list + confirmation on side effects; secrets via manager; egress boundaries; output guardrails; supply-chain trust.
- Cost: token budget; prompt/semantic caching; model routing; batching; cost alerts.
- Maintainability: config-driven capabilities (no core rewrite); versioned prompts/tools/models + rollback; modular decoupling; dependency hygiene; provider abstraction (no vendor lock-in).
- Evaluation: offline baseline; golden set + CI regression gate; runtime guardrails; quality SLO.
EOF

# ============================ plan-template gate snippet (evidence + tiers) ============================
write_file "$NFR/plan-template-nfr-gate.snippet.md" << 'EOF'
<!-- Merge into the Constitution Check section of .specify/templates/plan-template.md -->
### NFR Gates  (feature tier: <T0 | T1 | T2>)
For each gate REQUIRED by this tier (see constitution): mark Addressed + cite evidence,
or N/A + reason. Gates not required by the tier may be left blank.

| Gate | Status | Evidence (task ID / test / manifest path)  — or N/A reason |
|------|--------|-----------------------------------------------------------|
| G1 Performance    | | |
| G2 Availability   | | |
| G3 Observability  | | |
| G4 Security       | | |
| G5 Cost           | | |
| G6 Evaluation     | | |
| G7 Maintainability| | |

#### NFR Trade-offs (deliberate, accepted balances — not violations)
- <e.g. "Single-region LLM for now; availability SLO relaxed to 99.0% to control cost — revisit at GA.">
EOF

# ============================ spec-template snippet (elicitation) ============================
write_file "$NFR/spec-template-nfr.snippet.md" << 'EOF'
<!-- Merge into .specify/templates/spec-template.md so NFR inputs are captured up front.
     These answers are what the plan's NFR gates reason against. -->
## Non-Functional Context
- **Criticality tier:** T0 prototype | T1 internal | T2 production
- **Expected load / concurrency:** <peak RPS, concurrent sessions, or "low / batch">
- **Availability target (SLO):** <e.g. 99.5%, or "best-effort">
- **Latency expectation:** <e.g. first-token < 2s; full < 30s>
- **Data sensitivity:** <public / internal / PII / regulated>
- **Cost budget:** <$ per request or monthly ceiling, if any>
- **Trust boundary:** <sources of untrusted input; side-effecting tools used>
EOF

# ============================ tasks-template snippet (NFR task derivation) ============================
write_file "$NFR/tasks-template-nfr.snippet.md" << 'EOF'
<!-- Merge into .specify/templates/tasks-template.md.
     Generate the task lines below for each gate REQUIRED by the feature's tier; skip N/A gates. -->
## NFR-Driven Tasks
- G1 Performance: latency SLO + perf test; async/concurrency handling; rate limiter/semaphore; load test.
- G2 Availability: timeout/retry/circuit-breaker; health probes; idempotency keys; crash-resume + failover tests.
- G3 Observability: tracing/logging/metrics instrumentation; online quality metric; SLO alerts.
- G4 Security: injection-safe context assembly; tool allow-list + confirmation gates; secret handling; egress controls; SCA scan.
- G5 Cost: token-budget enforcement; caching; model routing; cost metric + alert.
- G6 Evaluation: eval baseline; golden set; CI regression gate; runtime guardrails.
- G7 Maintainability: config-driven capability; prompt/tool/model versioning + rollback; provider abstraction; complexity/coverage gates; SCA.
EOF

# ============================ worked example plan ============================
write_file "$NFR/EXAMPLE-plan.md" << 'EOF'
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
EOF

# ============================ MR review prompt ============================
write_file "$NFR/mr-review-prompt.md" << 'EOF'
# MR Auto-Review Prompt — NFR Gate Enforcement

> Drop this into your Claude Agent SDK MR-review step. The pipeline supplies the PR diff,
> the changed-file list, and (if available) the feature's tier from the linked spec/plan.
> The reviewer checks the diff against each NFR playbook's **Verification** fitness functions
> and returns a structured verdict that can hard-block the MR.

---

## Role

You are an NFR gate reviewer for an AI-agent codebase governed by `.specify/memory/constitution.md`
and the playbooks in `.specify/memory/nfr/`. You enforce the **Verification** (fitness-function)
items of each gate against the PR diff. You are precise and evidence-based: every finding cites a
`file:line`. You do not rewrite the code; you report.

## Inputs

- `PR_DIFF` — the unified diff.
- `CHANGED_FILES` — list of changed paths.
- `TIER` — `T0` | `T1` | `T2` from the linked plan. If absent, infer conservatively:
  user-facing / handles money or PII / serves live traffic ⇒ **T2**; internal tool ⇒ **T1**;
  throwaway spike ⇒ **T0**. State the assumed tier and why.

## Procedure

1. Determine `TIER` and the set of **required** gates:
   - T0 → G4
   - T1 → G3, G4, G6, G7
   - T2 → G1–G7
2. Decide which gates are **in scope for this diff** (e.g., no LLM call touched ⇒ G5 likely N/A;
   no external dependency added/changed ⇒ G2 may be N/A). A gate that is required by the tier but
   genuinely untouched by the diff is `N/A (out of scope)` — say why.
3. For each in-scope required gate, run its checks below against `PR_DIFF`. A gate **fails** if any
   of its checks is violated and not justified in the plan's NFR Trade-offs.
4. Produce the verdict in the output format. **Only a failing tier-required gate blocks the MR.**

## Gate checks (run against the diff)

**G1 Performance** — if the diff adds/changes LLM or tool calls, or a user-facing path:
- No synchronous/blocking LLM or HTTP client on an `async` code path.
- Independent sub-calls are parallelized (`asyncio.gather`), not awaited sequentially.
- Each LLM/tool call site is wrapped by a rate-limiter or semaphore.
- A latency-relevant test or SLO assertion exists for new user-facing paths.

**G2 Availability** — if the diff adds/changes an external dependency or deployment:
- Every new external call has explicit timeout + retry (backoff) + circuit breaker.
- A per-dependency fallback exists (no hard-fail path).
- New side-effecting actions accept an idempotency key (safe to replay).
- Deployment manifests define liveness+readiness probes and `replicas >= 2`.
- Long/stateful workflows use a checkpointer (resumable).

**G3 Observability** — if the diff adds an agent/LLM/tool execution path:
- New LLM/tool calls emit trace spans under a request root trace.
- Logs carry a correlation/trace id (no bare `print`/unstructured logs on the path).
- A metric is emitted for new cost/quality-relevant behavior.

**G4 Security** — if the diff handles untrusted input, tools with side effects, or sensitive data:
- Retrieved/tool/user content is delimited and treated as data — not concatenated into the
  system/instruction context as commands.
- New tools are on an allow-list; irreversible/high-impact actions require gating/confirmation.
- No secrets in code, logs, traces, or persisted state (flag any literal key/token/password).
- No sensitive data (e.g., user wallet/PII) sent to third-party endpoints without an egress allow-list.
- New dependencies are pinned; new MCP servers' scopes are stated.

**G5 Cost** — if the diff adds/changes LLM calls:
- A per-request token/cost ceiling is enforced (truncate/abort past it).
- Static prompts / tool defs use prompt/prefix caching.
- Model choice is right-sized (no large model for routing/classification); routing is explicit.

**G6 Evaluation** — if the diff changes prompts, tools, models, or agent behavior:
- An eval runs in CI for this change; a regression gate can fail the pipeline.
- A golden set covers the changed behavior; **no look-ahead bias** in any backtest/eval.
- Prompt/model changes are not shipped "vibe-tuned" with zero eval.

**G7 Maintainability** — for any non-spike code:
- A new capability is added via config/registry, not by editing core orchestration files
  (flag edits to core files when a config path was available).
- LLM access goes through the provider abstraction — flag scattered vendor SDK calls.
- New prompts/tools/models carry a version identifier and a rollback path.
- Complexity/lint and coverage thresholds are not regressed.

## Output format

```
## NFR Gate Review  (tier: <T0|T1|T2>{, assumed: reason if inferred})

| Gate | Required | Result | Finding (file:line) |
|------|----------|--------|---------------------|
| G1 Performance     | <yes/no> | ✅ / ⚠️ / ❌ / N/A | ... |
| G2 Availability    | ... | ... | ... |
| G3 Observability   | ... | ... | ... |
| G4 Security        | ... | ... | ... |
| G5 Cost            | ... | ... | ... |
| G6 Evaluation      | ... | ... | ... |
| G7 Maintainability | ... | ... | ... |

**Decision:** BLOCK | APPROVE-WITH-NITS | APPROVE

**Required changes (must fix to merge):**
- [G#] <specific change> — <file:line>

**Suggestions (non-blocking):**
- [G#] <nit>
```

## Rules

- ✅ pass · ⚠️ minor/suggestion · ❌ blocking failure · `N/A` not required by tier or out of scope.
- **BLOCK only if** at least one tier-required, in-scope gate is ❌ and not covered by a documented
  NFR Trade-off in the plan. Otherwise APPROVE-WITH-NITS (any ⚠️) or APPROVE.
- Every ❌/⚠️ must cite a concrete `file:line`. No vague findings.
- Honor documented NFR Trade-offs: if the plan justifies a deviation, downgrade ❌→⚠️ and note it.
- Do not invent issues to fill the table; an in-scope gate with no problems is ✅.
- Keep it terse. The required-changes list is the actionable part.
EOF

# ============================ constitution guard ============================
CONST=".specify/memory/constitution.md"
echo ""
if [ -f "$CONST" ]; then
  echo "NOTE: $CONST exists — left untouched. Merge the NFR Gates + Criticality Tiers"
  echo "      sections from the provided constitution.md, then run /speckit.constitution."
else
  echo "NOTE: no constitution found. Drop the provided constitution.md into $CONST."
fi

echo ""
echo "Scaffolded:"
echo "  $NFR/  (README, _TEMPLATE, 7 playbooks w/ fitness functions, 3 template snippets, EXAMPLE-plan.md, mr-review-prompt.md)"
echo "  $SKILL/SKILL.md"
echo ""
echo "Next steps:"
echo "  1. Place constitution.md at $CONST (or merge Tiers + NFR Gates)."
echo "  2. Merge the 3 snippets into their templates in $TPL/:"
echo "       plan-template-nfr-gate.snippet.md  -> plan-template.md  (gate + evidence)"
echo "       spec-template-nfr.snippet.md       -> spec-template.md  (elicitation)"
echo "       tasks-template-nfr.snippet.md      -> tasks-template.md (task derivation)"
echo "  3. Run /speckit.constitution to re-sync templates (it may re-touch them — re-merge if needed)."
echo "  4. Ensure .specify and .claude are NOT gitignored, then git add + commit."
echo "  5. Wire $NFR/mr-review-prompt.md into your CI MR-review step (checks diffs against each playbook's Verification)."
