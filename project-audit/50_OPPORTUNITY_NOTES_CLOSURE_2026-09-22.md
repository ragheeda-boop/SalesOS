# Opportunity Notes Closure — 2026-09-22

## Scope

Closed a real seller-workflow gap: the frontend's `addOpportunityNote()` had
been a no-op, so a seller could appear to add a deal note without any durable
record. The feature now persists and reads immutable notes for a commercial
opportunity.

## Implementation

- Added `commercial_opportunity_notes` with tenant, parent opportunity,
  authenticated author, body, creation time, and optional retry key.
- Added `GET` and `POST` `/api/v1/opportunities/{opportunity_id}/notes`.
- The API derives `author_id` from the authenticated user; a client cannot
  impersonate another seller in the stored record.
- Parent ownership is checked explicitly and is also enforced by row-level
  security.
- A `(tenant_id, opportunity_id, idempotency_key)` constraint returns the
  existing note for a safe retried request.
- The frontend store now submits the note then reloads notes for the affected
  opportunity. Its former no-op test now asserts the persisted result shape.

## Verification

An isolated temporary PostgreSQL 16 container was created only for this test
and removed after verification. No existing `salesos` or `salesos_test` data
was changed. In that isolated database:

1. `alembic upgrade x7y8z9a0b1c2` rebuilt the complete historical schema from
   an empty database.
2. `alembic upgrade head` applied
   `y8z9a0b1c2d3_commercial_opportunity_notes` successfully.
3. The database reported head `y8z9a0b1c2d3`, with both RLS and FORCE RLS set
   to `true` and exactly one tenant-isolation policy for the new table.
4. `tests/integration/test_opportunity_notes_rls.py`: **2/2 PASS**. It proves
   tenant A cannot read tenant B's notes, no tenant context sees zero rows,
   and a retry retains one authenticated-author note.
5. Python `compileall` passed and both API routes are registered.

## Limitation

The persistent local `salesos_test` database is a Master Data-only snapshot;
it lacks identity and commercial-opportunity tables. It cannot serve as a
Revenue Execution integration environment. That is an environment-contract
gap, not a reason to weaken the production migration or remove the
opportunity foreign key.

The frontend dependency tree in `D:\AISalesOS\salesos\frontend` remains
incomplete, so Jest, TypeScript, Next build, and browser validation could not
be rerun in this checkout. The changed frontend test is included but remains
unexecuted here.

## Roadmap effect

This closes one code-scope Sales Execution capability: durable seller notes
with tenant isolation and retry safety. The capability census moves from
**85/113 to 86/113 = 76.1%**. It does not change Phase 7 status or authorize
production.
