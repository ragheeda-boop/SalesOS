# Wave Verification Matrix

**Audit date:** 2026-07-22  
**Legend:** ✅ VERIFIED · 🟡 PARTIALLY VERIFIED · ❌ UNVERIFIED · 🚨 CONTRADICTED  
**Confidence:** 100 / 90 / 75 / 50 / 25 / 0 (see `06-confidence-score.md`)

Every row is a claim extracted from `PROGRESS-WAVE*.md` / `GA_STATUS.md` / related audit docs, checked against evidence or source.

---

## Wave 0 — Frontend unblockers

Source: `PROGRESS-WAVE0-FE.md`

| Claim | Evidence | Status | Confidence |
|-------|----------|--------|------------|
| `npm run lint` exit 0 | NONE (no log under evidence/) | ❌ UNVERIFIED | 25 |
| `npx tsc --noEmit` exit 0 | NONE | ❌ UNVERIFIED | 25 |
| `npm run build` exit 0 (51 pages) | NONE; no `.next` BUILD_ID archived | ❌ UNVERIFIED | 25 |
| Classification “build validated” | Conflicts with missing artifacts; APPENDIX-A baseline FAIL | 🚨 CONTRADICTED | 90 |
| Hooks/lint source fixes present | `TenantList.tsx` and related files in tree | 🟡 PARTIALLY VERIFIED | 75 |
| Dashboard routes exist in app router | `salesos/frontend/src/app/(dashboard)/**` pages present | ✅ VERIFIED | 90 |

---

## Wave 1 — Alembic / migrate gate

Source: `PROGRESS-WAVE1-3-5-PLATFORM.md`

| Claim | Evidence | Status | Confidence |
|-------|----------|--------|------------|
| Migrations 0035–0038 idempotent | Source inspection (`_table_exists` / guards) | ✅ VERIFIED | 90 |
| `0039` webhook migration exists | `salesos/backend/app/alembic/versions/0039_webhook_tables.py` | ✅ VERIFIED | 100 |
| `0040` graph tables migration exists | `0040_ensure_graph_tables.py` | ✅ VERIFIED | 100 |
| Local DB upgraded to head in Wave 1 session | No W1 upgrade log; later SQL verify 0039/0040 | 🟡 PARTIALLY VERIFIED | 75 |
| `check_alembic_head.py` exists + CI wiring | Script + `ci.yml` text | ✅ VERIFIED | 90 |
| Local `check_alembic_head.py → OK` transcript | NONE | ❌ UNVERIFIED | 25 |
| Production migrate not run | Consistent negative claim + migrate-prep JSON | ✅ VERIFIED | 90 |

---

## Wave 2 — Security P0

Source: `PROGRESS-WAVE2-SEC.md`

| Claim | Evidence | Status | Confidence |
|-------|----------|--------|------------|
| Decision Center IDOR `(id, tenant_id)` | Source + unit test in tree | 🟡 PARTIALLY VERIFIED | 75 |
| Targeted pytest **96 passed** | No pytest log/JUnit | ❌ UNVERIFIED | 25 |
| Webhook SSRF HTTPS + private block | `url_safety.py` + `evidence/wave2-load/ssrf-denied-*.json` | ✅ VERIFIED | 90 |
| KG SQL fallback default-off in prod | `config.is_kg_sql_fallback_allowed()` | ✅ VERIFIED | 90 |
| Forecast demo gate when `DEMO_MODE=false` | Source + tests on disk | 🟡 PARTIALLY VERIFIED | 75 |
| Staging/pentest not validated | Docs + evidence `production_secure_claim: false` | ✅ VERIFIED | 100 |

---

## Wave 2 — Load probes / residuals

Sources: `PROGRESS-WAVE2-LOAD.md`, `PROGRESS-WAVE2-RESIDUALS.md` · Evidence: `evidence/wave2-load/`

