# STORY-14-01 — Load/SLO harness companion (50-tenant pooled tier)

> **Honesty:** Not Production GO. Live prod traffic / prod kill not performed.  
> **POLICY_COUNT unchanged at 71** (no Alembic / FORCE RLS).  
> `feature_ai_copilot` remains **False**. Stage 6 GHCR stays quarantined.  
> BE tip HTTP companion for DevOps non-prod field load harness.  
> Does **not** reopen marketplace 13-xx. Does not re-land 14-02/14-03.

## Landed

| Piece | Detail |
|-------|--------|
| Targets | 50 concurrent simulated tenants; p95 ≤500ms; error_rate ≤1%; no pool exhaustion; no degradation trend |
| Profiles | `pooled_50_tenant_burst`, `pooled_50_tenant_sustained_sim` (CI compressed — not 2h field soak) |
| Remediation | Documented plan (`held` \| `needs_remediation`) on every run |
| Postmortems | Practice postmortem per run |
| HTTP | `/api/v1/load/meta`, `/run/{profile}`, `/run-all`, `/runs`, `/remediation`, `/postmortems` |
| Tests | `tests/unit/test_story_14_01_load_slo.py` |

## Non-goals

- Field 2h sustained soak / live k6 against prod
- Live prod kill / Production GO
- Enabling `feature_ai_copilot`
- Marketplace 13-xx reopen / 14-02/14-03 re-land
