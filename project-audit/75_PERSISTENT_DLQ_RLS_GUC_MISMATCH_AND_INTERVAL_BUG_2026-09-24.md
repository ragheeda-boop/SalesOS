# 75 — PersistentDeadLetterQueue: unsatisfiable RLS policy + missing GUC pinning + broken INTERVAL bind (2026-09-24)

## Summary

`runtime/event_runtime/persistent_dlq.py`'s `PersistentDeadLetterQueue` is the
**one genuinely live** class found broken this session (unlike the
dead/unregistered classes in reports 73 and 74) — it is wired into every
`EventRuntime` in production via `app/boot/startup.py`'s
`EventRuntime(session_factory=async_session, ...)`, and its `add()` method is
called for real every time a subscriber exhausts its retries. Three
independent, compounding bugs meant this class's entire reason for existing
("dead-lettered events survive process restarts") has never actually held:

1. **The table's own RLS policy checked a GUC variable name no code has ever
   set.** `event_dead_letters`'s original migration
   (`g1h2i3j4k5l6_phase4_dlq_persistence.py`) created its policy as:
   ```sql
   CREATE POLICY event_dl_tenant_isolation ON event_dead_letters
   USING (tenant_id = current_setting('app.current_tenant_id', true))
   ```
   Every other tenant-isolated table in this codebase uses the single
   universal convention `app.tenant_id`, set via
   `app.database.apply_tenant_guc()` / `set_config('app.tenant_id', ...)`.
   `app.current_tenant_id` has never been set by any code in this repository
   — confirmed via repo-wide grep. This made the policy permanently
   unsatisfiable regardless of any Python-level fix: even a session that
   correctly pins `app.tenant_id` still fails the `WITH CHECK`, because the
   policy is checking a different, always-NULL setting.
2. **No GUC pinning anywhere in the class.** None of `add`, `list_all`,
   `count`, `mark_replayed`, `purge_old` ever pinned `app.tenant_id` before
   querying — a second, independent bug on top of (1). Fixing only the
   migration without this would still fail (unpinned session → NULL GUC →
   policy still not satisfied); fixing only this without the migration would
   still fail (correct GUC name, but the policy checks the wrong one).
   Confirmed both are independently necessary via two separate red→green
   passes (see Verification).
3. **`purge_old()`'s `INTERVAL ':days days'`.** A bind parameter embedded
   inside a quoted string literal is not a valid asyncpg positional
   parameter — confirmed in isolation with a standalone script:
   `asyncpg.exceptions._base.InterfaceError: the server expects 0 arguments
   for this query, 1 was passed`. Every real call raised, was caught by the
   method's own `except Exception: return 0`, and silently returned 0 — old,
   already-replayed dead-letter rows were never purged. Fixed to
   `make_interval(days => :days)`.

Net effect before this fix: every real `add()` call from a genuinely
exhausted production subscriber silently failed (caught by `add()`'s own
`except Exception: logger.error("dlq_persist_failed", ...)`), meaning the
*only* copy of a dead-lettered event was the separate in-memory
`DeadLetterQueue`, which does not survive a process restart — exactly the
failure mode this class exists to prevent.

## Live vs. dead-code posture (continuing this session's established distinction)

`add()` is confirmed **live** (real call site: `EventRuntime._dispatch` on
subscriber exhaustion, wired at boot). `list_all`, `count`, `mark_replayed`,
`purge_old` have **zero callers anywhere in the codebase today** (confirmed
via repo-wide grep — the REST endpoints at `runtime/event_runtime/router.py`
read the separate in-memory `dead_letter_queue`, not this class) — fixed
ahead of any future caller, same posture as reports 73/74's findings, but
`add()` itself was actively losing production data today, not merely latent.

`mark_replayed`'s signature was widened from `mark_replayed(entry_id: str)`
to `mark_replayed(entry_id: str, tenant_id: str)` — safe because it has no
existing callers to break — so its own query could be tenant-scoped rather
than only tenant-pinned via GUC.

## Fixes

**`runtime/event_runtime/persistent_dlq.py`**:
- Added `from app.database import apply_tenant_guc` import.
- `add()`: pin `app.tenant_id` before the INSERT.
- `list_all()`, `count()`: pin `app.tenant_id` before the SELECT.
- `mark_replayed()`: widened signature to accept `tenant_id`; pin GUC; added
  explicit `AND tenant_id = :tenant_id` to the WHERE clause.
- `purge_old()`: pin GUC; fixed `INTERVAL ':days days'` →
  `make_interval(days => :days)`.

