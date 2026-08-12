# IL-2B.2 Claim / Lease / Dispatcher Hardening

**Date:** 2026-08-12  
**SHA:** `46d5fe3` (pushed to `master`)  
**Verdict:** **PASS** (unit/build-validated; Railway light check below)  
**Scope:** claim/run / dispatcher lease hardening — not live ResearchAgent/LLM, no `feature_ai_copilot` flip, no Alembic.

## Findings addressed

| ID | Gap | Fix |
|----|-----|-----|
| R1 | Research lease 30m ≫ Celery soft kill 110s → stuck CLAIMED | `LEASE_MS_RESEARCH=100s`, `LEASE_MS_FAST=90s` |
| R2 | Recover without gen bump | `recover_expired_leases` bumps `lease_generation` |
| R3 | Orphan RUNNING `agent_runs` blocks re-claim (`uq_agent_runs_active`) | Recover fails orphan runs |
| R4 | CLAIMED→RUNNING ignored rowcount | Abort + mark run FAILED when fence rejects |
| R5 | Beat overlap (`expires:120` vs 60s schedule) | `expires:55` |
| R8 | Nested Grounding sessions without GUC | `_tenant_scoped_session_factory` |
| R10 | Duplicate `PENDING` key in state machine | Merged `{CLAIMED, EXHAUSTED}` |
| — | Research lane `kinds_exclude` claimed unknown kinds | `kinds_include=RESEARCH_KINDS` |

## Tests (Docker)

```text
poetry run pytest tests/unit/test_il2b2_lease_hardening.py \
  tests/unit/test_agent_dispatcher.py \
  tests/unit/test_claim_due_kind_filter.py \
  tests/unit/test_agent_dispatch_tasks.py -q
→ 34 passed
```

Validation label: **build validated** (narrow Docker unit suite).

## Residual risk

- Long research still runs in-process under `agent_dispatch_all` soft limit — per-task Celery jobs not yet split.
- `complete_task`/`fail_task` still allow unfenced path when callers pass `lease_generation=None` (runtime now always fences).
- Nested GUC wrap covers ResearchAgent Grounding path only; other nested factories not audited.
- Soft-kill still burns `attempts` on claim (unchanged).
- No Alembic required for this hardening.

## Railway

**Pre-push light check (2026-08-12 ~17:49–17:52 UTC):** celery-worker Online; repeated `agent_dispatch_all` succeeded ~2.6–2.9s with `tenants_processed: 57`, `tasks_claimed: 0`, `errors: []`. No Handler/lease error lines in filtered window. (No secret dumps.)

Post-push: deploy will pick up lease/recover/fence hardening; no Alembic required.
