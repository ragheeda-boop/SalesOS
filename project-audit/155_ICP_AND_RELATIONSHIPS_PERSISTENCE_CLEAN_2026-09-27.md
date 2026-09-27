# 155 — `app/modules/gtm/icp_persistence.py` and `app/modules/relationships/store.py`: both fully clean, live, and defensively engineered

**Read-only in scope of production/salesos_test.** Pure source-code review; no database container needed.

## 1. Scope — resuming the loop under the standing 24-hour authorization

Per the renewed loop instruction: corrected the specific candidate list given (`Recommendation`, `Meeting`, `Email`, `OpportunityContact`, `Review`, `Quota`, `Territory` in `postgres_repositories.py`) — all seven were already completed in reports 127-128 (`Recommendation` fixed; the other six confirmed clean, closing that file's 17-class sweep). Searched for genuinely unchecked domain/DB-model conversion files instead: grepped every file containing `_to_domain`/`_row_to_`/`_model_to_domain` across `app/`, `domains/`, `runtime/` and cross-referenced against this session's full history. Two files had never been checked: `app/modules/gtm/icp_persistence.py` and `app/modules/relationships/store.py`.

## 2. `icp_persistence.py` — fully clean, live, exceptionally carefully engineered

Read the full 446-line file. `ICPProfile`'s real dataclass fields (`id, tenant_id, name, criteria, weights, description, schema_version, is_active, created_at, updated_at`) match `_row_to_profile()`'s construction exactly, with an explicit fail-safe validation layer (malformed stored JSON raises `ICPError` rather than yielding a half-valid profile). All raw SQL uses `CAST(:x AS type)` correctly (never the `:x::type` bind-scanner quirk found repeatedly elsewhere this session — reports 75/82/95/138). `icp_profiles.id` is `String(16)`, correctly matching the 12-hex-char IDs generated when none is supplied; `tenant_id` is genuinely `Uuid()`, correctly cast in every statement. Every method (`create`/`update`/`get`/`delete`/`list_for_tenant`/`list_active`) pins `app.tenant_id` before its query.

`SyncICPStore` (the thread-isolated sync facade for the frozen grounded agents, ADR-0109 Option A) correctly uses a dedicated `NullPool` engine on its own private event-loop thread — the established, previously-verified-correct pattern for bridging asyncpg's loop-bound connections across a sync/async boundary (reports 24's own history). Confirmed genuinely live: `get_sync_icp_store()` is called from `app/routers/copilot.py:177`.

**No bug found.** Two unused `created_by`/`updated_by` UUID audit columns exist on the table but are never populated by this code — not a defect (nothing crashes or silently drops data that was supposed to be captured), just an unused audit-trail pair, noted for completeness only.

## 3. `relationships/store.py` — fully clean, live, and explicitly defends against this session's most common bug classes

Read the full 304-line file. `RelationshipEdge`'s real dataclass fields match `_row_to_edge()`'s construction exactly. Every raw SQL statement uses `CAST(:x AS uuid/jsonb)` correctly. Most notably, `create()`'s `IntegrityError` recovery path **explicitly documents and correctly handles** the exact "rollback() discards the transaction-local tenant GUC pin" gotcha this session found and fixed as a real, live bug in report 83 (`signal_persistence.py`) — this file's own in-source comment reads: *"rollback() ends the transaction and discards the transaction-local app.tenant_id GUC — re-pin or the recovery SELECT below would be filtered to zero rows by FORCE RLS,"* immediately followed by the correct `await self._pin(db, tenant_id)` call before the recovery `SELECT`. This is strong evidence the author was directly aware of this bug class and defended against it proactively.

Verified the one apparent anomaly (`supersede()`'s `UPDATE` sets `updated_at`, a column absent from `_SELECT_COLS`) is **not** a bug: `commercial_relationship_edges.updated_at` is a real, `NOT NULL` column (migration `u1v2w3x4y5z6`) — it is simply not part of the `RelationshipEdge` domain contract's exposed fields (the dataclass itself has no `updated_at` field either), so its absence from `_SELECT_COLS`/`_row_to_edge()` is consistent, not a mismatch.

Confirmed genuinely live: `app/routers/relationships.py:41` constructs `RelationshipStore()`, and that router is mounted at boot (`app/boot/routers.py:152,154`, `/api/v1`, "Commercial Relationships").

**No bug found.**

## 4. Scope and safety

- No files changed — no bugs found in either file, matching the established practice of reporting genuine clean results rather than manufacturing findings.
- No database or container needed (pure source-code cross-reference against already-confirmed real schema/dataclass definitions).
- No gate closed by this report. No auto-merge, auto-resolution, or cluster-certify attempted.

## 5. Loop status

Continuing the standing 24-hour continuous-loop authorization. Disk space checked before starting (~2.46 GB free on D: — healthy). Both files checked in this tick represent this session's third consecutive genuinely clean result in the "domain contract vs. DB model" methodology after the earlier `postgres_repositories.py` sweep's high bug-yield — suggesting the remaining unchecked files in this codebase skew toward more recently-written, more carefully-reviewed code. Continuing to search for further unchecked candidates.
