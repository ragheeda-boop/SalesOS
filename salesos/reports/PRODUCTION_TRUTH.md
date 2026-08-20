# PRODUCTION TRUTH

**Captured:** 2026-08-08T16:30:00+03:00  
**Captured addendum:** 2026-08-08T18:43:00+03:00  
**Evidence Level:** E1 + E3 + E4 + **E5 + E6 collected**. Gate 0 remains **OPEN** (not all pass criteria met).  
**Mode:** Gate 0 — READ-ONLY verification  
**Gate 1:** LOCKED · **Gate 2:** LOCKED · **Gate 3:** LOCKED · **Gate 4:** LOCKED

---

## Evidence Classification

| Level | Definition | Available? |
|-------|-----------|------------|
| E1 | Source code / files on disk | YES |
| E2 | Configuration / documentation cross-reference | YES |
| E3 | CI/deploy configuration inspection | YES |
| E4 | Git history / test results | YES |
| E5 | Runtime verification (backend console, curl) | **YES — partial** (WAL `pg_settings`, `alembic_version` row, `/health`, `/api/v1/version` 404) |
| E6 | Dashboard verification (Railway, Vercel) | **YES — partial** (Railway Backups/Deployments, Vercel Deployments) |

**Gate 0 Status: OPEN** — E5/E6 evidence recorded; B-01 PARTIAL, B-03 VERIFIED DRIFT, B-05 UNKNOWN. Not a Production GO. Gate 1 remains LOCKED.

| Item | Judgment |
|------|----------|
| **B-01** | PARTIAL |
| **B-02** | VERIFIED CONFIGURATION — not PITR operational |
| **B-03** | VERIFIED DRIFT |
| **B-04** | VERIFIED |
| **B-05** | UNKNOWN |
| **Gate 0** | OPEN |
| **Gate 1–4** | LOCKED |

---

## B-01: Railway Backup Status

**Status:** PARTIAL  
**Evidence Level:** E3 (configuration) + E6 (Railway dashboard)  
**Pass Criteria:** Backup exists with schedule, retention, last backup timestamp  
**Result:** PARTIAL — production backup/restore lifecycle not conclusively established. Restore was not clicked.

### Runtime Evidence (E6) — 2026-08-08

- Railway managed **volume backups:** none.
- **PITR UI** window visible: 2026-08-06 22:29 → 2026-08-08 18:26 + Restore control (not used).
- Banner: Point-in-Time Recovery is only available for Pro plan.
- DIY buckets: `salesos-pitr` ≈ 96.0 MB · `salesos-backups` ≈ 20.2 MB.
- SalesOS backup service: **not present**.
- B-02 WAL archiving config ≠ verified backup + retention + restore lifecycle.

### Code-Level Evidence (E3)

| Item | Finding | Source |
|------|---------|--------|
| Backup Dockerfile | EXISTS at `infra/docker/backup/Dockerfile` | E1 |
| Dockerfile COPY paths | BROKEN — copies from `scripts/` but actual scripts at `infra/scripts/` | E1 (lines 3-4) |
| Backup script | EXISTS at `infra/scripts/backup-db.sh` — functional pg_dump with S3 upload, 7-day retention | E1 |
| Compose backup service | EXISTS in `docker-compose.prod.yml` lines 505-544 | E3 |
| Volume mount workaround | Compose mounts `./infra/scripts/backup-db.sh` bypassing broken Dockerfile COPY | E3 (line 517) |
| Cron schedule | 3 AM daily (`0 3 * * *`) | E3 (line 513) |
| Retention | 7 days (default in backup-db.sh) | E1 (line 9) |
| S3 upload | Configured via `S3_BUCKET` env var | E1 (lines 45-53) |

### Documentation Claims vs Reality

| Source | Claim | Reality |
|--------|-------|---------|
| GA_STATUS.md | "Backup DR DONE 2026-08-06" | E3: Backup Dockerfile UNBUILDABLE (wrong COPY paths); E6: no volume backups; no SalesOS backup service observed |
| Audit Verification V-01 | "Backup image cannot be built" | CONFIRMED — `infra/docker/backup/scripts/` directory does not exist |

---

## B-02: PostgreSQL WAL Configuration

**Status:** VERIFIED CONFIGURATION — **not** PITR fully operationally validated  
**Evidence Level:** E1+E3 (compose) + **E5 (runtime `pg_settings`)**  
**Pass Criteria:** Actual WAL configuration matches documentation  
**Result:** Runtime WAL archiving **is configured**. Repository compose does **not** represent that runtime. Restore/retention/RPO not validated.

### Runtime Evidence (E5) — 2026-08-08

