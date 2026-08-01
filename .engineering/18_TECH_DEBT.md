---
EngineeringOS: v3
GeneratedAt: 2026-08-01T20:10:52Z
RepositoryCommit: 9fa8e9f
RepositoryBranch: master
Generator: OpenCode
Status: Corrected (EOS v3.1 cycle)
EvidenceLevel: Measured
Revalidation: Active (DEC-142)
---

# 18 â€” TECH DEBT

> Recorded tech debt and structural defects. **Observation ledger â€” fixes are planned in `19`, executed per `25`, and never in this bootstrap.**

## 1. Debt items (severity)

| ID | Debt | Location | Sev | Found by |
|---|---|---|---|---|
| T-001 | SQL injection | `app/application/admin/data_quality.py` | CRITICAL | SEC audit (30 criticals) |
| T-002 | SQL injection | `app/modules/revenue_execution/service.py` | CRITICAL | SEC audit |
| T-003 | e2e CI job has no services | `ci.yml` | HIGH | SEC/CI finding |
| T-004 | `deploy.yml` undeclared outputs (`slot`, `image_tag`) | `deploy.yml` | HIGH | SEC/CI finding |
| T-005 | Event-bus split-brain (in_memory vs kafka) | compose vs k8s configmap | HIGH | observed |
| T-006 | Capability registry 4-way drift | 40 docs / 14 decorators / ~25 SDK / ~22 YAML | HIGH | observed (29 Â§4) |
| T-007 | Dual registry needs sync scripts to stay aligned | `runtime/capability_framework` + `sdk/capability_registry.py` | HIGH | EXEC-ARCHITECTURE-PRODUCT-REVIEW-2026-07-30 #9/#17 (DEBT-ARC-003, E-21) |
| T-008 | `@salesos/decision-platform` is a STUB (throws) | `frontend/packages/platform/decision/` | MEDIUM | AI_HONESTY.md |
| T-009 | 8 FE packages without `src` (13 with `src`); several stub/empty (no imports), incl. `@salesos/decision-platform` | `frontend/packages/*` | MEDIUM | heuristic (23) |
| T-010 | â‰¥10 single-file runtime dirs (workflow, agent, simulation, context, execution, memory, policy, recommendation, scheduler, widget); stub status heuristic, not individually proven | `runtime/` | MEDIUM | heuristic (23) |
| T-011 | ADR index/file conflicts (025/026/027/028 missing, 029 phantom, 032/033/034 conflicts) | `docs/adr/` | MEDIUM | observed (27) |
| T-012 | `server/server.js` permissive CORS (mock) | FE server | MEDIUM | observed |
| T-013 | Refresh-token family rotation enabled-state unverified (`0012_refresh_token_tables` in chain; live `alembic current` not run) | `app/alembic/versions/` | MEDIUM | retracted v3.0 "NOT enabled" claim |
| T-014 | Gitleaks config previously untracked/gitignored | repo | HIGH | SEC audit (verify current) |
| T-015 | Capability catalog self-inconsistencies | `docs/CAPABILITY_CATALOG.md` | MEDIUM | observed (29 Â§4 #7) |

## 2. Provenance

Aggregated from: `docs/vnext/TECHNICAL_DEBT.md` (registry), `security-audit-report-latest.json`, `docs/audit/ga-engineering-audit/`, `docs/audit/` architecture reviews, and direct repository observation (commit `3749c30`).

## 3. When this file changes

- Add items on discovery (observe-record). Do not remove history; mark `RESOLVED` with evidence when fixed (per `25`).
