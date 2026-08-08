# PRODUCTION CUTOVER PACKAGE — SalesOS DB Migration

**Date prepared:** 2026-08-07 · **Product:** SalesOS
**This is the OFFICIAL single reference for execution day.** Supporting docs stay as references; this package is the runbook.

| Field | Value |
|-------|-------|
| Range | `d1a8c35e7f09` → `e5f9a32b0c08` (15 revisions) |
| Migrate runner | `salesos-migrate-4750038c` (proven: staging + dress rehearsal, exit 0) |
| Target commit (app) | `4750038c` (Baseline Freeze v5.1.0-bootstrap-green) |
| Prod SalesOS deployment | `bdce3450-53d4-4bc4-90d8-4c940e0e1002` · digest `sha256:11b14ac5…` (2026-08-05) |
| Prod celery-worker | `sha256:5c9dde960ff6…` (Dockerfile.railway) |
| Prod celery-beat | `sha256:28d5284728…` (Dockerfile) |
| Measured window | **~60.6 s total; `a4f7c29e1b80` ≈ 20 s** (dress rehearsal, prod-data-size copy) |
| Status | **PREPARED — NOT EXECUTED.** Requires backup+restore verify, freeze, and signed GO below. |
| Validation | Rehearsal `build validated`; prod execution `not validated` until window |

**Guardrail (CTO, 2026-08-07):** do **not** execute outside an approved maintenance window; **no production writes** until soak completes (K2–K6) and this packet is signed.

---

## 1. T-0 Checklist (complete all boxes; record values in Evidence Matrix §5)

| # | Item | Required value | Status |
|---|------|----------------|--------|
| 1 | Backup ID | `<object-id / snapshot / WAL LSN>` | ☐ |
| 2 | Restore Verification ID | `<restore-drill id>` | ☐ |
| 3 | Git SHA (target) | `4750038c` | ☐ |
| 4 | Docker Image Digest | `sha256:11b14ac5…` (SalesOS) | ☐ |
| 5 | Railway Deployment ID | `bdce3450-…` (SalesOS) | ☐ |
| 6 | Current Alembic Revision | `d1a8c35e7f09` (SQL verify) | ☐ |
| 7 | Target Alembic Revision | `e5f9a32b0c08` | ☐ |
| 8 | Freeze Confirmed (no new revisions) | Yes/No + time | ☐ |
| 9 | Stakeholders Notified | names + channel | ☐ |
| 10 | Monitoring Enabled | `/health`, `/metrics`, logs on | ☐ |
| 11 | Rollback Environment Ready | scratch restore verified | ☐ |
| 12 | Soak K1–K6 closed + Project Owner review | K2–K6 (48–72h) | ☐ |
| 13 | Sign-off packet §6 signed | Project Owner | ☐ |

---

## 2. Minute-by-Minute Runbook

Legend: `EXPECT` = expected outcome · `EVID` = evidence to save (see §5).

### T-30 (window pre-open)
| Action | Command / check | EXPECT | EVID |
|--------|-----------------|--------|------|
| Confirm env = production | `railway status --project responsible-comfort` (env `652c450a-…`) | production env | screenshot |
| Pre-window prod health | `Invoke-WebRequest https://salesos-production-96c0.up.railway.app/health` | 200, all connected | JSON |
| Baseline alembic | psql `SELECT version_num FROM alembic_version;` | `d1a8c35e7f09` | SQL log |
| Traffic note | record current request rate / active connections | baseline | snapshot |

### T-15
| Action | Command / check | EXPECT | EVID |
|--------|-----------------|--------|------|
| Final backup | prod snapshot / pg_dump → record **Backup ID** | ID recorded | ticket |
| Restore verification | restore backup to scratch env | exit 0, rows match | drill log |
| Notify stakeholders | per comms plan | ack received | chat log |

### T-10
| Action | Command / check | EXPECT | EVID |
|--------|-----------------|--------|------|
| Reduce/instrument writes | confirm write-quiet plan; capture `pg_stat_activity` baseline | < baseline active | snapshot |
| Runner image available | `docker image inspect salesos-migrate-4750038c` | present | CLI out |
| Pre-tunnel | ensure no stale listeners on port 5436 | clear | — |

