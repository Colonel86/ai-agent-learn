# AI-Agent NFR Standard

> A reusable, **enforceable** standard for the non-functional requirements (NFRs) of
> AI-agent systems, built on top of [spec-kit](https://github.com/github/spec-kit)
> (Spec-Driven Development). It encodes seven cross-cutting engineering concerns as
> governance **gates**, **playbooks**, **template hooks**, a **skill**, and **CI checks** —
> so quality attributes are decided at plan time and verified in CI, not left to memory.

---

## Why this exists

Functional requirements describe what an agent *does*. Non-functional requirements —
performance, availability, security, observability, cost, maintainability, evaluation
quality — describe how *well* it does it. They are **cross-cutting**: every feature touches
them, and so they are easy to skip on any single feature and expensive to retrofit.

This standard makes them **first-class**: each concern is a gate that is checked during
`/plan` and enforced by CI. In architecture terms, the gates are the **architectural
characteristics** and the playbooks' Verification sections are **fitness functions** that
continuously confirm them. The "executable" guarantee comes from the CI/verification layer —
the prose gates only force the consideration; CI is what makes it real.

## How it works — the five layers

| Layer | Artifact | Role |
|-------|----------|------|
| 1. **Gate** | `constitution.md` | The "must consider" rule, applied **by criticality tier**, checked in the `/plan` Constitution Check. |
| 2. **Playbook** | `nfr/<concern>.md` | The "how to do it" depth + a **Verification** (fitness-function) section. Loaded on demand. |
| 3. **Template hooks** | three snippets | `spec` elicits NFR inputs → `plan` gates them **with evidence** → `tasks` derives NFR tasks. |
| 4. **Skill** | `nfr-architect/SKILL.md` | Routes interactive Claude Code work to the right playbook (works outside spec-kit too). |
| 5. **CI** | `mr-review-prompt.md` + `/speckit.analyze` | Hard-blocks MRs that violate a tier-required gate. |

## The seven gates

| Gate | Concern | In one line |
|------|---------|-------------|
| **G1** | Performance & Scalability | Latency SLO (TTFT, p99) + throughput/scale; async, caching, rate-limit handling, state externalization. |
| **G2** | Availability & Resilience | Provider failover, timeouts/retries/circuit-breakers, durable resumable workflows, idempotent side effects, health checks. |
| **G3** | Observability | Tracing spans, structured logs, golden signals + token cost, online quality eval, SLO alerts. |
| **G4** | Security & Safety | Prompt-injection defense, tool/permission boundaries, secrets, data egress, output guardrails, supply chain. |
| **G5** | Cost & Efficiency | Per-request token budget, prompt/semantic caching, model routing, batching, cost alerts. |
| **G6** | Evaluation & Quality | Offline baseline, golden set + CI regression gate, runtime guardrails, **no look-ahead bias**. |
| **G7** | Maintainability & Evolvability | Config-driven capabilities (no core rewrite), versioned prompts/tools/models, provider portability. |

## Criticality tiers

Gates apply **by tier** — so a throwaway spike isn't forced through production gates (which
just produces rubber-stamped "N/A"). Every feature declares its tier in the spec.

| Tier | Scope | Required gates |
|------|-------|----------------|
| **T0 — Prototype / Spike** | Throwaway, not user-facing | G4 (secrets; + injection if it takes untrusted input) |
| **T1 — Internal** | Internal users, limited blast radius | G3, G4, G6, G7 (G1/G2/G5 recommended) |
| **T2 — Production** | User-facing or business-critical | **All of G1–G7** |

## What's in the package

