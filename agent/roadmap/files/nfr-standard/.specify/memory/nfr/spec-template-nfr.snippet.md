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
