# Progress — Wave 12 / Wave 1 Prod Alembic Migrate **PREP ONLY**

**Date:** 2026-07-22  
**IDs:** PROD-W1-001 / PROD-W1-002 (execution deferred); Wave 12 cutover dependency  
**Product:** SalesOS (AQLIYA)  
**Target revision:** **`0040`** (`0040_ensure_graph_tables.py` — idempotent `graph_edges` / `graph_nodes` ensure; revises `0039`)  
**Prior pin:** Prep originally targeted **`0039`** (`0039_webhook_tables.py`). Local head advanced to **0040** after graph_edges drift repair — **0040 must be included in any future staging/prod upgrade path** after approval.  
**Classification:** **PREP DONE / EXECUTION BLOCKED pending approval**  
**Production:** still **NO-GO**  
**This session:** **No production Alembic. No kubectl to prod. No live prod migrate.**

---

## Verdict

| Item | Status |
|------|--------|
| Prep runbook (this file) | **DONE** |
| Local head verify `0040` | **DONE** (SQL + gate) — [evidence/wave12-migrate-prep/](./evidence/wave12-migrate-prep/) |
| Staging migrate execution | **NOT RUN** — blocked (no cloud staging / tabletop) |
| Production migrate execution | **NOT RUN** — **FORBIDDEN** until approvals + preconditions |
| Production GO claim | **No** |

---

## Gate of record

| Mechanism | Path | Behavior |
|-----------|------|----------|
| Migrate head gate | `salesos/backend/scripts/check_alembic_head.py` | Read-only; exit 0 iff `current == heads`; **never** upgrades |
| Pre-deploy wrapper | `salesos/scripts/pre-deploy-gates.ps1` | Fails on Alembic drift, `/health`, `SALESOS_TESTING` trap |
| CI (non-prod) | `salesos/.github/workflows/ci.yml` | `alembic upgrade head` then `check_alembic_head.py` on CI DB only |

**Policy:** Prefer **forward-fix** over Alembic downgrade. Schema downgrade in panic without a data plan is forbidden ([runbooks/deploy-rollback.md](./runbooks/deploy-rollback.md)).

---

## Preconditions (must be TRUE before any approved execution)

| # | Precondition | Current status | Evidence |
|---|--------------|----------------|----------|
| 1 | **Backup** taken and restore-verified for the target env | Local drill **DONE**; **prod backup OPEN** | [PROGRESS-WAVE10-BACKUP.md](./PROGRESS-WAVE10-BACKUP.md), [runbooks/backup-restore-drill.md](./runbooks/backup-restore-drill.md) |
| 2 | **Soak** accepted (48–72h or signed exception) | Short local loop only; `soak_complete_claim: false` | [PROGRESS-WAVE11-SOAK.md](./PROGRESS-WAVE11-SOAK.md) |
| 3 | **Staging deploy + rollback tabletop** | Local compose **DONE**; **cloud staging BLOCKED** | [PROGRESS-WAVE12-TABLETOP.md](./PROGRESS-WAVE12-TABLETOP.md), [PROGRESS-WAVE12-STAGING.md](./PROGRESS-WAVE12-STAGING.md) |
| 4 | **Staging Alembic** `current == heads` (`0040`) after upgrade | **OPEN** | [runbooks/go-live-checklist.md](./runbooks/go-live-checklist.md) T-3 #4 |
| 5 | **Pre-deploy gates** green on target | Local **PASS**; staging/prod **OPEN** | [PROGRESS-WAVE12-GATES.md](./PROGRESS-WAVE12-GATES.md) |
| 6 | **CTO + Tech Lead signatures** (GO / CONDITIONAL) | **UNSIGNED** | [runbooks/go-live-checklist.md](./runbooks/go-live-checklist.md), [PROGRESS-WAVE14-GO-LIVE.md](./PROGRESS-WAVE14-GO-LIVE.md) |
| 7 | Explicit human approval for **staging** then **prod** migrate commands | **Not granted** this session | — |
| 8 | Feature flags honest (`feature_ai_copilot=False`, `DEMO_MODE=false` in prod) | Local aligned; prod env **UNVERIFIED** | [AI_HONESTY.md](./AI_HONESTY.md) |

**Until rows 1–7 close (or formally risk-accepted in writing): EXECUTION BLOCKED.**

