# Durable GTM Capability Persistence — 2026-09-23

## Purpose

Remove the in-memory-only caveat from the eight STORY-11 GTM capabilities
(Market Sizing, Lead Discovery, Lookalike, Enrichment Waterfall, Contact
Verification, Website Intelligence, AI Outreach, Sequencing) by persisting
their result records in Postgres behind the canonical DEC-085 tenant policy,
proven end-to-end on a fresh ephemeral database with the restricted runtime
role. No production write, provider call, or Phase 7 data change occurred.

## Delivered changes

| Area | Change | Boundary retained |
|---|---|---|
| Schema | Migration `s9t0u1v2w3x4` (down_revision `r4s5t6u7v8w9`, Alembic head) creates one capability-discriminated table `gtm_capability_results` with a composite primary key `(capability, id)`, `tenant_id`, `name`, jsonb `payload`, `schema_version`, `created_at`, `updated_at`, an index on `(tenant_id, capability)`, `ENABLE ROW LEVEL SECURITY`, the canonical `tenant_isolation_gtm_capability_results` policy, `FORCE ROW LEVEL SECURITY`, and guarded CRUD grants to `salesos_app`. | One table, not eight; definitions and enrollments are capabilities `sequence_definition` / `sequence_enrollment`. |
| Store | `app/modules/gtm/durable_store.py` implements `PostgresGtmStore` (compute/discover/run/enrich/verify/analyze/draft/definition/enroll/advance/pause/resume/cancel/get/list), defines `DurableRecord` and `aresolve`. Every statement runs with the tenant GUC pinned; writes are `(capability, id)`-scoped, recompute bumps `schema_version` while preserving `created_at`, immutable-state ops (`enroll/advance/pause/resume/cancel`) keep the payload version, and a hidden cross-tenant PK collision surfaces as `PermissionError`. | Compute kernels stay in the pure engine modules; the table only persists their produced records. |
| Store wiring | The default stores in all eight `*_store.py` modules now resolve to `PostgresGtmStore(capability=...)`; the `Mem*Store` classes remain for unit tests and the legacy synchronous call path. | No `bind_store(...)` exists in any test; unit suites are unaffected. |
| Routers | The eight GTM routers wrap store calls in `await aresolve(...)` so a single handler shape serves both sync (Mem) and async (Postgres) stores. | `tenant_id` in durable writes must be a real UUID; Mem stores still accept any string. |
| Proof | New `tests/integration/test_gtm_durable_rls.py`: per-tenant persistence and listing, recompute version bump with preserved `created_at`, FORCE RLS hiding unpinned/cross-tenant reads, cross-tenant same-id reuse blocked, and a full definition→enroll→advance→pause→resume→cancel round trip. | Integration tests truncate `gtm_capability_results` per test so fixed ids stay hermetic. |

## Verification

Migrations ran from zero to `s9t0u1v2w3x4` on a fresh ephemeral
`pgvector/pgvector:pg16` database. The owner role is superuser there; the
runtime role `salesos_app` is non-superuser with no `BYPASSRLS`.

```text
68 passed in 2.88s
```

- 5 new durable/RLS proof tests + the existing Customer Success RLS reference + all 10 STORY-11 unit suites.
- The restricted-role run exposed two real defects fixed before acceptance: recompute returned a fresh `created_at` instead of the stored one (all create/state methods now return the exact saved payload), and a one-step sequence completed on first `advance`, making `pause` correctly illegal (test now uses a two-step definition).
- Python compilation of all touched modules and standalone router imports pass. The ephemeral database is removed after verification.

## Deliberate non-claims

- The 113-capability census stays **88/113 = 77.9% (78%)**: the eight GTM rows were already COMPLETE at code scope; this loop upgrades them from in-memory to durable and tenant-enforced, it does not open new rows.
- No shared `salesos_test` or production database was changed, no provider was called, no deployment occurred, and nothing was committed or pushed.
- Phase 7 remains capture-only on `salesos_test`; production remains **NOT APPROVED**.

## Next code-reachable work

1. Extend the durable layer to the remaining partial capabilities whose records are still in memory (price persistence, budget reservations) using the same pattern.
2. Verify the active GTM API paths through FastAPI route tests now that defaults are async-backed.
3. Restore the frontend toolchain in an adequate-space checkout before another census-affecting closure effort.

Production remains **NOT APPROVED**.