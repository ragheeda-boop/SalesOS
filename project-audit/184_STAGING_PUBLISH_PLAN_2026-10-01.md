# 184 — Staging publish plan (2026-10-01)

**Measured, not assumed.** Production stays **NOT APPROVED** until the steps below have their own evidence. This file is the execution list for the 8-hour loop. It does not close G2–G7 or G9–G16.

## What is already true

| Check | Evidence |
|---|---|
| Staging API image | `GET /version` on `https://salesos-staging.up.railway.app` returned `backend_commit=a200906d52b5dc269855b1896f45589c2ad2981b` |
| Schema | Same response: `schema_version=c3d4e5f6a7b9` (current Alembic head) |
| Process | `GET /health` returned `status=ok`, `database=connected`, fresh uptime after the successful deploy |
| Org-registration route | Empty `POST /api/v1/identity/org-registration-requests` returned 422 |
| Volume | `salesos-volume` mounted on SalesOS at `/data/jwks` |
| Postgres backups | Daily schedule already enabled on the staging Postgres service. Do not click Restore |
| Production environment | Not entered. Production database `salesos` not written |
| CORS | `OPTIONS` with `Origin: https://example.vercel.app` returned 400. `Origin: https://sales-os-jet.vercel.app` returned 200 and `access-control-allow-origin: https://sales-os-jet.vercel.app` |

## What is not true yet

| Gap | Evidence |
|---|---|
| Celery worker | Active deploy is `a200906d`, status Deployment successful, process `celery@… ready`. Connecting the branch made the dashboard follow `railway.json`, so that deploy ran `alembic upgrade head` (log: `Context impl PostgresqlImpl`, then the container stopped and Celery started). `railway.json` now skips that command when `RAILWAY_SERVICE_NAME` contains `celery` |
| Celery beat | Active deploy is the same `a200906d` commit, Deployment successful, about 2 minutes before the worker. Same `railway.json` pre-deploy applies |
| Frontend | Live UI is `https://sales-os-jet.vercel.app/login` (HTTP 200). `https://salesos-staging.vercel.app` is `DEPLOYMENT_NOT_FOUND`. The login HTML preconnects to `https://salesos-production-96c0.up.railway.app`. Browser API calls are same-origin and Next rewrites them to that baked `NEXT_PUBLIC_API_URL`. Do not retarget this production frontend at staging |
| Staging UI | There is no separate staging frontend deployment. A staging Vercel project with `NEXT_PUBLIC_API_URL=https://salesos-staging.up.railway.app` is still required before a public staging seller loop |
| Platform owner on staging | Local pilot has `ragheed@outlook.sa`. Staging was not queried for users. Do not invent the flag |
| Catalog | 296,746 companies stay in `salesos_test`. `md_global_companies` has no tenant RLS |
| External gates | PDPL (hosting outside KSA), SOC2, Google/Microsoft/GitHub SSO, Stripe, production AI provider. Code does not close these |

## Deploy order

1. Staging API stays on schema `c3d4e5f6a7b9`. The next push of `railway.json` redeploys it because auto-deploy is on. Its pre-deploy remains `alembic upgrade head` (already at head).
2. Worker and beat are Online on `a200906d`. The follow-up `railway.json` change skips Alembic when the service name contains `celery`, then those two services redeploy. Confirm deploy logs contain `Skipping init_db for celery background service` and both stay Online.
3. Do not change `NEXT_PUBLIC_API_URL` on `sales-os-jet.vercel.app`. That build talks to the production API. A separate staging frontend is the next host.
4. Staging already echoes `access-control-allow-origin` for `https://sales-os-jet.vercel.app`. Do not add a wildcard. Add the staging frontend origin only after that host exists.
5. Browser smoke on the frontend: login page renders, unauthenticated `/v3` redirects to login, register without an approval returns the owner-approval error. No password typed into the tool transcript.
6. After an account `ragheed@outlook.sa` exists on the staging database, set `is_platform_owner=true` for that row only.
7. Staging seller loop: owner approves one organization, manager registers, invite returns a one-time password to the owner in chat only, tenant admin cannot open `/owner/login`.
8. Production environment stays untouched until steps 2–7 pass and the owner asks for that environment.

## Out of this loop

- Merge to `master`
- Load the 296,746 catalog
- `feature_ai_copilot=true`
- History rewrite of the HS256 token in `3de118a5`
- Click Restore, New Environment, Disconnect, or Delete