| Claim | Evidence | Status | Confidence |
|-------|----------|--------|------------|
| Probe matrix 26/26 PASS (`T125056Z`) | `probe-summary-…T125056Z.json` overall PASS **while** competitors/network HTTP **500** | 🟡 PARTIALLY VERIFIED / false-PASS | 50 |
| Summary reconstructed after script failure | Explicit `note` in same JSON | ✅ VERIFIED (as reconstructed) | 100 |
| SSRF denies → 400; public HTTPS → 201 | `ssrf-denied-*.json` | ✅ VERIFIED | 90 |
| Cross-tenant `X-Tenant-Id` → 403 | `kg-tenant-*.json` | ✅ VERIFIED | 90 |
| Burst health/me/companies | `burst-*.json` | ✅ VERIFIED | 90 |
| Logger arity closed | Source `sdk/telemetry.py`; later KG edges 200 | 🟡 PARTIALLY VERIFIED | 75 |
| `graph_edges` via 0040 closed locally | `kg-graph-edges-*.json` + migration | ✅ VERIFIED | 90 |
| Production secure | `production_secure_claim: false` | ✅ VERIFIED (negative) | 100 |

---

## Wave 3 — Unit tests

| Claim | Evidence | Status | Confidence |
|-------|----------|--------|------------|
| `1524 passed, 20 skipped` | NONE | ❌ UNVERIFIED | 25 |
| Later `1542 passed, 2 skipped` | NONE (`PROGRESS-CONTINUATION.md` only) | ❌ UNVERIFIED | 25 |
| Quarantine via `QUARANTINE.txt` (20 skips) | File exists but **empty** (“Empty after 2026-07-22 fix wave”) | 🚨 CONTRADICTED (stale skip count) | 90 |
| Host Poetry/asyncpg broken | APPENDIX-A FAIL | ✅ VERIFIED | 90 |

---

## Wave 4 — FE image + infra (with 8/9)

Sources: `PROGRESS-WAVE4-FE-IMAGE.md`, `PROGRESS-WAVE4-8-9-INFRA.md`

| Claim | Evidence | Status | Confidence |
|-------|----------|--------|------------|
| `docker compose build frontend` exit 0 | Cited `fe-build.log` **MISSING** | ❌ UNVERIFIED | 25 |
| FE routes `/`, `/copilot`, `/analytics` → 200 | No W4 log; later crawl weak support | 🟡 PARTIALLY VERIFIED | 50 |
| Compose healthchecks / Neo4j HTTP probe | Compose YAML present | 🟡 PARTIALLY VERIFIED | 75 |
| Stack `up` + `/health/detailed` proven | Progress admits Not run | ❌ UNVERIFIED | 0 |
| INFRA: FE rebuild Not run vs FE-IMAGE: Done | Both progress docs | 🚨 CONTRADICTED | 90 |
| Hardcoded prometheus JWT removed | Only `prometheus-token.example` | ✅ VERIFIED | 90 |

---

## Wave 5 — Auth / API contracts

| Claim | Evidence | Status | Confidence |
|-------|----------|--------|------------|
| CSRF skip only if `api_key_authenticated` | Middleware source | 🟡 PARTIALLY VERIFIED | 75 |
| Missing auth → **401** (was 422) | Code path; no curl transcript in evidence | 🟡 PARTIALLY VERIFIED | 50 |
| `GET /metrics` scrape without JWT | `metrics.py` | 🟡 PARTIALLY VERIFIED | 75 |
| Live W5 probe matrix saved | NONE | ❌ UNVERIFIED | 25 |

---

## Wave 6 — AI honesty

Sources: `PROGRESS-WAVE6-7-AI-GATE.md`, `AI_HONESTY.md`

| Claim | Evidence | Status | Confidence |
|-------|----------|--------|------------|
| `AI_HONESTY.md` exists | File | ✅ VERIFIED | 100 |
| `feature_ai_copilot` default False | `config.py:76` | ✅ VERIFIED | 100 |
| FE Decision package STUB | `packages/platform/decision/index.ts` throws STUB | ✅ VERIFIED | 100 |
| Copilot API 403 when flag False | Router code; **no** live HTTP capture | 🟡 PARTIALLY VERIFIED | 75 |
| Nav/panel gated | FE source | 🟡 PARTIALLY VERIFIED | 75 |
| CTO signed AI scope | Pending/unsigned | ✅ VERIFIED (open) | 100 |

---

## Wave 7 — Governance docs

| Claim | Evidence | Status | Confidence |
|-------|----------|--------|------------|
| Root `AGENTS.md` + cursor essentials | Files present | ✅ VERIFIED | 100 |
| Six GO docs SUPERSEDED banners | Banner text present | ✅ VERIFIED | 100 |
| Wave 10 drill “not executed” (DOCS table) | Conflicts with Wave 10 “DRILL EXECUTED” | 🚨 CONTRADICTED (stale) | 90 |
| Production still no-go | Consistent | ✅ VERIFIED | 90 |