```
.specify/
  memory/
    constitution.md                     # core principles + 7 gates + tiers + governance
    nfr/
      README.md                         # module-library overview (points here for examples)
      _TEMPLATE.md                      # template for a new NFR module
      performance.md   availability.md  # 7 playbooks, each with a Verification section
      observability.md security.md
      cost.md          maintainability.md  evaluation.md
      plan-template-nfr-gate.snippet.md # → merge into plan-template.md  (gate + evidence)
      spec-template-nfr.snippet.md      # → merge into spec-template.md  (elicitation)
      tasks-template-nfr.snippet.md     # → merge into tasks-template.md (task derivation)
      EXAMPLE-plan.md                   # a real T2 feature with all 7 gates filled + evidence
      mr-review-prompt.md               # MR auto-review rule (checks diffs vs. Verification)
.claude/skills/nfr-architect/SKILL.md   # interactive routing skill
setup-nfr-library.sh                    # idempotent scaffolder (regenerates the above)
```

> Placement note: keep this file as the package/standard README. If you drop the standard
> into a repo that already has a root `README.md`, save this as `docs/nfr-standard.md` instead.

## Quick start

```bash
# from your repo root (the scaffolder is idempotent and never overwrites existing files)
bash setup-nfr-library.sh

# place the constitution (new project: use as-is; existing: merge the Tiers + NFR Gates sections)
cp constitution.md .specify/memory/constitution.md

# merge the three snippets into their spec-kit templates, then re-sync
#   plan-template-nfr-gate.snippet.md  -> .specify/templates/plan-template.md
#   spec-template-nfr.snippet.md       -> .specify/templates/spec-template.md
#   tasks-template-nfr.snippet.md      -> .specify/templates/tasks-template.md
/speckit.constitution      # re-syncs templates (re-merge if it re-touches them)

# ensure .specify and .claude are NOT gitignored, then commit
git add .specify .claude && git commit -m "Add AI-agent NFR standard"
```

## Daily workflow

1. **`/speckit.specify`** — describe the feature *and* fill the **Non-Functional Context**
   (tier, expected load, availability SLO, latency, data sensitivity, cost budget, trust boundary).
2. **`/speckit.plan`** — the Constitution Check runs the gates for the feature's tier. For each
   required gate, mark **Addressed + cite evidence** (task ID / test / manifest path) or **N/A + reason**.
   Record deliberate balances under **NFR Trade-offs**.
3. **`/speckit.tasks`** — generate the NFR-driven tasks for the applicable gates.
4. **`/speckit.analyze`** — cross-artifact check before implementing; catches gate violations.
5. **`/speckit.implement`** — build it.
6. **MR** — CI runs `mr-review-prompt.md`, checking the diff against each playbook's Verification;
   a failing tier-required gate **blocks** the merge.

See **`nfr/EXAMPLE-plan.md`** for a fully worked T2 plan with every gate filled out and evidenced.

## Evidence & trade-offs (what makes this real, not checkbox theater)

- **Evidence linkage** — marking a gate "addressed" is not enough; the plan must cite *where*
  it is satisfied (a task ID, a test name, or a manifest path). Unevidenced gates fail review.
- **Trade-offs** — NFRs conflict (cost ↔ availability, security ↔ latency, throughput ↔ guardrails).
  Deliberate, accepted balances go in the plan's **NFR Trade-offs** subsection — a justified
  decision, *not* a violation. The MR reviewer downgrades a documented trade-off from blocking to a note.

## CI enforcement

Wire **`nfr/mr-review-prompt.md`** into your MR-review step (e.g., a Claude Agent SDK job on
GitLab/Jenkins). It reads the diff, infers or reads the tier, runs each in-scope required gate's
checks, and returns a structured verdict (per-gate result with `file:line` evidence + a
BLOCK/APPROVE decision). Pair it with `/speckit.analyze` as a pre-implement gate.

## Extending the standard — add a module

1. `cp nfr/_TEMPLATE.md nfr/<concern>.md` and fill it in — **especially the Verification section**.
2. Add a `G#` gate to `constitution.md` with its tier applicability.
3. Add the line to all three template snippets and re-merge.

One concern per module. Keep playbooks lean; push long code samples to companion files loaded
on demand.

## Governance & versioning

The constitution is versioned (SemVer): **MAJOR** removes/redefines a principle or gate,
**MINOR** adds one, **PATCH** clarifies. After any amendment, re-run `/speckit.constitution`
so `plan`, `spec`, and `tasks` templates stay in sync.
