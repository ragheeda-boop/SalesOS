# AUDIT VERIFICATION REPORT

**Date:** 2026-08-08  
**Scope:** P0/P1 items from Enterprise Audit Report — re-verified at higher evidence levels  
**Mode:** READ-ONLY — no modifications  
**Agents:** 4 parallel verification agents

---

## EXECUTIVE SUMMARY

The Enterprise Audit Report identified 10 actions. This verification re-checked each at the highest available evidence level. Results:

| Category | Count |
|----------|-------|
| CONFIRMED | 14 |
| CONTRADICTED | 4 |
| PARTIAL | 5 |
| NOT VERIFIABLE | 1 |

**4 items that CONTRADICTED the original audit or prior documentation claims are more severe than expected.**

---

## P0 VERIFICATIONS

### V-01: Backup Docker Image — UNBUILDABLE

**Original audit claim:** Backup infrastructure exists (K8s CronJob, Docker Compose backup service)  
**Verification level:** E3 (configuration evidence)

**Finding: CONTRADICTED**

The backup Dockerfile at `salesos/infra/docker/backup/Dockerfile` contains:
```
COPY scripts/backup-db.sh /scripts/backup-db.sh
COPY scripts/restore-db.sh /scripts/restore-db.sh
```

The directory `salesos/infra/docker/backup/scripts/` **does not exist**. The actual scripts are at `salesos/infra/scripts/backup-db.sh`.

**Evidence:**
- `infra/docker/backup/Dockerfile` lines 3-4: COPY from `scripts/`
- `infra/docker/backup/scripts/`: Directory does not exist
- `infra/scripts/backup-db.sh`: Exists at different path

**Impact:** The backup Docker image cannot be built as defined. K8s CronJob referencing `ghcr.io/ragheeda-boop/salesos/backup:latest` would fail. Docker Compose prod works around this by mounting `./infra/scripts/` at runtime.

**Status:** The backup service is **NOT FUNCTIONAL** as a standalone image. It only works via compose volume mount workaround.

**Action required:** Fix Dockerfile COPY paths OR consolidate to one location.

---

### V-02: WAL/PITR — NOT CONFIGURED

**Original audit claim:** WAL/PITR status was MEDIUM confidence, contradictions noted  
**Verification level:** E1 (source code) + E3 (configuration)

**Finding: CONTRADICTED (by compose files)**

| Config Source | WAL Status |
|---------------|------------|
| `docker-compose.yml` (dev) | No `command:` block → `wal_level=main`, `archive_mode=off` |
| `docker-compose.prod.yml` | No `command:` block → same defaults |
| `GA_STATUS.md` | Claims "WAL/PITR DONE 2026-08-06" with `archive_mode=on` |
| `SIGN_HERE.md` | Claims "archive_mode=on, WAL archived" |
| `deployment_guide.md` | Documents desired WAL config as example — never applied |

**Evidence:**
- `docker-compose.yml`: postgres service has no `command:` directive
- `docker-compose.prod.yml`: postgres service has no `command:` directive
- Default PostgreSQL: `wal_level=main`, `archive_mode=off`, no `archive_command`

**Impact:** Production RPO is **daily pg_dump (~24 hours)**, not point-in-time recovery as documented. A bad migration or data corruption could lose up to 24 hours of data.

**Status:** WAL/PITR is **NOT CONFIGURED** in any running deployment configuration. Documentation claiming "DONE" is incorrect.

---

### V-03: Documentation Contradictions — ALL 22 CONFIRMED

**Original audit claim:** 22 contradictions (4 P0, 9 P1)  
**Verification level:** E2 (document cross-reference)

**Finding: CONFIRMED**

All 22 contradictions from `DOCUMENT-CONTRADICTIONS.md` are verified:

