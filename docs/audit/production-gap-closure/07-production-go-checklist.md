# Production GO Checklist

**Status: ALL ITEMS OPEN unless checked**  
**Authority:** This checklist gates Production GO. All items must be checked before Alembic migrate or production traffic.

---

## Section 1: Evidence Generation (OpenCode Autonomous)

- [ ] **G1 — FE toolchain logs**  
  Lint exit 0, tsc exit 0, build exit 0  
  Evidence: `evidence/wave0-fe/lint.log`, `tsc.log`, `build.log`

- [ ] **G2 — Unit pytest JUnit**  
  ~1542 passed, 2 skipped, 0 failures  
  Evidence: `evidence/wave3-pytest/junit.xml`, `pytest-report.json`

- [ ] **G3 — pg_dump/restore machine evidence**  
  Dump success, restore to disposable verified, row counts match  
  Evidence: `evidence/wave10-pg-dump/pg-dump-evidence.json`, `pg-restore-verify.json`

- [ ] **G4 — Auth contract probes**  
  13/13 PASS: register, login, me, 401, 403 CSRF, /metrics, etc.  
  Evidence: `evidence/wave5-auth-probes/auth-probe-summary.json`

- [ ] **G5 — Observability runtime exercise**  
  Prometheus targets UP, Grafana healthy, Loki available, no critical alerts  
  Evidence: `evidence/wave8-obs/obs-exercise-summary.json`

- [ ] **G6 — Security scanner run**  
  pip-audit + npm audit + architecture compliance + SBOM  
  Evidence: `evidence/wave9-secrets/scan-deps.log`, `sbom.json`

- [ ] **G7 — Alembic status transcript**  
  current = 0040, heads = 0040, check_alembic_head.py exit 0  
  Evidence: `evidence/wave1-alembic/alembic-status.log`

- [ ] **G8 — UI crawl with screenshots**  
  49 pages crawled, screenshots captured (40+ non-null)  
  Evidence: `evidence/wave13-full-ui-crawl/screenshots/*.png`

---

## Section 2: Extended Execution (OpenCode Start + Ops Monitor)

- [ ] **S1 — 48h local soak complete**  
  loop-summary with `soak_complete_claim: true`, wall-clock >= 48h, incidents reviewed  
  Evidence: `evidence/wave11-soak-48h-rerun/loop-summary-*.json`

- [ ] **S2 — WAL/PITR local drill**  
  PITR restore to timestamp succeeds on disposable; row counts match  
  Evidence: `evidence/wave10-pitr/pitr-restore-evidence.json`

---

## Section 3: Infrastructure (Manual / DevOps)

- [ ] **I1 — Cloud staging deployed**  
  `deploy-staging.yml` succeeds, health green, smoke 13/13  
  Evidence: `evidence/wave12-staging-cloud/deploy-*.json`

- [ ] **I2 — Staging rollback verified**  
  Rollback succeeds, health re-verified, frontend loads  
  Evidence: `evidence/wave12-staging-cloud/rollback-*.json`

- [ ] **I3 — Staging pre-deploy gates PASS**  
  SALESOS_TESTING clear, Alembic head match, /health 200  
  Evidence: `evidence/wave12-staging-cloud/gates-*.log`

---

## Section 4: Security

- [ ] **SE1 — Pentest or pilot residual acceptance**  
  Either full pentest report with remediation, OR signed pilot residual acceptance  
  Evidence: `evidence/wave2-pentest/` (pentest report or acceptance doc)

- [ ] **SE2 — No live secrets in git**  
  Gitleaks scan 0 findings; no hardcoded credentials  
  Evidence: `evidence/wave9-secrets/gitleaks-report.json`

- [ ] **SE3 — SSRF + tenant isolation confirmed**  
  Already locally verified; staging confirmation pending (I1)  
  Evidence: Existing `wave2-load/` + staging re-verification

---

## Section 5: Governance (Manual / Human)

- [ ] **GV1 — CTO signature**  
  SIGN_HERE.md CTO block: Date filled, Decision marked, Signature provided  
  Evidence: `SIGN_HERE.md` (updated)

- [ ] **GV2 — Tech Lead signature**  
  SIGN_HERE.md TL block: Date filled, Decision marked, Evidence reviewed checked, Signature provided  
  Evidence: `SIGN_HERE.md` (updated)

- [ ] **GV3 — RPO acceptance**  
  CTO documents accepted RPO (24h or WAL-based)  
  Evidence: `RPO_ACCEPTANCE.md`

