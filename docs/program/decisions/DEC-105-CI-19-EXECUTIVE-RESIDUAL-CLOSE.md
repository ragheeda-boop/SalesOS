# DEC-105 — CI-19 executive residual-close: non-alembic burn + alembic residual accepted; story CLOSED with residual

> **Status:** **Accepted**  
> **Date:** 2026-08-01  
> **Story:** CI-19 — Semgrep findings remediation  
> **Prior:** Waves 1/3/4/5 COMPLETE; Wave 2 Slice 1–6 + field-verify PARKED (DEC-103 / `30686789458` @ `abaae85`)  
> **Tip baseline inventory:** **19** open Semgrep OSS Code Scanning alerts @ `a02c8f1`  
> **DEC-085:** `get_db()` / `set_config` **untouched**  
> **Out of scope:** Wave 2 alembic RLS churn · Jest 30 · auth/RBAC/CSRF weaken · Semgrep severity drop · GHCR credentials (CI-08 / DEC-104)

---

## 1. Inventory @ tip (pre-land)

| Class | Count | Disposition |
|---|---:|---|
| Alembic RLS `avoid-sqlalchemy-text` (`0afbf3e6ae53`×4 + `065d1d3a466b`×3) | **7** | **Accepted residual** (DEC-103) — do not churn |
| Alembic `0020` raw/formatted SQL | **4** | **Accepted residual** (DEC-103) |
| Logger credential-disclosure (identity×2 + scraper_config×2) | **4** | **Fix-now** |
| Prototype-pollution residual (`state-runtime.ts` #835) | **1** | **Fix-now** |
| Triage-doc FP `detect-insecure-websocket` (`CI_19_SEMGREP_TRIAGE.md` #834) | **1** | **Fix-now** (doc wording) |
| DynamoDB CMK (`main.tf` #608 — SSE on, rule wants CMK) | **1** | **Fix-now** |
| GHA workflow-level secret env (`deploy-production.yml` #417) | **1** | **Fix-now** (unused; step already uses `secrets.*`) |
| **Total open** | **19** | |

**Out of scope / not inventing:** CI-08 GHCR 403 (ops).

---

## 2. Decision

1. **Burn** the **8** non-alembic leftovers with minimal real fixes (no `nosemgrep`, no severity drop, no SARIF gate weaken).  
2. **Re-affirm** alembic residual package (**11** = 7 text + 4 raw/formatted) as **accepted** — RLS / tenant migration churn risks DEC-085 / R-14.  
3. **CLOSE CI-19** as **COMPLETE with documented residual** (alembic only expected after land + SARIF lag).  
4. **R-24** → **Closed — mitigating residual** (alembic package remains visible in Code Scanning until/unless a future dedicated migration hygiene story).  
5. Do **not** claim whole-pipeline **CI GREEN**, Production GO, or finding-zero Semgrep.

### Remediations (this land)

| Alert class | Change |
|---|---|
| Logger ×4 | Identity: structured `auth.reset_*` logs without address / “Password” wording; scraper: “API key” → “auth config” (no secret values logged) |
| Prototype #835 | `ensureChild` / `readChild` helpers — blocked keys + null-prototype nests; no `obj = obj[key]` loop pattern |
| Triage #834 | Reword Wave 5 bullet so triage doc does not embed cleartext WS scheme literal |
| TF #608 | Dedicated `aws_kms_key.terraform_locks` + `kms_key_arn` on DynamoDB SSE |
| GHA #417 | Remove unused workflow-level `SLACK_WEBHOOK` (notify step already uses `secrets.SLACK_WEBHOOK_URL`) |

---

## 3. Acceptance / honesty

| Claim | Status |
|---|---|
| CI-19 story | **CLOSED** with residual (alembic **11**) |
| Wave 2 app SQL honesty | Unchanged — app `avoid-sqlalchemy-text` **0** (field-verified DEC-103) |
| Semgrep ERROR/WARNING + SARIF upload | **Unchanged** |
| Whole-pipeline CI GREEN | **Not met** (CI-08 GHCR 403 blocks Stage 6 publish) |
| Production GO / External pilot | **NO-GO** |
| Validation this land | **light validated** (inventory + targeted diffs); field CS closure expected after Security Scan SARIF on tip — upgrade when re-verified |

---

## 4. Expected post-land Code Scanning

| Bucket | Expected |
|---|---|
| Cleared this land (target) | **8** |
| Remaining accepted residual | **11** (alembic) |
| Semgrep CLI blocking (field tip last known) | Was **19** @ Wave 2 verify; target **~11** after this land |

---

## 5. Next READY (if any)

- **CI-08** (P0 BLOCKED) — org GHCR Packages write (DEC-104 Option A); not this track.  
- **CI-14** executive AC close **or** dedicated Jest 30 evidence (DEC-100 STOP).  
- **CI-22** remains OPEN (Phase 1 landed).  
- Optional future: dedicated Alembic SQL-hygiene story (not CI-19 reopen) if program wants alembic finding-zero.
