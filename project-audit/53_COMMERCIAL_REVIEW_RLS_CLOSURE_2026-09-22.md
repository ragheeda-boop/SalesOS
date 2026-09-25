# Commercial Review RLS Closure — 2026-09-22

## Finding

The commercial model census found that `commercial_reviews` has a direct
`tenant_id`, but no migration had enabled Row Level Security for it. The table
stores approval decisions for opportunities, quotes, and proposals, so leaving
it outside database enforcement was a real cross-tenant exposure risk.

The same census initially listed `commercial_insights` and
`commercial_evidence_items` as outside the central inventory. Their dedicated
earlier migration already applies RLS and FORCE RLS; they are now listed in the
central inventory so a future audit does not report a false gap.

## Correction

- Added `commercial_reviews`, `commercial_insights`, and
  `commercial_evidence_items` to `ALL_TENANT_TABLES`.
- Extended the current additive migration to enable and force the canonical
  tenant policy on `commercial_reviews`, revoke public access, and grant the
  non-superuser runtime role the needed CRUD rights.
- The migration's downgrade removes only the policy it creates and restores
  the previous RLS state for the repaired historical table.

## Verification

The full migration chain was rebuilt on a fresh temporary PostgreSQL 16
database. The runtime role was non-superuser and had no `BYPASSRLS` privilege.

- `tests/integration/test_commercial_review_rls.py`: **1/1 PASS**. The owner
  reads its review; another tenant and no tenant scope read zero rows.
- The final database inspection reported `RLS=true`, `FORCE RLS=true`, and one
  policy on `commercial_reviews`.
- Regression bundle for the six closures: **6/6 PASS**
  (opportunity notes 2, quota snapshot 1, territory 1, task detail 1, review
  isolation 1).
- No shared `salesos_test` or production database was changed. The temporary
  database was removed after verification.

## Roadmap effect

This is a security correction to an existing Reviews capability; it does not
increase the 113-capability product census. The roadmap remains
**88/113 = 77.9%**, and Production GO remains blocked by its separate gates.
