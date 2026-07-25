# Action Plan — Closing Production Blockers

**Strategy:** Execute every autonomous task immediately. Frame partial tasks. Document manual prerequisites. Build evidence packages per wave.

---

## Phase 1: Evidence Generation (OpenCode autonomous — ~2-4 hours)

Execute now. No infrastructure needed. Docker stack must be up.

### Task A1: Pytest Suite Evidence (closes B7)

```powershell
# From salesos/ directory
docker compose -f docker-compose.test.yml run --rm test pytest tests/unit `
  --junitxml=/app/test-results/junit.xml `
  --json-report --json-report-file=/app/test-results/pytest-report.json `
  -v 2>&1 | Tee-Object -FilePath "../docs/audit/ga-engineering-audit/evidence/wave3-pytest/pytest-stdout.log"
```

**Expected output:**
```
evidence/wave3-pytest/
  junit.xml                    # JUnit XML with per-test results
  pytest-report.json           # Machine-readable pass/fail/skip counts
  pytest-stdout.log            # Full stdout with exit code
```

**Validation:** `junit.xml` must show ~1542 passed, 2 skipped. Exit code = 0 when using `--strict-markers` with quarantine.

---

### Task A2: FE Toolchain Logs (closes B8)

```powershell
# From salesos/frontend/
Set-Location salesos/frontend

# npm run lint
npm run lint 2>&1 | Tee-Object -FilePath "../../docs/audit/ga-engineering-audit/evidence/wave0-fe/lint.log"

# npx tsc --noEmit
npx tsc --noEmit 2>&1 | Tee-Object -FilePath "../../docs/audit/ga-engineering-audit/evidence/wave0-fe/tsc.log"

# npm run build
npm run build 2>&1 | Tee-Object -FilePath "../../docs/audit/ga-engineering-audit/evidence/wave0-fe/build.log"
```

**Expected output:**
```
evidence/wave0-fe/
  lint.log     # Exit 0, no ESLint errors (Tailwind warnings acceptable)
  tsc.log      # Exit 0, clean typecheck
  build.log    # Exit 0, 51 static pages
```

**Note:** These require Node.js toolchain on host. If unavailable, use Docker:
```powershell
docker compose run --rm frontend sh -c "npm run lint && npx tsc --noEmit && npm run build"
```

---

### Task A3: pg_dump/restore Machine Evidence (closes B6)

```powershell
# From salesos/ directory
# Ensure Docker stack is up
docker compose ps  # confirm backend, postgres, etc. running

# Run backup
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/backup.ps1

# Run verification
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/verify-backup.ps1 `
  -EvidenceDir "../docs/audit/ga-engineering-audit/evidence/wave10-pg-dump/"
```

**Or using infra scripts (bash via Docker):**
```bash
docker compose exec backend bash -c "
  ./infra/scripts/backup-db.sh
"
```

**Expected output (evidence/wave10-pg-dump/):**
```
  pg-dump-YYYYMMDDTHHMMSSZ.json    # {dump_size_mb, toc_entries, table_count, exit_code, checksum}
  pg-restore-verify-*.json         # {row_counts_match, tables_restored, errors}
  pg-dump-stdout.log               # Full pg_dump output
```

---

### Task A4: Auth Contract Probes (closes B17)

```powershell
# From salesos/ directory
# Create evidence folder
New-Item -ItemType Directory -Force -Path "../docs/audit/ga-engineering-audit/evidence/wave5-auth-probes/"

# Run smoke-auth (curl-based, no browser needed)
$env:SMOKE_EMAIL = 'admin@salesos.io'
$env:SMOKE_PASSWORD = '<from env>'
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/smoke-auth.ps1 2>&1 |
  Tee-Object -FilePath "../docs/audit/ga-engineering-audit/evidence/wave5-auth-probes/smoke-auth-stdout.log"
```

**Expected output:**
```
evidence/wave5-auth-probes/
  smoke-auth-stdout.log                   # Full curl probe results
  auth-probe-summary.json                 # 13-pass summary (CSRF, 401, metrics, etc.)
```

---

### Task A5: Observability Exercise (closes B9)

```powershell
# From salesos/ directory
# Start observability profile (if not running)
docker compose --profile observability up -d

# Wait for services to be healthy
Start-Sleep -Seconds 30

# Capture Prometheus scrape targets
curl -s http://localhost:9090/api/v1/targets | Out-File "../docs/audit/ga-engineering-audit/evidence/wave8-obs/prometheus-targets.json" -Encoding utf8

# Capture Grafana health
curl -s http://localhost:3001/api/health | Out-File "../docs/audit/ga-engineering-audit/evidence/wave8-obs/grafana-health.json" -Encoding utf8

# Run a basic alert firing test (simulate backend down briefly)
# Check Prometheus alerts
curl -s http://localhost:9090/api/v1/alerts | Out-File "../docs/audit/ga-engineering-audit/evidence/wave8-obs/prometheus-alerts.json" -Encoding utf8

# Produce machine evidence summary
# (wrap in Python/PS1 to output structured JSON)
```

