# DEC-093 — JWT audience consumption CLOSED on Owner Platform admin

**Date:** 2026-08-01  
**Status:** Accepted  
**Product:** SalesOS  
**Owners:** Backend / Security  
**Related:** STORY-02-03 (`2379e5f` groundwork); DEC-091 (verify; keep OPEN — **superseded for consumption status**); Phase 0 DEC-008 GO (DEC-086)

---

## Context

DEC-091 kept **JWT audience consumption OPEN** because no router dependency called `decode_owner_*`. User authorized consumption: wire Owner Platform routes to `salesos-owner-platform` without weakening tenant `salesos-api` / `verify_token`.

## Decision

1. **Consume** owner audience on Platform admin (`app/modules/admin`, `/api/v1/admin/*` shell): router deps use `require_owner_role_dep` → `verify_owner_token` → `decode_owner_access_token` (`app/owner_auth.py`).
2. Scoped audit/AI-audit admin endpoints use `get_owner_scoped_tenant_id` (requires `X-Tenant-Id`; owner JWT has no `tenant_id`).
3. **Do not weaken** tenant path: `verify_token` → `decode_access_token` → audience `salesos-api` unchanged. Owner tokens still rejected on tenant deps.
4. **Do not edit** `get_db` / `SET LOCAL` (DEC-085 `set_config` only).
5. Mark JWT audience **consumption CLOSED** on board/DAG. STORY-02-03 groundwork remains DONE. Owner login mint UX was follow-up — **closed 2026-08-06** (see Follow-up closeout).
6. **Production GA / External pilot = NO-GO** unchanged. **CI GREEN not met.**

## Alternatives considered

- (a) Dual-accept tenant+owner on admin — rejected (weakens audience split).
- (b) Wait for full EPIC-04 Owner Console — rejected; existing Platform admin is the consumable Owner surface.
- (c) Patch tenant `dependencies.py` only — rejected after parallel overwrite risk; dedicated `owner_auth.py` isolates Owner deps.

## Evidence

| Check | Result |
|---|---|
| Owner dep accepts owner aud | `test_verify_owner_token_accepts_owner_audience` |
| Owner dep rejects tenant aud | `test_verify_owner_token_rejects_tenant_audience` |
| Tenant `verify_token` rejects owner | `test_verify_token_still_rejects_owner_audience` |
| Tenant `verify_token` accepts tenant | `test_verify_token_still_accepts_tenant_audience` |
| Admin router wires owner dep | `test_admin_router_wires_owner_role_dep` |
| Narrow pytest | `poetry run pytest tests/unit/test_jwt_audience_split.py -q` → **14 passed** |

## Follow-ups

- ~~Owner login / mint path for operators (EPIC-04/07).~~ **DONE** (2026-08-06) — see below.
- Optional adversarial HTTP TestClient suite against live `/api/v1/admin/tenants` (requires role+DB fixtures).
- Adjacent `/api/v1/admin/*` outside `modules/admin` (telemetry, benchmarks, SLA) remain tenant-gated — evaluate separately if they become Owner Console surfaces.
- Residual: dedicated Owner refresh rotation (token-family) — operators re-login at access expiry for now.

---

## Follow-up closeout — Owner login mint (2026-08-06)

**Status:** **DONE**  
**Validation:** **light validated** (route/source gate tests + greps; live HTTP bad-creds 401 spot-check; browser **not** claimed)

| Surface | Path / evidence |
|---|---|
| BE mint | `POST /api/v1/identity/owner/login` — authenticate → active `admin` role → `create_owner_access_token` / `create_owner_refresh_token` (`salesos-owner-platform`); audit `owner_login`; tenant `/login` unchanged |
| CSRF / suspension | Exempt + skip lists include owner login (same class as tenant login) |
| FE | `/admin/login` → `useOwnerLogin` → persist owner JWT; middleware public; Owner Console gate links to login |
| Unit | `tests/unit/test_jwt_audience_split.py` — **17 passed** (was 14; +owner login route/CSRF/suspension) |
| Live HTTP | After backend restart: OpenAPI lists `/api/v1/identity/owner/login`; bad password → **401** (not CSRF 403) |

**How to use (ops):**
1. Open `/admin/login` (or unauthenticated `/admin/*` redirects there).
2. Sign in with an **admin**-role user password.
3. Session stores `salesos-owner-platform` access JWT; navigate Owner Console `/admin`.
4. Tenant app remains `/login` → `salesos-api`.

**Honesty:** Does **not** claim Production GO, browser pass, or whole-pipeline CI GREEN. Owner refresh rotation family still residual.