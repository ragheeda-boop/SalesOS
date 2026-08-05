# Railway Deployment Config — LEGACY CANDIDATE (root copy)

> **This notice does not modify either Railway configuration file.** Both remain exactly as they were. This is a documentation marker only.

**Classification:** Legacy candidate — one of two conflicting configs, active one unconfirmed.
**Authority:** [`ADR-100: Repository Canonicalization`](../adr/0100-repository-canonicalization.md), Gap Analysis §5; `docs/audit/REPOSITORY_HEALTH_GATE_2026-08-05.md` §5, §7.
**Marked:** 2026-08-05 (ADR-100 Phase 3 — Legacy Isolation)

## The conflict

| | Root `railway.json` + `Dockerfile.railway` | `salesos/railway.json` |
|---|---|---|
| Build source | `Dockerfile.railway` (root) — `COPY`s source from `salesos/backend/...` into a fresh build context | `salesos/backend/Dockerfile` directly |
| Service variants | Single service only | Handles `celery-worker` and `celery-beat` via `$RAILWAY_SERVICE_NAME` branching |
| Pre-deploy step | None | `alembic upgrade head` |
| Restart policy | `ON_FAILURE`, max 3 retries | `ON_FAILURE`, max 10 retries |

These are materially different deploy definitions for what should be the same target. One of them is what Railway's dashboard actually builds from; the other is dead configuration that will silently drift out of sync with the real deployment.

## Why nothing has been deleted

**This cannot be determined by reading the repository.** Railway's build-source configuration lives in Railway's dashboard (out-of-repo state), not in git. Deleting the wrong file would not immediately break anything visible in CI, but would leave the *actually deployed* config unmaintained going forward, and deleting the *right* file without confirming first would be irreversible guesswork on a production deployment path.

## What happens next

See the **Pending Removal Register** in [`docs/architecture/LEGACY_ISOLATION_REGISTER.md`](../architecture/LEGACY_ISOLATION_REGISTER.md) for the exact unblocking condition (confirm the live Railway build source) and next action once confirmed.

**Until then: treat root `railway.json` and `Dockerfile.railway` as read-only legacy candidates. Do not edit, delete, or rely on either without first checking the Railway dashboard.**