**Expected output:**
```
evidence/wave8-obs/
  prometheus-targets.json     # All scrape targets status
  grafana-health.json         # Grafana API health
  prometheus-alerts.json      # Alert state
  obs-exercise-summary.json   # Structured PASS/FAIL per check
```

---

### Task A6: Alembic Upgrade Transcript (closes B16)

```powershell
# From salesos/ directory
docker compose exec backend alembic current 2>&1 |
  Tee-Object -FilePath "../docs/audit/ga-engineering-audit/evidence/wave1-alembic/alembic-current.log"

docker compose exec backend alembic heads 2>&1 |
  Tee-Object -FilePath "../docs/audit/ga-engineering-audit/evidence/wave1-alembic/alembic-heads.log"

docker compose exec backend alembic history 2>&1 |
  Tee-Object -FilePath "../docs/audit/ga-engineering-audit/evidence/wave1-alembic/alembic-history.log"
```

**Expected output:**
- alembic current = `0040 (head)`
- alembic heads = `0040`
- Full migration history from base → 0040

---

### Task A7: Security Scanner Run (closes B15)

```powershell
# From salesos/ directory
# Run dependency scanner
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/scan-deps.ps1 2>&1 |
  Tee-Object -FilePath "../docs/audit/ga-engineering-audit/evidence/wave9-secrets/scan-deps.log"

# Run architecture compliance
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/arch-compliance.ps1 2>&1 |
  Tee-Object -FilePath "../docs/audit/ga-engineering-audit/evidence/wave9-secrets/arch-compliance.log"

# Run SBOM generation
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/sbom.ps1
Copy-Item salesos/sbom.json "../docs/audit/ga-engineering-audit/evidence/wave9-secrets/sbom.json"
```

**Expected output:**
```
evidence/wave9-secrets/
  scan-deps.log             # pip-audit + npm audit results
  arch-compliance.log       # Architecture compliance scores
  sbom.json                 # CycloneDX 1.5 SBOM
```

---

### Task A8: UI Crawl With Screenshots (closes B14)

```powershell
# From salesos/ directory
# Modify the Playwright crawl config to enable screenshots
# Run full crawl
$env:SMOKE_EMAIL = 'admin@salesos.io'
$env:SMOKE_PASSWORD = '<from env>'
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/full-ui-crawl.ps1
```

**Note:** May require updating `full-ui-crawl.spec.ts` to set `screenshot: 'on'` in Playwright config. Output PNGs should be saved alongside the JSON report.

**Expected output:**
```
evidence/wave13-full-ui-crawl/
  full-ui-crawl-report.json   # Same JSON as before, but with non-null screenshot paths
  screenshots/                # PNG files per page (expected ~49 files)
    login.png
    dashboard.png
    companies.png
    ...
```

---

## Phase 2: Extended Execution (OpenCode starts — ops monitors)

### Task B1: 48h Local Soak (closes B1 partially)

```powershell
# From salesos/ directory (requires stack up)
$evidenceDir = "../docs/audit/ga-engineering-audit/evidence/wave11-soak-48h-rerun/"
New-Item -ItemType Directory -Force -Path $evidenceDir

# Start 48h soak as background job
$job = Start-Job -Name "soak-48h" -ScriptBlock {
  param($dir)
  Set-Location "salesos"
  python -u scripts/wave11-soak-gate.py `
    --api http://localhost:8000 `
    --fe http://localhost:3000 `
    --compose-dir . `
    --loop `
    --interval 300 `
    --duration-hours 48 `
    --evidence-dir $dir `
    --skip-alembic `
    2>&1 | Tee-Object -FilePath (Join-Path $dir "soak-48h-stdout.log")
} -ArgumentList $evidenceDir

# Monitor job
Write-Output "Soak job started: $($job.Id)"
Write-Output "Monitor with: Get-Job -Id $($job.Id)"
Write-Output "Check evidence: $evidenceDir"
```

**Critical:** This requires 48h wall-clock time. OpenCode cannot wait. The ops team must:
1. Monitor the host for sleep/hibernate (disable power saving)
2. Check every 8h that the process is still running
3. On completion (or termination), capture the loop-summary JSON
4. If terminated early, note wall-clock elapsed and termination reason

**Expected output after completion:**
```
evidence/wave11-soak-48h-rerun/
  loop-summary-YYYYMMDDTHHMMSSZ.json    # Final summary with total iter, pass/fail, soak_complete_claim
  loop-*-i00001..i00XXX.json            # Per-iteration gate results
  soak-48h-stdout.log                   # Full stdout
  soak-48h-stderr.log                   # Full stderr
  metrics-snapshot-*.json               # Optional: periodic /health/detailed snapshots
```

---

### Task B2: WAL/PITR Local Drill (closes B10 partially)

```powershell
# From salesos/ directory
# 1. Enable archive_mode on disposable container (already done in wave10-dr)
# 2. Generate test data
# 3. Force WAL switch
# 4. Capture WAL files listing
# 5. Test PITR restore to a timestamp

