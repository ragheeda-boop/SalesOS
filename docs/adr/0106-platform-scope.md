# ADR-106: Platform — Scope to SalesOS Only

**Status**: ACCEPTED
**Date**: 2026-08-07
**Author**: STAR Audit / Architecture
**Related**: D-01, ADR-101, ADR-102
**Supersedes**: nothing

---

## Context

PROJECT_BIBLE.md describes a 4-product platform: SalesOS, AuditOS, DecisionOS, LocalContentOS. The STAR audit (D-01) found **only SalesOS exists as code**. No AuditOS, DecisionOS, or LocalContentOS repositories, services, or code.

Current state:
- `salesos/` — the only product tree
- `docs/` — references to other products (vision only)
- No shared Core library

## Decision

**Scope v1.0 to SalesOS only.** Update documentation to reflect reality.

### Rationale
1. **Only SalesOS exists** — Building 3 additional products from zero is a multi-year effort
2. **SalesOS is not GA** — Focus on shipping the first product before expanding
3. **No shared Core** — The "shared Core" architecture exists only in documentation
4. **Market validation** — SalesOS must prove product-market fit before platform expansion

### What stays in v1.0
- SalesOS as the sole product
- Company/brand name retained
- Platform architecture documented for future reference

### What moves to v2.0+
- AuditOS (v2.0)
- DecisionOS (v2.0)
- LocalContentOS (v3.0)
- Shared Core library (v2.0)

## Consequences

- **Positive:** v1.0 scope is focused; team ships one product well
- **Negative:** "Multi-product platform" marketing claim becomes inaccurate for v1.0
- **Risk:** If market demands multi-product sooner, scope may need revisiting

## Evidence

- D-01: STAR Audit found only SalesOS exists
- `salesos/` — the only product tree
- No `auditos/`, `decisionos/`, `localcontentos/` directories
