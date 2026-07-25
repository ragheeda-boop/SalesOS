# Gate G-1: Architecture Review — SalesOS vNext Production Readiness

> **Gate**: G-1 | **Area**: Architecture Review | **Owner**: Chief Architect
> **Date**: 2026-07-17 | **Status**: ❌ FAIL

---

## Verdict

| Criterion | Result | Threshold |
|-----------|--------|-----------|
| Overall Compliance | **85–91%** | ≥ 95% for PASS, < 90% for FAIL |
| P0 Issues | **1 found** (Dual Widget SDK — ADR-003 violation) | 0 required |
| P1 Issues | **10 found** | ≤ 2 for PASS |
| **Verdict** | **❌ FAIL** | P0 issue present + compliance below threshold |

---

## Methodology

1. **Automated compliance scan**: Ran `scripts/arch-compliance.ps1` (6 checks across 1634 files)
2. **ADR audit**: Verified existence and completeness of all Architecture Decision Records
3. **Repository pattern audit**: Checked each domain for ABC interfaces + infrastructure implementations
4. **Domain boundary audit**: Verified no cross-domain imports via script + manual sampling
5. **Frozen interface audit**: Verified Identity and Widget SDK v1.0 surfaces for violations

---

## Findings

### P0 — Critical (1)

| ID | Domain | Rule | Description |
|----|--------|------|-------------|
| VIO-S0-01 | Widget SDK | ARC-3.4, ARC-9.1 | **Dual Widget SDKs**: ADR-003 froze Dashboard SDK v1.0, but `packages/workspace/` v5 contains a duplicate `createWidget()` with different implementation. ADR-0032 (Proposed) identifies this violation but is not yet accepted. Two `createWidget()` factories exist with overlapping but non-identical surfaces. This violates Engineering Constitution §3.4 (Frozen Interface) and §9.1 (Widget SDK mandatory). |

### P1 — High (10)

| ID | Domain | Rule | Description |
|----|--------|------|-------------|
| VIO-1 | Company Intelligence | ARC-9.1 | **Missing Container/View**: `company-360` widget has only raw components (`ActivityTimeline.tsx`, `DecisionPlatformPanel.tsx`, `KnowledgeGraphPanel.tsx`) without `*Container.tsx` + `*View.tsx` separation |
| VIO-5 | Cross-cutting | DF-4.1 | **localStorage business data**: `frontend/src/app/(dashboard)/settings/page.tsx` stores business data in localStorage instead of API-backed persistence |
| VIO-S0-02 | Identity | ARC-3.3 | **Repository bypass**: Identity service uses raw `db.execute()` directly instead of `UserRepository`/`TenantRepository` interfaces |
| VIO-S0-03 | Backend | Code quality | **main.py at 908 lines** exceeds 600-line limit (PROJECT_BIBLE §12.2.7) |
| VIO-S0-04 | Frontend | Code quality | **api.ts at 1734 lines** exceeds 600-line limit (PROJECT_BIBLE §12.2.7) |
| VIO-S0-05 | Backend | Migration | **init_db() bypasses Alembic** — creates tables via raw SQL, no Alembic baseline revision |
| VIO-S0-06 | Decision Center | ARC-3.3 | **InMemoryDecisionCenterRepository** still active in production — should be PostgreSQL |
| VIO-101 | Workflow | ARC-3.3 | **Domain at ~48%** — workflow domain implementation not started |
| VIO-102 | Timeline | ARC-3.3 | **Architecture redesign needed** — timeline at ~78%, repository pattern incomplete |
| VIO-2/3/4 | Cross-domain | DP-5.1 | **Scoring without Decision Platform**: 3 files (company-workspace.tsx, employee-360-page.tsx, KnowledgeGraphPanel.tsx) contain scoring/reasoning logic that bypasses the Decision Platform |

### P2 — Medium (4)