---

## Wave 8 — Observability

| Claim | Evidence | Status | Confidence |
|-------|----------|--------|------------|
| Root compose Prometheus/Grafana/Loki/OTel | `docker-compose.yml` | ✅ VERIFIED | 100 |
| salesos observability profile | `salesos/docker-compose.yml` | ✅ VERIFIED | 100 |
| Observability stack exercised | No `evidence/wave8*`; Not run | ❌ UNVERIFIED | 0 |
| Alerts match root scrape job | Root scrape `salesos-api`; alerts use `salesos-backend` | 🚨 CONTRADICTED | 75 |
| Live SLIs 72h | Open | ❌ UNVERIFIED | 0 |

---

## Wave 9 — Secrets hygiene

| Claim | Evidence | Status | Confidence |
|-------|----------|--------|------------|
| prometheus-token removed from git | Only `.example` | ✅ VERIFIED | 90 |
| `.gitleaks.toml` / `.trivyignore` | Present | ✅ VERIFIED | 100 |
| Security-scan workflow + continue-on-error | YAML | 🟡 PARTIALLY VERIFIED | 75 |
| Full scanner run | Not run | ❌ UNVERIFIED | 0 |
| Secret rotation in GH/K8s | Checklist only | ❌ UNVERIFIED | 0 |

---

## Wave 10 — Backup / DR

Sources: `PROGRESS-WAVE10-BACKUP.md`, `PROGRESS-WAVE10-DR-GAPS.md` · Evidence: `evidence/wave10-dr/`

| Claim | Evidence | Status | Confidence |
|-------|----------|--------|------------|
| Backup/restore scripts exist | `backup-db.sh`, `restore-db.sh` | ✅ VERIFIED | 100 |
| Local `pg_dump` SUCCESS (~21.5 MiB) | Markdown only; **no JSON** in evidence | ❌ UNVERIFIED | 25 |
| Restore row counts match | Markdown only | ❌ UNVERIFIED | 25 |
| Neo4j offline dump Done | `neo4j-admin-dump-*.json` | ✅ VERIFIED | 90 |
| Neo4j disposable load (node_count=0) | `neo4j-admin-load-*.json` | ✅ VERIFIED | 90 |
| Primary `archive_mode=off` | `postgres-wal-settings-*.txt` | ✅ VERIFIED | 100 |
| `pg_basebackup` blocked | `postgres-basebackup-blocked-*.json` | ✅ VERIFIED | 100 |
| Disposable archive_mode on | `postgres-disposable-archive-*.json` | ✅ VERIFIED | 90 |
| Primary PITR / S3 restore | Explicitly open | ❌ UNVERIFIED | 0 |

---

## Wave 11 — Soak

Sources: `PROGRESS-WAVE11-SOAK.md`, `PROGRESS-WAVE11-SOAK-48H.md` · Evidence: `wave11-soak/`, `wave11-soak-48h/`

| Claim | Evidence | Status | Confidence |
|-------|----------|--------|------------|
| Gate script exists | `salesos/scripts/wave11-soak-gate.py` | ✅ VERIFIED | 100 |
| Oneshot GATE PASS | `gate-2026-07-22T075625Z.json`, `…T102451Z.json` | ✅ VERIFIED | 90 |
| Short loop 5 iters / 1 fail | `loop-summary-…T083630Z.json` | ✅ VERIFIED | 90 |
| 4h loop 45 iters / 16 FAIL / exit 1 | `loop-summary-…T142544Z.json` | ✅ VERIFIED | 95 |
| `soak_complete_claim: false` (4h) | Same summary | ✅ VERIFIED | 100 |
| 48h started | README-48H + gate + loop files | ✅ VERIFIED | 90 |
| **48h complete** | Max ~i70 after ~6h wall-clock; **no** loop-summary | 🚨 CONTRADICTED if complete; docs correctly say incomplete | 100 |
| Cloud staging soak | Staging probe BLOCKED | ❌ UNVERIFIED (correctly absent) | 100 |

---

## Wave 12 — Gates / staging / migrate

