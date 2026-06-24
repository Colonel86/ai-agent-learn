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
