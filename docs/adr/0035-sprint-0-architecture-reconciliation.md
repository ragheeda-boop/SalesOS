# ADR-0035: Sprint 0 — Architecture Reconciliation

**Status**: Proposed
**Date**: 2026-07-17
**Author**: Architecture Review Board (Sprint 0)

---

## Context

The SalesOS build plan (IMPLEMENTATION_ROADMAP.md, IMPLEMENTATION_PLAN.md) defines:

```
Phase 0: Platform Stabilization (Sprints 1-2)
├── Sprint 1: Security & Critical Fixes
└── Sprint 2: Infrastructure & Performance
```

This plan was created with the implicit assumption of a **greenfield or near-greenfield** implementation. The IMPLEMENTATION_ROADMAP.md states:

> "قسّمنا Sprint 1 إلى Product Foundation، وليس 'Foundation UI'، لأن هدفه تجاري واضح: بناء الطبقة التي سترفع سرعة كل الـ Sprints التالية بـ 3x على الأقل."

**Sprint 0 Architecture Reconciliation (completed 2026-07-17) revealed:**

SalesOS is an **existing production platform**, not a greenfield project:
- 19 backend domain packages with working endpoints
- 13 frontend features with functional UIs
- 2,110+ tests at 93% coverage
- PostgreSQL with pg_trgm and pgvector extensions
- Neo4j graph database
- CI/CD pipeline with security, architecture, and test gates
- Docker Compose deployment validated

This fundamentally changes the architectural approach. The build plan's Sprint 1 is premature because:
1. We do not know the true baseline of the architecture
2. We do not know which documented patterns are actually enforced in code
3. We do not know the gap between approved ADRs and real implementation
4. Security fixes and infrastructure work should be informed by actual codebase analysis

---

## Decision

### 1. Sprint 0 — Architecture Reconciliation

A new Sprint 0 is introduced before Sprint 1. Sprint 0 is a **documentation-only sprint** with the following scope:

**IN SCOPE (Sprint 0):**
- Full codebase analysis (completed)
- Current architecture documentation
- Target architecture documentation
- Migration matrix (current → target)
- Technical debt identification and registration
- Architecture compliance measurement (not estimation)
- SES changelog (required SES updates)
- ADR updates required by real repository findings

**OUT OF SCOPE (Sprint 0):**
- Any production code modification
- Any refactoring
- Any scaffolding or new code generation
- Any database migrations
- Any deployment changes
- Any CI/CD changes

### 2. Updated Build Plan

The build plan is updated to insert Sprint 0:

```
Sprint 0: Architecture Reconciliation (NEW — this sprint)
├── CURRENT_ARCHITECTURE.md
├── TARGET_ARCHITECTURE.md
├── MIGRATION_MATRIX.md
├── TECHNICAL_DEBT_REGISTER.md (updated)
├── ARCHITECTURE_COMPLIANCE.md (updated with true scores)
├── SES_CHANGELOG.md
└── ADR updates (0032, 0033, 0034, 0035)

Sprint 1: Platform Stabilization (was Sprint 1 — unchanged order)
├── File size violations resolved
├── init_db() → Alembic baseline
├── InMemoryDecisionCenterRepository → PostgreSQL
└── Security fixes

Sprint 2: Infrastructure & Performance (was Sprint 2 — unchanged order)
├── Identity service → repository pattern
├── api.ts → domain-split files
├── API client duality consolidated
└── Performance fixes

Sprint 3+: Design System V2 onward (shifted by +0 — no sprint renumbering)
└── All subsequent sprints maintain their original numbering
```

### 3. SES Baseline

After Sprint 0 completes:
- The SES baseline is updated to reflect the true measured state
- Compliance scores are now measured (not estimated)
- Technical debt register is current
- Migration paths are documented

---

## Consequences

### Positive
- All implementation work is informed by actual codebase analysis
- Compliance scores are accurate, not aspirational
- Technical debt is formally tracked before feature work begins
- Sprint 1-2 estimates are more accurate
- Reduced risk of "surprise" architecture violations during feature development

### Negative
- Sprint 0 adds 1 sprint to the overall timeline (22 → 23 sprints)
- No production value delivered during Sprint 0 (documentation only)
- Risk of analysis paralysis (mitigated by scope definition)

### Neutral
- No code changes during Sprint 0 means zero regression risk
- All existing sprint deliverables remain unchanged
- Work orders do not need renumbering

---

## Compliance

| Deliverable | Format | Acceptance |
|-------------|--------|------------|
| CURRENT_ARCHITECTURE.md | `docs/CURRENT_ARCHITECTURE.md` | Review by CTO + Chief Architect |
| TARGET_ARCHITECTURE.md | `docs/TARGET_ARCHITECTURE.md` | Review by CTO + Chief Architect |
| MIGRATION_MATRIX.md | `docs/MIGRATION_MATRIX.md` | Review by CTO + Chief Architect |
| TECHNICAL_DEBT_REGISTER.md | `memory/technical-debt.md` (updated) | Review by Engineering Team |
| ARCHITECTURE_COMPLIANCE.md | `docs/ARCHITECTURE_COMPLIANCE.md` (updated) | Review by CTO + Chief Architect |
| SES_CHANGELOG.md | `docs/SES_CHANGELOG.md` | Review by CTO |
| ADR updates | `engineering-os/adr/ADR-0032*`, `docs/adr/0033*`, `0034*`, `0035*` | Architecture Review Board approval |

---

## References

- IMPLEMENTATION_ROADMAP.md: Original sprint structure (no Sprint 0)
- IMPLEMENTATION_PLAN.md: Phase 0 definition
- SES_CHANGELOG.md Change 008: Sprint 0 addition
- SES_CHANGELOG.md Change 009: Build order dependency graph correction
- MIGRATION_MATRIX.md: Full migration path including Sprint 0 insertion
