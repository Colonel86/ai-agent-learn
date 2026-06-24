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