---

## Upgrade path note (0039 → 0040)

Any approved **staging** or **production** `alembic upgrade head` must reach **`0040`**, not stop at `0039`:

| Revision | File | Role |
|----------|------|------|
| `0039` | `0039_webhook_tables.py` | webhook_subscriptions / webhook_deliveries |
| `0040` | `0040_ensure_graph_tables.py` | Idempotent ensure `graph_nodes` / `graph_edges` (0004 stamp/recreate drift repair) |

Environments already at `0039` must apply **`0040`** as part of the same approved upgrade window (or a follow-on approved migrate) before claiming `current == heads`.

---

## Freeze window

Aligned with [runbooks/go-live-checklist.md](./runbooks/go-live-checklist.md):

| Phase | When | Migrate rules |
|-------|------|----------------|
| **T-3** | ≥3 days before cutover | Staging RC images; staging `alembic upgrade head` + verify; soak in progress |
| **T-1** | Day before | **Code freeze** (hotfix-only); production backup object ID recorded; final GO/NO-GO review; rollback tabletop signed |
| **T-0** | Launch window | Migrate **before** opening traffic (PROD-W1-002); then images; smoke; gradual traffic |
| **T+1** | Next day | Continue/rollback decision; hypercare clock only after human GO |

Recommended migrate freeze: **no new Alembic revisions** after the release candidate that pins **`0040`** until hypercare day 3, unless emergency hotfix with dual CTO/TL ack.

---

## Exact commands — STAGING first (do not run until approved)

> Replace namespace / kube context with the **staging** values only.  
> **Do not** point these at production.

```bash
# 0) Confirm context is STAGING (human eyeball)
kubectl config current-context
kubectl config view --minify -o jsonpath='{.contexts[0].context.namespace}{"\n"}'

# 1) Pre-backup (staging Postgres — method per env; example compose-style)
# Prefer env-native backup Job / RDS snapshot. Record backup ID.
# Example pattern (compose staging only):
#   docker compose --profile backup run --rm backup backup-db

# 2) Read-only drift check BEFORE upgrade
kubectl exec -n <STAGING_NS> deploy/backend -- python scripts/check_alembic_head.py
# Expect FAIL if behind head; note current revision

kubectl exec -n <STAGING_NS> deploy/backend -- alembic current
kubectl exec -n <STAGING_NS> deploy/backend -- alembic heads
# Expect heads: 0040

# 3) Upgrade (staging only, after backup ID recorded)
# Applies through 0039 (webhooks) and 0040 (graph tables ensure) as needed
kubectl exec -n <STAGING_NS> deploy/backend -- alembic upgrade head

# 4) Verify
kubectl exec -n <STAGING_NS> deploy/backend -- alembic current
# Expect: 0040 (head)
kubectl exec -n <STAGING_NS> deploy/backend -- python scripts/check_alembic_head.py
# Expect: OK: alembic current == heads

# 5) Spot-check tables (0039 webhooks + 0040 graph)
kubectl exec -n <STAGING_NS> deploy/backend -- python -c \
  "import asyncio; from sqlalchemy import text; from app.db import ..."  # or psql:
# psql: SELECT version_num FROM alembic_version;
# psql: \dt webhook_*
# psql: \dt graph_*

# 6) Smoke: /health + auth critical path (Wave 13 list)
```

Compose-style staging (if applicable, **non-prod**):

```powershell
cd salesos
docker compose exec -T backend alembic upgrade head
docker compose exec -T backend python scripts/check_alembic_head.py
.\scripts\pre-deploy-gates.ps1 -BackendUrl http://127.0.0.1:8000
```

---

## Exact commands — PRODUCTION (BLOCKED — do not execute while NO-GO)

> **CRITICAL:** Do not run until GA_STATUS is no longer blocking migrate, CTO/TL have signed, staging succeeded, and an explicit migrate approval exists.

