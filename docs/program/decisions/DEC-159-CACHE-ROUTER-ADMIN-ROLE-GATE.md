# DEC-159 — Gate /api/v1/cache/* behind the "admin" role, not just any authenticated user (Accepted — CLOSED)

> **Status:** **Accepted — CLOSED 2026-09-23.**
> **Date:** 2026-09-23
> **Board:** Backend Platform / Security (SalesOS)
> **Finding:** `project-audit/63_CACHE_SERVICE_GRACEFUL_FAILOVER_CLOSURE_2026-09-23.md`, "Next code-reachable work" item 1
> **Out of scope:** the repeated-failure circuit breaker noted in the same report (item 2) — a separate, unrelated performance improvement, not touched here

---

## 1. Decision

**Accepted.** `/api/v1/cache/*` (`app/modules/cache/router.py`) now requires
the tenant "admin" role (`Depends(require_role_dep("admin"))`), not just any
authenticated user (`verify_token` alone, as before).

## 2. Why

This router exposes raw, caller-supplied-key `get`/`set`/`delete` plus a
wildcard `flush(pattern="*")` with **no per-key ownership or tenant-prefix
check** — any authenticated user, regardless of role, could previously read
or overwrite any cache key (including another tenant's, if they could guess
or discover its naming scheme, e.g. `company:<tenant>:<id>`) and flush the
entire shared cache with the default pattern. This is a materially wider
blast radius than a typical per-tenant business-resource endpoint (contacts,
opportunities, etc.), which is scoped by the authenticated tenant's own data.
There is no legitimate reason for an ordinary tenant user to hold this power
over shared infrastructure; the existing `require_role_dep("admin")`
mechanism (already used the same way by `app/routers/metrics.py`,
`benchmarks.py`, and others for infra/ops-level routers) is the correct,
already-established fit — simpler than inventing a new
`PermissionAction`/resource pair for a router that is not a specific
business resource.

## 3. What was NOT changed

- No change to `CacheService`/`RedisCache`'s public API or failover
  behavior (that was report 62/63's separate, already-closed fix).
- No new Postgres role, no RLS, no tenant-prefix enforcement added to the
  cache key namespace itself — this DEC closes the *access* gap (who may
  call these endpoints at all), not a *tenant-key-isolation* gap within the
  shared cache. A caller who legitimately holds "admin" for their own tenant
  can still, in principle, read/overwrite a cache key belonging to another
  tenant's naming scheme if they can guess it — this DEC does not claim to
  close that; it only removes the "any authenticated user, any role" surface.
  If the cache is ever used to hold sensitive per-tenant data that must not
  be readable by another tenant's admin, that is a separate, larger finding
  requiring key-namespace enforcement, not addressed here.
- The repeated-failure circuit breaker noted alongside this in report 63
  (item 2) — unrelated performance work, not touched.

## 4. Verification

- `app/modules/cache/router.py`: `Depends(verify_token)` → `Depends(require_role_dep("admin"))` at the `APIRouter(...)` level (covers all 5 endpoints: `/health`, `GET /{key}`, `POST /set`, `DELETE /{key}`, `POST /flush`). `require_role_dep("admin")` already depends on `verify_token` transitively via `get_current_user_role`, so no separate `verify_token` dependency is needed.
- `tests/unit/test_cache_admin_router.py` updated: overrides `get_current_user_role` (the stable, importable sub-dependency) instead of `verify_token`, since `require_role_dep(...)` is a factory producing a fresh closure per call and cannot be matched by identity from a second, separate call in test code. Added `test_non_admin_role_is_rejected_on_every_endpoint` (role="user", all 5 endpoints return 403) and `test_manager_role_is_also_rejected_admin_only` (role="manager" — confirms the role hierarchy's true admin-only cutoff, not just "not user").
- **Genuine red→green**: reverted the router to its pre-DEC-159 state (`verify_token` only), re-ran — all 6 tests failed, the 4 originally-passing tests now failing with `401` (no `verify_token` override present in the reverted test setup, matching exactly what would happen against the real endpoint with an anonymous caller) and the 2 new role-check tests failing with `assert 401 == 403`. Restored the fix, re-ran — 6/6 PASS.
- Full local `tests/unit/` regression: 3765 passed (up from 3763 — the 2 new tests), 1 pre-existing unrelated failure (`test_db05_slice4_deferred_8_rls_authority.py`, predates this session).
- No other test file references this router or depends on its previous permissive behavior (confirmed via grep).
- `app/boot/routers.py` also applies `dependencies=_auth` (`[Depends(verify_token)]`) at `include_router()` time for this and several other routers — this is pre-existing boilerplate, harmless alongside the new stricter router-level dependency (FastAPI dependency caching de-duplicates the repeated `verify_token` call; the new `require_role_dep("admin")` adds the actual tightening).

## 5. Records

- Finding: `project-audit/63_CACHE_SERVICE_GRACEFUL_FAILOVER_CLOSURE_2026-09-23.md` ("Next code-reachable work" item 1)
- `DECISION_LOG.md` entry: this DEC, filed above DEC-158
- **Not claimed:** cache key-namespace tenant isolation, the circuit-breaker performance fix, production readiness, or Phase 7 progress