- [ ] **GV4 — AI honesty PRC approved**  
  AI marketing scope reviewed and signed off  
  Evidence: `AI_HONESTY.md` (updated with PRC review)

- [ ] **GV5 — Feature freeze declared**  
  No new features without exception approval  
  Evidence: `LAUNCH_HYGIENE.md` (freeze declaration date)

- [ ] **GV6 — On-call roster published**  
  14-day hypercare schedule with escalation  
  Evidence: `LAUNCH_HYGIENE.md` (roster link)

- [ ] **GV7 — Production backup scheduled**  
  Daily 03:00 cronjob confirmed active  
  Evidence: `LAUNCH_HYGIENE.md` (cron confirmation)

- [ ] **GV8 — Staging RC digests confirmed**  
  Image digests pinned for release candidate  
  Evidence: `LAUNCH_HYGIENE.md` (digest list)

- [ ] **GV9 — SSL certificates provisioned**  
  Production domain SSL ready (Caddy auto-Let's Encrypt or manual)  
  Evidence: `LAUNCH_HYGIENE.md` (SSL verification)

---

## Section 6: Production Cutover (Only after ALL above checked)

- [ ] **P1 — Pre-migrate backup taken**  
  Full production pg_dump + Neo4j dump completed  
  Evidence: `evidence/wave3-prod-migrate/prod-pre-backup.json`

- [ ] **P2 — Alembic upgrade head executed on production**  
  `alembic upgrade head` exit 0; current = 0040  
  Evidence: `evidence/wave3-prod-migrate/prod-migrate-*.json`

- [ ] **P3 — Post-migrate health verified**  
  Backend /health = ok; all dependencies connected  
  Evidence: `evidence/wave3-prod-migrate/prod-post-health.json`

- [ ] **P4 — Production smoke test PASS**  
  13/13 smoke-auth PASS on production API  
  Evidence: `evidence/wave3-prod-migrate/prod-smoke-auth.json`

- [ ] **P5 — Production UI verified**  
  Frontend loads, login works, dashboard renders  
  Evidence: `evidence/wave3-prod-migrate/prod-ui-verify.json`

- [ ] **P6 — Monitoring verified on production**  
  Prometheus scraping, Grafana dashboard renders, alerts not firing  
  Evidence: `evidence/wave3-prod-migrate/prod-monitoring-verify.json`

- [ ] **P7 — On-call handoff confirmed**  
  First responder acknowledged, escalation tested  
  Evidence: `LAUNCH_HYGIENE.md` (handoff confirmation)

---

## Summary: GO gates

| Gate | Total items | Category |
|------|------------|----------|
| G1-G8 | 8 | Evidence (OpenCode autonomous) |
| S1-S2 | 2 | Extended Execution |
| I1-I3 | 3 | Infrastructure |
| SE1-SE3 | 3 | Security |
| GV1-GV9 | 9 | Governance |
| P1-P7 | 7 | Production Cutover |
| **TOTAL** | **32** | |

**Production GO requires ALL 32 items checked.**

---

## Pre-GO verification command

Before declaring GO, the following must ALL return true:

```powershell
# Verify evidence packages exist
$evidenceDirs = @(
  "wave0-fe", "wave1-alembic", "wave3-pytest", "wave5-auth-probes",
  "wave8-obs", "wave9-secrets", "wave10-pg-dump", "wave10-pitr",
  "wave11-soak-48h-rerun", "wave12-staging-cloud", "wave13-full-ui-crawl"
)
$missing = @()
foreach ($dir in $evidenceDirs) {
  $path = "docs/audit/ga-engineering-audit/evidence/$dir"
  if (-not (Test-Path $path)) { $missing += $dir }
}
if ($missing.Count -gt 0) {
  Write-Output "MISSING EVIDENCE: $($missing -join ', ')"
  exit 1
}

# Verify alembic head
docker compose exec backend alembic current | Select-String "0040"
if ($LASTEXITCODE -ne 0) { exit 1 }

# Verify health
$health = Invoke-RestMethod -Uri "http://localhost:8000/health"
if ($health.status -ne "ok") { exit 1 }

Write-Output "ALL PRE-CHECKS PASS"
```

---

## Sign-off

After all 32 items are checked, the following must sign:

| Role | Name | Signed | Date |
|------|------|--------|------|
| CTO | _____________ | [ ] | ________ |
| Tech Lead | _____________ | [ ] | ________ |
| DevOps | _____________ | [ ] | ________ |
| Security | _____________ | [ ] | ________ |
| Release Engineer | _____________ | [ ] | ________ |

**Only after all 5 signatures: PRODUCTION GO authorized.**
