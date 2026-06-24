# Project Constitution

> The immutable engineering contract for this project. Every spec, plan, task, and
> implementation MUST comply. Enforced via the **Constitution Check** in `/plan` and by CI.
> Amendments require a version bump and re-syncing the dependent templates.

**Version:** 1.0.0  |  **Ratified:** <YYYY-MM-DD>  |  **Last amended:** <YYYY-MM-DD>

---

## Core Principles

### I. Spec-Driven, Test-First
No implementation begins without an approved spec and plan. Tests (or an evaluation
baseline, for agent behavior) are written and shown to fail before implementation code.

### II. Probabilistic over Deterministic
Where real uncertainty exists, do not collapse it into hard classification. Prefer
probabilistic representations and surface confidence. Hard thresholds must be justified.

### III. Auditability & Reproducibility
Every consequential decision (routing, scoring, signal, eval result) must be traceable to
its inputs. No look-ahead bias in any backtest, eval, or replay. Runs must be reproducible
from persisted state.

### IV. Simplicity & Low Change-Cost
Avoid over-engineering. Adding a new capability should be a configuration change, not a
core rewrite. A change that forces edits to core files must be explicitly justified.

---

## Criticality Tiers

Every feature declares a **tier** in its spec. NFR gates apply **by tier** — this prevents
over-gating throwaway work and the rubber-stamped "N/A" that follows from one-size-fits-all.

| Tier | Scope | Required gates | Recommended |
|------|-------|----------------|-------------|
| **T0 — Prototype / Spike** | Throwaway, not user-facing | G4 (secrets; + injection if it takes untrusted input) | — |
| **T1 — Internal** | Internal users, limited blast radius | G3, G4, G6, G7 | G1, G2, G5 |
| **T2 — Production** | User-facing or business-critical | **All of G1–G7** | — |

A gate not required by the feature's tier may be skipped without justification. A required
gate must be **addressed with evidence** or marked **N/A with reason** (see Governance).

---

## Non-Functional Requirement (NFR) Gates

Each gate is tested during the Constitution Check in `/plan`. Detail for each gate lives in
the referenced playbook under `.specify/memory/nfr/`.

### G1. Performance & Scalability — *required: T2*
**Applies when:** the feature makes LLM/Agent calls, serves concurrent load, or has a
user-facing latency expectation.
**The plan MUST address:** a latency SLO (time-to-first-token; end-to-end p99); bottleneck
tier (orchestration / inference / tools); fully async non-blocking orchestration; inference
throughput or API rate-limit handling (TPM/RPM); agent-state externalization for scale-out;
queue-based execution + backpressure for long tasks.
→ `nfr/performance.md`

### G2. Availability & Resilience — *required: T2*
**Applies when:** the feature has external dependencies (LLM/tools/state) or serves live traffic.
**The plan MUST address:** LLM provider/region failover + graceful degradation; timeouts,
retries (backoff+jitter), circuit breakers, bulkheads on every external call; per-dependency
fallback (never hard-fail); workflow durability & resumability; idempotent side effects;
deep health checks + an availability SLO.
→ `nfr/availability.md`

### G3. Observability — *required: T1, T2*
**Applies when:** any Agent code reaches production.
**The plan MUST address:** distributed tracing across agent/LLM/tool spans; structured
logging with correlation IDs; the four golden signals + token/cost metrics; online quality
evaluation; alerting tied to SLO breaches.
→ `nfr/observability.md`

### G4. Security & Safety — *required: T0, T1, T2*
**Applies when:** the feature handles untrusted input, uses side-effecting tools, or touches sensitive data.
**The plan MUST address:** prompt-injection defense; tool & permission boundaries (least
privilege; high-risk actions gated/confirmed); secrets handling; PII/data-privacy + egress
boundaries; output guardrails + safe-fail; supply-chain trust (deps, MCP servers, models).
→ `nfr/security.md`

### G5. Cost & Efficiency — *required: T2 (recommended: T1)*
**Applies when:** the feature makes LLM calls.
**The plan MUST address:** token/cost budget per request and per loop iteration; prompt/
prefix + semantic caching; model right-sizing & routing; batching for non-realtime; cost
monitoring + alerting.
→ `nfr/cost.md`

### G6. Evaluation & Quality — *required: T1, T2*
**Applies when:** the change affects agent behavior, prompts, tools, or models.
**The plan MUST address:** offline eval baseline before tuning; golden test set + regression
gate before merge/deploy; runtime guardrails; a quality SLO and regression detection.
→ `nfr/evaluation.md`

### G7. Maintainability & Evolvability — *required: T1, T2*
**Applies when:** any code intended to live beyond a spike.
**The plan MUST address:** capabilities added via config/plugin without core changes;
versioning of prompts/tools/models/datasets with rollback; modular decoupling
(orchestration / tools / prompts / memory boundaries); dependency hygiene (pin, minimize,
SCA); code & test quality (complexity thresholds, coverage gate, docs); model/provider
portability (LLM access behind an abstraction — no single-vendor lock-in).
→ `nfr/maintainability.md`

---

## Governance

- **Enforcement order:** gates in `/plan` (surface) → `/speckit.analyze` before `/implement`
  (cross-artifact check) → CI MR auto-review (hard block).
- **Evidence linkage:** marking a gate "addressed" is *not* enough. The plan must cite **where**
  it is satisfied — a task ID, a test name, or a manifest path. Unevidenced gates fail review.
- **Trade-offs:** NFRs conflict (cost ↔ availability, security ↔ latency, throughput ↔ guardrails).
  Deliberate, accepted balances are recorded in the plan's **"NFR Trade-offs"** subsection — a
  trade-off is a *justified decision*, not a violation. Unintended violations still go in
  Complexity Tracking.
- **Amendments:** SemVer bump (MAJOR: principle/gate removed or redefined; MINOR: added; PATCH:
  clarification) and re-run `/speckit.constitution` so `plan-template.md`, `spec-template.md`,
  and `tasks-template.md` stay in sync.
- **Adding an NFR module:** copy `nfr/_TEMPLATE.md`; add a `G#` gate here (with tier applicability);
  add the checklist line to `plan-template.md`, the elicitation line to `spec-template.md`, and the
  task line to `tasks-template.md`. One concern per module.