| ID | Domain | Rule | Description |
|----|--------|------|-------------|
| VIO-S0-07 | Decision Platform | DP-5.2 | **Frontend Decision Engine stub** throws "Not implemented" — implement or officially deprecate |
| VIO-S0-08 | Backend | Performance | **BodyCacheMiddleware** blocks downstream middleware in POST requests |
| ADR-GAP | Governance | ARC-3.1 | **Missing ADR files**: ADR-004 through ADR-0020 and ADR-0029 have no standalone markdown files (referenced in docs but not filed). ADR-004 (Kafka for Event Streaming) referenced in design docs but undocumented as a formal ADR. |
| VIO-6 | Cross-cutting | DF-4.2 | **Direct fetch()**: `frontend/src/components/employee-360-page.tsx` uses fetch() instead of centralized `lib/api.ts` |

---

## Domain-Level Compliance Scores

### Automated Script Results (arch-compliance.ps1)

| Domain | Score | Status |
|--------|-------|--------|
| Identity | **100%** | 🟢 PASS |
| Widget SDK | **100%** (script) / **70%** (measured) | 🟢 SCRIPT / 🔴 MEASURED |
| Company | **95%** | 🟢 PASS |
| Search | **93%** | 🟡 NEAR |
| Scoring | **95%** | 🟢 PASS |
| CRM | **90%** | 🟡 NEAR |
| AI | **75%** | 🟡 IMPROVING |
| Timeline | **75%** | 🟡 NEEDS REDESIGN |
| Workflow | **96%** | 🟢 PASS (frontend only — backend not started) |
| **Overall (script)** | **91%** | 🟡 BELOW TARGET |
| **Overall (measured)** | **~85%** | 🔴 BELOW TARGET |

### Measured Scores (ARCHITECTURE_COMPLIANCE.md)

| Domain | Score | Status | Notes |
|--------|-------|--------|-------|
| Identity | 100% | 🟢 | Frozen interface — minor repo bypass issue (P1) |
| Widget SDK | 70% | 🔴 | Dual SDK violation (P0) |
| Company | 95% | 🟢 | Minor code smells only |
| Search | 88% | 🟡 | Repository pattern gaps |
| Scoring | 92% | 🟡 | InMemoryDecisionCenterRepository active |
| CRM | 88% | 🟡 | Monolithic api.ts |
| AI | 82% | 🟡 | No evaluation framework |
| Timeline | 78% | 🟡 | Architecture refactoring incomplete |
| Workflow | 48% | 🔴 | Implementation not started |

---

## Architecture Check Results

### 1. Domain Boundaries
- **Cross-domain imports**: ✅ 0 violations found across 1634 scanned files
- **Backend domains**: 19 domains in `backend/domains/` with clean separation
- **SDK layer**: `backend/sdk/` provides canonical cross-domain communication

### 2. Repository Pattern
| Domain | Interface | InMemory | PostgreSQL | Status |
|--------|-----------|----------|------------|--------|
| Workflow | `WorkflowRepository` ABC | `InMemoryWorkflowRepository` | `postgres_repo.py` | ✅ |
| Search | `SearchRepository` ABC | — | — (domain contract only) | 🟡 needs infra impl |
| Timeline | `TimelineRepository` ABC | — | — (in progress) | 🟡 refactoring |
| Employee | `EmployeeSignalRepository` ABC | — | `postgres_repo.py` | ✅ |
| Identity | `UserRepository`/`TenantRepository` | — | Via `SqlAlchemyRepository` | ✅ |
| Scoring | — | — | `postgres_repository.py` | ✅ |

### 3. Frozen Interfaces
| Interface | ADR | Status | Notes |
|-----------|-----|--------|-------|
| Identity | No specific ADR | ✅ No unauthorized changes found | Dashboard lists as "Frozen interface" — recommend formal ADR |
| Widget SDK v1.0 | ADR-003 | ❌ **Violated** | Workspace v5 creates duplicate `createWidget()` — ADR-0032 proposed but not accepted |

