# Progress — Wave 12 Deploy / Rollback TABLETOP (LOCAL)

**Date:** 2026-07-22  
**IDs:** PROD-W12-001 / PROD-W12-002 (tabletop acceptance prep)  
**Product:** SalesOS — local Docker Compose **NON-PROD only**  
**Runbook walked:** [runbooks/deploy-rollback.md](./runbooks/deploy-rollback.md)  
**Validation class:** **light validated** (local dry-run + recreate)  
**Production:** still **NO-GO** — no kubectl, no cloud staging, no Production GO claim

---

## Verdict

| Result | Detail |
|--------|--------|
| Tabletop walkthrough | **DONE** (docs + dry commands against local compose) |
| Safe local recreate | **EXECUTED** (`docker compose up -d --force-recreate --no-build backend frontend`) |
| First recreate attempt | **PARTIAL FAIL** — Kafka dependency unhealthy blocked backend/frontend start |
| Recovery | **DONE** — `--no-deps` / `docker start` after backend healthy |
| Post-recovery health | Containers **healthy**; host HTTP probes intermittently timed out (see notes) |
| Rollback model exercised | **DOCUMENTED** — pin previous image tag/digest (local analogue of `kubectl set image` / `rollout undo`) |
| Staging / production cutover | **NOT executed** |

---

## Checklist execution notes (deploy-rollback.md)

### Pre-deploy gates

| Step | Outcome |
|------|---------|
| `.\scripts\pre-deploy-gates.ps1` | **FAIL (parser)** — encoding/mojibake on line ~79 (`" — "` string) prevented script parse. Logged under evidence. Manual substitutes used: `/health`, compose status, image IDs. |
| Alembic head | Tabletop-day SQL `alembic_version=0039` (CLI hang quirk — Wave 11). **Current head = `0040`** after graph_edges fix — [PROGRESS-WAVE12-PROD-MIGRATE-PREP.md](./PROGRESS-WAVE12-PROD-MIGRATE-PREP.md) |
| Feature flags | From prior soak: `demo_mode=False`, `feature_ai_copilot=False` |
| Production kubectl | **Skipped** (NO-GO policy) |

### Deploy dry-run (local compose)

| Step | Command / action | Outcome |
|------|------------------|---------|
| Record rollback target | `docker inspect` backend/frontend Image IDs | **DONE** — see Pre-image IDs below |
| Recreate app services | `docker compose up -d --force-recreate --no-build backend frontend` | Exit **1** — `salesos-kafka-1` unhealthy → dependency failed |
| Cascaded deps | Compose also recreated redis / neo4j / kafka | Neo4j briefly unhealthy; Kafka slow to healthy |
| Wait healthy | Poll `State.Health` 3 min | Backend/frontend remained **Created** (not started) after dep fail |
| Recovery start | `docker compose up -d --no-deps --no-build backend frontend` then `docker start salesos-frontend-1` | Backend reached **healthy**; frontend **healthy** |
| Verify health | Container healthchecks green; host `Invoke-WebRequest` to `:8000`/`:3000` | **Mixed** — container healthy; one post-recovery probe window timed out (stack load) |

### Rollback dry-run (commands only — tags unchanged intent)

Local analogue of production rollback (previous image tag/digest):

```powershell
# Recorded previous (pre-tabletop) image IDs — rollback target
# backend:  sha256:4d7efe7e6f7fb3d3a9348c3e71cdabcaac88f8ced26039fc11e9752fd8fae451  (salesos-backend)
# frontend: sha256:ed834c955d44d2b3f34cdb6cec0c95a336b3a90700f2bf6bb354aa189707ebd1 (salesos-frontend:local)

# Local compose rollback pattern (dry — do not require rebuild):
docker tag 4d7efe7e6f7f salesos-backend:rollback-prev
# then set compose image / override and:
docker compose up -d --force-recreate --no-build --no-deps backend

# Prefer --no-deps when Kafka/Neo4j are flaky after cascade recreate.
```

K8s production analogue (**DO NOT RUN while GA_STATUS = NO-GO**):

```bash
kubectl rollout undo deployment/backend -n salesos
kubectl rollout undo deployment/frontend -n salesos
# or: kubectl set image deployment/backend backend=ghcr.io/.../backend:<PREV_SHA> -n salesos
```

### Tabletop checklist (from runbook)

| Item | Status |
|------|--------|
| Dry-run deploy + rollback on non-prod | **DONE** (local compose) |
| Who can approve `workflow_dispatch` production | **UNVERIFIED** (org process) |
| On-call primary/secondary named for T-0 | **UNVERIFIED** |
| `pre-deploy-gates.ps1` against staging + attach log | **OPEN** — script parse broken locally; staging host **UNVERIFIED** |

---

## Image identity evidence

| Phase | Backend | Frontend |
|-------|---------|----------|
| Pre-recreate | `salesos-backend` @ `sha256:4d7efe7e6f7f…fae451` | `salesos-frontend:local` @ `sha256:ed834c955d44…07ebd1` |
| Post-recovery | `salesos-backend` @ `sha256:27ac6fc72b41…99569ed` | `salesos-frontend:local` @ `sha256:ed834c955d44…07ebd1` (unchanged) |

**Note:** Backend Image ID changed across recreate/recovery despite `--no-build` intent (compose resolved a different local `salesos-backend` artifact). Frontend digest stable. Rollback documentation uses the **pre-recreate** IDs as the previous-tag target.

---

## Evidence paths

| Path | Contents |
|------|----------|
| `docs/audit/ga-engineering-audit/evidence/wave12-tabletop/` | pre/post JSON, recreate.log, pre-deploy-gates.log, tabletop-complete JSON |
| This file | Execution notes |

---

## Lessons for Wave 12 acceptance

1. Prefer **`--no-deps`** when tabletop-recreating only backend/frontend on a busy local stack — cascading Kafka/Neo4j recreate caused the failure mode.  
2. Fix `pre-deploy-gates.ps1` UTF-8/emoji string encoding before relying on it in CI/tabletop.  
3. Local tabletop ≠ staging tabletop. Staging host / GH Environment still **UNVERIFIED**.  
4. Still **NO-GO** for production deploy.

---

## Honesty labels

| Claim | Status |
|-------|--------|
| Local deploy/rollback tabletop | **light validated** |
| Staging tabletop | **not validated** |
| Production cutover | **not executed** / **production no-go** |