```bash
# 0) HARD STOP checks
# - GA_STATUS.md Decision must not be NO-GO without signed CONDITIONAL exception
# - kubectl context MUST be production (dual-person confirm)
# - Backup object ID recorded in change ticket

kubectl config current-context   # dual human confirm = production

# 1) Production backup (RDS snapshot / pg_dump to S3 — record ID)
#    Follow docs/ops/DR_RUNBOOK.md + Wave 10 runbook. Do not skip.

# 2) Optional maintenance / traffic hold (prefer migrate before traffic)
#    Do NOT open DNS/traffic until step 5 passes.

# 3) Pre-check (read-only)
kubectl exec -n salesos deploy/backend -- alembic current
kubectl exec -n salesos deploy/backend -- alembic heads
kubectl exec -n salesos deploy/backend -- python scripts/check_alembic_head.py

# 4) Upgrade — ONLY after dual approval (must include 0040)
kubectl exec -n salesos deploy/backend -- alembic upgrade head

# 5) Verify
kubectl exec -n salesos deploy/backend -- alembic current
# Expect: 0040 (head)
kubectl exec -n salesos deploy/backend -- python scripts/check_alembic_head.py
# Expect: OK

# 6) Then proceed deploy images / smoke per deploy-rollback.md T-0
```

**CI tag path** (`deploy-production.yml`) must not be treated as a substitute for the backup + staging tabletop + signatures above.

---

## Rollback plan

| Failure mode | Action | Notes |
|--------------|--------|-------|
| Upgrade fails mid-migration | Abort launch; **do not** open traffic | Capture Alembic error; restore from pre-migrate backup if DB left inconsistent |
| Upgrade succeeds; app smoke fails | Prefer **forward-fix** (code/config) | Image `kubectl rollout undo` if app-only |
| Data corruption / wrong env | Restore from **pre-migrate** `pg_dump` / snapshot | See [runbooks/backup-restore-drill.md](./runbooks/backup-restore-drill.md) |
| Panic schema reverse | **Default: NO** `alembic downgrade` | 0040→0039 drops graph ensure only if tables were created by 0040; 0039→0038 drops webhook tables — only with explicit data plan + CTO ack |
| Security P0 after cutover | Kill flags + image rollback + incident | [runbooks/deploy-rollback.md](./runbooks/deploy-rollback.md) |

0040 / 0039 downgrade (reference only — **not** default rollback):

```bash
# FORBIDDEN without data plan
# alembic downgrade 0039   # reverse 0040 graph ensure (may drop graph_* if created by 0040)
# alembic downgrade 0038   # drops webhook_subscriptions / webhook_deliveries
```

Preferred app rollback:

```bash
kubectl rollout undo deployment/backend -n salesos
kubectl rollout undo deployment/frontend -n salesos
```

---

## Local verify (this prep session) — NON-PROD

| Check | Result |
|-------|--------|
| SQL `alembic_version` | **`0040`** (re-verified after graph_edges fix) |
| `webhook_*` tables | **2** present (from 0039) |
| `graph_*` tables | present after **0040** (local) |
| `alembic heads` | **`0040 (head)`** |
| `alembic history -r 0035:0040` | **exit 0** (0035→…→0039→0040) |
| `check_alembic_head` via `pre-deploy-gates.ps1` | **PASS** (`0040` == `0040`) when re-run |
| `alembic current` CLI | Prefer SQL / `check_alembic_head` if CLI hangs (known Windows docker exec quirk) |
| `alembic check` | Advisory model↔DB drift only — **not** GO gate; gate of record is `current == heads` |
| Prod / staging upgrade | **Not executed** |

Earlier same-day prep evidence at head `0039` remains under [evidence/wave12-migrate-prep/](./evidence/wave12-migrate-prep/) as historical; current target head is **0040**.

---

## Honesty labels

| Claim | Label |
|-------|--------|
| Local head at 0040 | **light validated** (re-verify this session) |
| Staging migrate | **not validated** / **not executed** |
| Production migrate | **not executed** — **EXECUTION BLOCKED pending approval** |
| Overall GA | **production no-go** |

---

## Files touched this pass

- `docs/audit/ga-engineering-audit/PROGRESS-WAVE12-PROD-MIGRATE-PREP.md` (this file)
- `docs/audit/ga-engineering-audit/PROGRESS-WAVE12-GATES.md`
- `docs/audit/ga-engineering-audit/GA_STATUS.md` (scoreboard — head **0040**)
- `docs/audit/ga-engineering-audit/README.md` / go-live checklist head pins
- `docs/audit/ga-engineering-audit/evidence/wave12-migrate-prep/*` (new local verify artifacts)

**No commit** unless requested. **No production execution.**
