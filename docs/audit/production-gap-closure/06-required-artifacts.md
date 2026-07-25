# Required Artifacts — Complete Evidence Map

**For every blocker, the exact artifact that closes it.**

---

## B1: 48-72h Soak Complete

**Required artifact(s):**
```
evidence/wave11-soak-48h-rerun/
  loop-summary-YYYYMMDDTHHMMSSZ.json
    Required fields:
      {
        "timestamp": "<end ISO8601>",
        "duration_hours_requested": 48,
        "duration_hours_actual": <actual wall clock>,
        "total_iterations": <N>,
        "gate_pass_count": <N>,
        "gate_fail_count": <N>,
        "failures_by_type": {...},
        "soak_complete_claim": true | false,
        "production_go_claim": false,
        "incidents": [...],
        "human_review_required": true
      }
  loop-YYYYMMDD-HHMMSSZ-i00XXX.json  (all iteration JSONs)
  soak-48h-stdout.log
  soak-48h-stderr.log
  metrics-snapshot-*.json  (optional: periodic /health/detailed)
```

**Closing criteria:**  
`soak_complete_claim: true` and wall-clock >= 48h (or human-accepted shorter). Tech Lead reviews incident list and accepts or requires re-run.

---

## B2: Cloud Staging Deploy + Rollback

**Required artifact(s):**
```
evidence/wave12-staging-cloud/
  deploy-YYYYMMDDTHHMMSSZ.json
    {
      "environment": "staging-cloud-VPS",
      "deploy_status": "success",
      "image_digest": "sha256:...",
      "health_verified": true,
      "pre_deploy_gates": "PASS",
      "smoke_auth": "13/13 PASS",
      "frontend_verified": true
    }
  rollback-YYYYMMDDTHHMMSSZ.json
    {
      "rollback_status": "success",
      "target_digest": "sha256:... (previous)",
      "health_verified": true,
      "frontend_verified": true,
      "downtime_seconds": <N>
    }
  staging-health-check.log
  staging-smoke-auth.log
```

**Closing criteria:**  
Deploy succeeds, health verified, smoke 13/13 PASS, rollback succeeds, health re-verified. Both JSONs in evidence.

---

## B3: Production Alembic Migrate

**Required artifact(s):**
```
evidence/wave3-prod-migrate/
  prod-migrate-YYYYMMDDTHHMMSSZ.json
    {
      "environment": "production",
      "target_head": "0040",
      "alembic_upgrade_exit": 0,
      "alembic_current": "0040 (head)",
      "health_before": "ok",
      "health_after": "ok",
      "smoke_after": "PASS",
      "execution_approved_by": "<CTO/TL>",
      "backup_taken_before": true,
      "timestamp": "<ISO8601>"
    }
  prod-migrate-stdout.log
  prod-pre-migrate-health.json
  prod-post-migrate-health.json
  prod-post-migrate-smoke.json
```

**Closing criteria:**  
All preconditions met (B1, B2, B4, B5, B6). Upgrade exit 0. Health green before and after. Smoke PASS. Approved and documented.

---

## B4: CTO/TL Signatures

**Required artifact(s):**
```
docs/audit/ga-engineering-audit/SIGN_HERE.md  (updated)
  Both blocks filled:
    Status: SIGNED
    Name: <actual name>
    Date: YYYY-MM-DD
    Decision: [x] GO  or  [x] CONDITIONAL  or  [x] NO-GO
    Evidence reviewed: [x] Yes
    Conditions/notes: <filled if CONDITIONAL>
    Signature/ack: <actual signature or acknowledgment>
```

**Closing criteria:**  
Both CTO and TL blocks filled completely. No blanks. Decision explicitly marked.

---

## B5: Security Residual Acceptance

**Required artifact(s):**
```
evidence/wave2-pentest/
  # Option A: Full pentest
  pentest-report.pdf  (or pentest-findings.json)
  pentest-remediation.json  (fixed + accepted)
  pentest-sign-off.json  (signed acceptance)

  # Option B: Pilot residual acceptance (expedited)
  pilot-security-acceptance.json
    {
      "scope": "pilot only",
      "accepted_residuals": [
        "SSRF: DNS TOCTOU race window accepted for pilot (private IP block mitigates)",
        "SSRF: first-IP-only pin accepted (multi-IP redirect rare in pilot scope)",
        "KG SQL fallback: env-dependent, disabled in prod config",
        "No external pentest: accepted for pilot phase; full pentest before GA"
      ],
      "cto_ack": "<signature>",
      "security_ack": "<signature>",
      "conditions": "Full pentest required before Production GA"
    }
```