Railway production Postgres (`2744b8e0`, environment `production`).  
`SHOW wal_level; SHOW archive_mode; SHOW archive_command;` executed in Data Query UI → **0 rows / Query returned no rows**.  
Equivalent catalog query:

```sql
SELECT name, setting FROM pg_settings
WHERE name IN ('wal_level','archive_mode','archive_command')
ORDER BY name;
```

| name | setting |
|------|---------|
| `wal_level` | `replica` |
| `archive_mode` | `on` |
| `archive_command` | `/usr/local/bin/pgbackrest-archive-push-wrapper.sh %p` |

This proves **WAL archiving configuration**, not a successful restore drill or RPO/RTO.

### Code-Level Evidence (E3)

| Item | Finding | Source |
|------|---------|--------|
| Dev compose postgres | NO `command:` block → defaults: `wal_level=main`, `archive_mode=off` | E3 (`docker-compose.yml` lines 15-32) |
| Prod compose postgres | NO `command:` block → defaults: `wal_level=main`, `archive_mode=off` | E3 (`docker-compose.prod.yml` lines 11-36) |
| WAL assessment script | EXISTS at `infra/scripts/wal-pitr-local-assess.sh` — read-only | E1 |
| Deployment guide | Documents WAL config as example — never applied | E3 (`docs/deployment_guide.md` lines 1564-1584) |

### Documentation Claims vs Reality

| Source | Claim | Reality |
|--------|-------|---------|
| GA_STATUS.md | "WAL/PITR DONE 2026-08-06" with `archive_mode=on` | E3: Compose files have NO WAL configuration. **E5: Railway runtime HAS `archive_mode=on`.** |
| SIGN_HERE.md | "archive_mode=on, WAL archived" | E3 compose contradiction remains; E5 runtime matches the *claim* of archive_mode=on, not a restore proof |
| Audit Verification V-02 | "WAL/PITR NOT CONFIGURED" | True for **repository compose**. **False for Railway production runtime.** |

### Impact

Repository compose ≠ Railway production PostgreSQL configuration. Do not treat compose defaults as production truth. Do not claim PITR working from WAL settings alone.

---

## B-03: Alembic Migration Head

**Status:** VERIFIED DRIFT — production database is behind disk head  
**Evidence Level:** E1 (files) + E3 (docs) + **E5 (table read)**  
**Pass Criteria:** Record actual head; compare to disk and docs  
**Result:** Production ≠ disk; Production ≠ documentation. No migrate run. `alembic current` not used as authority.

### Runtime Evidence (E5) — 2026-08-08

```text
public.alembic_version.version_num = d1a8c35e7f09
```

Source: Railway Data UI table view (not `alembic current`).

```text
file     = salesos/backend/app/alembic/versions/d1a8c35e7f09_db05_slice4_enable_rls_deferred_8.py
revision = d1a8c35e7f09
```

Direct child on disk (not applied on production):

```text
e2b9d46f8a10_db05_slice5c_create_admin_global_trio.py
down_revision = d1a8c35e7f09
```

`alembic current` via SSH previously failed: `ModuleNotFoundError: No module named 'scripts'` (in `065d1d3a466b_enable_rls_company_features.py`). **Not fixed.** Finding only.

### Code-Level Evidence

| Source | Head Migration | Notes |
|--------|---------------|-------|
| Production DB (E5) | `d1a8c35e7f09` | Runtime row |
| Disk (alembic versions/) | Numeric series through `0052_add_decision_center_tenant_id.py` **plus later hash revisions** including `e2b9d46f8a10` | E1 — production is not tip |
| GA_STATUS.md | "0051" | E3 — stale vs runtime hash id |
| SIGN_HERE.md | "0040" | E3 — stale |
| Audit Verification V-04 | "Disk=0052, prod=unknown" | E3 — prod no longer unknown |

### Documentation Contradictions

| Source | Claim | Severity |
|--------|-------|----------|
| GA_STATUS.md | "Alembic 0051 (was 0049)" | P1 — contradicts disk and production `d1a8c35e7f09` |
| SIGN_HERE.md | References "0040" | P1 — stale |
| Audit contradiction register | RC-P1-06: "Alembic head: 0051 vs 0040 vs 0052" | P1 — runtime identity is `d1a8c35e7f09` |

---

## B-04: Vercel Deployment Status

**Status:** VERIFIED  
**Evidence Level:** E3 (CI configuration) + **E6 (Vercel dashboard)**  
**Pass Criteria:** Latest deployment matches expected commit  
**Result:** Latest Production Ready matches git HEAD recorded in this file (`f64c2a6`).

### Runtime Evidence (E6) — 2026-08-08

