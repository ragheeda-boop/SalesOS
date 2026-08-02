# Phase 1 Stream A — server sort + lifecycle response honesty

> **Stream:** Backend · tip follow-on after `d9d1472` activate  
> **Honesty:** Not Production GO. DEC-085 untouched. BE-only.

## Landed

| Item | Detail |
|------|--------|
| `sort` query | GET `/admin/tenants?sort=` — `created_desc` (default) / `created_asc` / `name_asc` / `name_desc` (FE-S04-19 keys) |
| Lifecycle response | `TenantLifecycleResponse` on suspend / activate / soft-delete |
| Soft-delete honesty | `is_active=false` only — **does not** set `provisioning_status=suspended` |

## Non-goals

- FE wire of `sort` / `/activate` (Stream B)  
- Production GO / GA GO
