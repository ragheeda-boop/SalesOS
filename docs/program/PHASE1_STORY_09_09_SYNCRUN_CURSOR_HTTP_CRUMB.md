# STORY-09-09 — SyncRun cursor_before/after HTTP (Stream A)

> **Honesty:** Not Production GO. DEC-085 untouched. No invented Odoo secrets.  
> No new Alembic / FORCE RLS (**POLICY_COUNT unchanged at 71**).  
> Unblocks FE Studio Monitor residual after FE-S09-07/08 honesty.

## Landed

| Piece | Detail |
|-------|--------|
| Schema | `SyncRunResponse.cursor_before` / `cursor_after` (dict, default `{}`) |
| HTTP | Existing `GET .../sync-runs` now returns cursor watermarks |
| Tests | model_validate includes write_date cursors; empty defaults |

## Acceptance

SyncRun list HTTP exposes incremental `write_date` cursors for Studio Monitor —
covered by `test_sync_run_response_includes_cursor_before_after`.

## Non-goals

- New cursor-only endpoint
- FE Monitor columns (Stream B follow-on)
- Live Odoo soak / Production GO
