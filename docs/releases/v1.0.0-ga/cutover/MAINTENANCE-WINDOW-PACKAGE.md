# Maintenance Window Package — SalesOS Prod DB Migration

**Date:** 2026-08-07 · **Product:** SalesOS
**Range:** `d1a8c35e7f09` → `e5f9a32b0c08` (15 revisions)
**Status:** **PREPARED — NOT EXECUTED. Requires explicit human approval + freeze.**
**Authorizing decision:** Project Owner 2026-08-07 — approved `REQUIRES MAINTENANCE WINDOW` (NOT `SAFE TO EXECUTE`).
**Source risk assessment:** [PROD-MIGRATION-RISK.md](../PROD-MIGRATION-RISK.md)
**Validation label:** `build validated` for the migrate runner (staging); **`not validated`** against prod DB until the window executes.

> AI assists. Humans decide. Evidence governs.
> This package is NOT approval. Execute only inside an approved, dated maintenance window with a recorded backup ID.

---

## 1. Why a maintenance window (Project Owner decision, verbatim intent)

- Highest risk: revision `a4f7c29e1b80` creates **37 indexes without `CONCURRENTLY`** on live hot tables → `ShareLock` blocks writes for the build duration.
- The soak (Path A) validates runtime/stability/workers/memory/health and is **independent of the DB migration** — so it runs now; migration waits for the window.

## 2. New de-risking evidence (read-only prod probe, 2026-08-07)

Live SELECT-only probe of the production Postgres (no writes):

| Metric | Value | Impact |
|--------|-------|--------|
| Target indexes already present | **0 of 37** | All 37 will be created (no idempotent skips) |
| `companies` size | **141,221 rows / 345 MB** | Largest hot table; dominant index-build cost |
| `contacts` rows | 44 | Negligible |
| `emails`, `meetings`, `commercial_contracts`, `licenses`, etc. | reltuples = -1 (≈ empty) | Index builds are near-instant |
| `contacts.name` / `name_ar` width | **VARCHAR(255)** | The 255→500 widen **will execute** (metadata-only for empty-to-small table) |
| `max_connections` | 500 (active 15) | Ample headroom during window |
| alembic_version | `d1a8c35e7f09` | Confirms starting point |

**Conclusion:** the 45+ minute upper bound in the risk assessment was sized for "large prod tables". Actual prod data shows `companies` at 345 MB is the only meaningful index target; **estimated write-impact window: ~2–10 minutes**, dominated by the 5 `companies` indexes + `audit_logs`/`commercial_*` builds. Dress rehearsal will confirm.

## 2a. Dress rehearsal result (EXECUTED 2026-08-07 — Project Owner-approved, scratch env)

A **read-only** prod `pg_dump` (19.4 MB) was restored into an isolated scratch Postgres 18 (port 5544, scratch-only), then the 15 migrations were run with the proven runner image `salesos-migrate-4750038c`. **No prod service or data was written.**

| Step | Target | Exit | Wall time |
|------|--------|:----:|----------:|
| rev1 | `e2b9d46f8a10` (admin trio) | 0 | 22.8 s |
| rev2-HIGH | `a4f7c29e1b80` (37 indexes + widen) | 0 | **19.7 s** |
| revs 3–15 | `upgrade head` remainder | 0 | 18.1 s |
| **Total** | `d1a8c35e7f09` → `e5f9a32b0c08` | **0** | **~60.6 s** |

**Verified post-migration (scratch):** alembic=`e5f9a32b0c08`; 134 tables; **companies=141,221 / tenants=57 preserved**; all 13 new tables present; **37/37 target indexes created**; contacts `name/name_ar` → VARCHAR(500); RLS enabled+forced on 4/4 hub tables; `sync_runs` = 25 partitions.

**Impact on the window estimate:** the feared `a4f7c29e1b80` index build measured **~20 s** on a production-data-size copy (not 45+ min). Total 15-revision window ≈ **~1 minute** wall clock single-threaded. Prod execution remains `not validated` until the approved window, but the rehearsal confirms feasibility and tightens sizing from "5–45+ min" to "**≈1–2 min** (single-threaded; allow headroom for shared-DB contention)".

**Evidence:** `enterprise-audit-board/history/EAB-2026-08-06-003/evidence/ops01-staging/migration-dress-rehearsal.json`. Scratch env destroyed; prod dump deleted.