| Claim | Evidence | Status | Confidence |
|-------|----------|--------|------------|
| `pre-deploy-gates.ps1` exists | Script | ✅ VERIFIED | 100 |
| Gates runtime PASS | Embedded string in migrate-prep JSON; **`evidence/wave12-gates/` missing** | 🟡 PARTIALLY VERIFIED | 50 |
| Local deploy/rollback tabletop | `wave12-tabletop/tabletop-complete-*.json` | 🟡 PARTIALLY VERIFIED | 75 |
| Staging cloud BLOCKED | `wave12-staging/probe-…163200Z.json` | ✅ VERIFIED | 95 |
| Virtual staging `:8001`/`:3002` | `wave12-staging-virtual/tabletop-complete-*.json` | ✅ VERIFIED | 90 |
| Prod migrate executed | `SUMMARY.json` `production_migrate_executed:false` | ✅ VERIFIED (not executed) | 95 |
| Backend image bake digests | Thin / narrative | ❌ UNVERIFIED | 25 |

---

## Wave 13 — Auth / UI / crawl

| Claim | Evidence | Status | Confidence |
|-------|----------|--------|------------|
| Auth smoke 13/13 PASS | `demo-admin-smoke-auth-*.json` | 🟡 PARTIALLY VERIFIED | 75 |
| Demo admin login 200 | `demo-admin-login-verify-*.json` | ✅ VERIFIED | 90 |
| Disposable auth probe 200s | `disposable-auth-probe-*.json` | ✅ VERIFIED | 90 |
| Playwright UI smoke PASS | Cited report not readable under evidence; HTML not in audit evidence | ❌ UNVERIFIED | 25 |
| Full UI crawl 49/49 shells, 136 clicks | `full-ui-crawl-report.json` (`passCount:49`, `clicksAttempted:136`, `clicksFailed:8`) | 🟡 PARTIALLY VERIFIED | 75 |
| Crawl screenshots | All `"screenshot": null`; 0 PNG in folder | 🚨 CONTRADICTED if claimed captured | 100 |
| Soft gate with API residuals | `pagesWithHttpErrors:14`, `pagesWithConsoleErrors:34`, `production_go:false` | ✅ VERIFIED | 95 |
| Scripts/specs exist | `full-ui-crawl.ps1`, `e2e/full-ui-crawl.spec.ts` | ✅ VERIFIED | 100 |

---

## Wave 14 — Go-live pack

| Claim | Evidence | Status | Confidence |
|-------|----------|--------|------------|
| Human review pack prepared | `PROGRESS-WAVE14-GO-LIVE.md` | 🟡 PARTIALLY VERIFIED | 75 |
| Hypercare not started | Docs | ✅ VERIFIED | 90 |
| `evidence/wave14*` | MISSING | ❌ UNVERIFIED | 0 |
| SIGN_HERE valid Production GO | Header UNSIGNED; body partial SIGNED/GO; blank Signature | 🚨 CONTRADICTED as GO | 95 |
| Production GO claimed | Explicitly NOT claimed in Wave 14 / GA_STATUS | ✅ VERIFIED (negative) | 100 |

---

## Cross-cutting special verifications

| Area | Finding | Status | Confidence |
|------|---------|--------|------------|
| Frontend lint/tsc/build post-fix | No exit-0 logs | ❌ | 25 |
| Backend pytest green | No JUnit/log | ❌ | 25 |
| Alembic current=head locally | SQL verify 0040 in soak-48h | 🟡 | 75 |
| IDOR / SSRF / CSRF / tenant / RBAC | Mixed: code + some probes; no pentest | 🟡 | 50–90 |
| Docker compose / health | Config yes; full stack exercise thin | 🟡 | 50 |
| Prometheus/Grafana/Loki runtime | Config yes; scrape matrix missing | ❌ | 0 |
| Staging cloud | BLOCKED evidenced | ✅ (blocked) | 95 |
| Production deploy/rollback | Not run | ❌ | 0 |
| Playwright browser GA | Soft local only | 🟡 | 50 |
| 48–72h soak | Incomplete | 🚨 if claimed done | 100 |
| Backup restore drill (pg) | Markdown only | ❌ | 25 |
| Load (k6) | Not run | ❌ | 0 |

---

**End of wave matrix.** Detail on gaps → `03-missing-evidence.md`. False positives → `04-false-claims.md`.
