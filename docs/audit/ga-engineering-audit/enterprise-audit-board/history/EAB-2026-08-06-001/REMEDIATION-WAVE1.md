# Remediation Wave 1 — EAB-2026-08-06-001

**Date:** 2026-08-06  
**Trigger:** Human «التالي» after Production GA NO-GO  
**Scope:** Highest-priority **code-fixable** P0s (enforcement + isolation half + FE SSR shell)  
**Validation:** **light validated** (Grep/Read spot-check only; no pytest / npm / runtime boot)  
**Verdict impact:** Does **not** change Production GA **NO-GO**. No commit.

---

## Findings addressed (partial)

| Finding ID | Wave 1 action | Status after Wave 1 |
|------------|---------------|---------------------|
| **EAB-001-P0-SEC-01** | Wired `app.state.db_session_factory = async_session` at startup (before testing early-return); entitlement / suspended-tenant / API-key middleware fail-closed with **503** if factory unset | **code-fixed; runtime not validated** |
| **EAB-001-P0-SEC-02** | **Safe half only:** refuse empty `APP_POSTGRES_PASSWORD` when `ENV` ∈ `{production,prod,staging,stage}` (no silent BYPASSRLS owner fallback). Dev/test fallback retained. | **partial** — lifetime AsyncSession singletons **still open** |
| **EAB-001-P0-FE-01** | Providers SSR-safe (Wave 1). Stream B: `@import "@salesos/tokens/css"` into globals; duplicate `:root` removed; `--color-*` / convenience aliases added to tokens. | **code-fixed; build not validated** |
| **EAB-001-P0-DUP-01** | Out of scope | **open** |
| **EAB-001-P0-OPS-01** | Out of scope | **open** |

---

## Files changed

| File | Change |
|------|--------|
| `salesos/backend/app/boot/startup.py` | Set `app.state.db_session_factory = async_session` before any early return |
| `salesos/backend/app/modules/admin/entitlement_middleware.py` | Fail-closed 503 if factory missing |
| `salesos/backend/app/modules/identity/suspended_tenant_middleware.py` | Fail-closed 503 if factory missing |
| `salesos/backend/app/modules/api_keys/middleware.py` | Fail-closed 503 if `X-API-Key` present and factory missing |
| `salesos/backend/app/config.py` | Raise `RuntimeError` on empty app password in non-dev envs |
| `salesos/backend/app/database.py` | Comment aligned with refuse-in-non-dev behavior |
| `salesos/frontend/src/app/providers.tsx` | SSR-safe provider shell (no null gate) |
| `salesos/frontend/src/app/globals.css` | Wave 1 `--bg-muted`; Stream B: import `@salesos/tokens/css`, remove duplicate `:root` |
| `salesos/frontend/packages/tokens/src/tokens.css` | `--bg-muted` + Stream B semantic `--color-*` / convenience aliases |

---

## Spot-check evidence (light)

- `startup.py`: `app.state.db_session_factory = async_session` present before `SALESOS_TESTING` early return.
- Middleware paths: all three read `db_session_factory` and return 503 when unset (no pass-through).
- `config.app_database_url`: production/staging empty password raises; development still falls back to `resolved_database_url`.
- `providers.tsx`: no `if (!ready) return null`.

**Not run:** full pytest, npm lint/build, Docker boot, live middleware probe.

---

## Residual risk

1. **Process-lifetime sessions** (`_timeline_session`, `_fs_repo_session`, `_dc_session`, `_opportunity_session`, `_workflow_session`) still lack per-request tenant GUC — isolation risk remains for those service paths (SEC-02 remainder).
2. **Dev/test owner fallback** still exists when `APP_POSTGRES_PASSWORD` empty — intentional for local boot; must never ship with `ENV=production|staging` unset password.
3. **Legacy** `salesos/backend/app/startup.py` not updated (main uses `boot/startup.py` only).
4. **FE token SoT:** Stream B wired `@import "@salesos/tokens/css"`; globals no longer duplicates `:root` — **build not validated**.
5. **Decision engines / DR / dual compose / MetaData** — untouched (out of Wave 1).
6. Staging/prod deploys **must** have `APP_POSTGRES_PASSWORD` set or boot will fail closed (intended).

---

## Recommended «التالي» (Wave 2)

1. **Runtime verify** SEC-01/02 half: Docker boot + gated path returns 403/503 with factory live; confirm staging env has app role password.
2. **SEC-02 remainder:** replace lifetime AsyncSessions with `session_factory` + DEC-085 GUC (timeline / DC / workflow / opportunity / feature-store domain).
3. **P0-DUP-01:** pick single Decision API SoT; deprecate colliding mounts behind flags.
4. FE token SoT import completed in Stream B (build validate when approved).

---

*Wave 1 — EAB-2026-08-06-001 — light validated — production no-go unchanged — no commit*