**Closing criteria:**  
Either pentest report with remediation sign-off, OR signed pilot residual acceptance listing all accepted risks.

---

## B6: pg_dump/restore Machine Evidence

**Required artifact(s):**
```
evidence/wave10-pg-dump/
  pg-dump-evidence.json
    {
      "timestamp": "<ISO8601>",
      "method": "pg_dump --format=custom --compress=9",
      "dump_exit": 0,
      "dump_size_bytes": <N>,
      "dump_size_human": "<X MiB>",
      "toc_entries": <N>,
      "tables_count": <N>,
      "checksum": "<sha256>"
    }
  pg-restore-verify.json
    {
      "restore_target": "disposable DB",
      "restore_exit": 0,
      "tables_restored": <N>,
      "row_counts": {
        "companies": <N>,
        "users": <N>,
        ...
      },
      "row_counts_match_source": true,
      "restore_wall_time_seconds": <N>
    }
  pg-dump-stdout.log
```

**Closing criteria:**  
Dump exits 0. Restore exits 0 with matching row counts. Both captured in machine-readable JSON.

---

## B7: Unit Pytest Suite Logged

**Required artifact(s):**
```
evidence/wave3-pytest/
  junit.xml
    <testsuite ... tests="<N>" failures="0" errors="0" skipped="2">
      <testcase ... />
      ...
    </testsuite>
  pytest-report.json
    {
      "summary": {
        "passed": <N>,
        "failed": 0,
        "skipped": 2,
        "total": <N>
      }
    }
  pytest-stdout.log  (full pytest -v output)
```

**Closing criteria:**  
JUnit XML with ~1542 tests, 0 failures, 2 skipped. Exit code 0. Machine-readable.

---

## B8: FE Lint/Typecheck/Build Logs

**Required artifact(s):**
```
evidence/wave0-fe/
  lint.log     — npm run lint output, exit 0, 0 ESLint errors
  tsc.log      — npx tsc --noEmit output, exit 0
  build.log    — npm run build output, exit 0, pages enumerated
  # OR combined:
  fe-toolchain.log  — all three commands with exit codes
```

**Closing criteria:**  
All three commands exit 0. Lint has 0 errors (warnings acceptable). TypeScript compiles clean. Build produces static output.

---

## B9: Observability Runtime Exercised

**Required artifact(s):**
```
evidence/wave8-obs/
  prometheus-targets.json     — All scrape targets UP
  prometheus-alerts.json      — No critical alerts firing (or documented)
  grafana-health.json         — HTTP 200, status healthy
  loki-ready.txt             — Ready/live
  obs-exercise-summary.json
    {
      "prometheus_up": true,
      "targets_up": ["salesos-backend", "postgres-exporter", "redis-exporter", "prometheus"],
      "grafana_healthy": true,
      "loki_available": true | false,
      "alerts_firing_critical": 0,
      "exercise_timestamp": "<ISO8601>"
    }
```

**Closing criteria:**  
Prometheus scraping salesos-backend (UP). Grafana healthy. No unexplained critical alerts.

---

## B10: WAL/PITR Proven (local)

**Required artifact(s):**
```
evidence/wave10-pitr/
  pitr-restore-evidence.json
    {
      "method": "PITR restore to timestamp",
      "disposable_container": true,
      "archive_mode": "on (disposable)",
      "wal_archived_count": <N>,
      "target_timestamp": "<ISO8601>",
      "restore_exit": 0,
      "pre_restore_row_count": <N>,
      "post_restore_row_count": <N>,
      "row_count_match": true,
      "pitr_functional": true
    }
  wal-archive-listing.txt
  pitr-drill-stdout.log
```

**Offsite/S3 (separate, requires infrastructure):**
```
evidence/wave10-offsite/
  s3-backup-verify.json
    {
      "s3_bucket": "<bucket>",
      "latest_backup_key": "<key>",
      "backup_size": <N>,
      "upload_verified": true,
      "download_test_passed": true
    }
```

**Closing criteria for local:** PITR restore succeeds on disposable; row counts match.

---

## B11: RPO Acceptance

**Required artifact(s):**
```
docs/audit/ga-engineering-audit/RPO_ACCEPTANCE.md
  Documented decision:
    Accepted RPO: 24h | WAL-based (~0 data loss)
    Signed by: CTO
    Date: YYYY-MM-DD
    Rationale: <text>
```

**Closing criteria:**  
Signed document stating accepted RPO target.

---

## B12: AI Honesty PRC