# Use existing evidence from wave10-dr as baseline
# Add new evidence for PITR restore test
```

**Expected output:**
```
evidence/wave10-pitr/
  pitr-restore-timestamp.json    # {target_timestamp, restore_success, row_count_before, row_count_after}
  wal-archive-listing.txt        # WAL files used for restore
  pitr-drill-summary.json        # Overall drill results
```

**Offsite/S3:** Cannot be automated. Requires:
- MinIO deployment or S3 bucket with credentials
- `S3_BUCKET` environment variable set
- `backup.ps1` run with S3 upload enabled

---

## Phase 3: Manual Prerequisites (OpenCode CANNOT execute)

### Task M1: Cloud Staging Unblock (B2)

**What's needed:**
1. GitHub Environment `staging` created with secrets:
   - `STAGING_HOST`
   - `STAGING_USER`
   - `STAGING_SSH_KEY`
2. `deploy-staging.yml` workflow published to `develop` branch
3. VPS provisioned with Docker + Compose
4. Run `deploy-staging.yml` → verify health → run `pre-deploy-gates.ps1` → tabletop complete

**Runbook:** `docs/audit/ga-engineering-audit/runbooks/staging-fill-in.md`

---

### Task M2: Signatures (B4)

**Who:** CTO and Tech Lead  
**What:** Hand-sign `SIGN_HERE.md` with:
- Date filled
- Decision: GO / NO-GO / CONDITIONAL
- Evidence-reviewed box checked
- Signature line signed
- Conditions documented if CONDITIONAL

---

### Task M3: RPO Acceptance (B11)

**Who:** CTO  
**What:** Document accepted RPO:
- Option A: 24h (daily backup) — simpler, higher data loss risk
- Option B: WAL-based (~0 data loss) — requires `archive_mode=on` on primary + PITR capability
- Signed decision

---

### Task M4: AI Honesty PRC (B12)

**Who:** CTO + Product  
**What:** Review and sign off on AI marketing scope:
- `feature_ai_copilot=False` remains default
- FE Decision Engine remains STUB
- No "AI-native" marketing claims
- Launch notes reviewed and approved

---

### Task M5: Pentest (B5)

**Who:** Security team or external pentest provider  
**What:** 
- Staging environment pentest (SSRF, IDOR, tenant isolation, CSRF, RBAC, API auth)
- Report with findings
- Remediation for critical/high findings
- Signed residual acceptance for accepted risks

---

### Task M6: Launch Hygiene (B13)

**Who:** Tech Lead + Ops  
**What:**
- Declare feature freeze (no new features without exception approval)
- Publish on-call roster for first 14 days
- Schedule production backup cron (daily 03:00)
- Confirm staging RC image digests

---

## Execution order

```
Phase 1 (autonomous — NOW):
  A1-A8 in parallel → evidence generation

Phase 2 (start — NOW):
  B1 (48h soak) → starts now, runs 48h
  B2 (WAL/PITR drill) → execute locally

Phase 3 (manual — requires humans):
  M1-M6 → parallel, humans must act

Blocking chain for Production GO:
  Phase 1 complete + Phase 2 complete + M1 + M2 + M3 + M4 + M5 + M6
  → then: B3 (prod migrate) → Production GO
```

---

## Evidence package structure after Phase 1+2

```
docs/audit/ga-engineering-audit/evidence/
├── wave0-fe/              # NEW: lint.log, tsc.log, build.log
├── wave1-alembic/         # NEW: alembic-current.log, alembic-heads.log, alembic-history.log
├── wave2-load/            # EXISTING
├── wave3-pytest/          # NEW: junit.xml, pytest-report.json, pytest-stdout.log
├── wave5-auth-probes/     # NEW: smoke-auth-stdout.log, auth-probe-summary.json
├── wave8-obs/             # NEW: prometheus-targets.json, grafana-health.json, alerts.json, summary.json
├── wave9-secrets/         # NEW: scan-deps.log, arch-compliance.log, sbom.json
├── wave10-dr/             # EXISTING
├── wave10-pg-dump/        # NEW: pg-dump JSON, pg-restore-verify JSON
├── wave10-pitr/           # NEW: pitr-restore JSON, wal-archive listing
├── wave11-soak/           # EXISTING
├── wave11-soak-48h/       # EXISTING (incomplete)
├── wave11-soak-48h-rerun/ # NEW: complete 48h soak with loop-summary
├── wave12-gates/          # EXISTING
├── wave12-migrate-prep/   # EXISTING
├── wave12-staging/        # EXISTING
├── wave12-staging-virtual/# EXISTING
├── wave12-tabletop/       # EXISTING
├── wave13-api-residual-fix/# EXISTING
├── wave13-auth-demo/      # EXISTING
├── wave13-full-ui-crawl/  # EXISTING + NEW screenshots
```
