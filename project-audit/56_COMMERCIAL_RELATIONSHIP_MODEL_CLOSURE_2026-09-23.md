# Commercial Relationship Model — Closure 2026-09-23

## Purpose

Close the **Commercial Relationship Model** row (capability-line 99, PARTIAL) by
establishing a tenant-aware, typed, lifecycle-managed relationship edge model
for `reports_to`, `influences`, `champion_for`, `blocks`, and `introduced_by`
between people and companies, persisted in Postgres behind the canonical
DEC-085 tenant policy, proven end-to-end on a fresh ephemeral database with the
restricted runtime role. No Neo4j dependency, no production write, no provider
call, and no Phase 7 data change occurred.

## Delivered changes

| Area | Change | Boundary retained |
|---|---|---|
| Schema | Migration `u1v2w3x4y5z6` (down_revision `s9t0u1v2w3x4`, Alembic head) creates `commercial_relationship_edges` (`tenant_id`, `edge_type`, `source_type`, `source_id`, `target_type`, `target_id`, `basis`, `confidence`, jsonb `evidence`, `observed_at`, `superseded_at`, `created_by`), indexes on `(tenant_id, source_type, source_id)`, `(tenant_id, target_type, target_id)`, `(tenant_id, superseded_at)`, a **partial unique index** `ux_relationship_edge_active` on `(tenant_id, edge_type, source_type, source_id, target_type, target_id) WHERE superseded_at IS NULL`, `ENABLE ROW LEVEL SECURITY`, the canonical `tenant_isolation_commercial_relationship_edges` policy, `FORCE ROW LEVEL SECURITY`, and guarded CRUD grants to `salesos_app`. | One table per edge, not a graph store; `opportunity_contacts` remains the stakeholder slice. |
| Model | `app/modules/relationships/models.py`: `RELATIONSHIP_EDGE_TYPES` taxonomy, `RelationshipEdge` dataclass, `normalize_edge()` validator (UUID tenant, `{person, company}` endpoints, self-loop rejection, `confidence ∈ [0,1]`, dict-only `evidence`, basis length cap, `known_basis`/`is_endpoint_type` helpers), `RelationshipError`. Pure module; no I/O. | Rejects malformed edges at the boundary; validation is independent of storage. |
| Store | `app/modules/relationships/store.py`: `RelationshipStore` with `create` (idempotent via unique-index `IntegrityError` recovery), `get`, `list` (tenant-scoped, optional `include_superseded`), `supersede` (no-op on already-superseded, sets `superseded_at` only on the live row), `count_active`. Every statement pins `app.tenant_id` transaction-locally; FORCE RLS backstop is defence in depth. | All resolvers unqualified by explicit tenant id; the GUC plus FORCE RLS is the sole authority. |
| Router | `app/routers/relationships.py`: `POST/GET /api/v1/relationships/edges`, `GET /api/v1/relationships/edges/{edge_id}`, `POST /api/v1/relationships/edges/{edge_id}/supersede`. Create/supersede gate on `contact:UPDATE`, list/get gate on `contact:READ`. Registered in `app/boot/routers.py` under `/api/v1`, tags `["Commercial Relationships"]`, auth dependencies. | No `relationship` resource exists in the registry; the door uses the closest existing resources. |
| Proof | `tests/unit/test_relationships.py` (24) + `tests/integration/test_relationships_rls.py` (7): per-tenant create/list/get/supersede round trips, cross-tenant visibility rejection, cross-tenant supersede rejection, FORCE RLS hiding unpinned reads, partial-unique re-creation after supersede, RLS/`FORCE`/policy/schema assertions, and **migration downgrade→upgrade round-trip** (table and partial index drop/recreate). | Integration tests truncate `commercial_relationship_edges` per fixture and reuse fixed ids, so suites stay hermetic. |

## Defects found and fixed during verification

- **GUC is transaction-local**: `set_config('app.tenant_id', :t, true)` is
  lost after a `rollback()`; the recovery `SELECT` then matches zero rows under
  FORCE RLS and surfaces a false `PermissionError`. The store now re-pins the
  GUC immediately after any rollback. This only surfaced on the ephemeral
  restricted-role database; the unit path never exercised rollback.
- **`timestamptz` binding**: `observed_at`/`superseded_at` must be bound as real
  `datetime`, not an ISO string, under asyncpg. A `_as_datetime()` helper
  normalizes both inputs and stored values.
- Removed a stray commit-before-raise in the cross-tenant supersede branch;
  the fixed path is rollback-then-raise.

## Verification

Migrations ran from zero to `u1v2w3x4y5z6` on a fresh ephemeral
`pgvector/pgvector:pg16` database (port 5439). The owner role is superuser
there; the runtime role `salesos_app` is non-superuser, no createdb/role, and
no `BYPASSRLS`.

```text
31 passed in 1.52s      # 24 unit + 7 RLS/lifecycle integration
22 passed in 1.38s      # adjacent suites (market sizing, sequencing, opportunity contact repos)
8 passed in 1.44s       # buying committee + Phase 6 relationships (no regression)
```

- Alembic single head: `u1v2w3x4y5z6 (head)`; `alembic upgrade head` idempotent;
  `downgrade s9t0u1v2w3x4` drops the table + partial index; `upgrade head` recreates.
- `pg_policy` shows the canonical policy; `relrowsecurity = t`, `relforcerowsecurity = t`.
- Partial unique index re-created identically after the round trip.
- Python compilation of all touched modules and standalone router imports pass;
  all 4 endpoints appear in OpenAPI (711 total paths). The ephemeral database is
  removed after verification.

## Deliberate non-claims

- The capability census moves from **88/113 = 77.9%** to **89/113 = 78.8%**:
  the Commercial Relationship Model row flips from PARTIAL to code-scope COMPLETE.
- No shared `salesos_test` or production database was changed, no provider was
  called, no deployment occurred, and nothing was committed or pushed.
- Phase 7 remains capture-only on `salesos_test`; production remains **NOT APPROVED**.
- `reports_to` typography here is metadata-grade (basis/evidence/observer);
  HR-grade org reporting and permissions propagate through their own
  authoritative stores, not this model.

## Next code-reachable work

1. Route the opportunity-role suggestion (from the 888 future-cycle user story)
   through a cache that reads `commercial_relationship_edges` so champion/blocker
   context is candidate when drafting relationship narratives.
2. Extend the RLS proof pattern to the remaining partial capabilities whose
   lifecycle is not tenant-enforced (price persistence, budget state).
3. Restore the frontend toolchain in an adequate-space checkout before another
   census-affecting UI closure effort.

Production remains **NOT APPROVED**.