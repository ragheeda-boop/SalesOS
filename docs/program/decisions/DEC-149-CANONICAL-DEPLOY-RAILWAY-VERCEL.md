# DEC-149 — Canonical deploy topology: Backend → Railway; Frontend → Vercel

> **Status:** **Accepted** — User governance ruling (2026-08-02) + Architecture Validation hybrid verdict; program DEC for Phase 0 deploy topology (same class as DEC-104 / DEC-016 authorization)  
> **Date:** 2026-08-02  
> **Board:** Chief Architect / ARB + Execution Orchestrator (SalesOS / AQLIYA) — program/governance scribe land  
> **Story / risk:** CI-09 / Phase 0 criterion **3.11** / **R-17** (SSH/VPS leg)  
> **Authority:** Architecture Validation session (hybrid) · user governance ruling · EXEC-ARCHITECTURE-PRODUCT-REVIEW · GA_STATUS · DEC-016 / DEC-120 · deploy configs  
> **Amends (consequence):** CI-09 reframed from ops VPS-secret provision to **BLOCKED BY GOVERNANCE**; does **not** close CI-09 or mark it obsolete  
> **Out of scope this land:** Editing `.github/workflows/*` · provisioning `VPS_*` / unused secrets · inventing ARB **4.1/4.8** PASS · Phase 0 exit · CI GREEN · Production GO · DEC-085

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
| Workflow migration (`deploy.yml`, `deploy-staging.yml`, related) | **Deferred** until assigned to Backend/DevOps **after** this DEC (this land does **not** modify workflows) |
| CI-09 / **3.11** | Remains **OPEN** — status **BLOCKED BY GOVERNANCE** (not CLOSED, not obsolete) |
| Validation label | **docs / light validated** (encodes Architecture Validation hybrid evidence; this land does **not** re-probe live deploys) |

**Honesty:** Live/audit topology (Railway + Vercel) and GitHub Actions deploy paths (still VPS/SSH, plus K8s alternate) were **hybrid**. This DEC resolves the **intended canonical target**. Implementation of workflow alignment is a follow-on assignment, not automatic close of CI-09.

---

## 2. Evidence pointers (Architecture Impact)

Cross-link: Architecture Validation session conclusion — verdict **hybrid** (Backend→Railway + Frontend→Vercel live/intended; GHA still VPS/SSH). Parent transcript: [Architecture Validation hybrid](6baea6ce-bf54-441d-92bb-961d9b609cc3). Evidence agent: [Deploy target vs CI-09](23ee1e07-fb76-48d0-8860-9d463b22a911).

| Surface | Path / pointer |
|---|---|
| Root Railway | `railway.json` (`Dockerfile.railway`, uvicorn, `/health`) |
| SalesOS Railway | `salesos/railway.json` (backend Dockerfile, alembic preDeploy) |
| Vercel FE | `salesos/frontend/vercel.json` |
| Vercel runbook | `salesos/frontend/docs/VERCEL_DEPLOY.md` |
| Exec architecture | `docs/audit/ga-engineering-audit/EXEC-ARCHITECTURE-PRODUCT-REVIEW-2026-07-30.md` — Railway as live deploy target |
| GA scoreboard | `docs/audit/ga-engineering-audit/GA_STATUS.md` — Railway BE + Vercel FE live |
| Railway R-14 | DEC-016 / DEC-120 — Railway Postgres / `APP_POSTGRES_*` path |
| Still VPS-encoded (unchanged this land) | `.github/workflows/deploy.yml` (`VPS_*`); `.github/workflows/deploy-staging.yml` (`STAGING_*`) |

---

## 3. CI-09 / criterion 3.11 framing (mandatory)

```text
CI-09
Status: BLOCKED BY GOVERNANCE
Reason: Current criterion assumes VPS deployment.
Project deployment architecture is Railway + Vercel.
Criterion requires formal governance update before implementation.
```

| Field | Value |
|---|---|
| Queue | **Governance Queue** (moved off Ops secret-provision queue) |
| Owner | **Chief Architect / ARB** |
| Dependency | **Deployment Decision** — this DEC (**Accepted**) names the target |
| Next action | **Assign workflow migration** to Backend/DevOps (Railway + Vercel); revise **3.11** AC evidence to match; do **not** provision unused `VPS_*` |
| Explicit non-actions | Do **not** close CI-09; do **not** mark obsolete; do **not** modify workflows in this land |

---

## 4. Consequence

1. Canonical deploy = **Railway (backend) + Vercel (frontend)**.  
2. CI-09 / **3.11** → **BLOCKED BY GOVERNANCE** on board, checklist, DAG; R-17 SSH/VPS leg noted as **governance mismatch**, not “missing ops secrets to invent.”  
3. Workflow migration remains **READY only after assignment** — no `.github/workflows/*` edits under this DEC.  
4. CI-08 (GHCR) remains a **separate** ops blocker if GHCR stays on a chosen promote path (DEC-104).  
5. Phase 0 remains **NO-GO**. **CI GREEN not met.** **Production GO not claimed.** DEC-085 untouched.

---

## 5. Records touched this land

| File | Change |
|---|---|
| This DEC | Canonical topology Accepted |
| `PHASE_0_EXIT_CHECKLIST.md` | **3.11** / Remaining-9 / Blocked Items → governance framing |
| `SPRINT_05_DELIVERY_BOARD.md` | CI-09 → Governance Queue / BLOCKED BY GOVERNANCE |
| `EXECUTION_DAG.md` | CI-09 block class → governance |
| `RISK_REGISTER.md` | R-17 SSH/VPS leg → governance note |
| `DECISION_LOG.md` | DEC-149 entry |

**Workflows unchanged. CI-09 not CLOSED. No VPS secrets requested.**
