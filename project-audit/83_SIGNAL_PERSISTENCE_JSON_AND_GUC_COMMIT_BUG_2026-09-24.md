# 83 — Company 360's signal persistence: invalid JSON serialization + a commit that silently wipes the tenant GUC mid-request (2026-09-24)

## Summary

`app/modules/company/signal_persistence.py`'s `upsert_signals()` is called
live from `app/modules/company/service.py`'s Company 360 view, with the
exact pattern: *persist computed signals, then immediately read them back
on the same request-scoped session* to build the "lifecycle-enriched"
response (also called from `app/modules/signal_marketplace/runtime_bridge.py`
on its own standalone session). Two independent bugs, together meaning
this feature has likely never worked correctly for any signal with real
extra data:

1. **`str(metadata)` is not valid JSON.** `company_signals.metadata` is
   `jsonb`; the code passed Python's `str(dict)` (single-quoted-key repr)
   as the bind value for an `INSERT ... VALUES (..., :meta)`. Every real
   signal carrying any field beyond the six explicitly recognized ones
   (`type`/`severity`/`title`/`description`/`source`/`confidence_score`) —
   i.e. any signal with genuinely non-empty metadata — failed the INSERT
   with an invalid-JSON error, silently caught by the per-signal
   `except Exception`, leaving `persisted` at `0`. Reproduced directly: a
   signal dict with one extra field always failed to persist before the
   fix. Fixed with `json.dumps(metadata)` and an explicit
   `CAST(:meta AS jsonb)`.
2. **`upsert_signals()` calls `db.commit()` on a session it does not own,
   which silently strips the tenant RLS GUC for the rest of the request.**
   `apply_tenant_guc()` pins `app.tenant_id` transaction-locally
   (`is_local=true`, per DEC-085) — a commit ends that transaction and the
   pin along with it. `company/service.py`'s Company 360 view reuses the
   *same* request-scoped session for `read_signals()` immediately
   afterward. Without re-pinning, that read is invisibly RLS-blocked
   (`company_signals` has FORCE RLS) and always returns `[]` — **signals a
   request had just written were invisible to that same request's own
   follow-up read, every single time**, regardless of bug 1. Reproduced
   directly: even after fixing bug 1 alone, `read_signals()` on the same
   session still returned `[]` immediately after a successful
   `upsert_signals()` call.

Net effect on the live Company 360 page: the "compute → persist → read
back enriched" signals section could never actually show the enriched,
persisted view it was designed for — bug 2 alone made the read-back
always fail silently (falling back to the transient, non-lifecycle-
enriched compute result, per the module's own "fail-graceful" design), and
bug 1 meant even a from-scratch persistence attempt with real signal data
would fail outright.

The same "commit strips the GUC" hazard existed identically in this
module's other three mutating functions (`expire_stale_signals()`,
`acknowledge_signal()`, `resolve_signal()`) — currently dead code
(confirmed via grep: zero callers), fixed for consistency ahead of any
future caller, same posture as this session's other dead-code findings.

## Fixes

**`app/modules/company/signal_persistence.py`**:
- Added `import json` and `from app.database import apply_tenant_guc`.
- `upsert_signals()`'s INSERT: `:meta` → `CAST(:meta AS jsonb)`; bind value
  `str(metadata)` → `json.dumps(metadata)`.
- All 4 functions that call `db.commit()` (`upsert_signals`,
  `expire_stale_signals`, `acknowledge_signal`, `resolve_signal`): added
  `await apply_tenant_guc(db, tenant_id)` immediately after the commit.

## Verification

Fresh ephemeral `pgvector/pgvector:pg16` container, `salesos_app`
restricted role.

**New file**: `tests/integration/test_signal_persistence_db.py` (3 tests):
- `test_upsert_then_read_on_the_same_session_sees_the_persisted_signal` —
  reproduces `company/service.py`'s exact call pattern (upsert then read on
  the same session) with a signal carrying extra metadata; asserts both
  the persisted count and the read-back content are correct.
- `test_upsert_with_metadata_does_not_silently_fail` — two signals with
  different metadata shapes (a scalar and a nested dict) both persist.
- `test_acknowledge_then_read_on_the_same_session_sees_the_update` —
  confirms the same GUC-repin fix applies to `acknowledge_signal()`.

**Genuine red→green, both bugs isolated independently**:
1. Reverted `json.dumps(metadata)` back to `str(metadata)`: re-ran,
   confirmed the exact predicted failure (`assert 0 == 2`, both signals
   logged as `upsert_failed`). Restored, re-confirmed passing.
2. Removed the `apply_tenant_guc()` re-pin from `upsert_signals()` only:
   re-ran, confirmed the exact predicted failure (`assert 0 == 1`, empty
   read-back immediately after a successful persist). Restored, re-
   confirmed passing.

**Combined session regression** (all integration tests from reports
68/70–83 run together in the same container): **50/50 PASS**, no
cross-fix regressions.

**Full local unit suite** (`tests/unit/`): **3766 passed, 0 failed** (4
skipped, 7 xfailed, 3 xpassed — all pre-existing categories) — clean
baseline reconfirmed.

## Production / Phase 7

This is a live-bug fix directly affecting the Company 360 page's signals
section. No production or `salesos_test` write; only a disposable,
ephemeral Postgres container was used, destroyed after verification.
Phase 7 remains BLOCKED; production remains **NOT APPROVED**.
