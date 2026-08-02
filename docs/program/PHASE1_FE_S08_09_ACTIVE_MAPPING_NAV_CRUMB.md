# FE-S08-09 — Active mapping load + tenant Integrations nav (Stream B)

> **Date:** 2026-08-02  
> **Owner:** Frontend Lead  
> **Tip base:** Hub HTTP STORY-08-06 + FE-S08-08  
> **Honesty:** Not Production GO. No invented Hub routes. `TenantList.tsx` untouched.

## Landed

| Piece | Detail |
|-------|--------|
| Hook | `useActiveHubMapping` → GET `/connections/{id}/mappings/active` |
| Map step | Load active mapping into editor + status line |
| Connect | Optional non-secret `connection_config` JSON (tip field) |
| Nav | Tenant sidebar + MobileNav `/integrations` (`nav.integrations`) |
| Tests | Active mapping client Jest + Map-step Studio Jest |

## Non-goals

- Unlinked cr_number badge list API (BE residual)
- Owner mint / Production GO
