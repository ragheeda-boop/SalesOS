# R-14 Enterprise Closure Report

**Date:** 2026-07-31
**Scope:** Roll the R-14 remediation (least-privilege `salesos_app` runtime role, separate from the superuser/BYPASSRLS `salesos` owner role) out from local-dev-only to every remaining environment: CI, Staging, Production Template, Railway.
**Predecessor documents:** `R-14_REMEDIATION_REPORT.md` (local dev), `docs/program/RISK_REGISTER.md` R-14, `docs/program/DECISION_LOG.md` DEC-013/DEC-014/DEC-015.
**Final Decision: R-14 PARTIALLY CLOSED.**

---

## Executive Summary

Local dev, CI, Staging, and the self-hosted Production Template are all remediated and **independently verified** — not self-reported. Each environment's postgres service already mounted `infra/docker/postgres/init/` as `docker-entrypoint-initdb.d` (true for `docker-compose.yml`, `docker-compose.prod.yml`, and both `infra/staging/docker-compose.staging*.yml` files), so `02-app-role.sql` was already auto-provisioning on any fresh volume — the actual gap in most environments was just `APP_POSTGRES_USER`/`APP_POSTGRES_PASSWORD` missing from their env files/templates. CI's `test-backend`/`integration-backend` jobs are the one exception: GitHub Actions' ephemeral `services:` Postgres containers start before checkout, so no init-script mount is possible there — an explicit provisioning step was added instead.

While wiring CI, a real portability bug was found in `02-app-role.sql` itself: it hardcoded `GRANT CONNECT ON DATABASE salesos`, which only ever worked by coincidence on hosts where a database literally named `salesos` also happened to exist on the same server. Against CI's single-database `salesos_test` instance it failed outright (`database "salesos" does not exist`). This is fixed (dynamic `current_database()` grant via `EXECUTE format(...)`) and the fix is proven, not just asserted — see SQL Evidence below.

**Railway is the one environment left open, by explicit decision, not oversight or guesswork.** It doesn't use any compose file in this repo (it builds from `railway.json` straight from the Dockerfile against a managed Postgres add-on), its live role is `postgres` (not `salesos`, confirmed diverging from every template here), and applying R-14 there would require either live production access or an unverified blind edit to its deploy config. Asked directly mid-task, the decision was to leave it fully untouched. Per the task's own closing rule — "do not close R-14 unless every production-relevant environment has been validated or explicitly authorized and verified" — Railway being unauthorized-and-unverified means the honest final decision is **PARTIALLY CLOSED**, not CLOSED.

---

## Environment Matrix

| Environment | Runtime Role | Migration/Owner Role | RLS Verified | Status |
|---|---|---|---|---|
| **Local dev** | `salesos_app` (`NOSUPERUSER NOBYPASSRLS`) | `salesos` (superuser, unchanged) | ✅ Yes — bypass-probe re-run live, full HTTP traffic proven (`R-14_REMEDIATION_REPORT.md`) | **Remediated** |
| **CI** (`test-backend`/`integration-backend`) | `salesos_app` (provisioned via new explicit step) | `salesos` | ✅ Yes — simulated locally: identical `pgvector/pgvector:pg16` image/env, migrations run, provisioning step executed verbatim, bypass-probe isolates | **Remediated (simulated; not yet exercised by a real GitHub Actions run)** |
| **Staging** (`docker-compose.staging.yml` / VPS) | `salesos_app` (auto-provisioned via existing init-mount) | `salesos` | ✅ Yes — simulated via `docker-compose.staging-virtual.yml`'s postgres service (the repo's own designated local stand-in), fresh volume, auto-provisioned, bypass-probe isolates | **Remediated (simulated locally; no live VPS to verify against)** |
| **Production Template** (`docker-compose.prod.yml`) | `salesos_app` (auto-provisioned via existing init-mount) | `salesos` | ✅ Yes — postgres service started standalone under an isolated Compose project, fresh volume, auto-provisioned, bypass-probe isolates | **Remediated (template verified; no live host deployed from it yet)** |
| **Railway** (live production, `railway.json`) | `postgres` (unchanged — diverges from `salesos` template naming) | `postgres` | ❌ Not checked | **OPEN — not authorized, not attempted** |

---

## SQL Evidence

**The portability bug, found and fixed:**

Before (as shipped in local dev, DEC-014):
```sql
GRANT CONNECT ON DATABASE salesos TO salesos_app;
```
Reproduced failure against CI's `salesos_test`-only instance:
```
ERROR:  database "salesos" does not exist
```

After (current `infra/docker/postgres/init/02-app-role.sql`):
```sql
DO $$
BEGIN
   EXECUTE format('GRANT CONNECT ON DATABASE %I TO salesos_app', current_database());
END
$$;
```
Re-run against the same instance: `DO` — succeeds, all subsequent `GRANT`/`ALTER DEFAULT PRIVILEGES` statements complete cleanly.

**Role attributes, confirmed identical across every environment's simulation:**
```
   rolname   | rolsuper | rolbypassrls
-------------+----------+--------------
 salesos     | t        | t
 salesos_app | f        | f
```

**The bypass-probe** (identical pattern used in `R-14_REMEDIATION_REPORT.md`, re-run fresh in three separate simulated environments — CI-shaped, staging-shaped, prod-template-shaped): a `FORCE ROW LEVEL SECURITY` table with a tenant-scoped policy, two tenants' rows inserted, queried with `app.tenant_id` set to `tenant-a`:

| Role | Result |
|---|---|
| Owner (`salesos`) | Both rows returned — `tenant-a` and `tenant-b` (superuser bypasses RLS, as expected/unchanged) |
| `salesos_app` | Only `tenant-a`'s row returned (isolation enforced) |