**`app/alembic/versions/f2e3d4c5b6a7_fix_event_dead_letters_guc_name.py`**
(new migration, new Alembic head, `down_revision = "e1d1c1225d00"`):
- Drops the wrong `event_dl_tenant_isolation` policy.
- Regenerates the canonical `tenant_isolation_event_dead_letters` policy via
  `app.alembic.lib.rls.generate_policy_sql()` — the same helper used for
  every other Category A tenant-isolation policy in this repo — checking
  `app.tenant_id` with both `USING` and `WITH CHECK`.
- Does not touch the table's columns, indexes, or ENABLE/FORCE RLS state
  (both already correct in the original migration).
- `downgrade()` restores the exact original wrong-GUC-name policy text, for a
  clean round trip.

**`tests/unit/test_phase4_platform.py`**: updated
`test_persistent_dlq_add_calls_session` (previously asserted
`execute.assert_called_once()`, now broken by the added GUC-pin call) to
assert `execute.await_count == 2`, with the first call's SQL containing
`set_config` and its params `{"tenant_id": "t-123"}`, and the second being
the INSERT — matching the new real call sequence.

## Verification

All on a fresh ephemeral `pgvector/pgvector:pg16` container, migrated from
zero to the new head `f2e3d4c5b6a7`, `salesos_app` restricted role
(non-superuser, `NOBYPASSRLS`).

**New file**: `tests/integration/test_persistent_dlq_rls_and_interval_db.py`
(2 tests):
- `test_add_persists_under_rls_and_is_tenant_scoped` — `add()` genuinely
  persists (`count(tenant_a) == 1`), and RLS correctly hides it from a
  different tenant (`count(tenant_b) == 0`).
- `test_purge_old_deletes_replayed_entries_past_the_window` — seeds one old
  (60-day) replayed entry and one recent replayed entry, calls
  `purge_old(older_than_days=30)`, asserts it deletes exactly the old one
  (`purged == 1`) and the recent one survives.

**Genuine red→green, both bugs isolated independently**:
1. *Migration-only isolation*: with the migration `f2e3d4c5b6a7` applied but
   the code-level `apply_tenant_guc()` call in `add()` temporarily removed,
   re-ran the test — confirmed it failed exactly as predicted
   (`assert 0 == 1`, with `dlq_persist_failed` logged). Restored the code
   fix, re-confirmed passing. This proves the GUC-pin code fix is necessary
   *even with* the corrected migration in place.
2. *Interval-bug isolation*: with the GUC pinning and migration both correct,
   reverted only `make_interval(days => :days)` back to
   `INTERVAL ':days days'`, re-ran `test_purge_old_deletes_replayed_entries_past_the_window`
   — confirmed it failed exactly as predicted (`assert 0 == 1`, the delete
   silently caught and returning 0). Restored the fix, re-confirmed passing.
3. *Migration round trip*: `downgrade()` → `upgrade()` confirmed via direct
   `pg_policy`/`pg_get_expr` inspection — downgrade correctly restores the
   original wrong-GUC-name policy text; upgrade correctly restores the
   `app.tenant_id`-checking policy with both `USING` and `WITH CHECK`.

**Unit regression**: `tests/unit/test_phase4_platform.py` —
`TestPersistentDeadLetterQueue` 7/7 pass with the updated call-count
assertion.

**Combined session regression** (all integration tests from reports 68/70–75
run together in the same container): **31/31 PASS**, no cross-fix
regressions — `test_dec157_orphan_keep_rls_db.py` (9), `test_effectiveness_force_rls.py` (1),
`test_relationships_rls.py` (7), `test_pipeline_analytics_score_deal_db.py` (2),
`test_knowledge_graph_custom_query_db.py` (3), `test_deal_health_computer_db.py` (1),
`test_attribution_engine_injection_and_isolation_db.py` (3),
`test_license_find_expiring_date_boundary_db.py` (3),
`test_persistent_dlq_rls_and_interval_db.py` (2).

**Full local unit suite** (`tests/unit/`, local Windows Python):
**3766 passed, 4 skipped, 7 xfailed, 3 xpassed, 0 failed** — clean baseline,
confirms the `test_phase4_platform.py` contract update and no other
regressions from this session's cumulative changes.

## Production / Phase 7

No production or `salesos_test` write. All verification used a disposable,
ephemeral Postgres container, destroyed after use. Phase 7 remains BLOCKED;
production remains **NOT APPROVED**.
