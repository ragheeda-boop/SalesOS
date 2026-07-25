# Staging Fill-In Runbook (credentials + publish path)

**ID:** PROD-W12-001 / PROD-W12-002 (staging unblock prep)  
**Status:** FILL-IN ONLY — no secrets committed; no SSH to unknown hosts; no production  
**Classification:** Ops prep; does **not** grant Production GO or staging tabletop DONE  
**Scoreboard:** [../GA_STATUS.md](../GA_STATUS.md) — **NO-GO**  
**Unblock checklist:** [../PROGRESS-WAVE12-STAGING-UNBLOCK.md](../PROGRESS-WAVE12-STAGING-UNBLOCK.md)  
**Probe status:** [../PROGRESS-WAVE12-STAGING.md](../PROGRESS-WAVE12-STAGING.md) — **BLOCKED** pending credentials

---

## Deploy model (do not confuse)

| Env | Path | Workflow | Orchestration |
|-----|------|----------|---------------|
| **Staging (this runbook)** | **SSH + Docker Compose on a VPS** | `salesos/.github/workflows/deploy-staging.yml` | Host dir `/opt/salesos-staging` + `infra/staging/docker-compose.staging.yml` |
| Production (out of scope) | Kubernetes | `deploy-production.yml` | `kubectl` / `infra/k8s/` |

**Kube vs SSH:** Staging acceptance for SalesOS in-repo is **SSH+Compose**, not kubectl. Zero kube contexts on a laptop does **not** block staging if VPS SSH secrets exist. Do **not** invent a staging kube cluster solely to unblock Wave 12.

---

## Exact GitHub secrets (names only — fill values in UI)

Create GitHub Environment **`staging`** on the SalesOS Actions repo (`ragheeda-boop/SalesOS` unless remapped).  
Prefer storing secrets **on Environment `staging`** (workflow jobs that SSH use `environment: staging`).

| Secret name | Purpose | Example shape (no real values here) |
|-------------|---------|--------------------------------------|
| `STAGING_HOST` | VPS hostname or IP reachable from GitHub-hosted runners | `staging.example.com` or `203.0.113.10` |
| `STAGING_USER` | SSH login user with access to `/opt/salesos-staging` | `deploy` / `ubuntu` |
| `STAGING_SSH_KEY` | Private key (PEM) matching host `authorized_keys` | Full private key body including `BEGIN`/`END` lines |
| `SLACK_WEBHOOK_URL` | Optional notify job | Incoming webhook URL — leave empty to skip |

**Not inventing:** Do not create placeholder secret *values*. Leave empty until a real non-prod VPS exists.

### Host-side (not GitHub secrets, but required)

| Item | Where | Notes |
|------|-------|-------|
| Filled `.env.staging` | `/opt/salesos-staging/.env.staging` | Copy from `salesos/.env.staging.example`; replace all `CHANGE_ME*`; **never commit** |
| Compose tree | `/opt/salesos-staging/infra/staging/docker-compose.staging.yml` | Sync/clone SalesOS tree so relative `env_file: ../../.env.staging` resolves |
| GHCR pull auth | On VPS: `docker login ghcr.io` | Package read for `ghcr.io/ragheeda-boop/salesos/{backend,frontend}` |
| Registry vars | In `.env.staging` or export on deploy | `REGISTRY=ghcr.io`, `IMAGE_NAMESPACE=ragheeda-boop/salesos`, `IMAGE_TAG=<short sha>` |

---

## GitHub Environment `staging`

| Field | Fill-in |
|-------|---------|
| Name | `staging` (exact) |
| Protection rules | Recommended: required reviewers for `workflow_dispatch`; wait timer optional |
| Deployment branches | Allow `develop` + manual `workflow_dispatch` from branches that contain the workflow file |
| Secrets | `STAGING_HOST`, `STAGING_USER`, `STAGING_SSH_KEY` (+ optional Slack) |
| Variables (optional) | Public staging API/FE base URLs for gates scripts |

Until this Environment exists, deploy jobs with `environment: staging` will fail closed (expected).

---

