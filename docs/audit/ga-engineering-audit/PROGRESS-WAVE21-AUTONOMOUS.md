# Progress — Wave 21 (2026-07-29 follow-up)

## Mission stance
Close remaining **reachable operational-engineering** items that don’t require human credentials / Google consent.

## What’s confirmed (this follow-up)
- **Prod Neo4j** is connected (`/health graph=connected`) via Railway `neo4j-prod` deploy `6163f9e3` and SalesOS prod deploy `b1973315`.
- **FE Vercel root-dir**: repo build root is `salesos/frontend` (Vercel deployments READY; see existing `VERCEL_DEPLOY.md`).
- **Railway Celery worker + beat** healthy in **staging and production**.
- **`worker_health_ping` asyncio residual closed** (Wave 21 follow-up) — staging + prod logs show `status=ok`, `database=connected` (no `get_event_loop` / missing-`func` errors).
- **Orphan Celery copy services removed** from production (no-deployment leftovers only).

## Repo / config changes (Celery)
- `salesos/backend/app/railway_celery_service.py` — Celery wrapper that serves `/health` while running worker/beat.
- `salesos/backend/railway.json` — Dockerfile build; substring match for `*celery-worker*` / `*celery-beat*` / `*celery*` so Railway copy-named services still skip `init_db` and start Celery (not uvicorn).
- `salesos/backend/domains/employee/tasks.py` — `_run_async` via `asyncio.run`; all sync Celery wrappers use it; import `sqlalchemy.func` for `_health_ping`.
- `salesos/backend/app/modules/communication_hub/tasks.py` — `_run` simplified to `asyncio.run` (same Celery sync bridge).
- `salesos/backend/domains/employee/tests/test_tasks.py` — focused tests for `_run_async` + health-ping wrapper.
- Deploy pattern: upload from `salesos/backend` with `--path-as-root` so `Dockerfile` is at archive root.

## Evidence — staging Celery
| Service | Deploy ID | Status | Runtime proof |
|---------|-----------|--------|---------------|
| `celery-worker` | `7314beb7-9625-43d4-bc86-896bfddb6f99` | **SUCCESS** | `worker_health_ping` → `{'status': 'ok', 'database': 'connected'}` (11:04:47Z) |
| `celery-beat` | `c4718775-295f-4999-98b2-191889b81dc7` | **SUCCESS** | beat schedule unchanged; emits health ping |

Prior Wave 21 worker IDs (`08161c0c`, `81dff2ac`) superseded by asyncio/`func` fix deploy.

## Evidence — production Celery
Railway production instances remain copy-named (serviceDuplicate):
- `celery-worker (Copy 3091)` service id `90499aec-e622-4c19-a5ae-e984e19e071d`
- `celery-beat (Copy 5338)` service id `485f439a-2134-4f06-90ed-d520aac05205`

| Service | Deploy ID | Status | Runtime proof |
|---------|-----------|--------|---------------|
| worker copy | `55ac43c3-d125-4c03-8693-eb1f93993389` | **SUCCESS** | `worker_health_ping` → `{'status': 'ok', 'database': 'connected'}` (11:06:54Z) |
| beat copy | `ad02c7fa-6b8d-4e2e-847f-ea6c8d61d8d5` | **SUCCESS** | prior beat ready; schedule unchanged |

## Orphan Celery copy cleanup (production)
**Kept (healthy, running):**
- `celery-worker (Copy 3091)` — active prod worker
- `celery-beat (Copy 5338)` — active prod beat

**Removed (production env, zero deployments / unused duplicates):**
- `celery-worker (Copy)` (`5a3587e9…`)
- `celery-worker (Copy 920)` (`d148189b…`)
- `celery-beat (Copy)` (`58330177…`)
- `celery-beat (Copy 3240)` (`c0b20681…`)

**Staging:** no orphan copies (canonical `celery-worker` / `celery-beat` only).

## Residual operational items from this ticket
**None (eng).** Asyncio health-ping bug + orphan copy hygiene closed with Railway log evidence.

## Human / approval-gated (unchanged)
- Soak claim, Google OAuth consent, interactive passwords, SIGN_HERE, SSRF pentest, DR/PITR — still **NO-GO**.
- No Google OAuth / user-password work attempted.

## Validation
- **light validated** via Railway deployment status + deploy logs (staging + production) including successful `worker_health_ping`.
- Focused unit tests added; host pytest **not run** (no local Celery/Poetry path; low-load).
- Not claiming Production GA GO.
