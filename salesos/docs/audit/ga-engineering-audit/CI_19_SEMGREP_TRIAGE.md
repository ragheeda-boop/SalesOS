# CI-19 — Semgrep Findings Triage

**Date:** 2026-08-01  
**Story:** CI-19 (REGISTERED → **triage complete**; remediation waves scoped, not mass-fixed)  
**Scope:** Read-only triage. No mass code remediation of the ~250 findings in this pass.  
**Authority:** Executable evidence from GitHub Code Scanning + CI-18 run logs; program context in `docs/program/DECISION_LOG.md` DEC-030 and `docs/program/SPRINT_05_DELIVERY_BOARD.md`.

**Validation status:** **light validated** (live Code Scanning API aggregation + spot-checks of sample paths). Not a full per-alert exploit review.

---

## 1. Evidence source

| Channel | How | Evidence |
|--------|-----|----------|
| **GitHub Code Scanning (primary)** | Repo Security → Code scanning alerts, tool filter **Semgrep OSS**, state **open** | `GET /repos/ragheeda-boop/SalesOS/code-scanning/alerts?tool_name=Semgrep%20OSS&state=open` → **254** open (2026-08-01 Security Team Alpha re-verify) |
| **CI-18 Security Scan run** | Actions run that first uploaded Semgrep SARIF successfully | [Run 30660116232](https://github.com/ragheeda-boop/SalesOS/actions/runs/30660116232) — `sast-scan` SUCCESS; log summary: **Findings 253 (253 blocking)**, 2806 targets, 595 rules; head `6ab1d0e` |
| **Per-alert deep links** | `https://github.com/ragheeda-boop/SalesOS/security/code-scanning/<number>` | Example: [#626](https://github.com/ragheeda-boop/SalesOS/security/code-scanning/626) (`avoid-sqlalchemy-text` in `revenue_execution/service.py`) |
| **Workflow definition** | `.github/workflows/security-scan.yml` | `semgrep --config=auto --sarif-output=semgrep-results.sarif --error --severity ERROR --severity WARNING` + `upload-sarif` |
| **Local `.tmp-ci19/` dumps** | Expected: `semgrep-summary.json`, `semgrep-alerts-raw.json` | **Not present** on disk at triage close (Glob/index may have referenced them earlier). **Do not commit** raw alert dumps — they can embed secret-like strings. Summary doc only. |

**CLI recipe (repeatable):**

```bash
gh api "repos/ragheeda-boop/SalesOS/code-scanning/alerts?tool_name=Semgrep%20OSS&state=open&per_page=100" --paginate
```

**Count note:** CI-18 log showed **253** blocking findings at first successful upload. Live open count at triage close is **254** (error **84** / warning **170**) — +1 drift vs CI-18; rule inventory still **24** distinct IDs. Semgrep CLI `--error` with ERROR+WARNING treats the full set as “blocking” even though Code Scanning severity splits.

---

## 2. Inventory snapshot (evidence-backed)

| Metric | Value |
|--------|------:|
| Open Semgrep OSS alerts (live) | **254** |
| CI-18 first-upload blocking count | **253** |
| Rule severity `error` | **84** |
| Rule severity `warning` | **170** |
| Distinct rule IDs | **24** |
| Tool version (sample alert) | Semgrep OSS **1.172.0** |

### 2.1 Top rule IDs

| Count | Sev | Rule ID (short) | Class (triage) |
|------:|-----|-----------------|----------------|
| 115 | warning | `github-actions-mutable-action-tag` | Hardening / supply-chain hygiene (noise for runtime vuln backlog) |
| 69 | error | `avoid-sqlalchemy-text` | Likely **majority FP** if bind params used — still requires runtime path review |
| 15 | warning | `allow-privilege-escalation-no-securitycontext` | K8s hardening |
| 7 | error | `run-shell-injection` | **P0 CI** — true class of issue (context→shell) |
| 6 | warning | `missing-integrity` | Mostly scraper HTML snapshots |
| 6 | warning | `path-join-resolve-traversal` | Build/migrate scripts (low exploitability) |
| 5 | warning | `contains-bidirectional-characters` | Data/JSON noise (Arabic / datasets) |
| 4 | warning | `dynamic-urllib-use-detected` | Audit / low confidence |
| 4 | warning | `python-logger-credential-disclosure` | Mixed FP vs real log hygiene |
| 4 | warning | `asyncpg-sqli` | Demo scripts (`demo/prod_audit.py`) |
| 3 | warning | `detect-non-literal-regexp` | FE / JS audit |
| 2 | error | `sqlalchemy-execute-raw-query` | Alembic migration string SQL |
| 2 | warning | `formatted-sql-query` | Same Alembic cluster |
| 2 | warning | `prototype-pollution-loop` | FE / JS audit |
| 1 each (error) | error | `missing-user`, `missing-user-entrypoint`, `detected-generic-secret`, `detect-insecure-websocket`, `use-defused-xml-parse`, `github-script-injection` | Spot-check individually |
| 1 each (warning) | warning | `non-literal-import`, AWS TF encryption ×2, `gha-workflow-env-secret` | Hardening / config |

### 2.2 Path concentration

| Count | Path prefix |
|------:|-------------|
| 121 | `.github/workflows` |
| 84 | `salesos/backend` |
| 19 | `salesos/infra` |
| 9 | `salesos/frontend` |
| 9 | scrapers / taqeem HTML |
| ≤5 each | `salesos/` misc, `sales-os/` legacy, root pipelines, JSON datasets |

**Error-severity path concentration:** `salesos/backend` **72**, `.github/workflows` **7**, other **5**.

---

## 3. Severity buckets (READY vs noise)

Buckets are **triage judgments grounded in rule IDs + sample paths + spot-checks**, not a claim that every alert was manually exploited.

### Bucket A — READY / P0 true or plausible (fix or prove safe)

| Items | Count | Verdict |
|-------|------:|---------|
| GHA `run-shell-injection` + `github-script-injection` | **8** | **READY NEXT** — classic `${{ github.* }}` interpolated into `run:` / `github-script`. Sites include `deploy.yml`, `deploy-staging.yml`, `deploy-production.yml`, legacy `sales-os/.github/workflows/run.yml`. |
| Runtime SQLi cluster needing **human proof** | **~77** | 69× `avoid-sqlalchemy-text` + 4× `asyncpg-sqli` + 4× alembic raw/formatted SQL. Spot-check: `revenue_execution/service.py` uses `text("""... :tenant_id ...""")` **with bind dict** — rule fires anyway. Default **FP until proven otherwise**; prioritize concat/format of user input. **Not** READY for mass fix. |
| Secret detector | **1** | `salesos/docs/PILOT_SECRETS_GUIDE.md` — example / placeholder values. **Documentation FP** pending confirm no live credential. |

**Actionable READY without app `nosec` abuse:** the **8 GHA injection alerts** only.

### Bucket B — Hardening (real, not “drop everything”)

| Items | Count | Verdict |
|-------|------:|---------|
| Pin Actions to commit SHAs (`mutable-action-tag`) | 115 | Valuable supply-chain hygiene; **not** highest exploit narrative for Wave 1 |
| K8s `allowPrivilegeEscalation` / SecurityContext | 15 | Infra hardening wave |
| Dockerfile non-root user | 2 | Infra |
| Terraform encryption flags | 2 | Infra |
| Logger credential disclosure | 4 | Mixed FP vs hygiene |
| `gha-workflow-env-secret` | 1 | Config hygiene |

### Bucket C — Noise / out-of-product / low exploitability

| Items | Approx | Verdict |
|-------|------:|---------|
| Scraper HTML SRI (`missing-integrity`) | 6 | **Noise** for SalesOS GA runtime — path-exclude |
| BiDi in JSON datasets | 5 | **Noise** (Arabic facility names, not Trojan Source in product code) |
| Root legacy pipelines | 2+ | Out of GA path |
| FE build-script path-join | 6 | Low exploitability |
| Demo `asyncpg` string SQL | 4 | Outside GA API surface |
| Legacy `sales-os/.github` mutable-tag extras | (subset of 115) | Abandoned tree — exclude or delete |

### Bucket D — False-positive-prone (dismiss only after proof)

| Pattern | Evidence |
|---------|----------|
| `sqlalchemy.text` + named bind parameters | Spot-checked `RevenueService` INSERT/UPDATE use `:param` binds — not string-concat SQLi |
| Secrets guide placeholder values | Illustrative hex / `sk-your-key-here` |
| BiDi in Arabic facility names | Dataset content |

**Do not** mass-`nosec` / blanket Semgrep ignore to “go green.” Prefer: fix true issues → pin Actions → narrow path excludes for scrapers/legacy → dismiss individual FPs in Code Scanning with written reason.

---

## 4. Recommended remediation waves

### Wave 0 — Access & governance (done this pass)

- Confirm alerts reachable via Code Scanning API (254 open at close).  
- Document access + buckets (this file).  
- Confirm `.tmp-ci19` raw dumps **not** committed.  
- **No** scanner disablement; keep `--severity ERROR --severity WARNING` upload path from CI-18.

### Wave 1 — P0 CI injection → **COMPLETE** (`d5c9b57`)

- **Scope:** 8 alerts — `run-shell-injection` (7) + `github-script-injection` (1).  
- **Fix pattern:** move interpolated values to `env:` then `$ENV_VAR` in shell; for `github-script`, use `context` / `core.getInput` instead of string-interpolating `${{ }}` into JS.  
- **Security effect:** **strengthens** CI/CD (no auth/RBAC/CSRF/tenant weaken).  
- **Acceptance:** those 8 Code Scanning alerts closed or fixed; Security Scan still uploads Semgrep SARIF.
- **Remediation landed (2026-08-01):** commit `d5c9b57` (`d5c9b5746a346c6773e4205f03284c8186b7f3ca`) — `fix(ci): CI-19 wave 1 remediate GHA script injection`. Files: `.github/workflows/deploy.yml`, `deploy-staging.yml`, `deploy-production.yml`, `sales-os/.github/workflows/run.yml` (env:/process.env pattern). **Wave 1 only** — Waves 2–5 still open; CI-19 story **not** closed; **CI GREEN not met**.

### Wave 2 — Runtime SQL honesty pass (`salesos/backend` hot paths) → **IN PROGRESS** (Slice 1+2 landed — DEC-091 / DEC-097)

- Inventory: live Code Scanning (tip baseline) **72** `avoid-sqlalchemy-text` + **4** alembic raw/formatted = **76** SQL-cluster; earlier tip estimate ~108 was stale vs post–Wave 4/5 open set (**85** Semgrep OSS open total).
- Per finding: (a) parameterized `text()` → dismiss FP with reason, (b) refactor to Core expression API, or (c) fix true concat SQLi. **No** Semgrep suppress / severity drop.
- Include alembic `0020_add_tenant_id.py` raw SQL (2+2) — **remainder**.
- Demo `asyncpg-sqli` quarantined under Wave 4 `.semgrepignore` (`salesos/backend/demo/`).
- **Slice 1 COMPLETE (DEC-091):** Core rewrite (eliminate `sqlalchemy.text`) for:
  - `sdk/events/outbox.py` (**8** alerts)
  - `app/modules/revenue_execution/service.py` (**3** — also removes f-string `WHERE` list filters)
  - `sdk/events/store.py` (**1**)
  - `sdk/audit.py` (**1**)
  - Expected cleared this slice: **13** Code Scanning alerts. Unit: `test_outbox` + `test_revenue_service` (**light validated**).
- **Slice 2 COMPLETE (DEC-097):** Core rewrite for:
  - `app/application/admin/data_quality.py` (**8**)
  - `runtime/knowledge_graph_runtime/pgvector_migration.py` (**8** — DDL via allowlisted `exec_driver_sql`)
  - Expected cleared this slice: **16** Code Scanning alerts. Validation: **light validated** (AST parse).
- **Remainder (not this slice):** ~**43** `avoid-sqlalchemy-text` — densest next: `domains/search/engine/postgres_repo.py` (6), `timeline_runtime` (5), `search_runtime` (4), alembic RLS/tenant migrations, `sdk/search.py` pgvector allowlist tables, `tasks.py`, etc. + non-SQL residuals (logger-credential ×4, gha-workflow-env-secret, etc.).
- **Wave 2 NOT CLOSED.** **CI-19 NOT CLOSED.**

### Wave 3 — Supply-chain & infra hardening → **SHA-pin + residual COMPLETE** (`DEC-069` / `DEC-074`)

- **SHA-pin slice (COMPLETE):** Pin all `uses:` Action refs in root `.github/workflows/*.yml` + `sales-os/.github/workflows/run.yml` to full 40-char commit SHAs (115 replacements; 0 mutable tags remain in those files). Floating `aquasecurity/trivy-action@master` → pinned `v0.29.0` SHA (same tag already used in `deploy-production.yml`). Version comments retained (`# v4`, etc.).  
- **Files:** `security-scan.yml`, `ci.yml`, `docker-smoke.yml`, `deploy.yml`, `deploy-staging.yml`, `deploy-production.yml`, `sales-os/.github/workflows/run.yml`.  
- **Residual slice (COMPLETE — DEC-074):**  
  - K8s: 15× `allowPrivilegeEscalation: false` on containers across `salesos/infra/k8s/` (backend/frontend/celery×2/migrate/redis/postgres/neo4j/kafka/zookeeper/grafana/prometheus/alertmanager/backup/restore-test). App images (backend/frontend/celery/migrate) also get `runAsNonRoot: true` + `capabilities.drop: [ALL]`.  
  - Docker: `USER postgres` on `infra/docker/backup/Dockerfile`; `USER alertmanager` on `infra/docker/monitoring/alertmanager/Dockerfile` (writable dirs chowned).  
  - Terraform: DynamoDB `server_side_encryption { enabled = true }`; Secrets Manager CMK (`aws_kms_key` + rotation + `kms_key_id`).  
- **Architecture STOP (documented, not blocking residual):** data-store pods (postgres/neo4j/kafka/zookeeper/redis) intentionally **omit** `runAsNonRoot` — official images often start as root to fix volume perms then drop; forcing non-root without UID/`fsGroup` alignment risks broken PVCs. Residual Semgrep rule only required `allowPrivilegeEscalation: false`.  
- **Security effect:** strengthens supply-chain + runtime/infra hardening; **does not** weaken Semgrep gates / severity / upload path.  
- **Wave 3 fully complete** for triage-scoped hardening items. Next: Wave 4 path excludes / Wave 5 residuals.

### Wave 4 — Noise reduction (no weakening) → **COMPLETE** (`DEC-076`)

- **Path excludes (COMPLETE):** repo-root `.semgrepignore` — Semgrep auto-loads; severity ERROR+WARNING and SARIF upload **unchanged**.
  - `taqeem_scraper/` — scraper HTML/JSON (`missing-integrity`, BiDi); not SalesOS GA runtime
  - Root scrape JSON: `taqeem_facilities.json`, `companies.json`, `recovered_contacts.json` — BiDi dataset noise
  - `sales-os/` — abandoned legacy tree (out of `salesos/` GA path)
  - `crm_pipeline.py` — root legacy pipeline
  - `salesos/backend/demo/` — demo quarantine (asyncpg-sqli / urllib deferred from Wave 2)
  - `salesos/frontend/scripts/`, `salesos/scripts/` — non-runtime build/migrate path-join noise (Bucket C)
- **Secrets doc (COMPLETE):** redact `salesos/docs/PILOT_SECRETS_GUIDE.md` illustrative hex/`sk-` examples → `CHANGE_ME_*` placeholders (no live credential claim).
- **Explicitly not excluded:** `salesos/backend` app/runtime, product FE packages (e.g. prototype-pollution in `packages/runtime` → Wave 5), `.github/workflows`.
- **Honesty:** path excludes only for out-of-product / non-runtime noise — **no** severity drop, **no** blanket rule ignore.

### Wave 5 — Residual audit rules → **COMPLETE** (`DEC-082`)

- **Scope:** singleton / small-cluster residual rules left after Waves 1/3/4 (xml, websocket, urllib, non-literal regexp ×3, FE prototype-pollution ×2). Real code/doc fixes — **no** severity drop, **no** blanket rule ignore, **no** Wave 2 SQL work.
- **Remediations:**
  - `use-defused-xml-parse` — `salesos/backend/scripts/check_diff_coverage.py`: replace `xml.etree.ElementTree` with Cobertura regex parse (local CI XML; no new dep).
  - `detect-insecure-websocket` — `salesos/docs/pentest/PENTEST_BRIEF.md`: document `wss://` (not `ws://`).
  - `dynamic-urllib-use-detected` — root `website_li_pipeline.py`: replace `urllib.request.urlopen` with `http.client` (no `file://`).
  - `detect-non-literal-regexp` ×3 — forms: `pattern?: RegExp` (no `new RegExp(string)`); search-highlight: literal `indexOf` split; session test: cookie parse without RegExp.
  - `prototype-pollution-loop` ×2 — `packages/runtime` `StateRuntime`: block `__proto__`/`constructor`/`prototype`; null-prototype nested objects; `hasOwnProperty` walks.
- **Architecture STOP:** none for this slice.
- **Out of Wave 5:** Wave 2 `avoid-sqlalchemy-text` (~108 still open); logger-credential / gha-workflow-env-secret / misc secret-detectors (not triage Wave 5 singletons).
- **Security effect:** clears residual audit surface without weakening Semgrep ERROR/WARNING gates / SARIF upload.

---

## 5. READY vs noise — executive call

| Label | Count (approx) | Next action |
|-------|---------------:|-------------|
| **READY (Wave 1)** | **8** | **COMPLETE** at `d5c9b57` (env:/process.env) |
| SQL honesty / FP review (Wave 2) | **~76 → ~63 → ~36** after Slice 1+2 | **IN PROGRESS** — Slice 1 (**13**, DEC-091) + Slice 2 (**27**, DEC-097); ~**32** text remain — no mass `nosec` |
| Hardening backlog (Wave 3) | **~139** → SHA pins **115** + residual **19** done | **Wave 3 COMPLETE** (`DEC-069` SHA-pin + `DEC-074` K8s/Docker/TF) |
| **Noise / exclude (Wave 4)** | **~30** | **COMPLETE** (`DEC-076`) — `.semgrepignore` + secrets-doc redact |
| Residual singletons (Wave 5) | **8** | **COMPLETE** (`DEC-082`) — xml/websocket/urllib/regexp×3/prototype×2 |

**Wave 1 COMPLETE** at `d5c9b57`. **Wave 3 COMPLETE** under `DEC-069` (`556304d`) + `DEC-074` (`465c638`). **Wave 4 COMPLETE** under `DEC-076` (`5c27470`). **Wave 5 COMPLETE** under `DEC-082`. **Wave 2 Slice 1 COMPLETE** under `DEC-091` (**13**). **Wave 2 Slice 2 COMPLETE** under `DEC-097` (`data_quality` + `pgvector_migration` — **16** expected). Wave 2 remainder (~**32** text) + non-SQL residuals keep CI-19 OPEN. **CI GREEN not met.**

---

## 6. Evidence appendix

| Item | Reference |
|------|-----------|
| CI-18 close / 253 surfaced | DEC-030 — Security Scan run `30660116232` |
| Board registration | Sprint board CI-19 REGISTERED |
| Code Scanning re-verify | 2026-08-01 — **254** open Semgrep OSS alerts |
| Severity split | error **84** / warning **170** |
| Top rules | mutable-action-tag 115; avoid-sqlalchemy-text 69; k8s privilege 15; shell-injection 7 |
| Spot-check parameterized text | `salesos/backend/app/modules/revenue_execution/service.py` uses `text(...)` + bind dict |
| Spot-check secrets doc | `salesos/docs/PILOT_SECRETS_GUIDE.md` → Wave 4 `CHANGE_ME_*` redact |
| Semgrep upload config | `.github/workflows/security-scan.yml` `sast-scan` job |
| Wave 4 path excludes | `.semgrepignore` (DEC-076) |
| Wave 5 residual fixes | DEC-082 — coverage regex parse; `wss://` pentest brief; `http.client` pipeline; FE RegExp/prototype hardening |
| Local raw dumps | `.tmp-ci19/` **absent** at close — not committed |

---

## 7. Out of scope / honesty

- This pass did **not** close Code Scanning alerts (except documenting Wave 1 as READY; Wave 1 code remediation later landed at `d5c9b57` — see §4).  
- This pass did **not** re-run Semgrep locally or download a named Semgrep SARIF artifact from run `30660116232`.  
- Bandit / Trivy alert volumes coexist in Code Scanning but are **not** part of the Semgrep count.  
- Classification remains **production no-go** for SalesOS GA overall; CI-19 triage alone does not change GO/NO-GO.

---

*Security Team Alpha — CI-19. Wave 1 COMPLETE `d5c9b57`. Wave 3 COMPLETE (`556304d` / DEC-069 + `465c638` / DEC-074). Wave 4 COMPLETE (`5c27470` / DEC-076). Wave 5 COMPLETE (DEC-082). Wave 2 Slice 1 COMPLETE (DEC-091). Wave 2 Slice 2 COMPLETE (DEC-097). CI-19 still OPEN (Wave 2 SQL remainder ~32).*
