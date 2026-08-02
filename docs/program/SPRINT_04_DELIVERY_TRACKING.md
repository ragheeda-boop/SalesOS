# Sprint 04 — Calendar Phase 1 delivery tracking

> **Opened:** 2026-08-02 (plan E2) after TRIGGER_POST_PHASE0_PLAN  
> **Authority:** [`SPRINT_PLAN/Sprint-04.md`](SPRINT_PLAN/Sprint-04.md) · [`POST_PHASE0_PARALLEL_EXECUTION_PLAN.md`](POST_PHASE0_PARALLEL_EXECUTION_PLAN.md)  
> **Honesty:** Separate from Sprint 05 Phase 0 board (26/26). **No Production GO.**

## Story status

| Story | Stream | Status | Tip / artifact |
|-------|--------|--------|----------------|
| STORY-04-01 Tenant extension | A1→A2 | **IN PROGRESS** | Alembic `f6b2e84c1a90` @ `64b44e9`; Docker upgrade proof pending |
| STORY-04-02 Provisioning workflow | A3 | **IN PROGRESS** | `provision_workflow` + `scripts/provision_tenant.py` |
| STORY-02-03 JWT audience | A4 | **CLOSED** (DEC-093) — reaffirm after migrate | [`PHASE1_A4_JWT_OWNER_AUDIENCE_CRUMB.md`](PHASE1_A4_JWT_OWNER_AUDIENCE_CRUMB.md) |
| FE Owner Console tenants | B1–B5 | **LANDED** (read/write + B4 sync) | `a8fd06e` / `b6ea2ef` / `825c18e` / crumbs |

## Gates still open

1. Tip Stages 1–5 green (Frontend Lint Prettier regressions being chased).  
2. Non-prod Alembic upgrade/downgrade proof for `f6b2e84c1a90`.  
3. D3 adversarial RLS after migrate.  
4. Demo script provision against non-prod + RLS isolation show.

## Explicit non-claims

- Phase 0 COMPLETE ≠ Production GO  
- Board 26/26 ≠ Sprint 04 feature complete  
- Local Jest PASS ≠ tip CI GREEN
