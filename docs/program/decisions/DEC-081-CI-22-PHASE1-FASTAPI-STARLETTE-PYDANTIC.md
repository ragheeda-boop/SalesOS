# DEC-081 — CI-22 Phase 1 (C1+C2): FastAPI / Starlette / Pydantic cascade land

> **Status:** **Accepted** (execution land)  
> **Date:** 2026-08-01  
> **Board:** Backend + Security (SalesOS)  
> **Story / risk:** CI-22 / R-21 starlette leg  
> **Authority:** DEC-054 register · DEC-073 plan (C0) · user full approval (run+push)  
> **Out of scope:** ecdsa / PyJWT migration · CI-16 reopen · auth/CSRF/RBAC weakening · Railway · CI-14

---

## 1. Scope (DEC-073 slices C1+C2)

| Package | Before (lock) | After (lock) | Constraint |
|---|---|---|---|
| `fastapi` | 0.111.1 | **0.141.1** | `>=0.136.0,<0.142.0` |
| `starlette` | 0.37.2 | **1.3.1** | **explicit** `>=1.3.1,<2.0` (FastAPI alone only requires ≥0.46) |
| `pydantic` | 2.8.2 | **2.13.4** | `>=2.9,<3` |
| `email-validator` | transitive only (FastAPI extras) | **2.3.0** (direct) | `>=2.0,<3` — required for pydantic `EmailStr` under bare fastapi≥0.136 |

## 2. Minimal app fixes (C3 lite)

FastAPI ≥0.136 rejects `Request | None = None` / `Request = None` as route param fields:

- `app/application/dashboard/router.py` → `request: Request`
- `runtime/knowledge_graph_runtime/router.py` → `request: Request` (2 sites)
- `Dockerfile`: copy `poetry.lock` with `pyproject.toml` (lock-faithful image install)

No auth/CSRF/RBAC middleware logic changed.

## 3. Decision

Accept CI-22 **Phase 1** as COMPLETE for the cascade land. Move board **REGISTERED → IN PROGRESS** (Phase 1 COMPLETE). Update R-21 starlette leg. Keep CI-22 OPEN for residual compatibility / field `pip-audit` corroboration. Do **not** claim CI GREEN. Do **not** reopen CI-16.

## 4. Validation

| Check | Result |
|---|---|
| Poetry lock | **fastapi 0.141.1 / starlette 1.3.1 / pydantic 2.13.4 / email-validator 2.3.0** |
| Host import `app.main` | **PASS** (`FastAPI SalesOS API`, 78 routes) |
| Host mypy `main.py` + `dashboard/router.py --follow-imports=skip` | **0** errors |
| Host pytest graphql introspection + middleware + post_middleware | **49 passed** |
| Host `pip-audit` (poetry export) | **NO starlette**; residual **ecdsa 0.19.2** only (DEC-057 accepted) |
| Label | **light validated** |

**CI GREEN not met.** Field Security Scan / full CI corroboration may trail.
