# DEC-149 — Canonical deploy topology: Backend → Railway; Frontend → Vercel

> **Status:** **Accepted** — User governance ruling (2026-08-02) + Architecture Validation hybrid verdict; program DEC for Phase 0 deploy topology (same class as DEC-104 / DEC-016 authorization)  
> **Date:** 2026-08-02  
> **Board:** Chief Architect / ARB + Execution Orchestrator (SalesOS / AQLIYA) — program/governance scribe land  
> **Story / risk:** CI-09 / Phase 0 criterion **3.11** / **R-17** (SSH/VPS leg)  
> **Authority:** Architecture Validation session (hybrid) · user governance ruling · EXEC-ARCHITECTURE-PRODUCT-REVIEW · GA_STATUS · DEC-016 / DEC-120 · deploy configs  
> **Amends (consequence):** CI-09 reframed from ops VPS-secret provision; governance land = **BLOCKED BY GOVERNANCE**; follow-on workflow land = **READY_FOR_REVIEW** — does **not** close CI-09  
> **Out of scope (governance land):** Editing `.github/workflows/*` · provisioning secret *values* · inventing ARB **4.1/4.8** PASS · Phase 0 exit · CI GREEN · Production GO · DEC-085  
> **Follow-on (2026-08-02, devops/ci-worker):** Workflow migration **implemented** — see §6. CI-09 / **3.11** → **READY_FOR_REVIEW** (not CLOSED).

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
| CI-09 / **3.11** | Remains **OPEN** — status **READY_FOR_REVIEW** (implementation landed; **not CLOSED**; Validation still required) |
| Validation label | **docs / light validated** (workflows aligned to DEC; live deploy field-verify **PENDING** Validation — do not claim CI GREEN / Production GO) |

**Honesty:** Governance land resolved the **intended canonical target**. Follow-on workflow land makes Railway+Vercel the **active GHA path**. CI-09 / **3.11** close only after Validation — **not** automatic.

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
| Active GHA (post migration) | `.github/workflows/deploy.yml` (Railway+Vercel); `.github/workflows/deploy-staging.yml` (Railway+Vercel) |
| Quarantined | `.github/workflows/deploy-production.yml` (K8s — DEC-149) |

---

## 3. CI-09 / criterion 3.11 framing (mandatory)

```text
CI-09
Status: READY_FOR_REVIEW
Reason: DEC-149 Accepted; workflow migration landed (Railway BE + Vercel FE).
Not CLOSED — pending Validation field-verify of deploy runs + required secret/var names provisioned.
Do not provision unused VPS_*.
```

| Field | Value |
|---|---|
| Queue | **Validation Queue** (was Governance Queue until DEC Accepted + workflows landed) |
| Owner | **Validation** (close gate); DevOps owns secret-name provision |
| Dependency | DEC-149 **Accepted** + workflow migration **landed** |
| Next action | Validation: field-verify Deploy Production / Staging on Railway+Vercel path; ops provision secret **names** in §6 (values out-of-band). Do **not** invent `VPS_*` |
| Explicit non-actions | Do **not** close CI-09 without Validation; do **not** mark obsolete; do **not** claim CI GREEN / Production GO |

---

## 4. Consequence

1. Canonical deploy = **Railway (backend) + Vercel (frontend)**.  
2. CI-09 / **3.11** → **READY_FOR_REVIEW** (implementation landed; **not CLOSED**).  
3. Active GHA path = `deploy.yml` / `deploy-staging.yml` (Railway+Vercel). K8s `deploy-production.yml` **quarantined**.  
4. CI-08 (GHCR) remains a **separate** ops blocker for Stage 6 publish (DEC-104); Railway `railway up` path does **not** require GHCR.  
5. Phase 0 remains **NO-GO**. **CI GREEN not met.** **Production GO not claimed.** DEC-085 untouched.

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
| `deploy.yml` | **Active prod path:** Railway `railway up` (cwd `salesos/`) + public `/health` gate; FE = Vercel Git (primary) + optional CLI |
| `deploy-staging.yml` | **Active staging path:** Railway staging `railway up` + health; FE = Vercel Git / optional CLI; **no** GHCR build/push, **no** SSH |
| `deploy-production.yml` | **Quarantined** (K8s) — tag push removed; `workflow_dispatch` requires `CONFIRM-K8S-QUARANTINE` |
| `ci.yml` Stage 6 | **Unchanged** (GHCR publish orthogonal — CI-08) |

### Required GitHub secret / variable **names** (values out-of-band — do not invent)

| Name | Scope | Purpose |
|---|---|---|
| `RAILWAY_TOKEN` | secret (`production` + `staging` envs) | Railway CLI auth |
| `RAILWAY_PROJECT_ID` | secret | Railway project |
| `RAILWAY_SERVICE_ID` | secret (`production`) | Backend service (prod) |
| `RAILWAY_ENVIRONMENT_ID` | secret (`production`) | Production environment |
| `RAILWAY_STAGING_SERVICE_ID` | secret (`staging`) | Backend service (staging) |
| `RAILWAY_STAGING_ENVIRONMENT_ID` | secret (`staging`) | Staging environment |
| `RAILWAY_HEALTH_URL` | var or secret (`production`) | Public backend base or `/health` URL |
| `RAILWAY_STAGING_HEALTH_URL` | var or secret (`staging`) | Staging public health URL |
| `VERCEL_TOKEN` | secret (optional CLI) | Vercel CLI; Git integration may suffice alone |
| `VERCEL_ORG_ID` | secret (optional CLI) | Vercel team/org id |
| `VERCEL_PROJECT_ID` | secret (optional CLI) | Project `sales-os` id (see `VERCEL_DEPLOY.md`) |

**Do not** provision `VPS_HOST` / `VPS_USER` / `VPS_SSH_KEY` / `STAGING_HOST` / `STAGING_USER` / `STAGING_SSH_KEY` for CI-09 close.

**Rollback:** Restore prior VPS/SSH workflow revisions from git history; re-enable K8s only with a superseding DEC. Prefer Railway dashboard redeploy / Vercel prior deployment for runtime rollback.

**CI-09 not CLOSED. No Production GO. CI GREEN not met.**