### T-5
| Action | Command / check | EXPECT | EVID |
|--------|-----------------|--------|------|
| Open prod tunnel | `railway connect Postgres --environment production --tunnel-only --port 5436` | TCP listening | log |
| Final stop check | re-confirm alembic `d1a8c35e7f09`, `/health` 200 | match | log |

### T-0 — MIGRATE
| Action | Command / check | EXPECT | EVID |
|--------|-----------------|--------|------|
| Run migration | `docker run --rm -e DATABASE_URL=… -e SECRET_KEY=… -e JWT_SECRET_KEY=… salesos-migrate-4750038c upgrade head` | **exit 0** | full stdout (save `migration-run.out`) |
| Watch locks | sample `pg_stat_activity` + `pg_locks` during run | no >2 min lock waits | samples |
| Record duration | note start/end UTC | ≈ 60–120 s | log |

### T+1
| Action | Command / check | EXPECT | EVID |
|--------|-----------------|--------|------|
| Verify alembic head | psql `SELECT version_num FROM alembic_version;` | `e5f9a32b0c08` | SQL log |
| Verify new tables | psql count on `subscriptions, usage_meters, dunning_cases, sync_runs, external_system_connections, field_mapping_configs, conflict_resolution_policies, admin_plans` | 8 tables | SQL log |
| Verify indexes | psql count of 37 target indexes | 37 | SQL log |
| Verify RLS | psql `relforcerowsecurity` on 4 hub tables | true/true | SQL log |
| Verify partitions | psql count `pg_inherits` parent `sync_runs` | 25 | SQL log |

### T+2 — App smoke
| Action | Command / check | EXPECT | EVID |
|--------|-----------------|--------|------|
| Prod `/health` | HTTP GET | 200, database/redis/cache/graph connected | JSON |
| Auth path | login + tenant list (critical path) | success | API log |
| Query latency | index-backed query vs T-30 baseline | no regression | metrics |

### T+5
| Action | Command / check | EXPECT | EVID |
|--------|-----------------|--------|------|
| Confirm app image matches | deployment digest `sha256:11b14ac5…` live | match | deployment ID |
| Worker/beat healthy | celery worker + beat status | Online | status |

### T+10
| Action | Command / check | EXPECT | EVID |
|--------|-----------------|--------|------|
| Log scan | `railway logs` for ERROR/Traceback | none | log excerpt |
| Metrics spot | `/metrics` growth normal | no spike | snapshot |

### T+15
| Action | Command / check | EXPECT | EVID |
|--------|-----------------|--------|------|
| Lock backlog check | `pg_stat_activity` blocked = 0 | 0 | snapshot |
| Confirm data intact | `companies=141,221`, `tenants=57` | match | SQL |

### T+30 — Window close
| Action | Command / check | EXPECT | EVID |
|--------|-----------------|--------|------|
| Close tunnel | stop tunnel process | gone | — |
| Final status | `/health` + alembic `e5f9a32b0c08` | green | JSON |
| Hypercare begins | 30–60 min observation per §2 T+30+ | no P0 | log |

---

## 3. Abort Matrix

| Condition | Decision | Action |
|-----------|----------|--------|
| Any migration step exit ≠ 0 | **STOP** | Do NOT open traffic. Capture error; restore from pre-migrate backup. |
| Lock wait > 2 min on hot table | **ABORT** | `pg_cancel_backend` on Alembic session; restore or re-run (indexes idempotent). |
| `/health` 5xx after migrate | **RESTORE** | Restore pre-migrate backup; do not debug forward in-place. |
| Smoke test failed (auth/tenant) | **RESTORE** | Restore; record; Project Owner review before retry. |
| Index build timeout (>5 min) | **HOLD** | Keep window open, sample locks, do NOT abort blindly; escalate to DBA. |
| Wrong environment detected | **STOP + RESTORE** | Full stop; restore; incident review. |
| Data integrity mismatch (row counts) | **RESTORE** | Restore; investigate before any retry. |
| Rehearsal-vs-live timing >10x | **HOLD** | Continue monitoring; escalate; do not expand window silently. |

---

## 4. Rollback Runbook

### Decision authority
- **Restore vs Forward-fix decided by:** on-call SRE + Project Owner on-scene; **Project Owner ack required** for restore-during-window or any prod revert.
- **Point of No Return:** the moment `alembic upgrade head` exits 0 and app smoke passes, the DB is at head. After that, **restore-from-backup is the only clean revert**; `alembic downgrade` is **NOT** the recovery path.

