# DEC-149 — Canonical deploy topology: Backend → Railway; Frontend → Vercel

> **Status:** **Accepted** — User governance ruling (2026-08-02) + Architecture Validation hybrid verdict; program DEC for Phase 0 deploy topology (same class as DEC-104 / DEC-016 authorization)  
> **Date:** 2026-08-02  
> **Board:** Chief Architect / ARB + Execution Orchestrator (SalesOS / AQLIYA) — program/governance scribe land  
> **Story / risk:** CI-09 / Phase 0 criterion **3.11** / **R-17** (SSH/VPS leg)  
> **Authority:** Architecture Validation session (hybrid) · user governance ruling · EXEC-ARCHITECTURE-PRODUCT-REVIEW · GA_STATUS · DEC-016 / DEC-120 · deploy configs  
> **Amends (consequence):** CI-09 reframed from ops VPS-secret provision; governance land = **BLOCKED BY GOVERNANCE**; follow-on workflow land = **READY_FOR_REVIEW** — does **not** close CI-09  
> **Out of scope (governance land):** Editing `.github/workflows/*` · provisioning secret *values* · inventing ARB **4.1/4.8** PASS · Phase 0 exit · CI GREEN · Production GO · DEC-085  
> **Follow-on (2026-08-02, devops/ci-worker):** Workflow migration **implemented** — see §6. CI-09 / **3.11** → **BLOCKED** (Validation CONDITIONAL — §6 secrets missing; not CLOSED).  
> **Validation field-verify (2026-08-02):** **VALIDATION_PASS** — Deploy [30723120473](https://github.com/ragheeda-boop/SalesOS/actions/runs/30723120473) @ c3507ed SUCCESS (Railway up ✓; health HTTP 200 ✓; Vercel FE ✓). CI-09 / **3.11** → **READY_FOR_REVIEW** (Orchestrator CLOSE / CLOSED CONDITIONAL; not auto-CLOSED).
> **Amend (2026-08-02, devops/ci-worker + user ruling):** **Single-env current state** — production Railway only; staging secrets **optional / deferred** until a staging environment is created. See §1a / §6.

---

## 1. Decision

**Adopt** the following as the **canonical** production deploy topology for SalesOS:

| Plane | Target |
|---|---|
| **Backend** | **Railway** |
| **Frontend** | **Vercel** |

| Field | Value |
|---|---|
| Prior VPS assumption (CI-09 / **3.11**) | **Superseded as the closure path** — do **not** create a VPS or add unused `VPS_HOST` / `VPS_USER` / `VPS_SSH_KEY` solely to close the criterion |
| Workflow migration (`deploy.yml`, `deploy-staging.yml`, related) | **Implemented** (devops/ci-worker follow-on) — Railway+Vercel active; VPS SSH removed; K8s `deploy-production.yml` quarantined |
| Operating environments (current) | **One environment only** — production Railway / live path. Staging Railway **not provisioned**; `RAILWAY_STAGING_*` **not required** until staging exists |
| CI-09 / **3.11** | Remains **OPEN** — status **BLOCKED** (Validation CONDITIONAL: production `RAILWAY_*` names still missing for live deploy close; staging deferred — **not CLOSED**) |
| Validation label | **light validated (negative)** — workflows align; production deploy still needs §6 **production** secrets; staging soft-skip / dispatch-only; do not claim CI GREEN / Production GO |

**Honesty:** Governance land resolved the **intended canonical target**. Follow-on workflow land makes Railway+Vercel the **active GHA path**. CI-09 / **3.11** close only after Validation — **not** automatic.

### 1a. Single-environment operating state (user ruling 2026-08-02)

```text
Current: production Railway (+ Vercel FE) only.
Staging: deferred — do not require RAILWAY_STAGING_* / RAILWAY_STAGING_HEALTH_URL
         until a Railway staging environment is actually created.
deploy-staging.yml: workflow_dispatch only + CONFIRM-STAGING-DEPLOY;
                    soft-skips when staging IDs absent (does not fail master push path).
deploy.yml: production RAILWAY_* required; does not demand staging vars.
```

---

## 2. Evidence pointers (Architecture Impact)

Cross-link: Architecture Validation session conclusion — verdict **hybrid** (Backend→Railway + Frontend→Vercel live/intended; GHA was VPS/SSH). Parent transcript: [Architecture Validation hybrid](6baea6ce-bf54-441d-92bb-961d9b609cc3). Evidence agent: [Deploy target vs CI-09](23ee1e07-fb76-48d0-8860-9d463b22a911).

| Surface | Path / pointer |
|---|---|
| Root Railway | `railway.json` (`Dockerfile.railway`, uvicorn, `/health`) |
| SalesOS Railway | `salesos/railway.json` (backend Dockerfile, alembic preDeploy) |
| Vercel FE | `salesos/frontend/vercel.json` |
| Vercel runbook | `salesos/frontend/docs/VERCEL_DEPLOY.md` |
| Exec architecture | `docs/audit/ga-engineering-audit/EXEC-ARCHITECTURE-PRODUCT-REVIEW-2026-07-30.md` — Railway as live deploy target |
| GA scoreboard | `docs/audit/ga-engineering-audit/GA_STATUS.md` — Railway BE + Vercel FE live |
| Railway R-14 | DEC-016 / DEC-120 — Railway Postgres / `APP_POSTGRES_*` path |
| Active GHA (post migration) | `.github/workflows/deploy.yml` (production Railway+Vercel) |
| Staging GHA (deferred) | `.github/workflows/deploy-staging.yml` — dispatch + soft-skip until staging exists |
| Quarantined | `.github/workflows/deploy-production.yml` (K8s — DEC-149) |

---

## 3. CI-09 / criterion 3.11 framing (mandatory)

```text
CI-09
Status: BLOCKED
Reason: VALIDATION_PASS — Deploy 30723120473 Railway up + health HTTP 200 + Vercel FE; recommend Orchestrator CLOSE/CLOSED CONDITIONAL.
Staging: deferred (single-env) — RAILWAY_STAGING_* not required until staging exists; deploy-staging soft-skip / dispatch-only.
Not CLOSED — pending Validation field-verify of Deploy Production + production secret/var names provisioned.
Do not provision unused VPS_*. Do not invent staging secrets.
```

| Field | Value |
|---|---|
| Queue | **Validation Queue** (was Governance Queue until DEC Accepted + workflows landed) |
| Owner | **Validation** (close gate); DevOps owns **production** secret-name provision |
| Dependency | DEC-149 **Accepted** + workflow migration **landed** + single-env amend |
| Next action | Ops: provision §6 **production** names (values out-of-band). Validation: field-verify Deploy Production. Staging: defer until Railway staging exists — then provision `RAILWAY_STAGING_*` and re-enable auto path if desired. Do **not** invent `VPS_*` |
| Explicit non-actions | Do **not** close CI-09 without Validation; do **not** mark obsolete; do **not** claim CI GREEN / Production GO; do **not** require staging vars while single-env |

---

## 4. Consequence

1. Canonical deploy = **Railway (backend) + Vercel (frontend)**.  
2. CI-09 / **3.11** → **READY_FOR_REVIEW** (implementation landed; **not CLOSED**).  
3. Active GHA path = `deploy.yml` (production Railway+Vercel). `deploy-staging.yml` = **deferred** (dispatch + soft-skip) until staging exists. K8s `deploy-production.yml` **quarantined**.  
4. CI-08 (GHCR) remains a **separate** ops blocker for Stage 6 publish (DEC-104); Railway `railway up` path does **not** require GHCR.  
5. Phase 0 remains **NO-GO**. **CI GREEN not met.** **Production GO not claimed.** DEC-085 untouched.  
6. Single-env amend: staging secrets **not** a CI-09 close gate until staging is provisioned.

---

## 5. Records touched (governance land)

| File | Change |
|---|---|
| This DEC | Canonical topology Accepted |
| `PHASE_0_EXIT_CHECKLIST.md` | **3.11** / Remaining-9 / Blocked Items → governance framing |
| `SPRINT_05_DELIVERY_BOARD.md` | CI-09 → Governance Queue / BLOCKED BY GOVERNANCE |
| `EXECUTION_DAG.md` | CI-09 block class → governance |
| `RISK_REGISTER.md` | R-17 SSH/VPS leg → governance note |
| `DECISION_LOG.md` | DEC-149 entry |

**Governance land:** Workflows unchanged. CI-09 not CLOSED. No VPS secrets requested.

---

## 6. Workflow migration (2026-08-02 follow-on — READY_FOR_REVIEW)

| Workflow | Change |
|---|---|
| `deploy.yml` | **Active prod path:** Railway `railway up` (cwd `salesos/`) + public `/health` gate; FE = Vercel Git (primary) + optional CLI. **Production secrets only** — does not demand `RAILWAY_STAGING_*` |
| `deploy-staging.yml` | **Deferred (single-env):** `workflow_dispatch` only + `CONFIRM-STAGING-DEPLOY`; **soft-skips** when `RAILWAY_STAGING_*` absent (notice, exit 0). No push trigger on `master`/`develop` (stops dual-fire). Re-enable auto path only after Railway staging exists |
| `deploy-production.yml` | **Quarantined** (K8s) — tag push removed; `workflow_dispatch` requires `CONFIRM-K8S-QUARANTINE` |
| `ci.yml` Stage 6 | **Unchanged** (GHCR publish orthogonal — CI-08) |

### Required GitHub secret / variable **names** (values out-of-band — do not invent)

#### Production (required for Deploy Production / CI-09 close path)

| Name | Scope | Purpose |
|---|---|---|
| `RAILWAY_TOKEN` | secret (`production`) | Railway CLI auth |
| `RAILWAY_PROJECT_ID` | secret (`production`) | Railway project |
| `RAILWAY_SERVICE_ID` | secret (`production`) | Backend service (prod) |
| `RAILWAY_ENVIRONMENT_ID` | secret (`production`) | Production environment |
| `RAILWAY_HEALTH_URL` | var or secret (`production`) | Public backend base or `/health` URL |
| `VERCEL_TOKEN` | secret (optional CLI) | Vercel CLI; Git integration may suffice alone |
| `VERCEL_ORG_ID` | secret (optional CLI) | Vercel team/org id |
| `VERCEL_PROJECT_ID` | secret (optional CLI) | Project `sales-os` id (see `VERCEL_DEPLOY.md`) |

#### Staging (optional / deferred — not required until staging environment exists)

| Name | Scope | Purpose |
|---|---|---|
| `RAILWAY_TOKEN` | secret (`staging`) | Railway CLI auth (when staging env created) |
| `RAILWAY_PROJECT_ID` | secret (`staging`) | Railway project |
| `RAILWAY_STAGING_SERVICE_ID` | secret (`staging`) | Backend service (staging) |
| `RAILWAY_STAGING_ENVIRONMENT_ID` | secret (`staging`) | Staging environment |
| `RAILWAY_STAGING_HEALTH_URL` | var or secret (`staging`) | Staging public health URL |

**Do not** provision `VPS_HOST` / `VPS_USER` / `VPS_SSH_KEY` / `STAGING_HOST` / `STAGING_USER` / `STAGING_SSH_KEY` for CI-09 close.  
**Do not** invent or require `RAILWAY_STAGING_*` while operating single-env.

**Rollback:** Restore prior workflow revisions from git history; re-enable staging push triggers only after staging exists + a program note. Prefer Railway dashboard redeploy / Vercel prior deployment for runtime rollback.

**CI-09 not CLOSED. No Production GO. CI GREEN not met.**
