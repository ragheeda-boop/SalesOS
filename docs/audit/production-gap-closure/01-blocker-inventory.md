# Blocker Inventory — Production Readiness

**Chief Release Engineer assessment, 2026-07-23**  
Compiled from: evidence-review, evidence-review-peer, GA_STATUS, SIGN_HERE, and repository source.

---

## Consolidated blocker list (deduplicated across all audits)

Every blocker below is extracted from audit and peer review findings, cross-referenced against repository source, and independently verified.

---

### B1 — 48–72h local soak incomplete

| Field | Detail |
|-------|--------|
| Source | GA_STATUS #1, SIGN_HERE #1, evidence-review Wave 11, peer-review confirmed |
| Description | 48h soak was STARTED (PID 21856) but only collected 72 loop iterations (~6h wall clock) before terminating with API failures. No `loop-summary` JSON was generated. |
| Status | **INCOMPLETE** — 72 of ~576 expected iterations; no summary artifact |
| Evidence exists | `wave11-soak-48h/` has 72 loop-*.json + stdout/stderr logs. Ends at T20:54 with GATE FAIL (api.ping timeout, health degraded) |
| Documentation | `PROGRESS-WAVE11-SOAK-48H.md` honestly states `soak_complete_claim: false` |
| Honesty | Excellent — docs do NOT claim soak complete |

---

### B2 — Cloud staging deploy + rollback blocked

| Field | Detail |
|-------|--------|
| Source | GA_STATUS #2, SIGN_HERE #2, evidence-review Wave 12 |
| Description | GitHub has 0 Environments named `staging`, 0 secrets. `deploy-staging.yml` workflow exists but no host credentials. `develop` branch absent. |
| Status | **BLOCKED** — confirmed by `probe-2026-07-22T163200Z.json` |
| Blocker type | Infrastructure (GitHub Environments + VPS credentials) |
| Dependencies | Human must provide: `STAGING_HOST`, `STAGING_USER`, `STAGING_SSH_KEY` |
| Prep | Staging-unblock checklist (`runbooks/staging-fill-in.md`) is DONE |
| Virtual | Local virtual staging on :8001/:3002 is DONE (not a cloud closure) |

---

### B3 — Production Alembic migrate not executed

| Field | Detail |
|-------|--------|
| Source | GA_STATUS #3, SIGN_HERE #3, evidence-review Wave 12 |
| Description | `production_migrate_executed: false`, `execution_blocked: true` |
| Status | **BLOCKED** — 8 preconditions not met (backup, soak, staging, signatures) |
| Prep | Migrate runbook DONE; local head verify 0040 DONE; pre-deploy-gates PASS local |
| Evidence | `wave12-migrate-prep/SUMMARY.json` — all checks green locally |

---

### B4 — CTO/TL GO signatures unsigned

| Field | Detail |
|-------|--------|
| Source | GA_STATUS #5, SIGN_HERE, evidence-review Wave 14 |
| Description | `SIGN_HERE.md` header = UNSIGNED. CTO/TL blocks show `Status: SIGNED` (contradictory) with blank dates, blank signatures, no evidence-review confirmation checked |
| Status | **UNSIGNED** — invalid for GO |
| Type | Governance / Human |
| Cannot be automated | Requires human inking |

---

### B5 — No staging pentest / security residuals

| Field | Detail |
|-------|--------|
| Source | GA_STATUS #4, SIGN_HERE #4, evidence-review Wave 2 |
| Description | SSRF pin hardened with residuals (DNS TOCTOU, first-IP only, httpx pool API coupling). KG SQL fallback policy env-dependent. No pentest report or signed residual acceptance exists. |
| Status | **OPEN** |
| Type | External security validation |
| Code | P0 fixes exist (IDOR, SSRF, KG tenant, forecast demo) — light validated |

---

### B6 — pg_dump/restore machine evidence missing

