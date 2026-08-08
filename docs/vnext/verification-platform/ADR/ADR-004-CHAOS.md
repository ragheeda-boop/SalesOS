# ADR-004 — Chaos Engineering

- **Status:** Proposed (post-GA, Phase 3)
- **Date:** 2026-08-07
- **Deciders:** Project Owner
- **Related:** GAP-ANALYSIS (Chaos), IMPLEMENTATION-PLAN §3.3

## Context

The soak validates stability under normal operation. It does **not** prove recovery from injected failures (Redis down, DB connection drop, worker kill, partition). Recovery behavior is currently untested at runtime.

## Decision

Adopt **LitmusChaos** (open-source) as the primary chaos engine, **staging-first**:

1. Scenarios: stop Redis, kill worker, drop DB connection, restart API.
2. Each scenario asserts recovery within SLA (health back to green, queue drains).
3. Evidence captured per scenario → EAB.

**Gremlin** (paid) considered if production-class chaos is ever required — prod runs only inside an owner-approved window.

## Consequences

- **+** Proves recovery behavior, not just uptime.
- **+** Open-source, no per-run cost for staging.
- **−** Complexity + risk of cascading failures → must run on isolated staging first.
- **−** Requires blast-radius guardrails (never prod without a window).

## Alternatives considered

- No chaos: rejected — recovery is unproven.
- Gremlin-only: rejected until paid/prod-class needed.

---

*ADR-004 — verification-platform — 2026-08-07*