### When to RESTORE (default for data/schema problems)
| Trigger | Why restore wins |
|---------|------------------|
| Migration failed mid-chain | DB state unknown; restore gives known-good |
| Data corruption / row mismatch | downgrade may truncate/fail (esp. `a4f7` VARCHAR shrink) |
| Smoke fail post-migrate | don't debug schema forward under pressure |
| Security incident | restore + incident response |

### When to FORWARD-FIX (app-level only)
| Trigger | Why forward-fix wins |
|---------|----------------------|
| Migrate OK, app config error | fix config, redeploy image |
| Feature-flag issue | toggle kill flag |
| Worker/beat problem | redeploy worker image |

### Commands (reference)
```powershell
# Restore path (primary): from pre-migrate backup/snapshot via Railway Postgres restore tooling.
# Forward-fix app: railway redeploy (previous deployment) — prod SalesOS only.

# Reference only — FORBIDDEN as default:
# docker run --rm -e DATABASE_URL=… -e SECRET_KEY=… -e JWT_SECRET_KEY=… salesos-migrate-4750038c downgrade d1a8c35e7f09
```
**Policy:** forward-fix + backup restore. No schema downgrade without a data plan and Project Owner ack ([deploy-rollback.md](./runbooks/deploy-rollback.md)).

---

## 5. Evidence Matrix

| Step | Evidence required | Where saved | Reviewed by |
|------|-------------------|-------------|-------------|
| T-30 health baseline | `/health` JSON + alembic SQL | `evidence/ops01-staging/cutover/` | Project Owner |
| T-15 backup | Backup ID + restore drill ID | change ticket | Project Owner |
| T-0 migration | full `migration-run.out` + exit 0 | `evidence/ops01-staging/cutover/` | Project Owner + DBA |
| T-0 locks | `pg_stat_activity`/`pg_locks` samples | same | DBA |
| T+1 schema verify | alembic + tables + indexes + RLS + partitions SQL | same | Project Owner |
| T+2 smoke | `/health` + auth path logs | same | Project Owner |
| T+10 log scan | `railway logs` excerpt | same | Project Owner |
| T+30 final | `/health` + alembic head | same | Project Owner |
| Sign-off | completed §6 packet | same | Project Owner archive |

---

## 6. Sign-off Packet

| Role | Signatory | Decision | Date/UTC | Signature/ID |
|------|-----------|----------|----------|--------------|
| Project Owner Review | | GO / CONDITIONAL / NO-GO | | |
| Project Owner Approval (final) | | GO / CONDITIONAL / NO-GO | | |
| Operations Approval (if in governance) | | GO / NO-GO | | |
| **Final** | | **GO / NO-GO** | | |

**FINAL GO requires ALL of:** ☐ Backup+restore verified · ☐ Soak K1–K6 closed + Project Owner review · ☐ Freeze confirmed · ☐ §1 checklist complete · ☐ No open P0 · ☐ EAB re-evaluation aligned.

---

## Cross-links (supporting only — this packet is the reference)
- [MAINTENANCE-WINDOW-PACKAGE.md](./MAINTENANCE-WINDOW-PACKAGE.md) — window sizing + rehearsal detail
- [PROD-MIGRATION-RISK.md](./PROD-MIGRATION-RISK.md) — per-revision risk
- [PROGRESS-WAVE12-PROD-MIGRATE-PREP.md](./PROGRESS-WAVE12-PROD-MIGRATE-PREP.md) — historical prep/policy
- [runbooks/deploy-rollback.md](./runbooks/deploy-rollback.md) — rollback policy
- [runbooks/backup-restore-drill.md](./runbooks/backup-restore-drill.md) — restore drill
- [SOAK-GATE-CHECKLIST.md](./enterprise-audit-board/history/EAB-2026-08-06-003/SOAK-GATE-CHECKLIST.md) — soak gates

## Honesty
- **Nothing executed.** No prod write/backup/migrate/restore. This packet is the prepared runbook.
- Rehearsal timing is ideal-case single-threaded; production faces shared-DB contention → keep window sized in minutes.
- Production GA remains **NO-GO** until soak + window + Row 5 signatures + EAB re-evaluation.