**Required artifact(s):**
```
docs/audit/ga-engineering-audit/AI_HONESTY.md  (updated)
  PRC review section added:
    Reviewed by: <CTO/Product name>
    Date: YYYY-MM-DD
    Decision: APPROVED | REJECTED (with reasons)
    Conditions: <any restrictions on AI marketing>
```

**Closing criteria:**  
Acknowledged review of AI marketing scope with explicit approval.

---

## B13: Launch Hygiene

**Required artifact(s):**
```
docs/audit/ga-engineering-audit/LAUNCH_HYGIENE.md
  Checklist:
    [x] Feature freeze declared (date: ...)
    [x] On-call roster published (link: ...)
    [x] Production backup scheduled (cron: daily 03:00)
    [x] Staging RC digests confirmed (sha256:...)
    [x] SSL certificates provisioned
    [x] Communication plan executed
```

**Closing criteria:**  
All T-7 items checked off with evidence pointers.

---

## B14: Screenshots (crawl)

**Required artifact(s):**
```
evidence/wave13-full-ui-crawl/
  screenshots/
    login.png       (visible page, non-null)
    dashboard.png
    companies.png
    ... (all 49 visited pages)
  full-ui-crawl-report.json  (with non-null "screenshot" fields)
```

**Closing criteria:**  
At minimum 40+ of 49 pages have visible PNG screenshots. Report JSON has `screenshot` fields pointing to files.

---

## B15: Security Scanners Run

**Required artifact(s):**
```
evidence/wave9-secrets/
  scan-deps.log       — pip-audit (0 critical) + npm audit (manageable)
  arch-compliance.log — Per-domain scores (should meet thresholds from check-coverage.ps1)
  sbom.json           — Valid CycloneDX 1.5 JSON
  gitleaks-report.json — 0 live secrets detected
```

**Closing criteria:**  
No critical vulnerabilities in deps. Architecture compliance within thresholds. SBOM generated. No live secrets leaked to git.

---

## B16: Alembic Transcript

**Required artifact(s):**
```
evidence/wave1-alembic/
  alembic-status.log      — alembic current + heads + recent history
  check-alembic-head.log  — check_alembic_head.py output + exit code
```

**Closing criteria:**  
alembic current = ['0040'], alembic heads = ['0040'], check_alembic_head.py exit 0.

---

## B17: Auth Contract Probes

**Required artifact(s):**
```
evidence/wave5-auth-probes/
  smoke-auth-stdout.log
    Must contain:
      [PASS] register -> 201
      [PASS] login -> 200
      [PASS] me -> 200
      [PASS] unauthenticated -> 401
      [PASS] GraphQL CSRF -> 403
      [PASS] /health -> 200
      [PASS] /metrics -> 200
      [PASS] frontend / -> 200
      ... (13 total)
  auth-probe-summary.json
    {
      "pass": 13,
      "fail": 0,
      "overall": "PASS",
      "timestamp": "<ISO8601>"
    }
```

**Closing criteria:**  
13/13 PASS. JSON summary with machine-readable pass/fail counts.

---

## Artifact dependency diagram

```
Evidence Artifacts                    Blockers Closed
─────────────────────────────────────────────────────
wave0-fe/lint+tsc+build.log     →    B8 ✓
wave1-alembic/alembic-status.log →   B16 ✓
wave3-pytest/junit.xml          →    B7 ✓
wave5-auth-probes/smoke-auth    →    B17 ✓
wave8-obs/prometheus-targets    →    B9 ✓
wave9-secrets/scan-deps.log     →    B15 ✓
wave10-pg-dump/pg-dump.json     →    B6 ✓
wave10-pitr/pitr-restore.json   →    B10 ✓ (local)
wave13-crawl/screenshots/*.png  →    B14 ✓
wave11-soak-48h/loop-summary    →    B1 ✓ (after 48h)
─────────────────────────────────────────────────────
  Phase 1+2 evidence complete

wave12-staging-cloud/deploy.json →   B2 ✓ (manual)
SIGN_HERE.md (completed)          →   B4 ✓ (manual)
RPO_ACCEPTANCE.md                 →   B11 ✓ (manual)
AI_HONESTY.md (PRC done)          →   B12 ✓ (manual)
LAUNCH_HYGIENE.md                 →   B13 ✓ (manual)
pentest-report OR residual-accept → B5 ✓ (manual/external)
─────────────────────────────────────────────────────
  All preconditions met

wave3-prod-migrate/prod-migrate   →   B3 ✓ (after all above)
─────────────────────────────────────────────────────
  PRODUCTION GO
```