| Field | Detail |
|-------|--------|
| Source | evidence-review Wave 10, peer-review confirmed |
| Description | `PROGRESS-WAVE10-BACKUP.md` claims ~21.5 MiB dump, 431 TOC, row count match. But NO JSON machine evidence exists in `evidence/wave10-dr/`. Only markdown narrative. |
| Status | **MARKDOWN ONLY** — not machine-evidenced |
| Available tooling | `backup.ps1`, `verify-backup.ps1`, `restore-test.ps1`, `backup-db.sh`, `restore-db.sh` ALL EXIST and can produce JSON |
| Can be automated | **YES** — run existing backup/restore scripts with evidence capture |

---

### B7 — Unit pytest ~1542 passed not logged

| Field | Detail |
|-------|--------|
| Source | evidence-review Wave 3, peer-review confirmed |
| Description | ~1542 passed, 2 skipped claimed in `PROGRESS-CONTINUATION.md`. No JUnit XML, no pytest JSON, no coverage report, no exit-code log in evidence. |
| Status | **NO ARTIFACT** |
| Available tooling | `check-coverage.ps1` exists with per-domain thresholds. `docker-compose.test.yml` includes pytest runner. |
| Can be automated | **YES** — run pytest inside Docker and capture JUnit XML + JSON output |

---

### B8 — FE lint/tsc/build exit-0 standalone logs missing

| Field | Detail |
|-------|--------|
| Source | evidence-review Wave 0, peer-review corrected |
| Description | Wave 0 claims `npm run lint`, `npx tsc --noEmit`, `npm run build` all exit 0. No standalone command logs exist. Docker `fe-build.log` EXISTS and proves Docker image build, but NOT host-level `npm run lint`/`tsc`/`build`. |
| Status | **PARTIAL** — Docker build proven; standalone host commands un-evidenced |
| Correction | Peer review upgraded Wave 0 confidence 15%→35%, Wave 4 25%→45% |
| CI workflow | `ci.yml` includes ESLint + tsc + build stages — evidence would come from CI |
| Can be automated | **YES** — run FE toolchain or capture CI output |

---

### B9 — Observability runtime not exercised

| Field | Detail |
|-------|--------|
| Source | evidence-review Wave 8, peer-review confirmed |
| Description | Prometheus/Grafana/Loki/OTel configured in compose files BUT no scrape matrix, Grafana dashboard proof, alert firing test, or 72h SLI log exists. |
| Status | **CONFIG ONLY** — no runtime proof |
| Available | `prometheus.yml`, `alerts.yml`, `grafana` datasources, compose profiles |
| Can be automated | **YES** — bring up observability profile + capture dashboard JSON + scrape matrix |

---

### B10 — Primary WAL/PITR + offsite backup not proven

| Field | Detail |
|-------|--------|
| Source | GA_STATUS #7, SIGN_HERE #7, evidence-review Wave 10 |
| Description | Primary Postgres `archive_mode=off` (stock compose). Disposable WAL archive proven (3 WAL files). No PITR restore-to-timestamp drill. No S3/MinIO offsite backup. No off-box Neo4j dump copy. |
| Status | **OPEN** |
| Evidence | `wave10-dr/postgres-wal-settings-*.txt` — archive_mode=off. `postgres-disposable-archive-*.json` — disposable WAL proven |
| Can be automated | **PARTIAL** — disposable WAL/PITR can be exercised locally. Offsite S3 requires external S3/MinIO. |

---

### B11 — RPO acceptance unsigned

| Field | Detail |
|-------|--------|
| Source | GA_STATUS #9, SIGN_HERE #8 |
| Description | RPO target (24h vs WAL) is UNSIGNED. CTO must decide acceptable RPO for production. |
| Status | **UNSIGNED** |
| Type | Governance / Human decision |
| Cannot be automated | Requires CTO approval |

---

### B12 — AI honesty — human PRC open

| Field | Detail |
|-------|--------|
| Source | GA_STATUS #6, SIGN_HERE #6 |
| Description | Code/docs gate DONE (API 403, FE hide, badges). BUT human PRC/launch-notes sign-off for AI marketing scope still OPEN. |
| Status | **CODE GATE CLOSED / HUMAN REVIEW OPEN** |
| Type | Governance |
| Cannot be automated | Requires human sign-off on AI marketing scope |

