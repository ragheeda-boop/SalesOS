# ADR-0033: Decision Engine Lifecycle Decision

**Status**: Proposed
**Date**: 2026-07-17
**Author**: Architecture Review Board (Sprint 0)

---

## Context

The Decision Platform is a core architectural component documented in:
- `docs/DECISION_PLATFORM_ARCHITECTURE.md` — complete system design
- `docs/ARCHITECTURE_BOOK.md §4` — Decision Platform chapter
- `docs/DOMAIN_MAP.md` — Decision Intelligence as CAP-016
- `salesos/docs/DECISION_PLATFORM_IMPLEMENTATION_PLAN.md` — implementation plan

The platform defines 8 engines: Decision, Rule, Scoring, Evidence, Recommendation, Explainability, Feedback, and Learning.

**Sprint 0 Architecture Reconciliation discovered:**

| Component | Backend Status | Frontend Status |
|-----------|---------------|-----------------|
| Decision Engine | ✅ Complete (`domains/decision/`) | ❌ **Stub** (`packages/platform/decision/index.ts` throws "Not implemented") |
| Rule Engine | ✅ Complete | N/A (backend-only) |
| Scoring Engine | ✅ Complete (`domains/scoring/`) | ✅ Connected via API |
| Evidence Engine | ✅ Complete | N/A |
| Recommendation Engine | ✅ Complete | ⚠️ Partial UI |
| Explainability Engine | ✅ Complete | ⚠️ Partial UI |
| Feedback Engine | ✅ Complete | ⚠️ Partial |
| Learning Engine | ⚠️ Partial | N/A |

The frontend Decision Engine stub is problematic because:
1. It is documented as a complete, frozen Decision Platform
2. Scoring domain compliance is lowered (92% instead of 95%) because the canonical scoring path requires `useDecision()`
3. New widgets cannot implement Decision Platform integration without a functional frontend Decision Engine
4. It creates a false sense of completeness in the ENGINEERING_DASHBOARD

---

## Decision

### Option A (Recommended): Implement Frontend Decision Engine

Implement the frontend Decision Engine fully in Sprint 11 (Phase 5), aligned with the approved build plan:

1. Implement `packages/platform/decision/` with:
   - `DecisionProvider` context (already exists in features)
   - `useDecision()` hook for scoring/recommendation access
   - API client integration with backend Decision Engine endpoints
   - Typed response envelopes for all Decision Platform outputs
   - Loading/error/degraded state handling

2. Wire to backend:
   - `POST /api/v1/decisions/evaluate` — already exists
   - `POST /api/v1/decisions/recommend` — already exists
   - `GET /api/v1/decisions/context/{id}` — already exists

3. Timeline: Sprint 11 (Phase 5), as originally planned in IMPLEMENTATION_PLAN.md

### Option B (Fallback): Officially Defer to v2.5

If resourcing constraints prevent Sprint 11 delivery:

1. Replace the stub with a clear deprecation notice
2. Update all documentation to reflect "v2.5 Planned" status
3. Adjust Scoring domain compliance target to 90% (acknowledging gap)
4. Remove Decision Engine from frozen interfaces list
5. Create a v2.5 work order

### Decision

**Option A is selected.** The Decision Engine is fundamental to the architecture. All 6 participating domains score lower without it. Sprint 11 is already allocated.

---

## Consequences

### Positive
- Decision Platform becomes end-to-end functional
- Scoring domain reaches 95% compliance
- New widgets have canonical scoring path
- Architecture documentation reflects reality

### Negative
- Requires 3-5 days engineering effort in Sprint 11
- Depends on backend Decision Engine stability
- API contract must match existing backend endpoints

### Neutral
- No changes to frozen interfaces
- No changes to existing widgets
- Build plan unchanged (Sprint 11 was already allocated)

---

## Compliance

| Check | Enforcement |
|-------|-------------|
| `packages/platform/decision/index.ts` no longer throws "Not implemented" | Unit test asserting `useDecision()` returns valid response |
| Decision Platform UI integrates with backend endpoints | Integration test for `POST /api/v1/decisions/evaluate` |
| Scoring domain compliance ≥ 95% | `scripts/arch-compliance.ps1` |

---

## References

- ADR-002: Dashboard as Projection
- DECISION_PLATFORM_ARCHITECTURE.md: Complete system design
- ARCHITECTURE_BOOK.md §4: Decision Platform chapter
- TD-S0-07: Decision Engine is non-functional stub
- SES_CHANGELOG.md Change 005: Decision Engine completeness