### 4. ADR Coverage
| Range | Status | Notes |
|-------|--------|-------|
| ADR-001 to ADR-003 | ✅ Filed | `engineering-os/adr/` |
| ADR-004 to ADR-020 | ❌ **Missing** | Referenced in docs (ADR-004: Kafka, ADR-005+) but no standalone files |
| ADR-0021 to ADR-0028 | ✅ Filed | `backend/docs/adr/` |
| ADR-0029 | ❌ **Missing** | Gap in numbering |
| ADR-0030 to ADR-0031 | ✅ Filed | `docs/adr/` |
| ADR-0032 | 📝 Proposed | Widget SDK reconciliation — not yet accepted |

### 5. Automated Compliance Check
- **Executed**: `pwsh scripts/arch-compliance.ps1`
- **Result**: 66/72 checks passed (91%), 6 violations found
- **Duration**: 7.7s over 1634 files

---

## Recommendations

### Immediate (Pre-GA, P0 resolution)

1. **Resolve Dual Widget SDK (P0)**: Accept ADR-0032 and consolidate `packages/workspace/` to depend on canonical `@salesos/widget-sdk`. Remove duplicate `createWidget()` before GA. This blocks the gate.

### Short-term (Sprint 0.5, P1 resolution)

2. **Fix company-360 Container/View**: Refactor `company-360` components into Container/View pattern per ARC-9.1
3. **Migrate Identity to repository pattern**: Route all Identity DB access through `UserRepository`/`TenantRepository`
4. **Move InMemoryDecisionCenterRepository to PostgreSQL**: Eliminate in-memory persistence in production
5. **Add Alembic baseline**: Replace raw SQL in `init_db()` with proper migration
6. **Refactor scoring logic to Decision Platform**: Convert 3 files (company-workspace, employee-360-page, KnowledgeGraphPanel) to use `useDecision()` or `ScoringEngine`
7. **Remove localStorage business data**: Move settings persistence to API-backed storage

### Medium-term (Sprint 1–2, P1–P2 resolution)

8. **Split main.py (908 lines)**: Extract into modular startup files
9. **Split api.ts (1734 lines)**: Split by domain
10. **File missing ADRs**: Create standalone ADR files for ADR-004 through ADR-0020 and ADR-0029
11. **Implement Timeline repository pattern**: Complete architecture refactoring
12. **Implement or deprecate Decision Engine stub**: Frontend stub currently throws "Not implemented"
13. **Fix BodyCacheMiddleware**: Ensure POST body is available to downstream middleware
14. **Replace direct fetch()**: Use centralized `lib/api.ts`

---

## Gate Requirements Checklist

| Requirement | Status | Evidence |
|-------------|--------|----------|
| No cross-domain imports | ✅ PASS | 0 violations found in 1634 files scanned |
| Repository pattern in all domains | 🟡 CONDITIONAL | All domains have interfaces; Workflow and Timeline need infra completion |
| Frozen interfaces unchanged | ❌ FAIL | Widget SDK v1.0 surface violated by Workspace v5 (`createWidget()` duplicate) |
| ADR coverage | 🟡 CONDITIONAL | 15 ADRs present (001-003, 0021-0028, 0030-0032); ADR-004 to ADR-020 and ADR-0029 missing |
| Compliance ≥ 95% | ❌ FAIL | 91% (script) / ~85% (measured) |
| 0 P0 issues | ❌ FAIL | 1 P0 (Dual Widget SDK) |
| ≤ 2 P1 issues | ❌ FAIL | 10 P1 findings |

---

## Sign-off

| Role | Sign-off | Date |
|------|----------|------|
| Chief Architect | ❌ Not signed — P0 issue unresolved | — |
| Backend Architect | ❌ Awaiting chief sign-off | — |
| Frontend Architect | ❌ Awaiting chief sign-off | — |
| SDK Architect | ❌ Awaiting chief sign-off | — |

**Next step**: Resolve P0 issue (Dual Widget SDK — accept ADR-0032, consolidate to single SDK), then re-run Gate G-1.
