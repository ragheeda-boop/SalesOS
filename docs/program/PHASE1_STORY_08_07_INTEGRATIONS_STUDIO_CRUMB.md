# STORY-08-07 — Integrations Studio UI (Stream B FE)

> **Date:** 2026-08-02  
> **Owner:** Frontend Lead  
> **Tip base:** Hub HTTP `f1d06aa` (STORY-08-06)  
> **Honesty:** Not Production GO. No invented Hub routes/secrets. `TenantList.tsx` untouched.

## Landed

| Piece | Detail |
|-------|--------|
| Client | `lib/api/integrationHub.ts` → `/api/v1/integrations/connections*` |
| Hooks | `integrationHubQueries.ts` |
| Tenant UI | `/integrations` — Connect / Test / Map / Schedule / Monitor / Disconnect |
| Owner pointer | `/admin/integrations` links to tenant Studio |
| Auth | `/integrations` added to `PROTECTED_PREFIXES` |
| Tests | API contract Jest + Studio render Jest + E2E hooks |

## Honesty

- Wired only to tip STORY-08-06 endpoints.
- `test_connection` uses BE FakeSourceConnector until Odoo GA.
- credential_ref is a reference string — demos must not invent production secrets.
- DOM-021 entitlement gate remains BE-enforced.

## Non-goals

- Live Odoo network I/O / Production GO
- Owner-minted JWT (DEC-093)
- `TenantList.tsx` edits
