# Autonomous Tasks — OpenCode Can Execute

**All tasks below require:**
- Docker Desktop running
- `salesos/` Docker stack up (`docker compose up -d`)
- Working Node.js toolchain (preferably inside Docker, or on host)
- `salesos/` as working directory

---

## Task 1: Pytest Suite with JUnit Output (B7)

**Command:**
```powershell
# From salesos/
New-Item -ItemType Directory -Force -Path "../docs/audit/ga-engineering-audit/evidence/wave3-pytest/"

docker compose run --rm backend bash -c "
  pip install pytest-json-report 2>/dev/null;
  python -m pytest tests/unit/ \
    --junitxml=/tmp/junit.xml \
    --json-report --json-report-file=/tmp/pytest-report.json \
    -v \
    2>&1 | tee /tmp/pytest-stdout.log
"

docker compose cp backend:/tmp/junit.xml "../docs/audit/ga-engineering-audit/evidence/wave3-pytest/junit.xml"
docker compose cp backend:/tmp/pytest-report.json "../docs/audit/ga-engineering-audit/evidence/wave3-pytest/pytest-report.json"

# Extract exit code
$exitCode = $LASTEXITCODE
Write-Output "pytest exit code: $exitCode"
```

**Evidence output:**
```
docs/audit/ga-engineering-audit/evidence/wave3-pytest/
  junit.xml              — JUnit machine-readable results
  pytest-report.json     — JSON pass/fail/skip counts
  pytest-stdout.log      — Full pytest stdout
```

**Expected results:**
- ~1542 passed (or near it)
- 2 skipped (mcp, obsolete_admin)
- exit code 0 (or 1 if TESTING flag causes failures — document)

**Validation:** Open `junit.xml`, count `<testcase>` elements, verify `failures="0"` or document failures.

---

## Task 2: FE Lint/Typecheck/Build Logs (B8)

**Command (Docker-based — preferred):**
```powershell
# From salesos/frontend/
New-Item -ItemType Directory -Force -Path "../../docs/audit/ga-engineering-audit/evidence/wave0-fe/"

docker compose run --rm frontend sh -c "
  cd /app &&
  echo '=== npm run lint ===' &&
  npm run lint 2>&1; echo EXIT:$? &&
  echo '=== npx tsc --noEmit ===' &&
  npx tsc --noEmit 2>&1; echo EXIT:$? &&
  echo '=== npm run build ===' &&
  npm run build 2>&1; echo EXIT:$?
" 2>&1 | Tee-Object -FilePath "../../docs/audit/ga-engineering-audit/evidence/wave0-fe/fe-toolchain.log"
```

**Command (host — if Node.js installed):**
```powershell
Set-Location salesos/frontend
npm run lint 2>&1 | Tee-Object -FilePath "../../docs/audit/ga-engineering-audit/evidence/wave0-fe/lint.log"
npx tsc --noEmit 2>&1 | Tee-Object -FilePath "../../docs/audit/ga-engineering-audit/evidence/wave0-fe/tsc.log"
npm run build 2>&1 | Tee-Object -FilePath "../../docs/audit/ga-engineering-audit/evidence/wave0-fe/build.log"
```

**Evidence output:**
```
docs/audit/ga-engineering-audit/evidence/wave0-fe/
  fe-toolchain.log  (or lint.log + tsc.log + build.log)
```

**Expected results:**
- lint: exit 0, 0 ESLint errors (Tailwind warnings acceptable)
- tsc: exit 0, clean noEmit
- build: exit 0, builds or lists 51 static pages

---

## Task 3: pg_dump/restore Machine Evidence (B6)

