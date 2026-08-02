# STORY-09-08 / 09-01 residual — Unlinked cr_number badge list API (Stream A)

> **Honesty:** Not Production GO. DEC-085 untouched. No invented Odoo secrets.  
> No new Alembic / FORCE RLS (**POLICY_COUNT unchanged at 71**).  
> Unblocks FE Studio Monitor residual after EPIC-09 (09-01..09-07) landed.

## Landed

| Piece | Detail |
|-------|--------|
| HTTP | `GET /api/v1/integrations/connections/{id}/unlinked-badges` |
| Source | SyncRun.`error_log` entries with `kind=unlinked_badge` |
| Helpers | `badge_items_from_partner_batch` + `MemUnlinkedBadgeStore` |
| Executor | CAP-028 SyncRunExecutor persists `unlinked_badges` into error_log |
| Tests | Partner batch → badges; error_log collect; scheduled tick persists |

## Acceptance

Unlinked Golden-Record join failures are listable for Studio Monitor (not silent
skip) — covered by `test_partner_batch_produces_unlinked_badge_items` +
`test_sync_run_executor_persists_unlinked_badges_in_error_log`.

## Non-goals

- Dedicated `unlinked_badges` ORM table / Alembic
- Live Muhide XML-RPC population
- FE Studio wiring (Stream B follow-on)
- Production GO