| Field | Value |
|-------|--------|
| Project | `muhide/sales-os` |
| Latest Production | **Ready** |
| Commit | `f64c2a6` |
| Branch | `master` |
| Alias | `sales-36ymk8p25` |
| Message | `docs: STAR audit records, comp...` |
| Time | ~2026-08-08 16:09 +0300 |
| Older Production still listed | `9f3c45b` (Wave 25) |

Matches E4 latest git commit `f64c2a66c6587ff2d11a859cec8e4a85d5539dca`.

### Code-Level Evidence (E3)

| Item | Finding | Source |
|------|---------|--------|
| Deploy trigger | Push to master → Vercel Git integration | E3 (`deploy.yml` lines 14-15) |
| Deploy workflow | `deploy.yml` — Railway backend + optional Vercel CLI | E3 |
| Vercel config | Git integration primary; CLI optional when `VERCEL_*` secrets set | E3 (`deploy.yml` line 4) |
| Frontend endpoint | `https://sales-os-jet.vercel.app` (200 OK per Wave 23) | E3 (GA_STATUS.md) |

---

## B-05: Deployed Backend Commit

**Status:** UNKNOWN  
**Evidence Level:** E3 (endpoint definition) + E4 (git) + **E5 (HTTP)** + **E6 (Railway Deployments)**  
**Pass Criteria:** Commit matches latest master; schema present  
**Result:** Production commit UNKNOWN — runtime version endpoint unavailable; CLI deploy shows no Git SHA.

### Runtime Evidence (E5 + E6) — 2026-08-08

| Probe | Result |
|-------|--------|
| `GET https://salesos-production-96c0.up.railway.app/api/v1/version` | **404** |
| `GET /version` | **404** (prior probe) |
| `GET /health` | **200** · `version`: `5.1.0-rc1` |
| Service | SalesOS · Online |
| Active deploy | `railway up` **via CLI** |
| Time | **2026-08-06 00:29 +0300** |
| Deploy id | `bdce3450-53d4-4bc4-90d8-4c940e0e1002` |
| Git SHA | **not shown** |
| Healthcheck path (Details) | `/health` |

Do not infer a specific backend git commit from FE `f64c2a6` or from `/health` `5.1.0-rc1`.

### Code-Level Evidence

| Item | Finding | Source |
|------|---------|--------|
| Version endpoint | `/api/v1/version` and `/version` — EXISTS **on disk** | E3 (`main.py` lines 416-464) |
| VersionResponse schema | Returns: service, api_version, backend_commit, build_date, build_id, schema_version, openapi_hash | E3 (`schemas.py` lines 84-99) |
| Schema version source | Reads from `alembic_version` table | E3 (`main.py` lines 442-448) |
| Backend commit source | `settings.build_commit` or `SOURCE_COMMIT` or `RAILWAY_GIT_COMMIT_SHA` | E3 (`main.py` lines 452-453) |
| Latest git commit | `f64c2a66c6587ff2d11a859cec8e4a85d5539dca` (2026-08-08 16:09:32 +0300) | E4 (git log) |
| Commit message | "docs: STAR audit records, completion docs, remaining ADRs (0103-0108)" | E4 |

Endpoint exists in current repository code and is **absent on the running production image**.

---

## Discrepancies Summary

### P0 — Critical (Decision Blockers)

| ID | Claim A | Source A | Claim B | Source B | Evidence |
|----|---------|----------|---------|----------|----------|
| DISC-01 | Backup DR DONE | GA_STATUS.md | Backup Dockerfile UNBUILDABLE; prod backup lifecycle unproven | Audit V-01 + E6 | E3 COPY paths broken; E6 no volume backups / no SalesOS backup service |
| DISC-02 | WAL/PITR DONE, archive_mode=on | GA_STATUS.md, SIGN_HERE.md | Compose has no WAL; runtime HAS WAL | Compose vs E5 `pg_settings` | Compose ≠ Railway. Runtime `archive_mode=on` is not PITR operational proof |
| DISC-03 | Alembic 0051 | GA_STATUS.md | Alembic 0052 / hash tip on disk | Disk files | E1+E5: production identity is `d1a8c35e7f09`, behind disk |
| DISC-04 | Multiple security scores (48→65→72→78→81→98%) | Various | 48/100 baseline | Enterprise Audit | E2: Score shopping across documents |

### P1 — High (Requires Resolution)

| ID | Issue | Evidence |
|----|-------|----------|
| DISC-05 | Alembic head: 0051 vs 0040 vs 0052 (three docs disagree) | E1+E3; runtime adds `d1a8c35e7f09` |
| DISC-06 | Staging parity "CLOSED" vs "NOT parity" | E3 |
| DISC-07 | Test counts: 1548/2009/2492 (three docs) vs actual ~220 BE + ~94 FE | E3 |
| DISC-08 | "READY with conditions" vs mandatory NO-GO | E3 |
| DISC-09 | Frontend/Backend deployment drift (Gate 0 session label **DISC-05**) | E5+E6: see Findings |

