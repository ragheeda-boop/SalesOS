# 82 — HybridSearchEngine (domains/search): 4 independent bugs, dead code (2026-09-24)

## Summary

`domains/search/engine/hybrid_search.py`'s `HybridSearchEngine` blends
full-text and semantic search via Reciprocal Rank Fusion. **Dead code**:
confirmed via repo-wide grep — instantiated nowhere except its own module
docstring's usage example; zero test coverage of any kind before this
session. Four independent bugs found, matching bug classes already
established repeatedly this session in the sibling search implementations
(reports 79/80/81):

1. **No tenant GUC pinning in either `_fulltext_search()` or
   `_semantic_search()`.** `companies` has RLS + FORCE RLS; without
   `app.tenant_id` pinned, the `c.tenant_id = :tid` predicate is never
   satisfied and both methods silently return 0 rows regardless of how
   much matching data exists — confirmed directly.
2. **The dynamic filter allowlist included `"activity"`, which does not
   exist on `companies`** (only `activity_description` does) — the same
   bug found in reports 79 and 81's sibling files. `_fulltext_search()`
   interpolates the field name directly into raw SQL
   (`"c." + field_name + " = :fltr_" + field_name`), so using it would
   raise `UndefinedColumnError`. Renamed to `activity_description`.
3. **`_semantic_search()`'s `:emb::vector` bind syntax is not recognized as
   a bind parameter at all by SQLAlchemy's `text()` scanner** — a bind
   name immediately followed by `::` (Postgres cast operator) is left as
   literal uncompiled text, producing
   `PostgresSyntaxError: syntax error at or near ":"` on every real call.
   The exact same quirk documented in report 75 (`:name::jsonb`). Fixed to
   `CAST(:emb AS vector)`.

Bug 4, discovered mid-investigation as a genuine investigation artifact
(not a code bug — documented for completeness): after this session's
`loop4h-runner` container was unexpectedly restarted (its fixed-duration
`sleep` entrypoint expired), the replacement container was recreated from
the *stale* `loop4h-backend:latest` image (built earlier in the session,
before several of today's fixes) and initially misconfigured with
`DATABASE_URL` pointed at the restricted `salesos_app` role instead of the
Postgres owner role — collapsing `owner_engine` (meant to bypass RLS for
test seeding) into the same restricted connection as the regular `engine`,
which made unrelated, already-fixed tests (report 68/114's DEC-157 suite)
fail with RLS violations on their own seed inserts. Diagnosed via direct
comparison against a known-good raw-SQL reproduction, traced to
`app/config.py`'s `app_database_url`/`resolved_database_url` split, and
resolved by recreating the container with `DATABASE_URL` set to the owner
(Postgres superuser) connection and `APP_POSTGRES_USER`/
`APP_POSTGRES_PASSWORD` set to the restricted role — restoring the correct
two-connection setup this test suite depends on. All of this session's
previously-fixed source files were then re-copied into the new container.
No source code in the repository was affected by this artifact.

## Fixes

**`domains/search/engine/hybrid_search.py`**:
- Added `from app.database import apply_tenant_guc`.
- `_fulltext_search()` and `_semantic_search()`: pin `app.tenant_id` before
  each query.
- `_fulltext_search()`'s dynamic filter `allowed` tuple:
  `"activity"` → `"activity_description"`.
- `_semantic_search()`: `:emb::vector` → `CAST(:emb AS vector)` (both the
  `SELECT` similarity expression and the `ORDER BY` clause).

## Verification

Fresh ephemeral `pgvector/pgvector:pg16` container, `salesos_app`
restricted role.

**New file**: `tests/integration/test_hybrid_search_engine_db.py`
(3 tests):
- `test_fulltext_search_finds_the_seeded_company_and_is_tenant_scoped` —
  seeds one company, confirms `_fulltext_search()` finds it and a
  different tenant sees nothing.
- `test_semantic_search_finds_the_seeded_company` — confirms
  `_semantic_search()` finds a company via its real embedding.
- `test_activity_description_filter_is_a_real_column` — confirms the
  renamed filter field works end to end.

**Genuine red→green, all 3 real code bugs isolated independently**:
- Bug 3 (`:emb::vector`): reverted the `CAST(...)` fix back to `:emb::vector`,
  re-ran, confirmed the exact predicted `PostgresSyntaxError: syntax error
  at or near ":"`. Restored, re-confirmed passing.
- Bug 1 (GUC pin, `_fulltext_search()`): removed the `apply_tenant_guc()`
  call, re-ran, confirmed the exact predicted `assert 0 == 1`. Restored,
  re-confirmed passing.
- Bug 2 (`activity` column) verified the same way as reports 79/81's
  identical finding: schema inspection confirming no bare `activity`
  column exists, plus the passing filter test.

**Combined session regression** (all integration tests from reports
68/70–82 run together in the same container, after resolving the
container-recreation artifact above): **47/47 PASS**, no cross-fix
regressions.

**Full local unit suite** (`tests/unit/`): **3766 passed, 0 failed** (4
skipped, 7 xfailed, 3 xpassed — all pre-existing categories) — clean
baseline reconfirmed.

## Production / Phase 7

Dead code, not wired anywhere; fixed ahead of any future wiring decision,
same posture as reports 73/74/76/77/79's dead-code findings. No production
or `salesos_test` write; only a disposable, ephemeral Postgres container
was used (recreated once mid-session, per the artifact above), destroyed
after verification. Phase 7 remains BLOCKED; production remains **NOT
APPROVED**.
