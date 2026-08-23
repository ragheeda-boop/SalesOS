# ADR-0109: ICP Profile Persistence (Postgres) and Runtime Wiring Decision

- **Status:** ACCEPTED (Option A implemented in Phase 4B, same day — see Implementation below)
- **Date:** 2026-08-23
- **Deciders:** PO + TL
- **Phase:** 4A — Security + ICP Foundation Gate
- **Related:** DEC-085 (canonical RLS / `app.tenant_id` GUC), Phase 3A/3B grounded agents, Data Readiness Gate report (2026-08-23)

## Context

Grounded Phases 1–3B proved all 13 intelligence agents against the single EvidencePack with deterministic zero-LLM contracts. The Data Readiness Gate (same day) scored **22/100** and identified the ICP layer as the first structural gap: profiles lived only in an in-memory store (`MemICPStore`), so every restart lost them and no tenant could ever have a real profile in a deployed environment.

## Decision

1. **Persist ICP profiles in Postgres** behind the canonical RLS pattern:
   - Table `icp_profiles` (migration `h2i3j4k5l6m8_phase4a_icp_profiles.py`), columns mirror the `ICPProfile` contract exactly (`criteria`/`weights` as JSONB payloads).
   - One policy `tenant_isolation_icp_profiles`, `USING ((tenant_id)::text = current_setting('app.tenant_id', true)) WITH CHECK (...)`, `ENABLE`+`FORCE ROW LEVEL SECURITY`.
   - Repository: `app/modules/gtm/icp_persistence.py::PostgresICPRepository` — async API matching `MemICPStore` semantics (create/get/update/list_for_tenant/list_active), per-statement GUC pin, version bump on update, fail-safe mapper that raises `ICPError` on any malformed stored payload instead of returning half-valid data.
2. **RAG corpus isolation closed** (migration `h1i2j3k4l5m7_phase4a_rag_rls.py`): direct tenant policy on `rag_documents`; chunks isolated via an `EXISTS` parent-document probe in both `USING` and `WITH CHECK` (no schema change to `rag_document_chunks`). Proven by `tests/unit/test_rag_rls.py` (8/8): no-GUC sees zero rows, cross-tenant read/write both blocked.
3. **Signal catalog classified GLOBAL_PLATFORM**: `signal_catalog` has no tenant_id and is populated from platform Knowledge Pack manifests; its read paths are intentionally unfiltered. Tenant-owned siblings (`signal_events`, `signal_subscriptions`) already carry canonical RLS policies.

## Consequences

- ICP profiles survive restarts and are tenant-isolated at the database level, not just application level.
- The persistence layer is **not yet consumed at runtime**: agents still receive `DEFAULT_ICP_STORE` (in-memory). This is deliberate — agent files are frozen during Phase 4A.
- Zero data population performed: local `icp_profiles` and `rag_documents` counts remain 0 outside transient test rows.

## DECISION REQUIRED (PO + TL): runtime wiring of ICP storage

The grounded ICP/recommendation agents call the store **synchronously** (`_active_profiles(store, tenant)` at `intelligence/agents/icp.py:53`) and default to `DEFAULT_ICP_STORE` when none is injected (`icp.py:217-219`). The new repository is **async**. Options:

| Option | Description | Trade-off |
|--------|-------------|-----------|
| **A — Adapter (recommended)** | Thin sync facade over the async repo (dedicated loop or pre-warmed cache per request) injected via the existing `icp_store=` parameter in `copilot.py`. Agents untouched. | Small adapter surface; keeps agent freeze intact |
| **B — Async-native agents** | Change agent call path to await the repo | Touches all 13 agents' shared loader path — violates Phase 4A freeze |
| **C — Dual-write shim** | Keep MemICPStore as the agent-facing store; background writer mirrors to Postgres | Eventual consistency; divergence risk |

Recommendation: **Option A**, executed in a dedicated follow-up phase with live A/B/C probes repeated after the swap.

## Implementation (Phase 4B, 2026-08-23 — Option A)

`SyncICPStore` lives beside the repository in `app/modules/gtm/icp_persistence.py`:

- **Dedicated event loop thread** (`icp-sync-adapter`, daemon): agent calls are synchronous while FastAPI's loop keeps running; coroutines are dispatched via `run_coroutine_threadsafe`.
- **Dedicated engine (NullPool)** built from `settings.app_database_url`: asyncpg connections bind to the loop that created them, so the adapter never shares the global app pool across loops. `PostgresICPRepository` now honors an injected session factory.
- **Failure containment**: read paths (`get`/`list_for_tenant`/`list_active`) degrade to honest-empty (`None`/`[]`) with a warning log — agents then emit their existing no-profile / INSUFFICIENT contracts instead of raising. Writes propagate errors.
- **Wiring**: `_build_coordinator()` in `app/routers/copilot.py` passes one shared `get_sync_icp_store()` singleton into both `ICPAgent(icp_store=…)` and `RecommendationAgent(icp_store=…)`. Zero agent-file changes.

### Verification
- `tests/unit/test_icp_sync_adapter.py` — 8 passed (sync-contract parity incl. version bump, cross-tenant None, scoping, failure containment, singleton identity)
- Live probes through `_build_coordinator` wiring:
  - Tenant A + pif company: `fit=UNKNOWN`, "No active ICP profile is available for this tenant.", 11 evidence items, 0.23s, `llm_called=False`
  - Tenant B cross-tenant: INSUFFICIENT EVIDENCE, 0.01s
  - Tenant C recommend cross-tenant: NO ACTION / INSUFFICIENT EVIDENCE, 0.00s
- Combined grounded+security scope after wiring: **126/126 passed**
- Quota unchanged: 44,535 ai_tokens / 52 events; `icp_profiles`=0 and `rag_documents`=0 outside transient test rows

### Phase 4C addendum — Admin API + full value loop (same day)

- `app/modules/gtm/icp_admin_router.py` exposes tenant-scoped CRUD (`GET/POST /api/v1/icp/profiles`, `GET/PATCH /icp/profiles/{id}`) over the repository; registered under `_auth` in `boot/routers.py`. Tenant identity always comes from auth deps, never the body. `PostgresICPRepository.delete()` added for lifecycle completeness.
- Fixed a persistence bug found by API tests: a criteria-only update previously **reset weights to defaults**; absent weights now mean "unchanged".
- Live end-to-end value proof (transient demo profile via the admin path): ICP agent returned `fit=MEDIUM`, 4 criteria evaluated with PASS/FAIL per criterion (`basis: DERIVED`, evidence [E2][E10]), score 3.0/6.0, confidence 0.8, zero LLM — then cleanup restored zero rows. The P1 data action is now unblocked: PO/Data can populate real profiles through the supported API instead of SQL.

## Verification

- `tests/unit/test_rag_rls.py` — 8 passed (isolation, no-GUC, FORCE flags guard)
- `tests/unit/test_icp_persistence.py` — 12 passed (cross-tenant None, no-GUC zero, version bump semantics, malformed-payload fail-safe, agent-contract mirror)
- `alembic current == h2i3j4k5l6m8` locally; `pg_policies` shows all three policies; persistent row counts 0 after runs
