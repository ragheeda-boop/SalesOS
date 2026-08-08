# APPENDIX B — Existing Audit Claim Verification

Cross-check of `docs/vnext/reports/*` and `docs/audit/current-state/*` against repository + runtime evidence (2026-07-22).

| Claim | Source | Status | Evidence | Notes |
|-------|--------|--------|----------|-------|
| GA GO; 0 P0; 0 P1; 15/15 gates | `GO_NO_GO_DECISION.md`, `GA_CHECKLIST.md` | **CONTRADICTED** | Lint/TS/build fail; alembic drift; unit tests not green | Docs appear aspirational / post-hoc without current CI green |
| PRC NO-GO; Dual Widget SDK P0 | `PRODUCTION_READINESS_REPORT.md`, `OPEN_ISSUES.md` | **PARTIALLY STALE** | Workspace uses `createWidget` from `@salesos/widget-sdk` | Dual-SDK P0 fixed; overall NO-GO still correct for other reasons |
| `main.py` 908 lines | OPEN_ISSUES VIO-S0-03 | **STALE (fixed)** | `salesos/backend/app/main.py` ~265 lines | Split into boot modules |
| `api.ts` 1734 lines | OPEN_ISSUES VIO-S0-04 | **STALE (fixed)** | `frontend/src/lib/api.ts` ~10 lines | Domain modules exist |
| InMemory Decision Center in prod | VIO-S0-06 | **STALE (fixed)** | `PostgresDecisionCenterRepository` in `boot/startup.py` | InMemory remains for tests only |
| init_db bypasses Alembic | VIO-S0-05 | **MOSTLY FIXED / REGRESSED OPERATIONALY** | Migration `0038` exists; **runtime DB not upgraded** | Code path improved; deploy state broken |
| Viewport missing | RESP-01 / G-9 | **STALE (fixed)** | `frontend/src/app/layout.tsx` exports `viewport` | |
| DR runbook missing | DR-03 | **STALE (fixed)** | `docs/ops/DR_RUNBOOK.md` | |
| OTel/Loki missing | OBS-01/02 | **PARTIAL** | Root compose has loki/otel/promtail; salesos compose does not | Split brain infra |
| Security 10/10 / 9.4/10 | current-state security + CHANGELOG claims | **OVERCLAIMED for GA** | Auth patterns strong; no pentest this audit; 422 auth errors; tests failing | Use **72/100** this audit |
| Webhooks unauthenticated SEC-001 | `TECHNICAL_DEBT.md` | **STALE (fixed)** | `modules/webhooks/router.py` router deps include `verify_token` | |
| GraphQL unauthenticated SEC-003 | TECHNICAL_DEBT | **STALE (fixed)** | `graphql/schema.py` context requires Bearer | Returns 401 |
| JWKS empty key SEC-004 | TECHNICAL_DEBT | **STALE (fixed)** | JWKS returns RSA `v2-rs256` | |
| AGENTS.md required | user rules | **CONFIRMED MISSING** | Root/salesos glob 0 files | Governance gap |
| multi-product platform | User rules / implied vision | **CONTRADICTED by repo** | Grep 0 hits for AuditOS/DecisionOS/LocalContentOS | Bible = SalesOS Project Bible |
| Overall maturity 7.5/10 | `01-executive-summary.md` | **STALE optimistic** | Build/runtime evidence lower | Recalibrated Production Readiness **42** |
| 2110+ tests 100% pass | repository map | **UNVERIFIABLE / CONTRADICTED** | Partial unit run not green; e2e not run | Do not cite as true |
| Stub runtimes | current-state map | **CONFIRMED** | agent/workflow/scheduler/execution/simulation ~1 line each | |
| BodyCacheMiddleware exists | PERF-01 remediation | **CONFIRMED present** | `common/middleware.py` BodyCacheMiddleware | Residual risk if mis-ordered not fully re-proven under load |

## Internal documentation contradiction

Same PRC cycle contains:

- `GO_NO_GO_DECISION.md` → **GO**
- `PRODUCTION_READINESS_REPORT.md` → **NO-GO**
- `GA_CHECKLIST.md` → all gates PASS
- `OPEN_ISSUES.md` → P0 + 10 P1 open

**Finding (P1 DOC-CONFLICT):** Release governance artifacts are not a single source of truth. CTO must treat **executable evidence** as authoritative over checklist markdown.