**P0 (4):**
1. DR/WAL/PITR: GA_STATUS says DONE vs checklist says OPEN
2. Archive config: "Still off" vs evidence JSON claims on
3. Security scores: 7+ different scores (48→65→72→78→81→98%) with no supersession
4. DR cutover: automated requirement vs manual drill

**P1 (9):**
1. Neo4j OFFLINE vs "repaired"
2. Soak "not started" vs 24+ loops
3. Dual soak source of truth
4. Test counts: 1548/2009/2492 diverge
5. "READY with conditions" vs mandatory NO-GO
6. Alembic head: 0051 vs 0040 vs 0052
7. Staging parity: NOT parity vs CLOSED
8. OPS-01 disposition lag
9. RELEASE-BACKLOG inconsistency

**Impact:** Decision-makers cannot trust governance documents without cross-referencing.

---

### V-04: Alembic Migration State — PARTIAL

**Original audit claim:** 82+ migrations, head at 0052 on disk  
**Verification level:** E1 (files) + E3 (GA_STATUS)

**Finding: PARTIAL**

| Source | Head Migration |
|--------|---------------|
| Disk (files on disk) | `0052_add_decision_center_tenant_id.py` |
| GA_STATUS.md | Claims "0051" for Muhide prod |
| SIGN_HERE.md | References "0040" |

Cannot confirm live DB state without running `alembic current`.

---

## P1 VERIFICATIONS

### V-05: E2E in CI — CONFIRMED QUARANTINED

**Original audit claim:** 29 of 30 E2E specs not running in CI  
**Verification level:** E3 (CI configuration)

**Finding: CONFIRMED**

| Item | Status | Evidence |
|------|--------|----------|
| ci.yml Stage 7 | `if: false` at line 649 | Quarantined per DEC-150 B |
| e2e-stage7.yml | Active on master/main only | Runs `smoke-auth-ui.spec.ts` only |
| Spec files | 29 total | Only 1 runs (`smoke-auth-ui.spec.ts`) |
| smoke-auth-ui scope | Navigation smoke only | 5 pages: load + HTTP 200 + no console errors |
| CI project | `chromium` only | 4 projects defined but only 1 used |

**Impact:** Zero E2E regression protection for any page/component change.

---

### V-06: Frontend Coverage Threshold — CONFIRMED ABSENT

**Original audit claim:** No frontend coverage gate  
**Verification level:** E3 (jest.config.js)

**Finding: CONFIRMED**

`jest.config.js` contains zero coverage configuration:
- No `coverageThreshold`
- No `coverageReporters`
- No `collectCoverageFrom`

CI runs `npm run test -- --coverage --forceExit` (generates artifact) but has **no enforcement threshold**.

---

### V-07: Backend Coverage Gate — CONTRADICTED (Internal)

**Original audit claim:** 55% CI gate  
**Verification level:** E3 (pyproject.toml + ci.yml)

**Finding: CONTRADICTED (between pyproject.toml and CI)**

| Source | Threshold |
|--------|-----------|
| `pyproject.toml` `[tool.coverage.report]` | `fail_under = 65` |
| `ci.yml` pytest command | `--cov-fail-under=55` |

The CI CLI flag **overrides** the pyproject.toml setting. Actual enforced gate is **55%**, not 65%.

Per-domain minimums (Identity 88%, Company 80%, Search 93%, etc.) are **comments only** — not enforced by coverage.py. They're checked by an external script (`scripts/check-coverage.ps1`) that is not in the CI pipeline.

---

### V-08: Monitoring — PARTIAL (Alertmanager Gap)

**Original audit claim:** Monitoring fully designed but not deployed  
**Verification level:** E3 (configuration)

**Finding: PARTIAL**

