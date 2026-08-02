# Sprint 04 — Calendar Phase 1 delivery tracking

> **Opened:** 2026-08-02 (plan E2) after TRIGGER_POST_PHASE0_PLAN  
> **Authority:** [`SPRINT_PLAN/Sprint-04.md`](SPRINT_PLAN/Sprint-04.md) · [`POST_PHASE0_PARALLEL_EXECUTION_PLAN.md`](POST_PHASE0_PARALLEL_EXECUTION_PLAN.md)  
> **Honesty:** Separate from Sprint 05 Phase 0 board (26/26). **No Production GO.**

## Story status

| Story | Stream | Status | Tip / artifact |
|-------|--------|--------|----------------|
| STORY-04-01 Tenant extension | A1→A2 | **IN PROGRESS** | Alembic `f6b2e84c1a90` @ `64b44e9`; notes [`PHASE1_A2_NONPROD_MIGRATE_NOTES.md`](PHASE1_A2_NONPROD_MIGRATE_NOTES.md) |
| STORY-04-02 Provisioning workflow | A3 | **IN PROGRESS** | `provision_workflow` + `scripts/provision_tenant.py` |
| STORY-02-03 JWT audience | A4 | **CLOSED** (DEC-093) — reaffirm after migrate | [`PHASE1_A4_JWT_OWNER_AUDIENCE_CRUMB.md`](PHASE1_A4_JWT_OWNER_AUDIENCE_CRUMB.md); admin tenants still `require_owner_role_dep` |
| FE Owner Console tenants | B1–B5 + FE-S04-06..45 + FE-S05-01..06 + FE-S06-01 | **LANDED** | tip `ca1fb19` plan-change + dunning + `/admin/billing` |
| D3 adversarial after A2 | Validation | **SUITE LANDED** (skip if pre-migrate) | `tests/integration/test_adversarial_rls_story_04_01.py` |

## Gates still open

1. Tip Stages 1–5 + Stage 3 green on latest tip (chase Frontend Lint / unit flakes).  
2. Non-prod Alembic upgrade/downgrade proof for `f6b2e84c1a90` (see migrate notes).  
3. D3 suite PASS after migrate (not skipped).  
4. Demo script provision against non-prod + RLS isolation show.

## Explicit non-claims

- Phase 0 COMPLETE ≠ Production GO  
- Board 26/26 ≠ Sprint 04 feature complete  
- Local Jest PASS ≠ tip CI GREEN
