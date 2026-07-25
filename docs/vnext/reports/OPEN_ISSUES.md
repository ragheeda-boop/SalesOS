# Open Issues — SalesOS vNext

> ## SUPERSEDED AS ISSUE REGISTER — 2026-07-22
>
> Many items below are **stale** (fixed or reframed). Do not use this list for GO/NO-GO.  
> **Authoritative findings:** [APPENDIX-C-FINDINGS-REGISTER.md](../../audit/ga-engineering-audit/APPENDIX-C-FINDINGS-REGISTER.md)  
> **Program backlog:** [PRODUCTION_PLAN.md](../../audit/ga-engineering-audit/PRODUCTION_PLAN.md)

---

> **Updated**: 2026-07-16
> **Status**: Pre-GA — Tracking all known issues before release *(historical; SUPERSEDED 2026-07-22)*

---


## P0 — Critical (1)

| ID | Domain | Issue | Impact | Remediation | Effort |
|----|--------|-------|--------|-------------|--------|
| VIO-S0-01 | Widget SDK | Dual Widget SDK — ADR-003 frozen interface violated by workspace v5 duplicate. Engineering Constitution §3.4, §9.1. | Blocks GA and Pilot. Widget inconsistency across dashboard and workspace. | Accept ADR-0032, consolidate to single SDK, remove duplicate | 3d |

---

## P1 — High (10)

| ID | Domain | Issue | Impact | Remediation | Effort |
|----|--------|-------|--------|-------------|--------|
| VIO-1 | Company | Missing Container/View in company-360 widget | Architecture pattern violation | Add *Container.tsx + *View.tsx wrappers | 2d |
| VIO-5 | Settings | localStorage business data instead of API-backed persistence | Data loss risk on browser clear | Migrate to PostgreSQL-backed store | 1d |
| VIO-S0-02 | Identity | Repository bypass — raw db.execute() instead of UserRepository interface | Architecture pattern violation | Refactor to use repository interfaces | 1d |
| VIO-S0-03 | Backend | main.py at 908 lines (limit: 600) | Maintainability | Split into smaller modules | 1d |
| VIO-S0-04 | Frontend | api.ts at 1734 lines (limit: 600) | Maintainability | Split by domain | 2d |
| VIO-S0-05 | Migration | init_db() bypasses Alembic — no baseline revision | Migration chain broken | Create Alembic baseline revision | 1d |
| VIO-S0-06 | Decision Center | InMemoryDecisionCenterRepository in production | Data loss on restart | Migrate to PostgreSQL repository | 2d |
| VIO-101 | Workflow | Domain at ~48% implementation | Feature gaps | Continue workflow implementation | 3d |
| VIO-102 | Timeline | Architecture redesign needed, repository pattern incomplete | Maintainability | Complete repository pattern | 2d |
| VIO-2/3/4 | Cross-domain | Scoring/reasoning logic bypassing Decision Platform in 3 files | Inconsistent scoring | Route through Decision Platform | 2d |

---

## P2 — Medium (15+)

| ID | Domain | Issue | Effort |
|----|--------|-------|--------|
| VIO-S0-07 | Decision Platform | Frontend Decision Engine stub throws "Not implemented" | 1d |
| VIO-S0-08 | Performance | BodyCacheMiddleware blocks downstream middleware in POST | 1d |
| ADR-GAP | Governance | ADR-004 through ADR-0020 missing standalone markdown files | 2d |
| VIO-6 | Frontend | Direct fetch() in employee-360-page.tsx instead of centralized api.ts | 1d |
| UX-01 | Frontend | Hardcoded colors breaking dark mode in 7 pages | 1d |
| UX-02 | Frontend | Forecast & Register pages not using @salesos/ui | 1d |
| UX-03 | Frontend | Inline empty/error states in 5 pages | 1d |
| UX-04 | Frontend | RTL: right-3 hardcoded in search page | 30min |
| A11Y-01 | Frontend | Register page missing id/htmlFor on inputs | 15min |
| A11Y-02 | Frontend | Search pagination chevrons lack aria-label | 15min |
| A11Y-03 | Frontend | Copilot clear-all button has title only, no aria-label | 15min |
| A11Y-04 | Frontend | Active nav links lack aria-current="page" | 15min |
| E2E-01 | Backend | Employee domain metadata column name conflicts with SQLAlchemy | 1d |
| E2E-02 | CI | E2E tests missing CI test credentials | 30min |
| RESP-01 | Frontend | Viewport meta tag missing from root layout.tsx | 15min |
| DR-01 | Infrastructure | PITR/WAL archiving not configured | 2d |
| DR-02 | Infrastructure | No multi-region DR strategy | 3d |
| DR-03 | Docs | No DR runbook | 1d |
| OBS-01 | Infrastructure | OTel collector not deployed | 2d |
| OBS-02 | Infrastructure | No log shipping to Loki | 1d |
| DOC-01 | Docs | Missing root Muhide/README.md | 1d |
| DOC-02 | Docs | No OpenAPI/Swagger spec committed | 1d |
| DOC-03 | Docs | ADR index incomplete | 1d |
| DOC-04 | Docs | Core docs English-only (no Arabic) | 2d |
| RC-01 | Release | Missing v3.0.0-RC CHANGELOG entry | 30min |

---

## Deferred (Post-GA)

| ID | Domain | Reason |
|----|--------|--------|
| TD-002 | Event Bus | Kafka migration deferred to post-GA (Phase 18) |
| TD-005 | Authorization | Pending full authorization review post-GA |
| OBS-03 | Tracing | Distributed tracing deferred to performance sprint |

---

## Remediation Summary

| Priority | Count | Total Effort |
|----------|-------|-------------|
| P0 | 1 | 3d |
| P1 | 10 | 17d |
| P2 | 25+ | ~20d |
| Deferred | 3 | — |
| **Total** | **39** | **~40 days** |