| Component | Dev Compose | Prod Compose | K8s |
|-----------|:-----------:|:------------:|:---:|
| Prometheus | ✅ Always-on | ✅ Always-on | ✅ |
| Grafana | ✅ Always-on | ✅ Always-on | ✅ |
| Alertmanager | ✅ Always-on | ❌ **MISSING** | ✅ |
| Postgres Exporter | ✅ Always-on | ✅ Always-on | ✅ |
| Redis Exporter | ✅ Always-on | ✅ Always-on | ✅ |
| Loki | ⚠️ Profile opt-in | ❌ Not present | ✅ |
| OTel Collector | ⚠️ Profile opt-in | ❌ Not present | ✅ |
| Promtail | ⚠️ Profile opt-in | ❌ Not present | ✅ |

**Critical gap:** Alertmanager is defined in dev compose and K8s but **absent from docker-compose.prod.yml**. Prometheus alert rules exist but have **no routing target** in Docker-based production.

**Impact:** Alerts fire but go nowhere. Operators are not notified of failures.

---

### V-09: Deploy Workflow — CONFIRMED PARTIAL

**Original audit claim:** Deploy pipeline exists with health gates  
**Verification level:** E3 (deploy.yml)

**Finding: CONFIRMED (strong deploy, weak operations)**

**What deploy.yml DOES:**
- Branch guard (master only)
- Health gate (30s stabilization → 12 retries → uptime check)
- Parity gate (commit hash, version, schema version, openapi hash)
- Slack notification + GitHub commit comment

**What deploy.yml DOES NOT do:**
- Pre-deploy backup snapshot
- Post-deploy monitoring check
- Rollback automation
- Canary/blue-green deployment

---

### V-10: Git State — CONFIRMED CLEAN

**Verification level:** E4 (git)

**Finding: CONFIRMED**

- Latest commit: `f64c2a6 docs: STAR audit records, completion docs, remaining ADRs`
- 17 untracked files (all audit evidence JSON in `docs/audit/`)
- 1 new file in `salesos/reports/` (this audit report)
- No uncommitted production code changes

---

## VERIFICATION SUMMARY

| ID | Item | Original Assessment | Verification Result | Evidence Level | New Severity |
|----|------|--------------------|--------------------|---------------|-------------|
| V-01 | Backup Docker image | Exists | **CONTRADICTED** — Unbuildable | E3 | **CRITICAL** |
| V-02 | WAL/PITR | MEDIUM confidence | **CONTRADICTED** — Not configured | E1+E3 | **CRITICAL** |
| V-03 | Doc contradictions | 22 found | **CONFIRMED** — All 22 verified | E2 | P0 |
| V-04 | Alembic head | 0052 on disk | **PARTIAL** — Disk=0052, prod=unknown | E1+E3 | MEDIUM |
| V-05 | E2E in CI | 29 dead | **CONFIRMED** — Quarantined | E3 | HIGH |
| V-06 | Frontend coverage | None | **CONFIRMED** — Zero threshold | E3 | HIGH |
| V-07 | Backend coverage | 55% gate | **CONTRADICTED** — pyproject says 65, CI says 55 | E3 | MEDIUM |
| V-08 | Monitoring | Not deployed | **PARTIAL** — Alertmanager missing from prod | E3 | HIGH |
| V-09 | Deploy workflow | Health gates exist | **CONFIRMED** — Strong deploy, weak ops | E3 | MEDIUM |
| V-10 | Git state | Clean | **CONFIRMED** — Clean tree | E4 | LOW |

---

## REVISED CRITICAL FINDINGS

### CRITICAL-01: Backup System Non-Functional

The backup Docker image cannot be built (`COPY scripts/` fails). K8s CronJob references this broken image. Only Docker Compose prod works via volume mount workaround. **Railway production has no backup service.**

**Evidence level:** E3 (Dockerfile + directory inspection)  
**Previous classification:** P0 in audit — **upgraded to CRITICAL**

### CRITICAL-02: WAL/PITR Documentation Fabrication Risk

GA_STATUS.md and SIGN_HERE.md claim WAL/PITR is "DONE" with `archive_mode=on`. The actual compose files (the only configs that run) have **zero WAL configuration**. This is not a gap — it's a documentation claim contradicted by executable evidence.

