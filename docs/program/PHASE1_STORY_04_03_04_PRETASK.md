# Phase 1 — STORY-04-03 / STORY-04-04 Backend slice

> **Stream:** Backend A · Sprint 05 stories after STORY-04-01/02 LANDED  
> **Honesty:** Not Production GO. DEC-085 untouched. BE-only.

## STORY-04-03 — Suspend read-only (LANDED this wave)

| Layer | Mechanism |
|-------|-----------|
| App | `SuspendedTenantWriteGuardMiddleware` — blocks POST/PUT/PATCH/DELETE when `provisioning_status=suspended` |
| Gateway | `ApiKeyMiddleware` — same write block for `X-API-Key` callers |
| Skip | `/api/v1/admin`, `/api/v1/auth`, health/docs (Owner can still activate) |

## STORY-04-04 — Retention (LANDED column cutover)

| Item | Detail |
|------|--------|
| Soft-delete | Stamps `tenants.deleted_at` + settings dual-write |
| Activate | Clears column + settings stamp |
| Hard-delete | If stamp present, enforce `tenant_deletion_retention_days` (default 30) unless `force_immediate=true` |
| Alembic | `d4b0e23f5a91` |
| Config | `Settings.tenant_deletion_retention_days` |

## Non-goals

- Gateway edge proxy outside this FastAPI process  
- Dropping settings dual-write key  
- Production GO / GA GO
