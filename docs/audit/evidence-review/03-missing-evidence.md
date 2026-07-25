# Missing Evidence Inventory

**Audit date:** 2026-07-22  
**Rule:** If a command or PASS is claimed and no artifact exists, evidence is **missing**. Missing ≠ assumed success.

---

## 1. Entire evidence folders absent

| Expected / implied folder | Status |
|---------------------------|--------|
| `evidence/wave0*` | **MISSING** |
| `evidence/wave1*` | **MISSING** |
| `evidence/wave3*` | **MISSING** |
| `evidence/wave4*` | **MISSING** |
| `evidence/wave5*` | **MISSING** |
| `evidence/wave6*` | **MISSING** |
| `evidence/wave7*` | **MISSING** |
| `evidence/wave8*` | **MISSING** |
| `evidence/wave9*` | **MISSING** |
| `evidence/wave12-gates/` | **MISSING** (cited from migrate-prep) |
| `evidence/wave14*` | **MISSING** |

**Present (machine artifacts):** `wave2-load`, `wave10-dr`, `wave11-soak`, `wave11-soak-48h`, `wave12-staging`, `wave12-staging-virtual`, `wave12-tabletop`, `wave12-migrate-prep`, `wave13-auth-demo`, `wave13-full-ui-crawl`, `wave13-api-residual-fix`.

---

## 2. Cited files that do not exist (broken pointers)

| Citation | Status |
|----------|--------|
| `docs/audit/ga-engineering-audit/fe-build.log` (Wave 4 FE image) | **MISSING** |
| `evidence/wave12-gates/gate-rerun-*.log` | **MISSING** |
| `gates-rerun-*.log` under migrate-prep | **MISSING** (only 3 JSON files in migrate-prep) |
| Playwright HTML report under `evidence/wave13-*` | **MISSING** |
| Readable `test-results/smoke-ui/smoke-auth-ui-report.json` as durable audit evidence | **WEAK / not found** at audit time |
| `pg_dump` / `pg_restore` JSON under `evidence/wave10-dr/` | **MISSING** |
| 48h `loop-summary-*.json` | **MISSING** (48h incomplete) |
| Crawl screenshots (`screenshot` field / PNG) | **MISSING** (all `null`) |

---

## 3. Commands claimed without saved exit-code transcripts

| Claimed command / outcome | Log/JUnit/JSON | Verdict |
|---------------------------|----------------|---------|
| `npm run lint` exit 0 | none | evidence missing |
| `npx tsc --noEmit` exit 0 | none | evidence missing |
| `npm run build` exit 0 | none | evidence missing |
| `docker compose build frontend` exit 0 | `fe-build.log` missing | evidence missing |
| `docker compose config` pass | none | evidence missing |
| `pytest` 96 / 1524 / 1542 passed | none | evidence missing |
| Wave 5 curl auth matrix | none | evidence missing |
| Live copilot 403 when flag False | none | evidence missing |
| Full gitleaks/trivy/pip-audit run | none (admitted not run) | evidence missing |
| Observability scrape / Grafana query | none | evidence missing |
| Cloud staging deploy/rollback | probe proves **BLOCKED**, not missing success | N/A |
| Production Alembic upgrade | explicitly not run | N/A |

---

## 4. Baseline vs remediation gap

`APPENDIX-A-BUILD-EVIDENCE.md` records:

- lint/tsc/build **FAIL**
- alembic current **0033** vs head **0038**
- pytest **NOT GREEN**
- several FE routes **404**

Progress waves claim remediation success. **There is no paired post-remediation command log pack** that replaces APPENDIX-A as green evidence. Later soak/crawl artifacts do not prove Wave 0 lint/build.

---

## 5. Media / browser artifacts

| Artifact type | Under audit `evidence/` |
|---------------|-------------------------|
| PNG / JPG screenshots | **0** for Wave 13 crawl |
| `trace.zip` | **0** |
| Playwright HTML report (copied into evidence) | **0** |
| Video / webm | **0** |
| Coverage `coverage.xml` / lcov for Wave 3 | **0** |

---

## 6. CI / GitHub Actions run artifacts

| Item | Status |
|------|--------|
| Workflow YAML in `salesos/.github/workflows/` | Present (config) |
| Saved Actions run logs for Wave remediation day | **Not archived** under `evidence/` |
| Staging Environment / secrets | Probe JSON shows Environments=0, secrets empty |
| `deploy-staging.yml` on remote `master` | Probe: HTTP 404 |

Config ≠ executed CI proof.

---

## 7. Minimum evidence pack required before any upgrade of verification class

To move from **PRODUCTION NOT VERIFIED** toward anything stronger, at minimum:

1. Saved stdout + exit codes: lint, tsc, build, pytest (Docker), alembic current/heads.  
2. Completed 48h (or 72h) soak `loop-summary` with `soak_complete_claim` policy decided by humans.  
3. Staging cloud deploy + rollback evidence (not virtual local only).  
4. Durable UI smoke + crawl reports **with** screenshots or traces.  
5. Machine evidence for `pg_dump`/`pg_restore` (sizes, TOC, row counts).  
6. Observability scrape proof or explicit waiver.  
7. Ink-complete CTO/TL signatures (or formal NO-GO).  
8. Pentest or signed residual acceptance for SSRF/KG.

Until then: **evidence is missing** for production readiness.