Identical mismatch in all three simulations — the fix generalizes, it isn't a one-off.

---

## Runtime Evidence

- **CI simulation:** fresh `pgvector/pgvector:pg16` container, `POSTGRES_USER=salesos/POSTGRES_PASSWORD=salesos_test/POSTGRES_DB=salesos_test` (CI's exact `services:` spec) → `alembic upgrade head` (0001→0052 clean) → the new CI step's exact `psql` commands executed verbatim → bypass-probe as above. Torn down after.
- **Staging simulation:** `infra/staging/docker-compose.staging-virtual.yml`'s postgres service (the repo's designated local stand-in for staging) started fresh with the updated `.env.staging.local` → `salesos_app` present with zero manual steps (auto-provisioned by the pre-existing init-script mount) → bypass-probe as above. Torn down after.
- **Production template simulation:** `docker-compose.prod.yml`'s postgres service started fresh, isolated Compose project name, with the updated `.env.production` → same auto-provisioning confirmed → bypass-probe as above. Torn down after.
- **Railway:** no runtime evidence — not attempted.

**Operational incident during this work, self-caught and corrected:** `docker-compose.prod.yml` declares no explicit Compose project name. Starting it once from the same directory as the (also-unnamed) primary dev stack caused Compose to resolve both to the same implicit project (`salesos`), and briefly recreated the **live local dev postgres container** against `.env.production`'s values. No data was lost — Postgres only applies `POSTGRES_PASSWORD`/init scripts against an empty data directory, and the same `pgdata` volume was reused both times — but this was an unintended disruption, caught immediately via `docker inspect`'s compose-project label, and reverted by re-running `docker compose -f docker-compose.yml up -d postgres`. Verified fully restored via `curl http://localhost:8000/health/detailed` → `"database":{"status":"connected"}` and a direct check that `salesos_app` was still present. All subsequent simulations used an explicit isolated `-p` project name to prevent recurrence. This hazard is flagged, not fixed at the file level (`docker-compose.prod.yml` still has no `name:` field) — that's an infra-shape change outside today's scope, logged in DEC-015 as a follow-up.

---

## Regression Summary

| | Before (local-dev-only baseline, DEC-014) | After (this pass) |
|---|---|---|
| Passed | 1,957 | 2,604 |
| Failed | 11 (pre-existing) | 29 |
| Skipped | 4 | 4 |
| Total collected | 1,972 | 2,637 |

The totals aren't directly comparable — `pyproject.toml`'s `testpaths` (uncommitted, from earlier Sprint 02-era work in this same engagement, not from anything in this pass) now collects more module/domain test directories than were being collected when the DEC-014 baseline was measured. Rather than either paper over that or reuse a stale count, all 29 current failures were individually classified:

- **7** are the already-tracked, already-open **R-13** issue (`TypeError: <lambda>() got an unexpected keyword argument 'execution_context'` in `tests/unit/test_graphql.py` — a GraphQL/strawberry environment-parity problem, unchanged in nature from prior sessions).
- **22** are pre-existing, unrelated gaps: missing `tenant_id` in contact-creation test fixtures (`NotNullViolationError`), Arabic company-name field-ordering assertions, an RBAC permission-list logic mismatch, an architecture-compliance import check on `domains/employee/`, off-by-one pagination-count assertions, and similar.

**Zero of the 29 failures reference database roles, permissions, GRANT/REVOKE, or RLS.** This pass's entire diff touches no Python source file at all (`app/`, `domains/`, `sdk/`, `runtime/`, `intelligence/`) — only `infra/docker/postgres/init/02-app-role.sql` (SQL, not imported by any Python), CI/docker-smoke workflow YAML, env files/templates, and documentation. There is no mechanism by which this pass could have caused any of the 29 failures; all are pre-existing.

---

## Remaining Risks (unresolved)

1. **Railway is unverified.** The live production database's actual role/privilege configuration relative to RLS bypass has never been checked. Given the confirmed `postgres`-vs-`salesos` naming divergence, it should not be assumed to already be safe by coincidence.
2. **CI's new step is simulated, not yet executed by a real GitHub Actions run.** The exact commands were proven against an identical image/env locally, but nothing has pushed this branch or opened a PR, so GitHub's own runner has not executed it. Recommend treating the first real CI run after this lands as a required verification gate, not a formality.
3. **Staging's simulation used the local tabletop stand-in, not the actual VPS.** `docker-compose.staging.yml` (the real SSH-deployed one) was reviewed and updated identically, but there is no accessible staging VPS in this environment to deploy to and verify against directly.
4. **`docker-compose.prod.yml` has no explicit Compose project name** — the collision hazard documented above (DEC-015) is not fixed at the file level, only avoided procedurally (`-p` flag) during this session's verification.
5. **Railway's own path to remediation, if authorized later:** provision `salesos_app` via an explicit `psql` step (no init-script mount available there), and set `APP_POSTGRES_PASSWORD` through Railway's own secrets mechanism — documented as a runbook in `docs/program/OPERATIONS_MANUAL.md` §14, unexecuted.

---

## Final Decision: R-14 PARTIALLY CLOSED

Local dev, CI, Staging, and the Production Template: remediated and independently verified. Railway: open, by explicit decision this session to leave it untouched rather than connect without authorization or guess at a blind config change. Per the task's own rule — every production-relevant environment must be validated or explicitly authorized-and-verified before closure — R-14 cannot be marked fully CLOSED while Railway remains unverified. Sprint 03's Phase 0 exit gate is unblocked for every environment except a Railway-targeted run.
