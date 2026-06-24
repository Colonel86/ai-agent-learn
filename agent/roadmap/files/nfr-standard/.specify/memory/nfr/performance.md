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
