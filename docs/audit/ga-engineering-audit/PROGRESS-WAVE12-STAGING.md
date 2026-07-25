# Progress — Wave 12 Staging (cloud) Deploy + Rollback

**Date:** 2026-07-22  
**Re-probe UTC:** `2026-07-22T16:32:00Z`  
**IDs:** PROD-W12-001 / PROD-W12-002 (staging tabletop acceptance)  
**Product:** SalesOS (AQLIYA)  
**Verdict:** **BLOCKED** — staging (cloud/VPS) **not accessible** (no real VPS / credentials / Environment / remote publish)  
**Prep:** **DONE** — workflow + compose aligned to SSH+GHCR; fill-in runbook + unblock checklist authored  
**Local virtual stand-in:** **DONE** — [PROGRESS-WAVE12-STAGING-VIRTUAL.md](./PROGRESS-WAVE12-STAGING-VIRTUAL.md) (does **not** close this cloud blocker)  
**Validation class (cloud):** **not validated** (probe only; no cloud deploy/rollback executed)  
**Production:** still **NO-GO** — no Production GO claim; no production kubectl / prod Alembic run

**Unblock in one sitting:** [PROGRESS-WAVE12-STAGING-UNBLOCK.md](./PROGRESS-WAVE12-STAGING-UNBLOCK.md)  
**Local virtual path (until VPS exists):** [PROGRESS-WAVE12-STAGING-VIRTUAL.md](./PROGRESS-WAVE12-STAGING-VIRTUAL.md)  
**Fill-in secrets/paths:** [runbooks/staging-fill-in.md](./runbooks/staging-fill-in.md)

---

## Staging accessible?

| Question | Answer |
|----------|--------|
| Staging (cloud/VPS) accessible from this workstation? | **N** |
| Staging (cloud) deploy + rollback tabletop executed? | **N** |
| Local virtual staging tabletop done? | **Y** — [PROGRESS-WAVE12-STAGING-VIRTUAL.md](./PROGRESS-WAVE12-STAGING-VIRTUAL.md) |
| Local (primary) tabletop already done? | **Y** — [PROGRESS-WAVE12-TABLETOP.md](./PROGRESS-WAVE12-TABLETOP.md) |

---

## What was probed (read-only / non-destructive) — re-probe `2026-07-22T16:32:00Z`

| Probe | Result |
|-------|--------|
| `gh auth` | Logged in as `ragheeda-boop` (scopes include `repo`) |
| Repo | `ragheeda-boop/SalesOS` — **default branch = `master`** |
| `develop` branch | **absent** on remote (API: no commit for ref `develop`) |
| `kubectl config get-contexts` | **0 contexts** (not required for SSH+Compose path) |
| `kubectl` current-context / `~/.kube/config` | **not set** / **absent** |
| Staging compose (workspace) | Present: `salesos/infra/staging/docker-compose.staging.yml` |
| Staging workflow (workspace) | Present: `salesos/.github/workflows/deploy-staging.yml` (local **modified**; jobs use `environment: staging`) |
| Staging workflow on `master` | **HTTP 404** — not published |
| Staging workflow on `develop` | **N/A** — branch missing |
| GitHub Environments | **`total_count`: 0** — Environment `staging` **does not exist** |
| GitHub Actions secrets (repo) | **empty list** — no `STAGING_HOST` / `STAGING_USER` / `STAGING_SSH_KEY` |
| Env `staging` secrets | **HTTP 404** (environment missing) |
| `salesos/.env.staging` | Exists; **4× `CHANGE_ME`**; no host/SSH; API URLs localhost-oriented |
| 48h soak PID `21856` | **Still running** — **not killed** (local soak; unrelated to cloud staging) |

**Evidence:** [evidence/wave12-staging/probe-2026-07-22T163200Z.json](./evidence/wave12-staging/probe-2026-07-22T163200Z.json)  
Prior: [evidence/wave12-staging/probe-2026-07-22T102534Z.json](./evidence/wave12-staging/probe-2026-07-22T102534Z.json)

---

## What ran / did not run

### Ran