**Command:**
```powershell
# From salesos/
New-Item -ItemType Directory -Force -Path "../docs/audit/ga-engineering-audit/evidence/wave10-pg-dump/"

# Run backup via infra script
docker compose exec -T postgres bash -c "
  apt-get update -qq && apt-get install -y -qq python3 2>/dev/null;
  pg_dump --version
" | Out-File "../docs/audit/ga-engineering-audit/evidence/wave10-pg-dump/pg-version.txt" -Encoding utf8

# pg_dump custom format
docker compose exec -T postgres bash -c "
  pg_dump -U \$POSTGRES_USER -d \$POSTGRES_DB \\
    --format=custom \\
    --compress=9 \\
    --file=/tmp/salesos-pg-dump.dump 2>&1;
  echo EXIT:\$?;
  ls -lh /tmp/salesos-pg-dump.dump;
  pg_restore --list /tmp/salesos-pg-dump.dump | wc -l
" | Tee-Object -FilePath "../docs/audit/ga-engineering-audit/evidence/wave10-pg-dump/pg-dump-stdout.log"

# Produces: dump exit code, size, TOC entry count
```

**Then produce structured JSON evidence:**
```powershell
# Create evidence JSON (manual assembly from stdout)
@"
{
  "id": "PROD-B6-PG-DUMP-EVIDENCE",
  "timestamp_utc": "$(Get-Date -Format 'yyyy-MM-ddTHH:mm:ssZ')",
  "environment": "local-docker-compose-NON-PROD",
  "method": "pg_dump --format=custom --compress=9",
  "dump_exit": 0,
  "dump_size": "see-stdout",
  "toc_entries": "see-stdout",
  "restore_test": "SEE verify-backup.ps1 OUTPUT",
  "production_go": false
}
"@ | Out-File "../docs/audit/ga-engineering-audit/evidence/wave10-pg-dump/pg-dump-evidence.json" -Encoding utf8
```

**Evidence output:**
```
docs/audit/ga-engineering-audit/evidence/wave10-pg-dump/
  pg-version.txt           — pg_dump version
  pg-dump-stdout.log       — Full pg_dump output with exit code, size, TOC
  pg-dump-evidence.json    — Structured JSON
```

---

## Task 4: Auth Contract Probes (B17)

**Command:**
```powershell
# From salesos/
New-Item -ItemType Directory -Force -Path "../docs/audit/ga-engineering-audit/evidence/wave5-auth-probes/"

# Requires SMOKE_EMAIL and SMOKE_PASSWORD in environment
# (retrieve from .env or docker compose config)
$env:SMOKE_EMAIL = 'admin@salesos.io'
$env:SMOKE_PASSWORD = '<FROM_ENV>'

powershell -NoProfile -ExecutionPolicy Bypass -File scripts/smoke-auth.ps1 2>&1 |
  Tee-Object -FilePath "../docs/audit/ga-engineering-audit/evidence/wave5-auth-probes/smoke-auth-stdout.log"
```

**Evidence output:**
```
docs/audit/ga-engineering-audit/evidence/wave5-auth-probes/
  smoke-auth-stdout.log    — 13-probe results (register, login, me, 401, 403, GraphQL CSRF, /health, /metrics, /, frontend, rate-limit)
```

**Expected results:**
- 13/13 PASS (or document failures)
- Unauthenticated → 401
- GraphQL CSRF → 403
- /metrics → 200
- register → 201, login → 200

---

## Task 5: Observability Runtime Exercise (B9)

**Command:**
```powershell
# From salesos/
New-Item -ItemType Directory -Force -Path "../docs/audit/ga-engineering-audit/evidence/wave8-obs/"

# Ensure observability profile is up
docker compose --profile observability up -d loki otel-collector promtail
Start-Sleep -Seconds 20

# Wait for Prometheus healthy (check port)
$maxAttempts = 10
for ($i=1; $i -le $maxAttempts; $i++) {
  try {
    $health = Invoke-WebRequest -Uri "http://localhost:9090/-/ready" -TimeoutSec 5 -UseBasicParsing
    if ($health.StatusCode -eq 200) { break }
  } catch { Start-Sleep -Seconds 5 }
}

# Capture scrape targets
Invoke-WebRequest -Uri "http://localhost:9090/api/v1/targets" -UseBasicParsing |
  Select-Object -ExpandProperty Content |
  Out-File "../docs/audit/ga-engineering-audit/evidence/wave8-obs/prometheus-targets.json" -Encoding utf8

# Capture alerts state
Invoke-WebRequest -Uri "http://localhost:9090/api/v1/alerts" -UseBasicParsing |
  Select-Object -ExpandProperty Content |
  Out-File "../docs/audit/ga-engineering-audit/evidence/wave8-obs/prometheus-alerts.json" -Encoding utf8

# Capture Grafana health
Invoke-WebRequest -Uri "http://localhost:3001/api/health" -UseBasicParsing |
  Select-Object -ExpandProperty Content |
  Out-File "../docs/audit/ga-engineering-audit/evidence/wave8-obs/grafana-health.json" -Encoding utf8

# Capture Loki health (if observability profile)
try {
  Invoke-WebRequest -Uri "http://localhost:3100/ready" -UseBasicParsing -TimeoutSec 5 |
    Select-Object -ExpandProperty Content |
    Out-File "../docs/audit/ga-engineering-audit/evidence/wave8-obs/loki-ready.txt" -Encoding utf8
} catch { "Loki not available" | Out-File "../docs/audit/ga-engineering-audit/evidence/wave8-obs/loki-ready.txt" -Encoding utf8 }
```

