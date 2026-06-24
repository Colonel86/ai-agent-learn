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
