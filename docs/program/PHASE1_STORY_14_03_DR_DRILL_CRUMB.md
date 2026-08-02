# STORY-14-03 — DR drill (backup/restore, RTO/RPO measured)

> **Honesty:** Not Production GO. Live production backup/restore not performed.  
> **POLICY_COUNT unchanged at 71** (no Alembic / FORCE RLS).  
> `feature_ai_copilot` remains **False**. Stage 6 GHCR stays quarantined.  
> Mirrors STORY-14-02 CI/non-prod harness + practice postmortem pattern.  
> Do **not** re-land STORY-14-02.

## Landed

| Piece | Detail |
|-------|--------|
| Targets | RTO ≤4h (`14400s`), RPO ≤1h (`3600s`) |
| Drills | `full_backup_restore`, `point_in_time_recovery` (non-prod fixtures) |
| Measurement | `rto_seconds` / `rpo_seconds` + `within_rto` / `within_rpo` on each report |
| Postmortems | Practice postmortem per drill |
| HTTP | `/api/v1/dr/meta`, `/run/{kind}`, `/run-all`, `/drills`, `/postmortems` |
| Tests | `tests/unit/test_story_14_03_dr_drill.py` |

## Non-goals

- Live prod restore / primary kill
- STORY-14-01 load / 14-02 re-land / 14-04 pentest / 14-06 field AI failover
- AI 12-03 invent / marketplace 13-xx reopen
- Production GO