**Evidence output:**
```
docs/audit/ga-engineering-audit/evidence/wave8-obs/
  prometheus-targets.json   — All scrape targets + health
  prometheus-alerts.json    — Active/firing alerts
  grafana-health.json       — Grafana API health response
  loki-ready.txt            — Loki readiness
  obs-exercise-summary.json — Structured summary (see below)
```

**Validation:** Targets must show `salesos-backend` UP. Grafana must return 200. No critical alerts firing.

---

## Task 6: Security Scanner Execution (B15)

**Command:**
```powershell
# From salesos/
New-Item -ItemType Directory -Force -Path "../docs/audit/ga-engineering-audit/evidence/wave9-secrets/"

# Run dependency scanner
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/scan-deps.ps1 2>&1 |
  Tee-Object -FilePath "../docs/audit/ga-engineering-audit/evidence/wave9-secrets/scan-deps.log"

# Run architecture compliance check
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/arch-compliance.ps1 2>&1 |
  Tee-Object -FilePath "../docs/audit/ga-engineering-audit/evidence/wave9-secrets/arch-compliance.log"

# Generate SBOM
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/sbom.ps1
if (Test-Path "scripts/sbom.json" -or Test-Path "salesos/sbom.json") {
  Copy-Item -Path (Get-ChildItem -Recurse -Filter "sbom.json" | Select-Object -First 1).FullName `
    -Destination "../docs/audit/ga-engineering-audit/evidence/wave9-secrets/sbom.json"
}

# Check for git leaks (gitleaks — if installed)
if (Get-Command gitleaks -ErrorAction SilentlyContinue) {
  gitleaks detect --source . --report-path "../docs/audit/ga-engineering-audit/evidence/wave9-secrets/gitleaks-report.json" --no-git 2>&1 |
    Tee-Object -FilePath "../docs/audit/ga-engineering-audit/evidence/wave9-secrets/gitleaks-stdout.log"
}
```

**Evidence output:**
```
docs/audit/ga-engineering-audit/evidence/wave9-secrets/
  scan-deps.log           — pip-audit + npm audit results
  arch-compliance.log     — Per-domain architecture scores
  sbom.json               — CycloneDX 1.5 SBOM
  gitleaks-report.json    — (if gitleaks available) Secret scan results
```

---

## Task 7: Alembic Upgrade Transcript (B16)

**Command:**
```powershell
# From salesos/
New-Item -ItemType Directory -Force -Path "../docs/audit/ga-engineering-audit/evidence/wave1-alembic/"

docker compose exec -T backend bash -c "
  echo '=== ALEMBIC CURRENT ===';
  alembic current;
  echo '';
  echo '=== ALEMBIC HEADS ===';
  alembic heads;
  echo '';
  echo '=== ALEMBIC HISTORY (last 10) ===';
  alembic history | head -20
" | Tee-Object -FilePath "../docs/audit/ga-engineering-audit/evidence/wave1-alembic/alembic-status.log"

# Also run check_alembic_head.py
docker compose exec -T backend python scripts/check_alembic_head.py 2>&1 |
  Tee-Object -FilePath "../docs/audit/ga-engineering-audit/evidence/wave1-alembic/check-alembic-head.log"
