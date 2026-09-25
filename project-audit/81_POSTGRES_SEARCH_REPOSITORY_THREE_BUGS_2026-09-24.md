# 81 — PostgresSearchRepository: the real production search backend, with 3 independent pagination/filter bugs (2026-09-24)

## Summary

While widening this session's file-review from `runtime/` to `domains/`,
found `domains/search/engine/postgres_repo.py`'s `PostgresSearchRepository`
— confirmed via grep as the **actual production search backend**: wired at
boot (`app/boot/startup.py`) as `SearchRuntime(..., search_repo=
PostgresSearchRepository(session_factory=async_session))`, and
`SearchRuntime._fulltext_search()`/`suggest()` delegate to it whenever
`search_repo` is set — which it always is. This class had **zero dedicated
test coverage** before this session (confirmed via grep: no test file
exercised its real behavior). Three independent bugs found:

1. **The `"activity"` filter field's underlying column stub was a second,
   separate, nonexistent `activity` column** — identical bug to report 79's
   finding in the sibling `runtime/search_runtime/__init__.py`. The table
   already declared a correct `activity_description` column further down.
   Fixed the same way: removed the duplicate stub, renamed the public
   `ALLOWED_FILTER_FIELDS` entry from `"activity"` to
   `"activity_description"`. Not reachable from any live router today (no
   endpoint exposes this filter), fixed ahead of any future caller.

2. **Page 1 of any search never generated a `next_cursor`, even when more
   results existed.** `search_raw()`/`search_by_filters()` only over-fetched
   `safe_limit + 1` rows (the technique `_finalize_search_rows()` uses to
   detect "there's more") when `use_cursor` was already `True` — but on a
   genuine first request there is no cursor yet, so the plain-offset branch
   fetched exactly `safe_limit` rows and `has_next` could never be `True`.
   This is a hard deadlock: a client can never obtain the first cursor
   needed to reach page 2, even though `total` (correctly computed via a
   window function) shows more rows exist. Found by my own new test — the
   very first version of it failed with `next_cursor is None` on an
   explicitly 5-row, 3-per-page seed. Fixed by always over-fetching by 1,
   applying the `offset()` only in the non-cursor branch.

3. **`encode_search_cursor()`'s `round(rank, 10)` broke the keyset
   equality tie-break for any two rows with the same rank.** `ts_rank()`
   returns Postgres `real` (float4, confirmed via `pg_typeof`); once
   promoted to Python float64 it commonly shows many apparent decimal
   places of representation noise (e.g.
   `0.0607927106320858` for a value that only has ~7 significant figures of
   real precision). `round(rank, 10)` truncated to 10 *decimal places*
   (not significant figures), producing a value
   (`0.0607927106`) that no longer exactly equals the same row's freshly
   recomputed rank on the next query. Since `_cursor_predicate()`'s tie-break
   branches all require `rank_expr == cursor_rank`, and the truncated
   cursor value could no longer match (nor did it correctly compare `<`,
   since the truncation could go either direction), **every row failed
   every branch of the predicate** whenever there was a real tie — a very
   common real-world case (bulk-inserted rows sharing an identical
   `updated_at` within one transaction, and/or identical `ts_rank` for
   similarly-scored matches). The result: page 2 silently returned **zero
   rows and `total=0`**, not merely the wrong rows. Fixed by removing the
   rounding entirely — `json.dumps` round-trips a Python float exactly
   (repr-precision), so there was never a reason to round in the first
   place.

Bugs 2 and 3 compound: even after fixing bug 2 (so a `next_cursor` is
finally produced), bug 3 alone was enough to make following that cursor
return nothing. Both were required for real pagination to work at all.

## Fixes

**`domains/search/engine/postgres_repo.py`**:
- `ALLOWED_FILTER_FIELDS`: `"activity"` → `"activity_description"`.
- Table stub: removed the duplicate `column("activity", String)`.
- `search_raw()` and `search_by_filters()`: changed
  `if use_cursor: stmt.limit(safe_limit+1) else: stmt.limit(safe_limit).offset(offset)`
  to always `stmt.limit(safe_limit + 1)`, applying `.offset(offset)` only
  when not using a cursor.
- `encode_search_cursor()`: `round(rank, 10)` → `rank` (no rounding).

## Verification

Fresh ephemeral `pgvector/pgvector:pg16` container, `salesos_app`
restricted role.

**New file**: `tests/integration/test_postgres_search_repository_db.py`
(2 tests):
- `test_activity_description_filter_field_works_end_to_end` — confirms the
  renamed filter field works via `search_by_filters()`.
- `test_real_keyset_cursor_pagination_advances_correctly` — seeds 5 rows,
  requests page 1 (`page_size=3`) via the real `SearchQuery`/`search()`
  entry point, confirms a `next_cursor` is produced, follows it, and
  confirms page 2 returns the remaining 2 *disjoint* rows.

**Genuine red→green, all 3 bugs isolated independently**:
- Bug 2: reverted just `search_raw()`'s over-fetch change back to the
  original `if use_cursor: ... else: ...` branch, re-ran, confirmed the
  exact predicted failure (`next_cursor is None` despite `total=5` and
  `page_size=3`). Restored, re-confirmed.
- Bug 3: reverted just the rounding fix, re-ran, confirmed the exact
  predicted failure (`assert 0 == 2`, `total=0`, empty items on page 2).
  Restored, re-confirmed.
- Bug 1 verified the same way as report 79's identical fix (schema
  inspection confirming no bare `activity` column exists, plus the passing
  filter test).
- A standalone debug script (outside the test suite, deleted after use)
  reproduced the exact root cause live: `ts_rank` confirmed as `real` via
  `pg_typeof`, and the raw rank/cursor values printed showed the precise
  `0.0607927106320858` vs `0.0607927106` mismatch before the fix.

**Combined session regression** (all integration tests from reports
68/70–81 run together in the same container): **44/44 PASS**, no
cross-fix regressions.

**Full local unit suite** (`tests/unit/`): **3766 passed, 0 failed** (4
skipped, 7 xfailed, 3 xpassed — all pre-existing categories) — clean
baseline reconfirmed.

## Production / Phase 7

This is a live-bug fix in the actual production search backend: pagination
past page 1 was never reachable at all (bug 2), and even a corrected
`next_cursor` would have returned nothing whenever rank ties occurred (bug
3) — a realistic, common condition, not an edge case. No production or
`salesos_test` write; only a disposable, ephemeral Postgres container was
used, destroyed after verification. Phase 7 remains BLOCKED; production
remains **NOT APPROVED**.
