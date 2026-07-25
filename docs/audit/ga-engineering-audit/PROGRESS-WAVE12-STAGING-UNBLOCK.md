# Progress — Wave 12 Staging UNBLOCK (human ops, one sitting)

**Date:** 2026-07-22  
**Re-probe UTC:** `2026-07-22T16:32:00Z` — still **BLOCKED** (no Env/secrets; workflow not on `master`; `develop` absent)  
**IDs:** PROD-W12-001 / PROD-W12-002  
**Goal:** Unblock cloud staging tabletop **without** inventing secrets or touching production  
**Prep status:** **DONE** (docs + workflow/compose alignment in workspace)  
**Runtime status:** still **BLOCKED** until items below are filled by a human with credentials  
**Production:** still **NO-GO**

**Fill-in detail:** [runbooks/staging-fill-in.md](./runbooks/staging-fill-in.md)  
**Probe:** [PROGRESS-WAVE12-STAGING.md](./PROGRESS-WAVE12-STAGING.md)  
**Local analogue:** [PROGRESS-WAVE12-TABLETOP.md](./PROGRESS-WAVE12-TABLETOP.md)  
**Local virtual staging (ports `:8001`/`:3002`, not cloud):** [PROGRESS-WAVE12-STAGING-VIRTUAL.md](./PROGRESS-WAVE12-STAGING-VIRTUAL.md) — **DONE** as stand-in; cloud remains **BLOCKED**

---

## One-sitting checklist (human)

Work top-to-bottom. Skip kube entirely unless you deliberately choose a K8s staging cluster (not the in-repo default).

### 0. Confirm path (2 min)

- [ ] Staging model = **SSH + Compose VPS** (`deploy-staging.yml` → `/opt/salesos-staging`)
- [ ] Production K8s path = **out of scope** for this sitting
- [ ] No production hosts, kubecontexts, or Alembic upgrades

### 1. Publish workflow (10–15 min)

- [ ] Ensure `.github/workflows/deploy-staging.yml` exists at the **SalesOS GitHub repo root** (copy from workspace `salesos/.github/workflows/deploy-staging.yml` if needed)
- [ ] Merge to `develop` (push trigger) and/or the branch used for `workflow_dispatch`
- [ ] Verify Actions UI shows **Deploy Staging** (not 404 on default/`develop`)
- [ ] Confirm deploy/health/smoke/rollback jobs declare `environment: staging`

### 2. GitHub Environment + secrets (10 min)

- [ ] Create Environment named exactly `staging`
- [ ] Add Environment secrets (values only in GitHub UI — never in git):

  | Name | Value from |
  |------|------------|
  | `STAGING_HOST` | Real staging VPS hostname/IP |
  | `STAGING_USER` | SSH user |
  | `STAGING_SSH_KEY` | Deploy private key |
  | `SLACK_WEBHOOK_URL` | Optional |

- [ ] Optional: protection rules (required reviewer) on Environment `staging`

### 3. Staging VPS layout (15–20 min)

- [ ] Provision or identify **non-prod** VPS only
- [ ] Layout:

  ```text
  /opt/salesos-staging/
    .env.staging                 # filled; mode 600; not in git
    infra/staging/docker-compose.staging.yml
    (rest of SalesOS tree as needed for relative paths)
  ```

- [ ] Copy `salesos/.env.staging.example` → host `.env.staging`; replace every `CHANGE_ME*`
- [ ] Set public URLs / `DOMAIN` away from localhost when DNS exists
- [ ] Keep `FEATURE_AI_COPILOT=false` / `DEMO_MODE=false` unless explicitly approved
- [ ] `docker login ghcr.io` on host (package read for `ragheeda-boop/salesos/*`)
- [ ] Confirm compose resolves images:

  `ghcr.io/ragheeda-boop/salesos/{backend,frontend}:${IMAGE_TAG}`

### 4. Smoke deploy + rollback tabletop (20–30 min)

- [ ] Record current backend/frontend tags **and digests** on host (evidence JSON)
- [ ] Actions → Deploy Staging → `workflow_dispatch` (or push to `develop`)
- [ ] Wait health: backend `/health` 200; frontend 200 (via SSH localhost or staging URL)
- [ ] Force rollback path: either failing smoke (auto job) **or** manual previous `IMAGE_TAG` compose up
- [ ] Re-check health after rollback
- [ ] Run `salesos/scripts/pre-deploy-gates.ps1` against staging API; save log
- [ ] Write evidence under `docs/audit/ga-engineering-audit/evidence/wave12-staging/`
- [ ] Flip [PROGRESS-WAVE12-STAGING.md](./PROGRESS-WAVE12-STAGING.md) **BLOCKED → DONE (staging tabletop)** with honest validation label
- [ ] Update [GA_STATUS.md](./GA_STATUS.md) Wave 12 staging line

### 5. Explicit non-goals this sitting

- [ ] ~~kubectl apply / rollout on production~~
- [ ] ~~Production Alembic~~
- [ ] ~~Commit `.env.staging` / SSH keys~~
- [ ] ~~Claim Production GO~~

---

## Local rollback digests (reference only)

From local tabletop — **re-record on staging**; do not treat as GHCR tags:

| Pin | Digest |
|-----|--------|
| Backend rollback target | `sha256:4d7efe7e6f7fb3d3a9348c3e71cdabcaac88f8ced26039fc11e9752fd8fae451` |
| Frontend local | `sha256:ed834c955d44d2b3f34cdb6cec0c95a336b3a90700f2bf6bb354aa189707ebd1` |

---

## What human must supply (summary)

1. Staging VPS identity (`STAGING_HOST` + SSH user/key)  
2. GitHub Environment `staging` + secret **values**  
3. Filled host `.env.staging` (passwords, JWT, URLs)  
4. GHCR pull auth on the VPS  
5. Merge/publish of `deploy-staging.yml` to the Actions-visible branch  

Until those five exist: staging cloud remains **BLOCKED**. Prep alone ≠ tabletop.

---

## Honesty labels

| Claim | Status |
|-------|--------|
| Unblock checklist authored | **DONE** |
| Workspace workflow + compose aligned to SSH/GHCR | **DONE** (pending human merge to remote) |
| Staging cloud tabletop | **BLOCKED** / **not validated** |
| Production | **NO-GO** |
