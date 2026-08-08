# ADR-105: Revenue Brain — Defer to v2.0

**Status**: ACCEPTED
**Date**: 2026-08-07
**Author**: STAR Audit / Architecture
**Related**: D-07, ADR-101, ADR-102
**Supersedes**: nothing

---

## Context

The MASTER_BLUEPRINT.md describes Revenue Brain as "NBA (Next Best Action) per user per context" — the central AI intelligence layer. The STAR audit (D-07) found **no implementation**.

Current SalesOS has:
- Feature store (7 score computers) — deterministic, not AI-driven
- Decision Center (PostgreSQL-backed) — rule-based, not ML-based
- Analytics (basic) — descriptive, not predictive

None of these constitute a Revenue Brain. The gap is total.

## Decision

**Defer Revenue Brain to v2.0.** Remove from v1.0 scope.

### Rationale
1. **No foundation exists** — Revenue Brain requires: ML pipeline, feature engineering, model training, real-time inference
2. **Decision Center is rule-based** — The existing "decision" system is CRUD + rules, not AI-driven
3. **Dependencies** — Revenue Brain requires: Event Bus (in-memory), AI Memory (basic), Feature Store enhancement, Model Registry (not built)
4. **Data requirements** — NBA requires historical conversion data, interaction patterns, and pipeline outcomes that don't exist yet

### What stays in v1.0
- Feature store (7 score computers) — deterministic scoring
- Decision Center (PostgreSQL-backed) — rule-based decisions
- Analytics (basic) — descriptive reporting

### What moves to v2.0
- ML pipeline
- Feature engineering
- Model training + registry
- Real-time inference
- NBA engine

## Consequences

- **Positive:** v1.0 analytics scope is clear; deterministic scoring is sufficient for GA
- **Negative:** "AI-native revenue intelligence" marketing claim becomes inaccurate for v1.0
- **Risk:** If competitors ship AI-driven NBA, v2.0 delivery timeline is critical

## Evidence

- D-07: STAR Audit found no implementation
- `salesos/backend/app/modules/decision_center/` — rule-based CRUD
- `salesos/backend/app/domains/feature_store/` — deterministic scoring
