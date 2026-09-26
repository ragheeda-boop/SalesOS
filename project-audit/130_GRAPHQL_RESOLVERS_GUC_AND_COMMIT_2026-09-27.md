# 130 — The entire /graphql API surface: unpinned RLS on every resolver, plus two write mutations that never committed

**Read-only in scope of production/salesos_test.** Verification ran against a disposable, ephemeral `pgvector/pgvector:pg16` container (`sweep-pg10`) migrated to head `f2e3d4c5b6a7`, with the restricted `salesos_app` role provisioned via `infra/docker/postgres/init/02-app-role.sql`, torn down after use. No write to `salesos_test` or production.

## 1. Reachability — live, mounted, no coverage gap excuse

`app/boot/routers.py:685` mounts `graphql_router` at `/graphql` with real auth dependencies. This is the most severe finding of this session's Phase 2 sweep, by scope: not one call path, but **every single field** in the schema — `company`, `search`, `opportunities`, `pipeline`, `createOpportunity`, `updateCompany` (6 of the schema's 6 data-bearing resolvers; `enrichCompany` delegates to a Celery task and opens no session of its own).

## 2. Bug 1 (all 6 resolvers) — no tenant GUC pin anywhere in the GraphQL layer

Strawberry GraphQL resolvers are plain async functions invoked by the schema executor — they never go through FastAPI's `Depends()` injection system, so they never receive a session via `Depends(get_db_session)`. `TenantContextMiddleware`'s own docstring states the mechanism plainly: it "stor[es tenant_id] in a ContextVar so `get_db()` can `SET LOCAL app.tenant_id`... without this, RLS policies return zero rows." The middleware itself never calls Postgres — only `get_db()` does, and only for sessions it hands out itself.

Every one of the 6 resolvers instead opened its own bare `async_session()` directly, bypassing `get_db()` entirely — so the tenant_id string each resolver correctly read (from `info.context["tenant_id"]` or the `_current_tenant_id` ContextVar via `get_current_tenant_id_context()`) was never actually pinned into Postgres. `companies`, `commercial_opportunities`, and the pipeline tables all have FORCE RLS. Confirmed directly: a real, just-seeded company/opportunity, queried immediately afterward with the correct tenant_id in every application-layer `WHERE` clause, returned zero rows — RLS silently filtered them out regardless of the explicit filter matching.

**Fix**: `apply_tenant_guc(db, tenant_id)` added immediately after opening the session, in all 6 resolvers (`_get_company`, `_search_companies`, `_opportunities`, `_pipeline` in `query.py`; `_create_opportunity`, `_update_company` in `mutation.py`).

## 3. Bug 2 (found only while building the test for `_search_companies`) — `tenant_id` was never passed to `SearchQuery` at all

`_search_companies` never read `tenant_id` from `info.context` in the first place — `SearchQuery(query=query, page_size=limit)` left `tenant_id` at its dataclass default `""`. `CompanySearchRepository`'s query does `Company.tenant_id == uuid.UUID(query.tenant_id)`, so `uuid.UUID("")` raises `ValueError: badly formed hexadecimal UUID string` on **every** call, unconditionally, with no surrounding try/except in this resolver — every real search request has always errored, independent of bug 1. Fixed by reading `tenant_id = info.context.get("tenant_id", "")` and passing it into `SearchQuery(..., tenant_id=tenant_id)`.

## 4. Bug 3 (found only after fixing bug 1, while writing the round-trip test) — neither write mutation ever committed

Once bug 1's fix let `_create_opportunity` actually see its own tenant for the first time, the created opportunity still vanished the instant its `async with async_session()` block exited — the session log showed the `INSERT` immediately followed by `ROLLBACK`, never `COMMIT`. `get_db()` auto-commits on a clean request exit (`await session.commit()` in its `else` branch after `yield session`) — the *entire reason* ordinary REST routes using the same `OpportunityService`/`CompanyService` never need to call `commit()` themselves. GraphQL resolvers, having bypassed `get_db()` for the session itself, also silently lost this auto-commit. Neither `OpportunityService.create_opportunity()` nor `CompanyService.update_company()` calls `commit()` internally (confirmed via grep) — both write mutations have discarded every real write since inception, while still returning a populated (in-memory-only) response object to the caller, making the failure invisible to anyone testing by inspecting the mutation's own response.

