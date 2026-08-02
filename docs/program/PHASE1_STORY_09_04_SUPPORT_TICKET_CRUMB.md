# STORY-09-04 — SupportTicket via helpdesk.ticket (Stream A)

> **Honesty:** Not Production GO. DEC-085 untouched. No invented Odoo secrets.  
> No new Alembic / FORCE RLS (**POLICY_COUNT unchanged at 71**).  
> Unlinked badge list API remains residual (not scoped here).

## Landed

| Piece | Detail |
|-------|--------|
| Pull | `OdooAdapter.pull_incremental(model="helpdesk.ticket")` + ticket fields |
| Sync | `sync_support_tickets` → OBJ-019 SupportTicket projection |
| Stages | `OdooTranslator(strict_stages=True)` — no raw helpdesk stage passthrough |
| PII | Ticket `description` scrubbed via AI-GR-001 before landing scrubbed text |
| Tests | Translated stages, unmapped rejection, done/closed → solved aliases |

## Acceptance

`helpdesk.ticket` synced correctly — covered by
`test_helpdesk_ticket_synced_with_translated_stage`.

## Non-goals

- Persist `support_tickets` ORM + FORCE RLS (follow-on; POLICY_COUNT discipline)
- Unlinked cr_number badge list API
- Live XML-RPC / vault password material
- Production GO
