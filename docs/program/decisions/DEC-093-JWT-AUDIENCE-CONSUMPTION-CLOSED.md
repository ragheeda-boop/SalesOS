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
5. Mark JWT audience **consumption CLOSED** on board/DAG. STORY-02-03 groundwork remains DONE. Owner login mint UX remains future EPIC work; mint helpers already exist.
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

- Owner login / mint path for operators (EPIC-04/07).
- Optional adversarial HTTP TestClient suite against live `/api/v1/admin/tenants` (requires role+DB fixtures).
- Adjacent `/api/v1/admin/*` outside `modules/admin` (telemetry, benchmarks, SLA) remain tenant-gated — evaluate separately if they become Owner Console surfaces.