**Fix**: `await db.commit()` added at the end of `_create_opportunity()`'s success path, and inside `_update_company()`'s existing `try` block (with `await db.rollback()` added to its `except` branch, matching the fail-safe pattern already used elsewhere in this session).

## 5. Why this was never caught

`tests/unit/test_graphql.py` stubs `app.state.db_session_factory` for unrelated entitlement-middleware reasons, but the resolvers themselves call `app.database.async_session` — a different factory the stub never touches. The suite's own tests for exactly these code paths use assertions that cannot distinguish "correctly returns nothing" from "always returns nothing": `test_graphql_company_query_not_found` queries a company ID of all zeros (genuinely nonexistent — passes whether or not RLS ever worked), and `test_graphql_opportunities_query`'s own comment reads "May return empty list or error — either is fine as long as no crash." Neither test ever seeds a real row and checks it comes back.

## 6. Verification — genuine red→green, and an environment-methodology correction applied from the outset this time

New `tests/integration/test_graphql_resolvers_guc_db.py` (4 tests) calls the resolver functions directly (Strawberry's own invocation contract — a plain object exposing `.context`, plus positional args), against real seeded rows: `_get_company`, `_search_companies` (asserting it also does not raise), a `_create_opportunity` → `_opportunities` → `_pipeline` round trip, and `_update_company`.

Following report 129's disclosed correction, this container was set up correctly from the start: `02-app-role.sql` applied, then reconnected as `salesos_app` (`NOSUPERUSER NOBYPASSRLS`) for every test run in this investigation.

Reverting exactly the two fixed files (scoped `git stash push -- app/graphql/query.py app/graphql/mutation.py`): all 4 tests fail — each resolver's own `WHERE ... tenant_id = ...` query matches nothing despite the seeded row genuinely existing, confirmed directly in the SQL log (`SELECT ... WHERE companies.id = $1 AND companies.tenant_id = $2` immediately followed by `ROLLBACK`, no row). Restored: all 4 PASS.

Regression: this new suite (4) + the existing `tests/unit/test_graphql.py` (7, unaffected): **11/11 PASS**. Ruff (`E4,E7,E9,F,I`) on all 3 changed/new files: 0 findings. `compileall` and `git diff --check` clean.

## 7. Scope and safety

- Files changed: `salesos/backend/app/graphql/query.py` (4 resolvers: GUC pin + the `_search_companies` tenant_id fix), `salesos/backend/app/graphql/mutation.py` (2 resolvers: GUC pin + commit), `salesos/backend/tests/integration/test_graphql_resolvers_guc_db.py` (new).
- `salesos_test` and production: untouched. Only the disposable container was written to.
- No gate closed by this report. No auto-merge, auto-resolution, or cluster-certify attempted.

## 8. Loop status

Continuing the standing 24-hour continuous-loop authorization. This closes the GUC/RLS-pinning audit's remaining candidate list from report 129 (`relationships/store.py`, `quote/engine/service.py`, `agent_runtime/dispatcher.py`, `agent_runtime/tasks.py`, `signal_actions/hitl_router.py`, `signal_actions/router.py` — all checked and confirmed clean) plus a wider re-grep that surfaced this report's finding (`app/graphql/query.py`, `app/graphql/mutation.py`) and two more clean files (`app/modules/gtm/durable_store.py`, `runtime/nba_engine/api/router.py`). Remaining unchecked from that wider grep: `app/main.py`, `app/startup.py`, `app/modules/signal_marketplace/seeding.py` (all likely boot-time/platform-scope, lower priority) and `app/tasks.py` (5 `async_session()` sites, zero GUC pinning anywhere in the file — a real candidate for the next tick).
