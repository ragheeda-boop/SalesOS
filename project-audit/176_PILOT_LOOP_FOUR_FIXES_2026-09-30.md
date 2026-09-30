# 176 — Pilot loop: four live fixes on the seller path (2026-09-30)

**Scope:** make the seller loop work end to end against a disposable stack. Production was not touched.
**Stack:** containers `pilot-pg`, `pilot-redis`, `pilot-api` (port 8010) and `pilot-test` on network `pilot-net`, all from image `salesos-pilot-backend:local`, Alembic head `a1b2c3d4e5f7`. The stack was torn down after verification.
**Classification:** pilot-ready with conditions. Production remains **NOT APPROVED**.

## 1. Fixes (committed and pushed)

| Commit | Defect | Evidence |
|---|---|---|
| `ac6d1b28` | The backend image contained the private JWKS key directory `app/modules/identity/_keys/`, and non-root `salesos` could not write keys there (PermissionError at boot). | `.dockerignore` excludes the key directory. The production stage of `salesos/backend/Dockerfile` sets `SALESOS_JWKS_KEY_DIR=/data/jwks` and creates that directory owned by `salesos`. Rebuilt image: no key file inside, API boots, login works. |
| `0f217957` | `RateLimitMiddleware` wrapped `await self.app(...)` in the same `try` as the Redis calls. An app error made it fall back and dispatch the request a second time, and `POST /register` hung. | The app is now called once, outside any `try`; only the Redis incr/expire calls are guarded. New `test_rate_limit_middleware_single_dispatch.py` (2 tests) failed against HEAD (`2 == 1`) and passes now. |
| `5c94f07c` | `GET /reviews/{review_id}` was declared before `/reviews/pending` and `/reviews/kpis`. Starlette matches the first route, so both static routes returned 404. | Static routes are now declared first. New `test_commercial_review_route_order.py` has 3 tests. |
| `85947d22` | **P0.** Self-registration accepted a client-supplied `tenant_id`, so anyone could join an existing tenant. | A supplied `tenant_id` now returns 400 `register.tenant_id_not_allowed`, and a new tenant is always a fresh `uuid4`. New `test_register_rejects_existing_tenant.py` failed against HEAD. Live: tenant A registered, logged in and created a company. Registering B with A's `tenant_id` returned 400. The E2E fixtures and assertions are updated to match. |

Combined targeted run: 50 passed. Five failures in `TestP1FrontendPages` are environmental: the backend container has no frontend mount. They are not regressions.

Secret scan of `32f52503..85947d22` (10 files): the only pattern match is the synthetic fixture password `Str0ng!Passw0rd#2026`, which is not a secret. The push was a fast-forward; there was no force push, amend or history rewrite.

## 2. Proven live (port 8010, restricted role)

- CSRF token, registration, login.
- Honest empty states.
- Company create, get and Company 360.
- Contacts, opportunities, pipeline and activities endpoints.
- Review static routes, after the fix.

## 3. Observed, not fixed (need decisions)

1. **Review actor can be spoofed.** `decide_review` reads `decided_by` from a client query parameter instead of the authenticated user.
2. **`/invite`** is admin-gated, but:
   - it returns `temporary_password` in the response body;
   - it swallows role-update failures with a bare `except: pass`.
3. **First user of a self-registered tenant is not an admin.** They get only the `user` role, so no one in that tenant can:
   - invite colleagues;
   - create tasks, proposals or reviews.

   This blocks a self-serve pilot tenant. The fix needs an RBAC policy decision: first user becomes admin, or tenants are provisioned by an operator.
4. **`Dockerfile.railway` and `Dockerfile.celery`** do not yet set `SALESOS_JWKS_KEY_DIR` to a writable directory. This is a DevOps follow-up before any Railway build.
5. **The E2E journey test was not run.** It flips roles through `db_session`, which may be blocked by RLS.

## 4. Pilot conditions (unchanged, human or ops)

| Gate | Condition |
|---|---|
| G2 | 2,661 P3 pairs to review |
| G3 | Short-CR adjudication |
| G4 | Remaining P1 backlog, plus correct values for the 52 MATERIAL_ERROR rows |
| G5 | Apollo-only stratum |
| G8 | Production not open |
| G9 | Staging Google OAuth |
| G10 | Railway backup schedule |
| G11 | `preDeployCommand` drift |
| G12 | SSO |
| G13 | PDPL |
| G14 | SOC2 |
| G15 | Customer Success lifecycle |
| G16 | Learning / adaptive ICP |

No gate was closed. `feature_ai_copilot` was not changed. There were no Apollo or external calls and no writes to the `salesos` database.
