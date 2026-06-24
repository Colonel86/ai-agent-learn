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
