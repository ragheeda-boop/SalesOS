# STORY-08-05 — SyncRun + CAP-028 scheduling (Stream A)

> **Honesty:** Not Production GO. DEC-085 untouched. No invented secrets.

## Landed

| Piece | Detail |
|-------|--------|
| Table | `sync_runs` Alembic `c4d8e21a9f07` (revises `f2b8c79d3e06`) |
| Partitions | Monthly RANGE on `started_at` (2026–2027 + DEFAULT) |
| RLS | FORCE tenant isolation → **POLICY_COUNT 69 → 70** |
| CAP-028 | `schedule_connection_sync` + `tick_with_sync_logging` via workflow JobScheduler |
| Service | `SyncRunService` start/finish + failure classes |
| Tests | CAP-028 tick logs SyncRun; connection_unreachable classified; cross-tenant |

## Acceptance

Sync runs on schedule via existing CAP-028, logs to SyncRun — covered by
`test_cap028_interval_tick_logs_sync_run`.

## Non-goals

- STORY-08-06 ConflictResolutionPolicy
- Live Odoo network pull in this land (injected pull callable)
- Integrations Studio UI
