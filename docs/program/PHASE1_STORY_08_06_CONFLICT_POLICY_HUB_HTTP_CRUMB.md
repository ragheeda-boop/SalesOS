# STORY-08-06 — ConflictResolutionPolicy + Hub HTTP (Stream A)

> **Honesty:** Not Production GO. DEC-085 untouched. No invented secrets.

## Landed

| Piece | Detail |
|-------|--------|
| Table | `conflict_resolution_policies` Alembic `e5f9a32b0c08` (revises `c4d8e21a9f07`) |
| RLS | FORCE → **POLICY_COUNT 70 → 71** |
| Pure | Write-back feedback-loop exclusion (`assert_no_feedback_loop_pull` / filter) |
| HTTP | `/api/v1/integrations/connections*` connect/test/map/schedule/monitor/disconnect + conflict-policy |
| Tests | Dedicated feedback-loop exclusion unit suite |

## Acceptance

Write-back feedback-loop exclusion rule verified — `test_write_back_feedback_loop_exclusion_dedicated`.
Hub HTTP unblocks FE STORY-08-07 Studio surfaces (DOM-021).

## Non-goals

- Live Odoo adapter network I/O (test uses FakeSourceConnector)
- Production GO / browser E2E
