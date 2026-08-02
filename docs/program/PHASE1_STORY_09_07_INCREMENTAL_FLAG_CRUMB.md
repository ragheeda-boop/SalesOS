# STORY-09-07 — Incremental write_date cursor + feature_odoo_integration (Stream A)

> **Honesty:** Not Production GO. DEC-085 untouched. No invented Odoo/vault secrets.  
> No new Alembic / FORCE RLS (**POLICY_COUNT unchanged at 71**).  
> Grade-A flag `feature_odoo_integration` — global off; Muhide via tenant override.

## Landed

| Piece | Detail |
|-------|--------|
| Flag | Seeded `feature_odoo_integration` (InMemory Grade-A seed; global `enabled=False`) |
| Gate | Hub connect / test / schedule for `connector_key=odoo` → 403 when flag off |
| Cursor | `pull_odoo_incremental_for_sync` + `MemConnectionCursorStore`; SyncRun `cursor_before`/`after` |
| Tests | Seed off, Muhide override on, two-tick write_date advance, flag-off blocked |

## Acceptance

`write_date` cursor working across scheduled ticks; `feature_odoo_integration`
live for Muhide via tenant override — covered by
`test_write_date_cursor_persists_across_scheduled_ticks` +
`test_muhide_tenant_override_enables_odoo_flag`.

## Ops note (Muhide)

Real Muhide tenant UUID is resolved from slug=`muhide` (not committed). Enable via
admin feature-flag tenant override for that UUID. No secrets in-repo.

## Non-goals

- Live XML-RPC / vault credentials
- Alembic data seed of flag row (create via admin API / ops)
- Unlinked badge list API
- Production GO