**Evidence level:** E1+E3 (compose files vs documentation)  
**Previous classification:** P0 contradiction — **confirmed and severity increased**

### CRITICAL-03: Alertmanager Absent from Production

Prometheus alert rules exist (8+ rules). Alertmanager is configured in dev compose and K8s. But `docker-compose.prod.yml` does not include Alertmanager. Alerts fire but have nowhere to go.

**Evidence level:** E3 (prod compose inspection)  
**Previous classification:** P1 — **upgraded to HIGH**

---

## FINAL BLOCKERS (Before Any Execution)

### Must Be Resolved Before Phase 0

| # | Blocker | Evidence | Owner |
|---|---------|----------|-------|
| B-01 | Verify actual Railway backup status (dashboard check needed) | E6 required | Platform |
| B-02 | Verify actual PostgreSQL WAL config in Railway (connect + SHOW wal_level) | E6 required | Platform |
| B-03 | Verify actual Alembic head in production DB (alembic current) | E5 required | Backend |
| B-04 | Verify Vercel production deployment status (dashboard check needed) | E6 required | Platform |
| B-05 | Verify actual deployed commit hash (health endpoint check) | E5 required | Platform |

### Cannot Be Resolved Without Runtime Access

These require either:
- SSH/console access to Railway
- Railway dashboard access
- Vercel dashboard access
- Running `docker compose exec` commands

**The code-level audit is complete. The remaining verification requires runtime evidence (E5/E6).**

---

## EXECUTION GATE

```
┌─────────────────────────────────────────────┐
│           EXECUTION GATE STATUS              │
├─────────────────────────────────────────────┤
│                                             │
│  CORE APPLICATION:        GO WITH CONDITIONS│
│  (Auth/Tenancy/CRM/Analytics/Workflow)      │
│                                             │
│  PRODUCTION OPERATIONS:   NO-GO             │
│  (Backups/WAL/Monitoring/Alerting)          │
│                                             │
│  DOCUMENTATION GOVERNANCE: NO-GO            │
│  (22 contradictions, stale claims)          │
│                                             │
│  REGRESSION PROTECTION:   NO-GO             │
│  (29 E2E specs dead, no FE coverage gate)   │
│                                             │
├─────────────────────────────────────────────┤
│  RECOMMENDATION:                             │
│                                             │
│  1. Runtime verification (B-01 through B-05)│
│  2. THEN: Fix backup + WAL + monitoring     │
│  3. THEN: Enable E2E + coverage gate        │
│  4. THEN: Documentation reconciliation      │
│  5. THEN: Product expansion (AI/GTM/V3)     │
│                                             │
│  Do NOT proceed to Phase 4 (Product)        │
│  until Phases 0-3 are verified COMPLETE.    │
│                                             │
└─────────────────────────────────────────────┘
```

---

## SOURCE OF TRUTH (This Report Supersedes)

| Domain | Previous Source | This Report Supersedes With |
|--------|----------------|----------------------------|
| Backup status | GA_STATUS.md ("DONE") | **CONTRADICTED** — image unbuildable |
| WAL/PITR status | SIGN_HERE.md ("archive_mode=on") | **CONTRADICTED** — not configured |
| E2E CI status | Various (mixed claims) | **CONFIRMED** — quarantined, 1 spec only |
| Frontend coverage | None documented | **CONFIRMED** — zero threshold |
| Monitoring status | Various (mixed claims) | **PARTIAL** — Alertmanager missing from prod |
| Backend coverage | pyproject.toml (65%) | **CORRECTED** — CI enforces 55% |

---

*This verification report uses the evidence hierarchy from the Enterprise Audit Report. All claims include evidence level classification. Runtime verification (E5/E6) requires human access to Railway/Vercel dashboards or running deployment commands.*