- `gh auth status`, `gh repo view`, environments API, secret list (names / empty), workflow API  
- Content probe for `deploy-staging.yml` on `master` / `develop` / `main`  
- kubectl context / kubeconfig presence  
- Process check for soak PID `21856` (observe only)  
- Redacted `.env.staging` placeholder count (no secret values written to evidence)

### Did **not** run (blocked / policy)

- Any `kubectl apply` / production path  
- SSH deploy / `workflow_dispatch` of staging deploy  
- Creating or inventing secret values  
- Killing soak process  

---

## Exact missing pieces (BLOCKERS)

| # | Missing piece | Expected shape |
|---|---------------|----------------|
| 1 | **Staging VPS identity** | Real non-prod host → secret `STAGING_HOST` |
| 2 | **SSH credentials** | `STAGING_USER` + `STAGING_SSH_KEY` on Environment `staging` |
| 3 | **GitHub Environment `staging`** | Create exactly named `staging`; attach secrets above |
| 4 | **Publish `deploy-staging.yml`** | At SalesOS repo root `.github/workflows/` on Actions-visible branch (`master` today; also create/use `develop` if keeping push trigger) |
| 5 | **Host layout** | `/opt/salesos-staging` + filled `.env.staging` (no `CHANGE_ME`) + compose tree |
| 6 | **GHCR pull on VPS** | `docker login ghcr.io` for `ghcr.io/ragheeda-boop/salesos/*` |

**Staging deploy model in-repo:** SSH + Docker Compose on a VPS (not kubectl). Zero kube contexts does **not** unblock or block this path by itself.

**Remote nuance:** default branch is **`master`**; workflow `on.push.branches: [develop]` but **`develop` does not exist** on remote — publish must include branch strategy (create `develop` **or** adjust trigger / use `workflow_dispatch` from a branch that contains the file).

---

## Checklist — run when staging exists

Use this on a confirmed **non-prod** staging target only. Do **not** touch production clusters.

### A. Access prerequisites

- [ ] Confirm target is staging (hostname) — document in evidence  
- [ ] Create Environment `staging` + secrets `STAGING_HOST`, `STAGING_USER`, `STAGING_SSH_KEY`  
- [ ] Publish `deploy-staging.yml` so Actions UI shows **Deploy Staging** (not 404)  
- [ ] Place filled `.env.staging` on the staging host (never commit secrets)  
- [ ] Confirm GHCR pull works on staging host  

### B. Staging tabletop (deploy + rollback)

- [ ] Record current image tags/digests on host (rollback target)  
- [ ] Actions → Deploy Staging → `workflow_dispatch` (or push to configured branch)  
- [ ] Wait health: backend `/health` 200; frontend 200  
- [ ] Exercise rollback (workflow job or previous `IMAGE_TAG` compose up)  
- [ ] Re-verify health after rollback  
- [ ] Run `.\scripts\pre-deploy-gates.ps1` against staging API; attach log  
- [ ] Write evidence under `docs/audit/ga-engineering-audit/evidence/wave12-staging/`  
- [ ] Update this file **BLOCKED → DONE (staging tabletop)** with honest validation label  
- [ ] Update [GA_STATUS.md](./GA_STATUS.md) Wave 12 staging line  

### C. Still forbidden until GO gates clear

- [ ] Production kubectl apply / rollout  
- [ ] Production Alembic upgrade  
- [ ] Claiming Production GO  

---

## Honesty labels

| Claim | Status |
|-------|--------|
| Staging config inventory | **DONE** (this report; re-probed) |
| Staging prep (no credentials) | **DONE** — UNBLOCK + fill-in + workflow/compose alignment |
| Staging cloud tabletop | **BLOCKED** / **not validated** |
| Local compose tabletop | **DONE** (separate) — [PROGRESS-WAVE12-TABLETOP.md](./PROGRESS-WAVE12-TABLETOP.md) |
| Production cutover | **not executed** / **production no-go** |

---

## Scoreboard impact

Wave 12 staging **prep DONE**; staging **acceptance OPEN/BLOCKED** pending human credentials. Local gates + local tabletop do **not** satisfy staging tabletop. **NO-GO** unchanged. Re-probe confirms **no credential appearance** since morning probe.
