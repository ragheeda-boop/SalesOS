# Remediation Wave 2 — EAB-2026-08-06-001

**Date:** 2026-08-06  
**Trigger:** Human mandate «كمل الكل» after Wave 1 — close remaining code-fixable P0s  
**Scope:** SEC-02 remainder (lifetime sessions), FE-01 tokens SoT, DUP-01 Decision HTTP SoT, SEC-03 ContextVar reset; SEC-04 hygiene  
**Streams:** A (BE sessions) · B (FE tokens) · C (Decision SoT) — parallel Task agents  
**Validation:** **light validated** (Grep/Read/AST + Docker probe; see [REMEDIATION-VERIFY.md](./REMEDIATION-VERIFY.md))  
**Verdict impact:** Does **not** change Production GA **NO-GO**. No commit.

---

## Findings addressed

| Finding ID | Wave 2 action | Status after Wave 2 |
|------------|---------------|---------------------|
| **EAB-001-P0-SEC-01** | Unchanged from Wave 1 (factory + fail-closed) | **code-fixed** (runtime light-probed) |
| **EAB-001-P0-SEC-02** | Replaced five process-lifetime `AsyncSession`s with `FactoryBoundRepository` + `tenant_scoped_session` (DEC-085 GUC); Wave 1 password refuse retained | **code-fixed** |
| **EAB-001-P0-FE-01** | `@import "@salesos/tokens/css"` SoT; deduped globals `:root`; semantic aliases; SSR shell kept | **code-fixed** (build not validated) |
| **EAB-001-P0-DUP-01** | Decision Center = canonical HTTP SoT; Runtime remounted `/api/v1/decision-runtime`; collisions cleared | **partial** — engines + FE twin name remain |
| **EAB-001-P1-SEC-03** | `TenantContextMiddleware` resets ContextVar Token in `finally` | **code-fixed** |
| **EAB-001-P1-AIGOV-01** | Labels + Decision SoT doc; `feature_ai_copilot` still False | **partial** |
| **EAB-001-P1-DUP-02** | Capability notes in DECISION-API-SOT (search dual already non-colliding) | **partial** (doc) |
| **EAB-001-P2-SEC-04** | Prod/staging compose pin empty `SALESOS_TESTING`; boot/CSRF ERROR if prod+flag | **mitigated** |

---

## Files changed (high level)

| Area | Files |
|------|-------|
| BE sessions | `salesos/backend/app/database.py`, `boot/startup.py`, `common/middleware.py`, `domains/timeline/engine/recorder.py`, `domains/workflow/event_subscriber.py` |
| Decision SoT | `salesos/backend/app/boot/routers.py`, `runtime/decision_runtime/router.py`, FE decisions page path update, e2e path strings |
| FE tokens | `salesos/frontend/src/app/globals.css`, `packages/tokens/src/tokens.css`, decision package README |
| Docs | `DECISION-API-SOT.md`, `STREAM-A-SEC-02-03.md` |
| Tests (expectations only) | `tests/unit/test_middleware.py`, `tests/e2e/test_critical_paths.py` |
| Compose hygiene | `salesos/docker-compose.prod.yml`, `infra/staging/docker-compose.staging.yml`, local `JWT_ALGORITHM: RS256` pin |
| TrustedHost fix (verify) | `salesos/backend/app/boot/middleware.py` — CORS origins ≠ TrustedHost hostnames |

---

## Spot-check evidence (light)

- Startup: no `app.state._timeline_session = sess` (count 0); `FactoryBoundRepository` used for timeline / FS / DC / opportunity / workflow.
- Middleware: `set_current_tenant_id` → try/finally `reset_current_tenant_id(token)`.
- Routers: Decision Runtime `prefix="/api/v1/decision-runtime"`.
- FE: globals starts with `@import "@salesos/tokens/css"`; providers still SSR-safe (no null gate).
- AST parse OK for `database.py`, `startup.py`, `middleware.py`, `routers.py`.
- Docker (pre-restart): `/health` → 200; `/api/v1/decisions` → 401; API-key probe → 401 (not fail-open skip).

**Not run:** full pytest, npm lint/build, browser pass.

---

## Residual risk

1. **DUP-01:** three decision engines still in tree; FE STUB vs `salesos/packages/platform/decision` twin name hazard remains.
2. **FactoryBoundRepository:** multi-step workflow updates are per-method commits (not one transaction).
3. **Legacy** `app/startup.py` may still hold lifetime-session pattern if ever used.
4. **FE build** not validated — token import path assumes Next resolves `@salesos/tokens/css`.
5. **OPS-01** / MetaData islands / fitness CI — Wave 3.

---

## Recommended Wave 3

1. OPS compose honesty + DR checklist deferral  
2. ADR-101/102, SES waiver, lineage map, bible banners, MetaData freeze, fitness plan  
3. Program status matrix + FINDINGS status sync  

---

*Wave 2 — EAB-2026-08-06-001 — light validated — production no-go unchanged — no commit*