---

## 3. Preconditions (ALL must be TRUE before the window opens)

| # | Precondition | Status 2026-08-07 |
|---|--------------|-------------------|
| 1 | Final backup taken **and restore-verified** for prod (object ID recorded) | **OPEN — REQUIRED at T-0** |
| 2 | 72h staging soak passed + Project Owner review (K2–K6) | OPEN (soak in progress, i8 PASS) |
| 3 | Migration Dress Rehearsal clean (time/lock/errors/resources measured) | **DONE — CLEAN PASS (~60.6s total; a4f7 ≈20s)** |
| 4 | Migrate image can `import scripts.generate_rls_policies` | **PROVEN** (`salesos-migrate-4750038c` succeeded on staging) |
| 5 | Code freeze (no new Alembic revisions) | OPEN — freeze at window open |
| 6 | Explicit human approval + signed GO for the window | **NOT GRANTED** |
| 7 | Write-quiet (or reduced-write) plan agreed | OPEN |

---

## 4. Window playbook (T-0 sequence)

### Phase 0 — HARD STOP checks (dual human)
- [ ] Confirm environment = **production** (`96032c9a…` / `652c450a…`)
- [ ] `alembic current` = `d1a8c35e7f09` (SQL: `SELECT version_num FROM alembic_version;`)
- [ ] Backup object ID recorded in the change ticket
- [ ] `/health` 200 on prod before any change

### Phase 1 — Final backup + restore verification
```bash
# Railway: use the Postgres service snapshot / WAL tooling (prod has WAL+PITR to salesos-pitr-w-…)
# Record: object ID / snapshot name / WAL LSN. Do NOT skip restore verification.
```

### Phase 2 — Migrate (runner image, proven pattern)
Build the disposable runner from the **clean worktree at `4750038c`** (repo head), exactly as staging used:

```powershell
# From repo root worktree wt-4750038c (or a fresh `git worktree add` at 4750038c)
docker build -f Dockerfile.migrate -t salesos-migrate-prod-<window> .
```

Then run against prod via tunnel (port e.g. 5436; **do not** reuse staging port 5435):

```powershell
# 1) Open prod Postgres tunnel (railway connect Postgres --environment production --tunnel-only --port 5436)
# 2) Export DATABASE_URL for the tunnel endpoint, inject dummy SECRET_KEY/JWT_SECRET_KEY (Settings() validation only)
docker run --rm \
  -e "DATABASE_URL=postgresql+asyncpg://postgres:<PASS>@host.docker.internal:5436/railway" \
  -e "SECRET_KEY=migrate-runner-dev-only" \
  -e "JWT_SECRET_KEY=migrate-runner-dev-only" \
  salesos-migrate-prod-<window> upgrade head
# Exit 0 = success. Capture full output to evidence/.
```

### Phase 3 — Verify (read-only)
```sql
SELECT version_num FROM alembic_version;             -- expect e5f9a32b0c08
SELECT count(*) FROM pg_indexes WHERE indexname IN (…new indexes…);
-- Table spot-checks: subscriptions, usage_meters, dunning_cases, sync_runs (partitions),
-- external_system_connections, field_mapping_configs, conflict_resolution_policies, admin_plans
```

### Phase 4 — App smoke + traffic
- [ ] Deploy prod SalesOS/celery to `4750038c` images (or confirm already deployed)
- [ ] `/health` 200, `database/redis/cache/graph` connected
- [ ] Auth critical path (login + tenant list) passes
- [ ] Performance monitoring: check index-backed query latency vs pre-migration baseline

### Phase 5 — Hypercare
- [ ] Observe 30–60 min post-window for lock/backlog/P0
- [ ] Watch `pg_stat_activity` for stuck `ShareLock` waiters
- [ ] Keep window open until Project Owner signs off

---

## 5. Rollback plan (preferred: restore from backup)

| Failure mode | Action |
|--------------|--------|
| Migration fails mid-chain | **Do NOT open traffic.** Capture Alembic error; restore from pre-migrate backup. |
| Migration succeeds; smoke fails | Prefer **forward-fix** (config/code); `railway redeploy` previous image if app-only. |
| Data corruption / wrong env | Restore pre-migrate `pg_dump`/snapshot (runbook: [backup-restore-drill.md](../runbooks/backup-restore-drill.md)). |
| `a4f7` downgrade (VARCHAR shrink) | **FORBIDDEN as default.** Reverse ALTER can fail/truncate. Restore is the rollback. |
| Index build hangs / lock wait | `pg_cancel_backend` on the Alembic session, then restore or re-run (indexes idempotent). |

