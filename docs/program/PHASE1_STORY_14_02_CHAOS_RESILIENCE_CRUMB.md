# STORY-14-02 — Chaos / Phase 6 resilience harness

> **Honesty:** Not Production GO. Live connector/AI/DB kill not performed.  
> **POLICY_COUNT unchanged at 71** (no Alembic / FORCE RLS).  
> `feature_ai_copilot` remains **False**. Stage 6 GHCR stays quarantined.  
> Does **not** reopen marketplace 13-xx. PARK 12-03 unless AI-Lead paired.

## Landed

| Piece | Detail |
|-------|--------|
| Faults | `connector_outage`, `ai_provider_outage`, `db_failover` |
| Handlers | Clean abort + backoff; simulated AI failover ≤30s SLO; DB retryable reconnect |
| Postmortems | Practice postmortem per drill (MASTER_EXECUTION_PLAN §8) |
| HTTP | `/api/v1/chaos/meta`, `/run/{kind}`, `/run-all`, `/drills`, `/postmortems` |
| Tests | `tests/unit/test_story_14_02_chaos_resilience.py` |

## Non-goals

- STORY-14-01 load test / 14-03 DR / 14-04 pentest / 14-06 live AI failover field
- Live Odoo/HubSpot GO / R-02 invent-close
- Production GO / enabling `feature_ai_copilot`
- Marketplace 13-xx reopen