Write-Output "check_alembic_head exit code: $LASTEXITCODE"
```

**Evidence output:**
```
docs/audit/ga-engineering-audit/evidence/wave1-alembic/
  alembic-status.log       — alembic current + heads + history
  check-alembic-head.log   — check_alembic_head.py output
```

**Expected:** `alembic current = ['0040']`, `alembic heads = ['0040']`, `check_alembic_head.py` exit 0

---

## Task 8: UI Crawl With Screenshots (B14)

**Prerequisite:** Check Playwright config for screenshot capability.

**First, verify Playwright config:**
```powershell
# Check salesos/frontend/playwright.full-crawl.config.ts for screenshot settings
Select-String -Path "salesos/frontend/playwright.full-crawl.config.ts" -Pattern "screenshot"
```

**Command:**
```powershell
# From salesos/
$env:SMOKE_EMAIL = 'admin@salesos.io'
$env:SMOKE_PASSWORD = '<FROM_ENV>'

# Ensure screenshots directory exists
New-Item -ItemType Directory -Force -Path "../docs/audit/ga-engineering-audit/evidence/wave13-full-ui-crawl/screenshots/"

powershell -NoProfile -ExecutionPolicy Bypass -File scripts/full-ui-crawl.ps1 2>&1 |
  Tee-Object -FilePath "../docs/audit/ga-engineering-audit/evidence/wave13-full-ui-crawl/crawl-stdout.log"
```

**If screenshots still null after run:** Modify `full-ui-crawl.spec.ts` to add:
```typescript
// In page.goto() context, add:
await page.screenshot({ path: `screenshots/${pageName}.png`, fullPage: true });
```

**Evidence output:**
```
docs/audit/ga-engineering-audit/evidence/wave13-full-ui-crawl/
  full-ui-crawl-report.json  — with non-null screenshot paths
  crawl-stdout.log           — Full crawl stdout
  screenshots/
    login.png
    register.png
    dashboard.png
    companies.png
    ... (49 expected)
```

---

## Validation after all autonomous tasks

After all 8 tasks, verify the evidence directory:

```powershell
Get-ChildItem -Recurse -Path "../docs/audit/ga-engineering-audit/evidence/wave*-*" -Directory |
  Sort-Object Name |
  ForEach-Object { Write-Output "$($_.Name): $((Get-ChildItem $_.FullName).Count) files" }
```

Expected evidence folders after autonomous execution:
```
wave0-fe              >= 1 file
wave1-alembic         >= 2 files
wave2-load            >= 19 files (existing)
wave3-pytest          >= 3 files
wave5-auth-probes     >= 1 file
wave8-obs             >= 4 files
wave9-secrets         >= 3 files
wave10-dr             >= 6 files (existing)
wave10-pg-dump        >= 2 files
wave10-pitr           >= 2 files (if B2 run)
wave11-soak           >= 55 files (existing)
wave11-soak-48h       >= 76 files (existing)
wave11-soak-48h-rerun >= TBD (after 48h)
wave12-gates          >= 4 files (existing)
wave12-migrate-prep   >= 5 files (existing)
wave12-staging        >= 2 files (existing)
wave12-staging-virtual >= 6 files (existing)
wave12-tabletop       >= 6 files (existing)
wave13-api-residual-fix >= 7 files (existing)
wave13-auth-demo      >= 4 files (existing)
wave13-full-ui-crawl  >= 51+ files (existing + screenshots)
```

---

## Estimated time

| Task | Est. Wall Clock | Notes |
|------|----------------|-------|
| T1: Pytest | 5-10 min | Docker run; depends on suite size |
| T2: FE toolchain | 15-25 min | npm install may be needed inside Docker |
| T3: pg_dump | 2-5 min | pg_dump size ~21 MiB |
| T4: Auth probes | 1-2 min | Curl-based, fast |
| T5: Observability | 3-5 min | Wait for services healthy |
| T6: Security scan | 5-10 min | Scanner execution time |
| T7: Alembic | 1 min | Three docker exec commands |
| T8: UI crawl | 5-10 min | 49 pages, 136 clicks via Playwright |
| **Total Phase 1** | **~1 hour** | All tasks can run in parallel |