**Policy:** Prefer forward-fix + backup restore. Alembic downgrade of 15 steps is NOT the recovery path ([deploy-rollback.md](../runbooks/deploy-rollback.md)).

---

## 6. Index impact analysis (`a4f7c29e1b80`)

- 37 additive `CREATE INDEX` calls, each guarded by `_index_exists` / `_table_exists` (idempotent).
- Non-`CONCURRENTLY` → `ShareLock` on the target table for build duration → **writes blocked per-table, not global**.
- Largest real target: `companies` (345 MB / 141K rows) → **5 indexes**; expect the majority of the window here.
- Other tables near-empty → seconds each.
- `contacts.name/name_ar` VARCHAR(255)→(500): metadata-only for a 44-row table.
- **Measured:** entire rev2 (`a4f7c29e1b80`) completed in **~20 s** on a prod-data-size copy (see §2a). Per-table `ShareLock` windows are brief and sequential; no table exceeds ~345 MB.
- **Downgrade risk:** `ALTER COLUMN … TYPE VARCHAR(255)` is unsafe if any value >255 (none today; still, restore-first).

---

## 7. Migration Dress Rehearsal runbook (separate env)

Objective: restore a **production copy** to a separate environment, run the 15 migrations, and measure time / lock / errors / resource usage. If clean, the window becomes predictable.

1. **Take a prod logical backup** (pg_dump) or use WAL/snapshot — record object ID.
2. **Provision a scratch Postgres** (local Docker `postgres:18` + pgvector, or a new Railway Postgres in a scratch project). Never reuse staging/prod.
3. **Restore** the backup into scratch.
4. **Run the migrate runner** (`salesos-migrate-4750038c`) against scratch `upgrade head`.
5. **Measure:** wall-clock time per revision (or total), lock waits (`pg_stat_activity` during run), errors, `companies` index build seconds, peak memory/CPU.
6. **Assert:** exit 0; `alembic_version=e5f9a32b0c08`; RLS policies count on new tables; spot-check rows.
7. **Record** results in the evidence dir; update window estimate.
8. Destroy scratch env after.

**Note:** dress rehearsal does NOT touch prod data or prod services; it is a copy-restore in isolation.
**Status:** **EXECUTED 2026-08-07** — CLEAN PASS, ~60.6 s total / rev2 ≈20 s. See §2a + `evidence/ops01-staging/migration-dress-rehearsal.json`.

---

## 8. Cross-links

| Doc | Role |
|-----|------|
| [PROD-MIGRATION-RISK.md](../PROD-MIGRATION-RISK.md) | Risk assessment (15-rev chain, per-rev risk) |
| [PROGRESS-WAVE12-PROD-MIGRATE-PREP.md](../PROGRESS-WAVE12-PROD-MIGRATE-PREP.md) | Historical prep (older head pin `0040`; policy: forward-fix, restore-first) |
| [runbooks/deploy-rollback.md](../runbooks/deploy-rollback.md) | Rollback policy |
| [runbooks/backup-restore-drill.md](../runbooks/backup-restore-drill.md) | Restore drill |
| [SOAK-GATE-CHECKLIST.md](../enterprise-audit-board/history/EAB-2026-08-06-003/SOAK-GATE-CHECKLIST.md) | Soak K1–K6 status |

---

## 9. Honesty

- **No production writes.** Rehearsal ran on an isolated scratch copy from a read-only prod `pg_dump`; prod services/data untouched.
- Probe data is **read-only SELECT** from prod; row counts for some tables are `reltuples` estimates (`-1` = stats not analyzed → treated as empty).
- The runner-image approach is **build validated** (ran successfully on staging and on the rehearsal scratch to `e5f9a32b0c08`); prod execution remains **not validated** until the window.
- Rehearsal timing is single-threaded on a local scratch container — production will face shared-DB contention; treat ~60 s as the ideal-case floor and keep the window sized for minutes, not the rehearsal's exact numbers.
- Production GA remains **NO-GO** until EAB re-evaluation after soak + window + Row 5 signatures.
