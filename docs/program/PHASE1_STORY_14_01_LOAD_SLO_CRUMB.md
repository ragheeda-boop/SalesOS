# STORY-14-01 — Load/SLO harness companion (50-tenant pooled tier)

> **Honesty:** Not Production GO. Live prod traffic / prod kill not performed.  
> **POLICY_COUNT unchanged at 71** (no Alembic / FORCE RLS).  
> `feature_ai_copilot` remains **False**. Stage 6 GHCR stays quarantined.  
> **BE status: CLOSED** (tip HTTP companion complete). DevOps owns field 50-tenant / 2h soak residual.  
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

## DevOps field harness (Stream C) — STARTED

| Piece | Detail |
|-------|--------|
| Script | `salesos/scripts/story_14_01_nonprod_load_harness.py` |
| Modes | `companion` (local MemLoadSloHarness) · `http` (tip `/api/v1/load/*`) |
| Safety | Refuses known prod host markers unless `--allow-deployed-nonprod` (operator-asserted non-prod only) |
| Status | Script tip-landed (DevOps). Companion **light validated** (exit 0, both profiles within_slo). `--mode http` **not validated** (no `SALESOS_TOKEN`). Field 2h soak **not validated**. No live prod kill / No Production GO |

## Non-goals

- Field 2h sustained soak / live k6 against prod
- Live prod kill / Production GO
- Enabling `feature_ai_copilot`
- Marketplace 13-xx reopen / 14-02/14-03 re-land
