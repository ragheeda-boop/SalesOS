# 80 — GET /api/v1/search: cursor-based pagination was completely non-functional (2026-09-24)

## Summary

While reviewing `runtime/search_runtime/router.py` (companion file to
report 79's `SearchRuntime` fixes), found that `GET /api/v1/search`'s
pagination has never actually worked for any caller that follows the
API's own contract. This router is genuinely live (mounted at boot, real
REST endpoint), and had **zero prior test coverage of any kind** —
confirmed via grep, no test file referenced this router before this
session.

Two independent bugs:

1. **`decode_cursor` was imported but never called anywhere in the
   function.** `offset` passed to `SearchRuntime.search()` was hardcoded
   to `0` regardless of the `cursor` query parameter. Every response
   correctly generated a `next_cursor`, but following it in a subsequent
   request silently returned page 1 again — pagination beyond the first
   page was completely broken for every real caller, with no error of any
   kind to signal it.
2. **The cursor's sort-value component was fabricated.** `next_cursor` was
   built from `getattr(last, "created_at", None)`, but `SearchResultItem`
   (the dataclass every search result item actually is) has no
   `created_at` attribute at all — the `getattr` always returned `None`,
   falling back to `datetime.utcnow().isoformat()` on every single call.
   Even if bug 1 were fixed by actually decoding the keyset cursor, the
   encoded sort value would never correspond to anything real.

Root cause: `SearchRuntime.search()` only ever supports a plain numeric
`offset` — none of its fulltext/semantic/hybrid query paths implement a
true keyset `WHERE` condition. The router nonetheless reused
`sdk.pagination`'s generic `encode_cursor`/`decode_cursor`, which is
designed for genuine id+sort_value keyset pagination (used correctly
elsewhere in this codebase for endpoints whose queries do implement that
condition) — a capability this endpoint's underlying search engine never
had. That mismatch, not a typo, is why `decode_cursor` was imported and
then silently never used: there was nothing meaningful to decode into.

## Fix

**`runtime/search_runtime/router.py`**:
- Removed the unused `from sdk.pagination import decode_cursor,
  encode_cursor` import (and the now-unused `datetime` import).
- Added two small local functions matching what this endpoint can actually
  do: `_encode_offset_cursor(offset: int) -> str` and
  `_decode_offset_cursor(cursor: str) -> int` — a plain base64-encoded
  integer offset, with `HTTPException(422)` on a malformed or negative
  value (rather than silently ignoring it, matching the "reject, don't
  ignore" posture used elsewhere in this codebase).
- `search()`: decode `cursor` into a real `offset` before calling
  `sr.search(...)`; encode `next_cursor` from `offset + limit`.
- Deliberately did **not** attempt to retrofit a true keyset condition into
  `SearchRuntime`'s query methods — that would be a materially larger
  change spanning every strategy's SQL construction, and this endpoint
  never actually needed keyset semantics in the first place; offset-based
  pagination is a complete, working fix for what this API genuinely
  supports.

## Verification

Fresh ephemeral `pgvector/pgvector:pg16` container, `salesos_app`
restricted role.

**New file**: `tests/integration/test_search_runtime_router_pagination_db.py`
(2 tests, real HTTP requests via `TestClient` against the actual mounted
router):
- `test_next_cursor_actually_advances_to_a_different_page` — seeds 7
  companies, requests page 1 (`limit=5`), follows the returned
  `next_cursor`, and asserts page 2 returns the remaining 2 rows with **no
  overlap** with page 1's row IDs.
- `test_invalid_cursor_is_rejected_not_silently_ignored` — a malformed
  cursor value returns `422`, not a silent fallback to page 1.

**Genuine red→green**: reverted the fix (`offset` hardcoded back to `0`,
`next_cursor` always encoding `0 + limit`), re-ran the pagination test —
confirmed it failed with the exact predicted symptom:
`AssertionError: assert 5 == 2`, with page 2's 5 returned rows being the
identical IDs as page 1's. Restored, re-confirmed both tests passing.

**Combined session regression** (all integration tests from reports
68/70–80 run together in the same container): **42/42 PASS**, no
cross-fix regressions.

**Full local unit suite** (`tests/unit/`): **3766 passed, 0 failed** (4
skipped, 7 xfailed, 3 xpassed — all pre-existing categories) — clean
baseline reconfirmed.

## Production / Phase 7

This is a live-bug fix: any real client of `GET /api/v1/search` that
followed the documented `next_cursor`/pagination contract has never been
able to see results past the first page. No production or `salesos_test`
write; only a disposable, ephemeral Postgres container was used, destroyed
after verification. Phase 7 remains BLOCKED; production remains **NOT
APPROVED**.