---

## Findings (record only — not remediations)

These are **findings**, not a fix list. Gate 0 remains read-only. Do not deploy, migrate, Restore, or change Railway/Vercel from this section.

1. **Repository compose ≠ Railway production PostgreSQL configuration.** Compose has no WAL `command:` block; production `pg_settings` shows `wal_level=replica`, `archive_mode=on`, pgBackRest archive wrapper.
2. **Migration drift.** Production `alembic_version` = `d1a8c35e7f09`; disk contains at least child `e2b9d46f8a10` and newer revisions. Docs citing 0040 / 0051 are stale.
3. **DISC-09 (session DISC-05) — Frontend/Backend deployment drift.** Production frontend deployment is verified at `f64c2a6`; backend runtime commit is not verifiable because the canonical `/api/v1/version` endpoint returns 404. The last known successful backend deployment is older than the verified frontend deployment (`railway up` CLI, 2026-08-06 00:29 +0300, no Git SHA).
4. **Backup/PITR lifecycle unproven.** WAL archiving is configured; volume backups are empty; PITR UI vs Pro banner conflict; DIY buckets exist; SalesOS backup service not observed; Restore not executed.

---

## Gate status

**Gate 0 is CLOSED only when pass criteria for all 5 items are met and this file holds E5/E6 evidence.**  
E5/E6 evidence is now recorded. Pass criteria are **not** all met.

```text
GATE 0  → OPEN
GATE 1  → LOCKED
GATE 2  → LOCKED
GATE 3  → LOCKED
GATE 4  → LOCKED
```

No further B-05 search. Do not run Alembic upgrade. Do not click Restore. Do not change infrastructure from Gate 0.

Documentation baseline in this file is updated. **Gate 0 itself remains OPEN.**

---

## Approved addendum (verbatim) — 2026-08-08T18:43+03:00

```text
**Captured addendum:** 2026-08-08T18:43+03:00
**Evidence Level:** E5 + E6 collected. Gate 0 remains OPEN (not all pass criteria met).

E5 = YES (partial: WAL pg_settings, alembic_version row, /health, /api/v1/version 404)
E6 = YES (partial: Railway Backups/Deployments, Vercel Deployments)

## B-01 — PARTIAL
Volume backups: none. PITR UI window 2026-08-06 22:29 → 2026-08-08 18:26 + Restore (not clicked).
Banner: PITR only available for Pro plan. Buckets: salesos-pitr ~96.0 MB, salesos-backups ~20.2 MB.
SalesOS backup service: not present. WAL config (B-02) ≠ backup/restore lifecycle verified.

## B-02 — VERIFIED CONFIGURATION (not PITR fully validated)
Source: pg_settings on Railway production Postgres (SHOW returned 0 rows in Data UI).
wal_level = replica
archive_mode = on
archive_command = /usr/local/bin/pgbackrest-archive-push-wrapper.sh %p
Finding: Railway runtime ≠ repository compose (compose has no WAL command block).

## B-03 — VERIFIED DRIFT
public.alembic_version.version_num = d1a8c35e7f09
File: d1a8c35e7f09_db05_slice4_enable_rls_deferred_8.py
Child on disk: e2b9d46f8a10 (down_revision = d1a8c35e7f09)
alembic current: ModuleNotFoundError: No module named 'scripts' (not fixed).
Docs 0040/0051 stale. Production ≠ disk head. No migrate run.

## B-04 — VERIFIED
Vercel muhide/sales-os Production Ready f64c2a6 master
~2026-08-08 16:09 +0300 (sales-36ymk8p25). Matches git HEAD recorded in this file.

## B-05 — UNKNOWN
GET /api/v1/version → 404. GET /health → 200 version 5.1.0-rc1.
Active deploy: railway up via CLI, 2026-08-06 00:29 +0300, id bdce3450-53d4-4bc4-90d8-4c940e0e1002.
Git SHA: not shown. backend_commit unverifiable.
DISC-05: Production frontend verified at f64c2a6; backend runtime commit is not verifiable because canonical /api/v1/version returns 404. Last known successful backend deployment is older than the verified frontend deployment.

Gate 0 status: OPEN. Do not start Gate 1.
```

In this file’s discrepancy register, the session label **DISC-05** above is recorded as **DISC-09** to avoid colliding with pre-existing DISC-05 (Alembic 0051 vs 0040 vs 0052).

---

*Gate 0 remains READ-ONLY for remediations. This file update is documentation baseline only. No Production GO.*
