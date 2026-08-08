# ADR-103: Digital Twin — Defer to v2.0

**Status**: ACCEPTED
**Date**: 2026-08-07
**Author**: STAR Audit / Architecture
**Related**: D-06, ADR-101, ADR-102
**Supersedes**: nothing

---

## Context

The MASTER_BLUEPRINT.md describes Digital Twin as a "real-time computational mirror" — a flagship capability. The STAR audit (D-06) found **zero components** implemented. No model, no service, no API, no test.

Current SalesOS has:
- Company CRUD + 360 view
- Employee profiles + signals + scoring
- Feature store (7 score computers)
- Audit trail

None of these constitute a Digital Twin. The gap is total.

## Decision

**Defer Digital Twin to v2.0.** Remove from v1.0 scope.

### Rationale
1. **No foundation exists** — Building from zero requires significant R&D (real-time event processing, computational models, state synchronization)
2. **Core CRM is not GA** — SalesOS itself is still in conditional GO status; adding unproven AI features increases risk
3. **Dependencies** — Digital Twin requires: Event Bus (Kafka currently in-memory), Knowledge Graph (Neo4j offline), AI Memory (basic persistence only)
4. **Customer value** — Saudi B2B customers need CRM + pipeline + billing first; Digital Twin is a differentiator, not a requirement

### What stays in v1.0
- Company/Employee CRUD + 360 view
- Feature store score computers
- Audit trail (foundation for future twin)

### What moves to v2.0
- Real-time event streaming to twin
- Computational models per entity
- State synchronization
- Twin-specific APIs

## Consequences

- **Positive:** v1.0 scope clarified; team focuses on GA-critical items
- **Negative:** Marketing materials must be updated; "Digital Twin" removed from v1.0 pitch
- **Risk:** If competitors offer similar features, v2.0 delivery timeline becomes critical

## Evidence

- D-06: STAR Audit found zero components
- `salesos/backend/app/domains/` — no twin-related domain
- `salesos/frontend/` — no twin-related pages
