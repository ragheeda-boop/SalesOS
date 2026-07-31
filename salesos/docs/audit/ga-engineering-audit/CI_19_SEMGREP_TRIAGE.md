# CI-19 — Semgrep Findings Triage (253 blocking)

**Date:** 2026-08-01  
**Story:** CI-19 (REGISTERED → triage complete this pass)  
**Scope:** Read-only triage. No mass code remediation in this pass.  
**Authority:** Executable evidence from GitHub Code Scanning + CI-18 run logs; program context in `docs/program/DECISION_LOG.md` DEC-030 and `docs/program/SPRINT_05_DELIVERY_BOARD.md`.

**Validation status:** **light validated** (live Code Scanning API pull + spot-checks of sample paths). Not a full per-alert exploit review.

---

## 1. How to access the 253 findings

| Channel | How | Evidence |
|--------|-----|----------|
| **GitHub Code Scanning (primary)** | Repo Security → Code scanning alerts, tool filter **Semgrep OSS**, state **open** | `GET /repos/ragheeda-boop/SalesOS/code-scanning/alerts?tool_name=Semgrep%20OSS&state=open` → **253** alerts (2026-08-01 pull) |
| **CI-18 Security Scan run** | Actions run that first uploaded Semgrep SARIF successfully | [Run 30660116232](https://github.com/ragheeda-boop/SalesOS/actions/runs/30660116232) — `sast-scan` SUCCESS; log summary: **Findings 253 (253 blocking)**, 2806 targets, 595 rules; head `6ab1d0e` |
| **Per-alert deep links** | `https://github.com/ragheeda-boop/SalesOS/security/code-scanning/<number>` | Example: [#626](https://github.com/ragheeda-boop/SalesOS/security/code-scanning/626) (`avoid-sqlalchemy-text` in `revenue_execution/service.py`) |
| **Workflow definition** | `.github/workflows/security-scan.yml` | `semgrep --config=auto --sarif-output=semgrep-results.sarif --error --severity ERROR --severity WARNING` + `upload-sarif` |
| **Run artifacts** | Actions artifacts for that run | Present: `gitleaks-results.sarif`, `pip-audit-report`, `npm-audit-report`, `sbom`. **No dedicated Semgrep SARIF artifact** — findings land via Code Scanning upload, not a downloadable named Semgrep artifact on that run |

**CLI recipe (repeatable):**

```bash
gh api "repos/ragheeda-boop/SalesOS/code-scanning/alerts?tool_name=Semgrep%20OSS&state=open&per_page=100" --paginate
```

**Note on “blocking”:** Semgrep CLI used `--error` with ERROR+WARNING severities, so the scan summary counts all 253 as blocking even though Code Scanning severity splits into **error (84)** and **warning (169)**.

---

## 2. Inventory snapshot (evidence-backed)

| Metric | Value |
|--------|------:|
| Open Semgrep OSS alerts | **253** |
| Rule severity `error` | **84** |
| Rule severity `warning` | **169** |
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
| 4 | warning | `logger-credential-disclosure` | Mixed FP vs real log hygiene |
| 4 | warning | `asyncpg-sqli` | Demo scripts (`demo/prod_audit.py`) |
| 2 | error | `sqlalchemy-execute-raw-query` | Alembic migration string SQL |
| 2 | warning | `formatted-sql-query` | Same Alembic cluster |
| 2 | warning | `detect-non-literal-regexp` | FE / JS audit |
| 2 | warning | `prototype-pollution-loop` | FE / JS audit |
| 1 each (error) | error | `missing-user`, `missing-user-entrypoint`, `detected-generic-secret`, `detect-insecure-websocket`, `use-defused-xml-parse`, `github-script-injection` | Spot-check individually |
| 1 each (warning) | warning | `non-literal-import`, AWS TF encryption ×2, `gha-workflow-env-secret` | Hardening / config |

### 2.2 Path concentration

| Count | Path prefix |
|------:|-------------|
| 121 | `.github/workflows` |
| 84 | `salesos/backend` |
| 19 | `salesos/infra` |
| 8 | `salesos/frontend` |
| ≤3 each | scrapers, root pipelines, `sales-os/` legacy, docs, JSON datasets |

**Error-severity path concentration:** `salesos/backend` **72**, `.github/workflows` **7**, infra/docs/legacy remainder.

---

## 3. Severity buckets (Security Lead classification)

Buckets below are **triage judgments grounded in rule IDs + sample paths + spot-checks**, not a claim that every alert was manually exploited.

### Bucket A — P0 true / plausible vulns (fix or prove safe)

| Items | Count | Why |
|-------|------:|----|
| GHA `run-shell-injection` + `github-script-injection` | **8** | Classic `${{ github.* }}` / needs outputs interpolated into `run:` / `github-script`. Confirmed sites: `deploy.yml` (L46–55, L265, L322+), `deploy-staging.yml`, `deploy-production.yml`, legacy `sales-os/.github/workflows/run.yml`. Even when values are SHAs/tags today, pattern is unsafe if attacker-controlled fields ever enter those expressions. |
| Runtime SQLi cluster needing **human proof** | **~77** | 69× `avoid-sqlalchemy-text` + 4× `asyncpg-sqli` + 4× alembic raw/formatted SQL. Spot-check: `revenue_execution/service.py` uses `text("""... :tenant_id ...""")` **with bind dict** — rule fires anyway (MEDIUM CONFIDENCE). Treat as **default FP until proven otherwise**, but prioritize files that concatenate/format user input into SQL. |
| Secret detector | **1** | `salesos/docs/PILOT_SECRETS_GUIDE.md` — guide contains **example** hex / `sk-your-key-here` placeholders. Classify **documentation FP** pending confirm no live credential; do **not** weaken scanners — redact examples or mark as examples for Code Scanning dismiss with reason. |

**P0 actionable without app nosec abuse:** the **8 GHA injection alerts**.

### Bucket B — Hardening / hygiene (real improvements, not “drop everything”)

| Items | Count |
|-------|------:|
| Pin Actions to commit SHAs (`mutable-action-tag`) | 115 |
| K8s `allowPrivilegeEscalation` / SecurityContext | 15 |
| Dockerfile non-root user | 2 |
| Terraform encryption flags | 2 |
| Logger credential disclosure (env-var *names* vs tokens) | 4 |
| `gha-workflow-env-secret` | 1 |

### Bucket C — Noise / out-of-product / low exploitability

| Items | Approx |
|-------|------:|
| Scraper HTML SRI (`taqeem_scraper/*.html`) | 6 |
| BiDi in JSON datasets (`companies.json`, taqeem JSON) | 5 |
| Root legacy pipelines (`website_li_pipeline.py`, `crm_pipeline.py`) | 2+ |
| FE build scripts path-join (`migrate-css-vars.js`, `analyze-bundle.js`) | 6 |
| Legacy `sales-os/.github` (beyond injection already in A) | mutable-tag extras |
| Demo `asyncpg` string SQL outside GA API surface | 4 |

### Bucket D — False-positive-prone patterns (dismiss only after proof)

| Pattern | Evidence |
|---------|----------|
| `sqlalchemy.text` + named bind parameters | Spot-checked `RevenueService` INSERT/UPDATE use `:param` binds — not string-concat SQLi |
| Secrets guide placeholder values | Doc instructs `openssl rand` + paste; samples are illustrative hex / `sk-your-key-here` |
| BiDi in Arabic facility names | Dataset content, not Trojan Source in executable product code |

**Do not** mass-`nosec` / blanket Semgrep ignore to “go green.” Prefer: fix true issues → pin Actions → narrow path excludes for scrapers/legacy → dismiss individual FPs in Code Scanning with written reason.

---

## 4. Phased remediation waves

### Wave 0 — Access & governance (done this pass)

- Confirm 253 alerts reachable via Code Scanning API.  
- Document access + buckets (this file).  
- **No** scanner disablement; keep `--severity ERROR --severity WARNING` upload path from CI-18.

### Wave 1 — READY NEXT (P0 CI injection) — **recommended to implement next**

- **Scope:** 8 alerts — `run-shell-injection` (7) + `github-script-injection` (1) in active deploy workflows (+ legacy `sales-os` if still retained).  
- **Fix pattern:** move untrusted/interpolated values to `env:` then reference `$ENV_VAR` in shell; for `github-script`, use `context` / `core.getInput` instead of string-interpolating `${{ }}` into JS.  
- **Security effect:** **strengthens** CI/CD (no auth/RBAC/CSRF/tenant weaken).  
- **Risk:** low; deploy workflow behavior preserved if env mapping is correct.  
- **Acceptance:** those 8 Code Scanning alerts closed or fixed on `master`; Security Scan still uploads Semgrep SARIF.

### Wave 2 — Runtime SQL honesty pass (`salesos/backend` app/sdk hot paths)

- Inventory all 69 `avoid-sqlalchemy-text` by file (outbox, data_quality, search repos, revenue_execution, etc.).  
- For each: (a) keep parameterized `text()` and **dismiss FP** with reason, or (b) refactor to Core expression API, or (c) fix true concat/format SQLi.  
- Include alembic `0020_add_tenant_id.py` raw SQL (2+2) — migrations often FP but must not concatenate untrusted input.  
- Defer demo `asyncpg-sqli` to Wave 4 or delete/quarantine demo scripts.

### Wave 3 — Supply-chain & infra hardening

- Pin top-used Actions to full SHAs (chips away at 115). Prefer workflow-by-workflow (ci, security-scan, deploy) over big-bang.  
- Add `securityContext` / `allowPrivilegeEscalation: false` on k8s manifests (15).  
- Dockerfile USER fixes (2).  
- Terraform encryption flags (2).

### Wave 4 — Noise reduction (no weakening)

- Exclude or stop scanning non-product trees in Semgrep config: `taqeem_scraper/`, root scrape JSON, legacy `sales-os/` if abandoned — **via path excludes**, not severity drop.  
- Redact/replace placeholder secrets in `PILOT_SECRETS_GUIDE.md` with obviously fake tokens (`CHANGE_ME_*`).  
- FE build-script path-join / prototype-pollution: fix or dismiss as non-runtime.

### Wave 5 — Residual audit rules

- Remaining singleton/error rules (xml, websocket, urllib, regexp) — case-by-case.

---

## 5. Recommendation: which wave is READY next

**Implement Wave 1 next** (GitHub Actions shell/script injection — 8 findings).

Reasons:

1. Grounded in concrete file/line alert locations under `.github/workflows/deploy*.yml`.  
2. Fixes **strengthen** pipeline integrity; no product security control is relaxed.  
3. Small, reviewable diff; does not require mass backend refactors or FP debates.  
4. Unblocks clear P0 CI/CD risk while Wave 2 SQLi work is scoped with bind-param FP awareness.

**Do not start next with:** mass SHA-pinning of 115 Actions (valuable, but not the highest exploit narrative) or blanket `nosec` on 69 `sqlalchemy.text` calls (would **weaken** signal and may hide real concat bugs).

---

## 6. Evidence appendix

| Item | Reference |
|------|-----------|
| CI-18 close / 253 surfaced | DEC-030 — Security Scan run `30660116232` |
| Board registration | Sprint board CI-19 REGISTERED |
| Code Scanning pull | 2026-08-01 — 253 open Semgrep OSS alerts |
| Severity split | error 84 / warning 169 |
| Top rules | mutable-action-tag 115; avoid-sqlalchemy-text 69; k8s privilege 15; shell-injection 7 |
| Spot-check parameterized text | `salesos/backend/app/modules/revenue_execution/service.py` uses `text(...)` + bind dict |
| Spot-check secrets doc | `salesos/docs/PILOT_SECRETS_GUIDE.md` placeholder examples |
| Semgrep upload config | `.github/workflows/security-scan.yml` `sast-scan` job |

---

## 7. Out of scope / honesty

- This pass did **not** close any Code Scanning alerts.  
- This pass did **not** re-run Semgrep locally or download a Semgrep SARIF artifact (none named on run `30660116232`).  
- Bandit / Trivy alert volumes coexist in Code Scanning but are **not** part of the 253 Semgrep count.  
- Classification remains **production no-go** for SalesOS GA overall; CI-19 triage alone does not change GO/NO-GO.

---

*Security Lead — CI-19 triage. Next implementation story: Wave 1 GHA injection remediation.*
