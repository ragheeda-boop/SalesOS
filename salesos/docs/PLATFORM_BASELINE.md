# SalesOS — Platform Baseline

> **Sprint 0.5 Deliverable: Platform Freeze**
> Date: 2026-07-17 | Status: 🧊 IMMUTABLE
>
> This document establishes the immutable baseline of the SalesOS platform.
> No architectural element documented here may change without an approved ADR.
> All future work is measured against this baseline.

---

## 1. Baseline Declaration

Effective 2026-07-17, the SalesOS platform architecture is frozen at the state documented in:

| Document | Version | Status |
|----------|---------|--------|
| `docs/CURRENT_ARCHITECTURE.md` | Sprint 0 | 🧊 Frozen |
| `docs/TARGET_ARCHITECTURE.md` | Sprint 0 | 🧊 Frozen |
| `docs/MIGRATION_MATRIX.md` | Sprint 0 | 🧊 Frozen |
| `docs/ARCHITECTURE_INVENTORY.md` | Sprint 0.5 | 🧊 Frozen |
| `docs/ARCHITECTURE_COMPLIANCE.md` | Sprint 0 update | 🧊 Frozen |
| `docs/SES_CHANGELOG.md` | Sprint 0 | 🧊 Frozen |
| `memory/technical-debt.md` | Sprint 0 update | 🧊 Frozen |
| `docs/PROJECT_BIBLE.md` | v2.0.0 | 🧊 Frozen |
| `engineering-os/ENGINEERING_CONSTITUTION.md` | v1.0 | 🧊 Frozen |
| `engineering-os/ENGINEERING_DASHBOARD.md` | 2026-07-14 | 🧊 Frozen |
| `docs/MASTER_BLUEPRINT.md` | V5.0 | 🧊 Frozen |
| `engineering-os/adr/ADR-001*` | Accepted | 🧊 Frozen |
| `engineering-os/adr/ADR-002*` | Accepted | 🧊 Frozen |
| `engineering-os/adr/ADR-003*` | Accepted | 🧊 Frozen |
| `engineering-os/adr/ADR-0032*` | Proposed | 🧊 Frozen |
| `docs/adr/0033*` | Proposed | 🧊 Frozen |
| `docs/adr/0034*` | Proposed | 🧊 Frozen |
| `docs/adr/0035*` | Proposed | 🧊 Frozen |

All documents above are collectively the **Platform Baseline**. Any modification requires an ADR.

---

## 2. Frozen Interfaces

The following interfaces are frozen and cannot be modified without new ADR + Architecture Review Board approval:

| Interface | ADR | Frozen Since |
|-----------|-----|-------------|
| Identity Domain API contracts | ADR-001 | 2026-07-10 |
| Widget SDK v1.0 API surface (`createWidget()`, types, lifecycle, telemetry, permissions, flags, contract tests) | ADR-003 / ADR-0032 | 2026-07-10 |
| `describeWidgetContract()` testing utility | ADR-003 | 2026-07-10 |
| Kernel Layer services | MASTER_BLUEPRINT §3 | 2026-07-10 |
| Domain boundaries (13 bounded contexts) | DOMAIN_MAP.md | 2026-07-17 |
| API prefix convention (`/api/v1/{domain}`) | ARCHITECTURE_BOOK | 2026-07-17 |

---

## 3. SES Baseline

Performance budgets at baseline (verified by benchmark at 100k companies):

| Endpoint | p50 | p95 | Status |
|----------|-----|-----|--------|
| GET /companies/{id} | 3ms | 6ms | ✅ Within budget |
| POST /search | 3ms | 6ms | ✅ Within budget |
| GET /dashboard | 50ms | 88ms | ✅ Within budget |
| GET /timeline | 25ms | 100ms | ✅ Within budget |
| POST /enrich (async) | 50ms | 100ms | ✅ Within budget |
| POST /decision/evaluate | 15ms | 30ms | ✅ Within budget |
| GET /pipeline/summary | 10ms | 25ms | ✅ Within budget |
| Partial Search (ILIKE) | 30ms | <50ms | ✅ Within budget |

Quality baselines:

| Metric | Baseline | Target |
|--------|----------|--------|
| Unit Test Coverage | 93% | ≥ 85% |
| Integration Test Coverage | 70% | ≥ 70% |
| E2E Coverage | 60% | ≥ 60% |
| Total Tests | 2,110+ | ≥ 2,000 |
| Architecture Compliance | 85% | ≥ 95% |
| Security Posture | 10/10 | ≥ 9.5/10 |
| Production Readiness | 9/10 | ≥ 9/10 |
| File Size Limit | 2 violations | 0 violations |

---

## 4. Compliance Baseline

Measured compliance scores at freeze:

| Domain | Measured | Target | Gap | Freeze Status |
|--------|----------|--------|-----|---------------|
| Identity | 100% | 95% | +5% | ✅ On-target |
| Widget SDK | 70% | 95% | -25% | ⚠️ ADR-0032 in progress |
| Company | 95% | 95% | 0% | ✅ On-target |
| Search | 88% | 95% | -7% | ⚠️ Needs work |
| Scoring | 92% | 95% | -3% | ⚠️ Near target |
| CRM | 88% | 95% | -7% | ⚠️ Needs work |
| AI | 82% | 95% | -13% | ⚠️ Improving |
| Timeline | 78% | 95% | -17% | ⚠️ Needs redesign |
| Workflow | 48% | 95% | -47% | 🔴 Not started |
| **OVERALL** | **85%** | **95%** | **-10%** | **🟡 Needs work** |

---

## 5. Technical Debt Baseline

| Severity | Count | Items |
|----------|-------|-------|
| Critical | 1 | TD-S0-01 (Dual Widget SDKs) |
| High | 6 | TD-S0-02 through TD-S0-06, TD-002 |
| Medium | 4 | TD-S0-07, TD-S0-08, TD-S0-10, TD-005 |
| Low | 1 | TD-S0-09 |
| **Total Active** | **12** | |

---

## 6. Architecture Inventory Summary

| Category | Count |
|----------|-------|
| Backend Python files | 1,540 |
| Frontend TypeScript files | 646 |
| Backend domains | 17 |
| App modules | 24 |
| API routers | 18 |
| Alembic migrations | 37 |
| SDK modules | 18 |
| Intelligence modules | 20 |
| Frontend features | 13 |
| Frontend packages | 13 |
| App route segments | 28+ |
| Foundation components | 22 |
| E2E test specs | 26 |
| Test files (all) | 539+ |
| CI/CD workflows | 6 |
| ADRs | 8 |
| Documentation files | 100+ |
| Work orders | 25 |

---

## 7. Change Protocol

From this baseline onward:

1. **No architectural change** may be made without an approved ADR
2. **No frozen interface** may be modified without Architecture Review Board approval
3. **No new domain** may be created without ADR + Domain Map update
4. **No new widget SDK** may be created — all widgets use the canonical SDK
5. **No new architecture document** shall be created unless required by an ADR
6. **Compliance scores** are measured, not estimated — automated via `scripts/arch-compliance.ps1`
7. **Baseline deviations** are tracked as technical debt and must have a repayment plan

---

## 8. Sign-off

| Role | Status | Date |
|------|--------|------|
| Chief Architect | ⏳ Pending | — |
| CTO | ⏳ Pending | — |
| Engineering Team | ⏳ Pending | — |

---

*This baseline supersedes all prior architectural assumptions. All future work references this baseline.*