---

### B13 — Launch hygiene (freeze, on-call, prod backup)

| Field | Detail |
|-------|--------|
| Source | SIGN_HERE #9, go-live-checklist T-7/T-1 |
| Description | Feature freeze not declared. On-call roster not published. Prod backup not scheduled. Staging RC digests not confirmed. |
| Status | **NOT PREPARED** |
| Type | Operations / Governance |
| Cannot be automated | Requires operational planning decisions |

---

### B14 — UI crawl screenshots null

| Field | Detail |
|-------|--------|
| Source | evidence-review Wave 13, peer-review confirmed |
| Description | Full UI crawl 49/49 pages passed shells, but ALL 49 pages have `screenshot: null`. 0 PNG files in `screenshots/` directory. 14 pages with HTTP errors, 34 with console errors. |
| Status | **NO SCREENSHOTS** |
| Available | `full-ui-crawl.ps1` script exists; Playwright config has screenshot capability |
| Can be automated | **YES** — re-run crawl with screenshot capture enabled |

---

### B15 — Security scanners not run

| Field | Detail |
|-------|--------|
| Source | evidence-review Wave 9 |
| Description | `.gitleaks.toml` and `.trivyignore` exist but no scanner run output in evidence. Security-scan workflow exists but no saved run. |
| Status | **NOT RUN** |
| Available | `scan-deps.ps1` (pip-audit + npm audit), `security-audit.ps1` (10-category audit), `security-scan.yml` (GitHub Action with Gitleaks + Trivy) |
| Can be automated | **YES** — run scanners locally or capture CI output |

---

### B16 — Alembic upgrade transcript missing for local

| Field | Detail |
|-------|--------|
| Source | evidence-review Wave 1 |
| Description | No original `alembic upgrade head` stdout transcript for the local upgrade from 0033 to 0040. Later SQL verify JSONs prove current=0040 but no step-by-step upgrade log. |
| Status | **PARTIAL EVIDENCE** — state proven, execution not captured |
| Can be automated | **YES** — re-run upgrade with log capture or use existing SQL verify |

---

### B17 — Wave 5 auth contract probes not archived

| Field | Detail |
|-------|--------|
| Source | evidence-review Wave 5 |
| Description | Code changes for CSRF, 401, /metrics exist. BUT no curl transcript or probe JSON of the actual auth contract tests. |
| Status | **NO ARCHIVED PROBE** |
| Available | `smoke-auth.ps1` and `smoke-auth.sh` produce 13-checks probe output |
| Can be automated | **YES** — run smoke-auth and save evidence JSON |

---

## Summary: 17 blockers, 4 categories of resolvability

| Can OpenCode resolve? | Count | Blocker IDs |
|-----------------------|-------|-------------|
| **YES — autonomous** | 8 | B6, B7, B8, B9, B14, B15, B16, B17 |
| **PARTIAL — start/frame** | 2 | B1 (48h soak — can start, can't wait), B10 (local WAL yes, offsite S3 no) |
| **NO — external infra** | 1 | B2 (GitHub Environments + VPS) |
| **NO — governance/human** | 5 | B4, B11, B12, B13 |
| **NO — external security** | 1 | B5 (pentest) |
| **NO — prod access** | 1 | B3 (production DB) |

Note: B3 (prod migrate) also blocked by B1, B2, B4, B5, B6 as preconditions — even with prod access it cannot be done.

---

## Verified against repository (2026-07-23)

All blocker statuses verified by:
- Reading evidence folders (all 12 wave directories)
- Reading all progress docs (31 files)
- Reading all scripts (29 PS1, 6 PY, 3 SH, 6 infra SH)
- Reading all compose files (7 files)
- Reading all CI workflows (5 files)
- Reading all runbooks (8 files)
- Cross-referencing GA_STATUS, SIGN_HERE, evidence-review, peer-review

**No blocker was found to be already resolved but undocumented.**