## Publish `deploy-staging.yml` (fixes default-branch 404)

**Fact (re-probe `2026-07-22T16:32:00Z`):** workflow exists in the Muhide/workspace tree at `salesos/.github/workflows/deploy-staging.yml` (local modified), but Actions API for `deploy-staging.yml` returned **HTTP 404**. Default branch is **`master`** (not `main`). Branch **`develop` does not exist** on `ragheeda-boop/SalesOS` — so the coded `push: branches: [develop]` trigger cannot fire until `develop` is created **or** the trigger is changed.

Human ops must:

1. Ensure the SalesOS GitHub repo root contains `.github/workflows/deploy-staging.yml` (same file as under `salesos/` in this monorepo workspace — note Muhide nests under `salesos/`; the Actions repo expects `.github/` at **repo root**).  
2. Publish onto an Actions-visible branch: at minimum **`master`** (default), and/or create **`develop`** to match the push trigger.  
3. Confirm: Actions → Workflows → **Deploy Staging** visible (no 404).  
4. Do **not** put secret values in the workflow YAML.

Triggers (as coded):

- `push` to `develop` (branch currently **missing** on remote)  
- `workflow_dispatch` with optional `version` image tag (requires the workflow file on the branch you dispatch from)

---

## Rollback digests from local tabletop (analogue only)

Local compose tabletop ([../PROGRESS-WAVE12-TABLETOP.md](../PROGRESS-WAVE12-TABLETOP.md)) recorded these **local** image IDs. Use them as the **pattern** for staging evidence; **re-record on the staging host** before any cloud tabletop (local digests are not GHCR tags).

| Role | Digest / ID | Notes |
|------|-------------|-------|
| Rollback target (pre-recreate backend) | `sha256:4d7efe7e6f7fb3d3a9348c3e71cdabcaac88f8ced26039fc11e9752fd8fae451` | `salesos-backend` local |
| Frontend (stable across local tabletop) | `sha256:ed834c955d44d2b3f34cdb6cec0c95a336b3a90700f2bf6bb354aa189707ebd1` | `salesos-frontend:local` |
| Post-recovery backend | `sha256:27ac6fc72b41f8bdc23937d44f39aa46e577e73e1e9d02d142607d4ee99569ed` | Not the rollback pin |

**Staging rollback pattern (SSH+Compose):**

```bash
cd /opt/salesos-staging
# Record BEFORE deploy:
docker compose -f infra/staging/docker-compose.staging.yml images
docker inspect --format='{{.Image}} {{.RepoDigests}}' "$(docker compose -f infra/staging/docker-compose.staging.yml ps -q backend)"

export REGISTRY=ghcr.io IMAGE_NAMESPACE=ragheeda-boop/salesos
export IMAGE_TAG=<PREVIOUS_SHORT_SHA>   # e.g. abc1234 from prior successful deploy
docker compose -f infra/staging/docker-compose.staging.yml pull backend frontend
docker compose -f infra/staging/docker-compose.staging.yml up -d backend frontend
```

Workflow auto-rollback job sets `IMAGE_TAG` from the pre-deploy tag captured in `deploy-staging` outputs (`previous_tag`). Prefer pinning **short SHA tags** pushed by the workflow, not the mutable `:staging` floating tag, when recording evidence.

---

## Pre-deploy gates against staging (after access exists)

```powershell
cd salesos
.\scripts\pre-deploy-gates.ps1
# Point health checks at staging API base URL once DNS/SSH tunnel is known
```

Attach log under `docs/audit/ga-engineering-audit/evidence/wave12-staging/`.

---

## Still forbidden

- Production kubectl / production Alembic  
- Committing `.env.staging` or SSH private keys  
- Claiming staging tabletop **DONE** or Production **GO** without evidence  
- SSH to hosts whose identity is unverified

---

## Honesty

| Claim | Status |
|-------|--------|
| Fill-in names + publish steps documented | **DONE** (this file) |
| Secrets values present | **Human must supply** |
| Staging cloud tabletop | **BLOCKED** until secrets + host + published workflow |
| Production | **NO-GO** |
