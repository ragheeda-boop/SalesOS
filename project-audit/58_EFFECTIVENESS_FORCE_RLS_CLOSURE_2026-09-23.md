# Effectiveness Tables FORCE RLS Closure — 2026-09-23

> **CORRECTION (2026-09-23, same day):** this report's own "Next
> code-reachable work" item 1 ("confirm the 13 dead-table candidates... then
> drop them") is **wrong** — those tables are live, not dead. See
> `project-audit/59_ORPHAN_KEEP_TABLES_RLS_GAP_2026-09-23.md`. The
> `account_funnel`/`score_observations` FORCE RLS fix documented below is
> unaffected and stands as verified.

## Purpose

Close row 57 (RLS / tenant isolation completeness) in the reconciled register
(report 57) by fixing a mechanically-discovered gap: `account_funnel` and
`score_observations` — both live tables used by the Effectiveness and Signal
Actions modules — had `ENABLE ROW LEVEL SECURITY` and a tenant policy from
their originating migrations, but neither had ever been given
`FORCE ROW LEVEL SECURITY`, unlike every one of the other 122 RLS-enabled
tables in the current schema. No production, `salesos_test`, or shared
database was written to; all verification ran on a fresh, disposable
`pgvector/pgvector:pg16` container built and torn down for this closure only.

## How the gap was found

Report 57's mechanical audit built the current source into a fresh Docker
image (`docker build`, not a bind mount — see report 57 §1 for why a bind
mount silently produced stale/empty results in this environment) and ran
`alembic upgrade head` against a brand-new ephemeral database, then queried
`pg_class.relrowsecurity` / `relforcerowsecurity` and `pg_policies` directly
instead of trusting any document's stated policy count. Of 124 tables with
RLS enabled, exactly 2 lacked `FORCE`. Cross-referencing both table names
against the application code (`app/modules/effectiveness/__init__.py`,
`app/modules/signal_actions/{router,hitl_router}.py`) confirmed they are live,
not legacy/orphaned tables, which is what made this a real fix rather than
dead-table hygiene (contrast with the 21-table finding in report 57 §3, which
*is* mostly dead-table hygiene and was deliberately left alone).

## Delivered changes

| Area | Change | Boundary retained |
|---|---|---|
| Migration | `salesos/backend/app/alembic/versions/70193187420d_force_rls_effectiveness_tables.py` (down_revision `u1v2w3x4y5z6`, new Alembic head) adds `ALTER TABLE ... FORCE ROW LEVEL SECURITY` to `account_funnel` and `score_observations` only | Does not touch the existing table shape, the existing policy definition, or any grant. This is the narrowest possible fix for the narrowest possible gap. |
| Test | `salesos/backend/tests/integration/test_effectiveness_force_rls.py` — asserts `relrowsecurity`/`relforcerowsecurity` are both `true` and exactly one canonical `tenant_isolation_*` policy remains per table, via `app.database.async_session` (the same `salesos_app` runtime-role connection every other RLS test in this repo uses) | Regression-shaped: this test will fail if a future migration ever removes the FORCE clause again. |

## Why this matters (and why it was verified behaviorally, not just by catalog flag)

