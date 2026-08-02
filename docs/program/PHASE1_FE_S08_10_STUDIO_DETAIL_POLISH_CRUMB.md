# FE-S08-10 — Studio connection detail + baseline_fields polish (Stream B)

> **Date:** 2026-08-02  
> **Owner:** Frontend Lead  
> **Tip base:** Hub HTTP STORY-08-06 + FE-S08-09  
> **Honesty:** Not Production GO. No invented Hub routes / unlinked badge list.  
> `TenantList.tsx` untouched.

## Landed

| Piece | Detail |
|-------|--------|
| Connection detail | Tip fields: id, connector_key, is_active, credential_ref, cursor_state |
| Map | `baseline_fields` csv → tip mapping create body; hydrate from active GET |
| Monitor | Refresh sync runs (tip GET `/sync-runs`) |
| Disconnect | Confirm checkbox before deactivate |
| Command palette | `go.integrations` → `/integrations` |
| Tests | Studio detail/baseline/disconnect Jest + commands count |

## Non-goals

- Unlinked cr_number badge list API (BE-blocked)
- Owner mint / Production GO
