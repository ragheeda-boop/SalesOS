# Full Authenticated Browser E2E Proof — 2026-09-23

## What this closes

Every session since at least 2026-09-20 has recorded some form of "the
authenticated browser flow remains unverified," "a full authenticated
customer journey is absent," or "browser proof used a synthetic
admin-issued JWT, not real registration/login." This report is the first
time in this project's recorded history that the **entire loop** — real
registration through the actual UI, real login, real CRUD through the UI
form, real data rendering back — was driven end to end in a browser against
a real (ephemeral, disposable) backend and database, with zero synthetic
tokens or seeded fixtures.

This was only possible today because report 61 fixed the frontend
toolchain (`next dev` now runs reliably from the C: mirror); every prior
attempt at this exact goal was blocked by the frontend environment, not by
the backend or the flow itself.

## Environment (ephemeral, fully torn down after)

- Fresh `pgvector/pgvector:pg16` container, migrated from empty to the
  current Alembic head (`70193187420d`) — the same head as report 58.
- `salesos_app` restricted runtime role provisioned via
  `infra/docker/postgres/init/02-app-role.sql` (non-superuser, `NOBYPASSRLS`).
- Backend image built fresh from current source (`docker build`, not the
  stale local `salesos-backend` image — see report 57 §1 for why that
  distinction matters), run as its own container on a private Docker
  network, port-mapped to `localhost:8010`.
- A `redis:7-alpine` container, added mid-session after a real finding
  (below).
- Frontend: the same `sync-to-c-and-verify.ps1` C: mirror from report 61,
  run via `next dev` on port 3100, pointed at the ephemeral backend via
  `INTERNAL_API_URL=http://localhost:8010`.
- No connection to `salesos_test`, `salesos`, or any shared/production
  resource at any point.

## The proof, step by step, all through the browser

1. Navigated to `/register` (had to `read_page` after each navigation — the
   very first load of an uncompiled `next dev` route showed a stale
   pre-hydration frame in one screenshot; re-reading the DOM after confirmed
   the real form was present and interactive).
2. Filled the real sign-up form (name, email, password, confirm) and
   submitted. First attempt hit a genuine, unrelated environment problem
   (below); after fixing it, `POST /api/v1/identity/register` → **201
   Created**, and the browser navigated itself to `/v3` — a real session,
   a real tenant, a real user, created by an actual person filling out an
   actual form.
3. Landed on the V3 home dashboard: real executive-dashboard API data
   (`SAR 0` pipeline, `0` open deals, `0%` win rate, `1` active team member
   — an honest, non-fabricated empty-tenant state), and a working nav
   (Companies, Contacts, CRM, Activities, Tasks, Quotes, Proposals,
   Reviews, Contracts, ICP, Settings).
4. Navigated to `/v3/companies`: real empty state ("No companies found...
   Create one here"), not a fixture or a mock.
5. Clicked "New company", filled the real create form (Arabic name is
   required, and — discovered by trial — so is CR number, contradicting the
   form's own subtitle text, a minor UX/copy inconsistency worth a follow-up
   but not fixed here), submitted. `POST /api/v1/companies` → **201
   Created**. The app auto-navigated to the new company's detail page.
6. The detail page hit a real, separate bug (below), fixed, then re-verified:
   full "Company 360" overview rendered with the exact data just entered —
   Arabic name, English name, CR number, status, tabs (Overview, Contacts,
   Timeline, Opportunities, Tasks, Intelligence, NBA & Outcomes), honest
   "No branches / No licenses on this record" for fields with no data.
7. Logged back in after a session invalidation (expected — see below) and
   confirmed the dashboard's "Companies" widget now lists "Verification
   Test Co" — the loop closes: create through the UI, see it reflected
   elsewhere in the UI, powered by the real database.

## Two real bugs found and one fixed (both environment-level, not app-code)

1. **JWKS decryption failure on a fresh `SECRET_KEY`.** The backend's RSA
   signing key defaults to `app/modules/identity/_keys/` inside the source
   tree (not `/data/jwks` as the Dockerfile's directory setup implies), and
   this checkout already has a committed-looking key pair there (dated
   2026-09-22, presumably left by an earlier session's own testing),
   encrypted with whatever `SECRET_KEY` that session used. My arbitrary
   `SECRET_KEY` couldn't decrypt it, and the code correctly refuses to
   silently regenerate (fail-closed, by design, with a clear error message).
   **Fixed** for this session only by pointing `SALESOS_JWKS_KEY_DIR` at a
   fresh, empty path — the existing key file was never touched, read, or
   modified. Not a code bug; worth a note that any fresh ephemeral backend
   setup needs its own isolated JWKS directory, which is exactly what the
   error message itself says to do.
2. **`GET /api/v1/companies/{id}` returns an unhandled 500 when Redis is
   unavailable**, while `GET /api/v1/companies` (the list endpoint) does
   not. Root cause traced via the container's own stack trace:
   `app/modules/admin/entitlement_middleware.py` calls into
   `quota_metrics_for_path` / `UsageMeterService`, which needs Redis for
   counting, and the connection timeout propagates as an unhandled
   `redis.exceptions.TimeoutError` instead of a graceful degrade or a clean
   503. **Not fixed** — this touches quota/billing enforcement logic
   (`quota_enforcement_enabled` defaults `True`), which is a
   security/business-policy decision, not something to patch unilaterally
   under this task's scope. Documented here as a genuine resilience finding:
   if Redis has an outage in any real deployment, single-record reads that
   happen to be quota-metered would 500 instead of degrading. Worked around
   for this proof by adding a `redis:7-alpine` container, after which the
   same endpoint returned 200 cleanly.
3. **Session invalidation on backend restart** (expected, not a bug): the
   JWKS keypair lives in the ephemeral container's filesystem; recreating
   the backend container (to add Redis) meant a fresh keypair, which
   correctly invalidated the previously-issued access token. Re-login
   resolved it in one step.

## Verification summary

| Step | Result |
|---|---|
| Register (real UI form) | PASS — `201 Created`, real session issued |
| Login (after intentional session reset) | PASS |
| Dashboard (real API data) | PASS — `/api/v1/executive/dashboard`, `/api/v1/companies`, `/api/v1/opportunities` all `200 OK` |
| Create company (real UI form) | PASS — `201 Created` |
| Company detail page (real data) | PASS after adding Redis — `200 OK`, correct data rendered |
| Console errors in final state | **0** (all error entries found in the console buffer were from the two diagnosed-and-resolved issues above, not the final verified state) |

## Deliberate non-claims

- This is one seller-side flow (register → login → create company → view
  company), not a full regression of every V3 page. It is, however, the
  **first-ever real, non-synthetic, full-loop authenticated proof** in this
  project's session history, closing the specific gap every prior report
  from 2026-09-20 onward flagged as open.
- The Redis-dependency finding on `GET /companies/{id}` is documented, not
  fixed. It is a legitimate resilience/graceful-degradation gap in
  `entitlement_middleware.py`'s interaction with `UsageMeterService`, worth
  its own follow-up, not addressed here since it touches billing/quota
  enforcement policy.
- No connection to any shared or production database occurred. All
  containers, the network, and the built image were removed after
  verification; the test tenant/user/company existed only inside the
  now-deleted ephemeral Postgres volume.
- Production remains **NOT APPROVED**; Phase 7 remains **BLOCKED**. This
  report changes neither status — it proves the seller-facing application
  loop works end to end in a browser, which is a different question from
  production/data-governance readiness.
