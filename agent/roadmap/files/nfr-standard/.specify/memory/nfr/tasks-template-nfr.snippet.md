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