`FORCE ROW LEVEL SECURITY` only changes behavior for the table's **owner**
role when that owner is not a superuser and does not have `BYPASSRLS` — the
application's own traffic (via `salesos_app`, which is neither superuser nor
owner nor `BYPASSRLS`) is unaffected either way. In this repository's current
local/dev bootstrap, the owner role (`postgres` in the pgvector image, or
`salesos` per `infra/docker/postgres/init/02-app-role.sql`'s own comment) is a
superuser, which means the flag is a defense-in-depth measure today, not an
exploitable-in-this-exact-setup hole. To confirm the fix is real and not
theatre, a manual, one-time proof was run (not committed as a permanent test,
since it requires reassigning table ownership, which is not something a
regression suite should do to a shared schema):

1. Inserted one `account_funnel` row for `tenant-a`.
2. Created a throwaway `NOSUPERUSER NOBYPASSRLS` role and made it the table's
   owner (`ALTER TABLE account_funnel OWNER TO temp_owner`).
3. Connected as `temp_owner` with no `app.tenant_id` GUC set:
   - **With `FORCE ROW LEVEL SECURITY` (the post-fix state):** `SELECT
     count(*)` → **0**. The owner is correctly blocked.
   - **After manually removing `FORCE`** (simulating the pre-fix state):
     same query → **1**. The owner sees the row — this is exactly the gap
     that existed on these two tables before this migration.
4. Restored `FORCE`, restored ownership to the original owner, dropped the
   throwaway role, deleted the test row.

This directly demonstrates the vulnerability class the fix closes: on any
deployment where the connecting/owning role for these tables is not a
superuser (a realistic scenario on managed Postgres providers that do not
grant superuser to the migration role — not the case in this project's
current local bootstrap, but exactly the scenario `FORCE` exists to guard
against), an un-pinned session could read across tenants on these two tables
specifically, while every other table in the schema was already protected.

## Verification

Migrations ran from empty to `70193187420d` on a fresh ephemeral
`pgvector/pgvector:pg16` container (owner role `postgres`, superuser there by
construction of the base image; the runtime role `salesos_app` was
provisioned via the repository's own `infra/docker/postgres/init/02-app-role.sql`
and is non-superuser, `NOBYPASSRLS`, `NOCREATEDB`, `NOCREATEROLE`).

```text
tests/integration/test_effectiveness_force_rls.py::test_account_funnel_and_score_observations_force_rls PASSED

53 passed in adjacent RLS regression scope (test_adversarial_rls*.py ×11,
test_rls_policy_generation.py, plus this new test) — 5 errors in
test_rls_policy_generation.py are a pre-existing environmental coupling
(that file hardcodes a fallback database literally named "salesos_test" via
TEST_DATABASE_URL, unrelated to this migration) and are unchanged by this
closure.
```

- `alembic upgrade head` → `70193187420d`; `alembic downgrade u1v2w3x4y5z6`
  removes `FORCE` from both tables (confirmed via `pg_class` query: both
  flip from `t` to `f`) while leaving `ENABLE`/the policy untouched;
  `alembic upgrade head` re-applies and both flip back to `t`. Full
  downgrade→upgrade round trip proven, not assumed.
- Single Alembic head confirmed both statically (parsed all 127
  revision/down_revision pairs, zero missing links, zero extra heads) and by
  the live migration run completing without error.
- Manual ownership-reassignment proof in the section above.
- Python `compileall` of the new migration and test file passed.
- Ephemeral container, network, and rebuilt Docker images were all removed
  after verification (`docker rm -f`, `docker network rm`, `docker rmi`).

## Deliberate non-claims

- This closes exactly one narrow gap on two tables. It does **not** address
  the 21 tenant_id-bearing tables with no RLS at all (report 57 §3) — most of
  those are confirmed-dead legacy tables and the remainder are owner-plane
  billing tables that need an architecture decision, not a code fix, before
  any RLS is added.
- No `salesos_test` or production database was touched. No provider was
  called. No deployment, staging, commit, or push occurred.
- The manual ownership-reassignment proof is not a permanent regression test
  — it is documented evidence from a one-time run on the same disposable
  container used for the rest of this closure's verification, and is
  reproducible by following the exact commands recorded above.
- Phase 7 remains BLOCKED; production remains **NOT APPROVED**. This closure
  changes nothing about either.

## Next code-reachable work

1. Confirm the 13 dead-table candidates in report 57 §3 (Feature Store
   orphan-keep tables, legacy `decisions`/`decision_feedback_loop`,
   `domain_events`, `activity_records`) are genuinely unreferenced anywhere
   (including background jobs and raw-SQL call sites this session's grep may
   have missed), then drop them in a dedicated hygiene migration rather than
   granting them RLS.
2. Get a PO/TL decision on whether the 6 owner-plane billing tables
   (`subscriptions`, `usage_meters`, `usage_meter_events`, `dunning_cases`,
   `platform_billing_invoices`, `stripe_webhook_events`) ever need
   cross-tenant reads from an owner-platform path; only then design their RLS
   treatment.
3. Delete the stray `0afbf3e6ae53_enable_rls_all_tenant_tables.py.bak` file
   found during this audit — it is not a live revision and is pure clutter.
