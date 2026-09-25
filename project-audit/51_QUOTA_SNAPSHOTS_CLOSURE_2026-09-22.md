# Quota Snapshots Closure — 2026-09-22

## Scope

Closed a Revenue Planning persistence gap. `PostgresQuotaRepository` returned
quota snapshots without storing them and always listed an empty result. A
manager could take a snapshot but could not retrieve a durable historical
record after the request finished.

## Implementation

- Added `commercial_quota_snapshots`: an immutable, tenant-scoped historical
  record of quota rows, team aggregate, totals, attainment, and creation time.
- Added `GET /api/v1/revenue-planning/quotas/snapshots` with a bounded `limit`
  and summary-only response shape.
- Kept the existing `POST /quotas/snapshot` contract and made it durable.
- Serializes every quota and its dates when the snapshot is created, then
  reconstructs the domain model on read. A later quota update therefore cannot
  alter the recorded snapshot.
- Added retry-safe `save_snapshot`: repeating a request with the same snapshot
  identifier returns the immutable existing row instead of changing it.
- Discovered that the older `commercial_quotas` and `commercial_territories`
  tables were outside the central RLS inventory. The same migration now enables
  and forces their tenant policies, revokes public access, and gives the
  runtime role only the CRUD permissions each workflow needs.
- Repaired `find_territory_for_account`: it previously built an invalid
  PostgreSQL JSON operator expression. It now casts the stored JSON list to
  JSONB and uses array containment for an exact account membership lookup.

## Verification

An isolated temporary PostgreSQL 16 container was created from an empty
database and removed after testing. Source, migrations, reports, and test code
remain under `D:\\AISalesOS`; neither `salesos` nor `salesos_test` was written.

1. `alembic upgrade head` completed the complete migration chain through
   `z9a0b1c2d3e4`.
2. The application role was a non-superuser without `BYPASSRLS`.
3. `tests/integration/test_quota_snapshots_rls.py`: **1/1 PASS**. It proves:
   - a snapshot retains `150,000` target and `25,000` attained after the
     underlying quota changes to `80,000`;
   - the historic record returns through the new API handler;
   - a second tenant and a session with no tenant context both receive no rows.
4. Existing quota domain suite: **21/21 PASS**.
5. `tests/integration/test_territory_postgres_rls.py`: **1/1 PASS**. It proves
   account lookup works through PostgreSQL JSON data and the same account id
   resolves only within the caller's tenant; no tenant context returns no rows.
6. Python compilation and migration head checks passed.
7. Database inspection reported `RLS=true`, `FORCE RLS=true`, and one policy
   each for `commercial_quotas`, `commercial_territories`, and
   `commercial_quota_snapshots`. The snapshot table grants `INSERT` to the
   runtime role and intentionally does not grant `UPDATE`.

## Environment limitation

The durable local `salesos_test` database is a Master Data snapshot and lacks
the commercial tables required by Revenue Planning. It remains unsuitable as a
Revenue Execution integration environment. This closure was proven in a fresh
isolated database; it did not migrate a shared test or production database.

The frontend checkout at `D:\\AISalesOS\\salesos\\frontend` still lacks a usable
dependency tree, so TypeScript, Jest, Next build, and browser verification are
not evidence for this backend/API closure.

## Roadmap effect

This closes one code-scope Revenue Planning capability: durable historical
quota snapshots with enforced tenant isolation. The capability census moves
from **86/113 to 87/113 = 77.0%**. Phase 7 and Production GO remain unchanged.
