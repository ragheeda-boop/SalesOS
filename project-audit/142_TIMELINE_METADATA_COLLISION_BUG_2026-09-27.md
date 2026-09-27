# 142 — domains/timeline/engine/postgres_repo.py: caller metadata could silently corrupt or crash reads; a separate dead-scoring-logic finding disclosed

**Ephemeral, disposable Postgres container only (`sweep-pg15`, `pgvector/pgvector:pg16`, destroyed after use).** No `salesos_test` or production contact.

## 1. Scope — fourth file in the `domains/*/postgres_repo.py` sweep

`domains/timeline/engine/postgres_repo.py` (207 lines, `PostgresTimelineRepository`) checked against `domains/timeline/models.py`'s `TimelineEventModel` and `domains/timeline/contracts/models.py`'s `TimelineEvent`/`Actor`/`Target` dataclasses.

## 2. The real bug — caller-supplied metadata could silently overwrite reserved serialization keys, crashing the next read

`append()` built its JSONB payload as:

```python
payload = {
    "actor": _serialize_actor(event.actor),
    "target": {...},
    "outcome": event.outcome.value,
    "event_id": event.event_id,
    **event.metadata,
}
```

`event.metadata` is spread **last**, at the top level, alongside the four reserved serialization keys. `TimelineRecorder.on_domain_event()` (`domains/timeline/engine/recorder.py:151`) passes `metadata=data` — the **raw** domain-event payload dict, straight through with no filtering. `app/boot/startup.py`'s `_init_timeline_subscriber()` wires a wildcard subscription (`event_runtime.register("*", _on_timeline_event, ...)`) that routes **every domain event published anywhere in the application** through this exact path via `app.state.timeline_recorder` — this table is genuinely, heavily live (confirmed via `_init_timeline_recorder`'s `FactoryBoundRepository(PostgresTimelineRepository, async_session)` wiring), not dead code.

If any real domain event's `data` payload ever contains a top-level key literally named `"actor"`, `"target"`, `"outcome"`, or `"event_id"` — plausible for many event shapes across dozens of independent publishers in this codebase — the dict-literal spread silently overwrites the reserved serialization field with whatever value the caller's metadata happened to carry, no error at write time. If that overwritten value isn't the expected dict shape, the **next read** of that row crashes: `_row_to_event()` → `_deserialize_actor(data, ...)` calls `a.get(...)` on `data["actor"]` unconditionally — an `AttributeError: 'str' object has no attribute 'get'` if `data["actor"]` is now a plain string. `query()`/`get_by_target()`/`get_by_actor()` rebuild every row in one list comprehension with no per-row exception handling, so a single poisoned row breaks the **entire page**.

## 3. Fix — eliminate the collision at the source; harden the read side against any already-existing corruption

- **`append()`**: nest metadata under its own `"metadata"` key (`"metadata": dict(event.metadata)`) instead of splatting it at the top level. This removes the entire collision class for every future write, permanently.
- **`_row_to_event()`**: reads `data.get("metadata")` first; if it's a dict, uses it directly. Otherwise falls back to the old flat-extraction shape (`{k: v for k, v in data.items() if k not in (...)}`) — **backward compatible** with every row already written under the old format, since this table has been live since the app's early history.
- **`_deserialize_actor()` / `_deserialize_target()`**: hardened with `isinstance(a, dict)` / `isinstance(t, dict)` checks before calling `.get(...)`, falling back to the safe default (system actor / column-derived target) instead of crashing — defends against any row that may already be corrupted in a live database from before this fix, not just future writes. `_deserialize_actor` also wraps the `ActorType(...)` enum lookup in a `try/except ValueError` for the same reason.

## 4. Verification — genuine red→green

New `tests/integration/test_timeline_metadata_collision_db.py` (2 tests) against a fresh, disposable, fully-migrated Postgres container (`e1d1c1225d00`/`a1b2c3d4e5f7` head — includes this session's own DEC-157 and `graph_nodes` RLS migrations):

- `test_metadata_key_named_actor_does_not_corrupt_or_crash`: writes an event with `metadata={"actor": "some-unrelated-string-value", ...}`, reads it back, asserts the **real** actor (`user-42`/`Real Caller`) survived untouched and the caller's own `"actor"` metadata key round-tripped correctly.
- `test_legacy_flat_splatted_row_still_reads_back`: hand-inserts a `TimelineEventModel` row in the **old** flat-splatted shape (no nested `"metadata"` key) and confirms it still reads back correctly — proving backward compatibility.

Reverting exactly the fixed file (scoped `git stash push -- salesos/backend/domains/timeline/engine/postgres_repo.py`): the collision test fails with the **exact predicted** `AttributeError: 'str' object has no attribute 'get'` at `postgres_repo.py:29` (raw INSERT payload confirmed in the captured SQL log: `{"actor": "some-unrelated-string-value", ...}` — the real actor was genuinely overwritten); the legacy-compat test still passes (expected — the reverted code *is* the legacy format). Restored: both PASS.

Regression: `domains/timeline/tests/test_timeline.py` (12 tests) + both new tests: **14/14 PASS**, no change. Ruff (`E4,E7,E9,F,I`): 3 pre-existing, unrelated findings (`I001`/`F401`) in the changed file, identical before and after (confirmed via scoped stash/pop — only the line number of the second `I001` shifted from the added lines, 0 new findings); the new test file is Ruff-clean. `compileall` and `git diff --check` clean.

## 5. A separate, disclosed non-bug: `_calc_importance()` scores 8 event types that can never occur

`_calc_importance()`'s `high`/`medium` sets reference 8 event-type strings (`"deal.won"`, `"deal.lost"`, `"contract.renewed"`, `"decision.created"`, `"decision.accepted"`, `"golden_record.created"`, `"company.enriched"`, `"funding.received"`) that do not exist anywhere in `ActivityType`'s strict 12-value enum. Confirmed `PostgresTimelineRepository.append()` is the **only** real production writer to `timeline_entries` (repo-wide grep; the one other match is an unrelated test file's own direct SQL setup), and `event_type=event.activity.value` can therefore never be one of these 8 strings — they are permanently unreachable dead branches inside the scoring function. Also confirmed `TimelineEventModel.importance` has **zero** downstream consumers anywhere in the codebase (a second grep found the only other "importance" reference in `domains/timeline/` is an unrelated Decision Platform score dict field, not this column) — this is a write-only, never-read database column. **Not fixed**: with zero consumers, this is a cosmetic scoring-completeness gap with no observable behavioral impact, not a defect matching this session's bar for "real bug" (crash, data loss, or incorrect user-visible output). Documented for visibility only.

## 6. Scope and safety

- Files changed: `salesos/backend/domains/timeline/engine/postgres_repo.py` (fix), `salesos/backend/tests/integration/test_timeline_metadata_collision_db.py` (new).
- One disposable, ephemeral Postgres container (`sweep-pg15`) used for verification; destroyed after (`docker rm -f`). No `salesos_test` or production contact.
- No gate closed by this report. No auto-merge, auto-resolution, or cluster-certify attempted.

## 7. Loop status

Continuing the standing 24-hour continuous-loop authorization. This is the fourth file checked in the `domains/*/postgres_repo.py` sweep and the first with a genuine bug (after three clean results: `decision_center` report 139, `feature_store` report 140, `workflow` report 141) — a real, live, previously-undetected defect in a heavily-used, wildcard-subscribed write path. Remaining candidates: `domains/notifications/postgres_repo.py`, `domains/employee/postgres_repo.py`.
