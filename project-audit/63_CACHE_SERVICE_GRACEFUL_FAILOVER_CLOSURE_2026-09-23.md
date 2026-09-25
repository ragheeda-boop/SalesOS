# CacheService Graceful Redis Failover — Closure — 2026-09-23

## Purpose

Fix the real bug report 62 found and deliberately did not fix: `GET
/api/v1/companies/{id}` raised an unhandled `redis.exceptions.TimeoutError`
and returned a raw 500 when Redis was unreachable, while `GET
/api/v1/companies` (the list endpoint, which does not use the cache) was
unaffected. This is a pure resilience fix to the shared cache layer — it
does not touch quota/entitlement enforcement policy, which report 62
correctly identified as out of scope for a unilateral change.

## Root cause

`app/boot/startup.py::_init_cache` always sets `app.state.cache` to a real
`CacheService` instance regardless of whether Redis is actually reachable
(only the boot-time health-check *log line* reflects connectivity). Every
caller that does `cache = getattr(request.app.state, "cache", None)` then
`if cache: await cache.get(...)` (e.g. `app/modules/company/router.py`'s
`get_company`) therefore always attempts the real Redis call. `sdk/cache/__init__.py`'s
`CacheService` — described in its own docstring as the class "all modules
use... instead of talking to Redis directly" — had **no error handling on
any method**, so any transient or permanent Redis outage surfaced as an
unhandled exception all the way to the client.

The codebase already has the correct pattern one file over:
`sdk/cache/redis_cache.py::RedisCache` catches `RedisError` (which
`TimeoutError` is confirmed to subclass) on every method and degrades to a
safe default, with its own passing test suite (`tests/unit/test_redis_cache.py`).
`CacheService` was a second, parallel implementation that never got the
same treatment.

## Delivered changes

| File | Change |
|---|---|
| `sdk/cache/__init__.py` | `CacheService.get/set/delete/delete_pattern/exists/clear_all` now each catch `RedisError` (and `json.JSONDecodeError`/`TypeError` where relevant to `get`/`set`), log a warning, and degrade to the same safe defaults `RedisCache` already uses (`None` for `get`, no-op for writes, `False` for `exists`). `remember()` is unaffected directly but now inherits the safety through `get`/`set`. |
| `tests/unit/test_cache_service_failover.py` | New. A `FailingRedis` stub whose every method raises `redis.exceptions.TimeoutError` proves each `CacheService` method degrades gracefully instead of raising; a `WorkingRedis` stub proves normal operation is unchanged; one guard test asserts `TimeoutError` really is a `RedisError` subclass (the assumption the whole fix depends on). |

No other file changed. No migration, no schema change, no API contract
change — callers that already do `if cache: await cache.get(...)` get the
fix automatically since the exception simply no longer escapes.

## Verification

Built the current source into a fresh image, copied in the test tree
(no live database needed — this is a pure unit-level fix with in-memory
stub Redis clients):

```text
tests/unit/test_cache_service_failover.py: 12/12 PASS
tests/unit/test_redis_cache.py:            19/19 PASS  (regression — unaffected)
tests/unit/test_feature_store_cache.py + test_entitlement_cache_ttl_story_06_04.py
  + domains/search/tests/test_search_cache.py:          29/29 PASS  (adjacent cache
                                                          consumers — no regression)
```

Ruff (`E4,E7,E9,F,I`) and `python -m py_compile` pass on both changed files.
Docker image and container removed after verification.

## Deliberate non-claims

- This does not re-verify the original failing endpoint
  (`GET /api/v1/companies/{id}`) against a live Redis outage end-to-end —
  that was already proven manually in report 62 (before this fix existed,
  it 500'd; the stub-based unit tests here prove the underlying class no
  longer raises, which is the mechanism the endpoint depends on). Re-running
  the full ephemeral backend+DB+"Redis intentionally down" browser scenario
  was judged unnecessary given the unit coverage matches `RedisCache`'s own
  already-accepted verification bar.
- Does not touch `app/modules/admin/entitlement_middleware.py` or any
  quota/entitlement enforcement decision — that middleware already fails
  closed correctly with its own try/except (report 62's initial suspicion
  that it was the culprit was itself corrected during investigation; the
  real fault was the separate cache layer).
- No production, `salesos_test`, or shared database was touched. No
  deployment, commit, or push occurred.
- Phase 7 remains **BLOCKED**; production remains **NOT APPROVED**. This is
  an isolated resilience fix, not a readiness change.

## Follow-up audit (same session) — a second, independent bug found

Audited every `app.state.cache` call site (9 files) for bypasses of the
now-fixed `CacheService` (e.g. reaching into `cache._redis` directly). None
found — every caller goes through `CacheService`'s public methods, so the
graceful-failover fix above covers all of them transitively.

The audit did surface a second, unrelated, real bug: `app/modules/cache/router.py`
(the `/api/v1/cache/*` admin API, mounted with only `verify_token` as its
guard) called `cache.set(entry.key, entry.value, ttl=entry.ttl)` and
`cache.flush(pattern=req.pattern)` — but `CacheService`'s actual methods are
`set(key, value, ttl_seconds=300)` and `delete_pattern(pattern)`; neither
`ttl` nor `.flush()` exist on the class. `POST /api/v1/cache/set` and `POST
/api/v1/cache/flush` therefore raised an unhandled `TypeError`/`AttributeError`
on every call — a live, reachable, always-broken endpoint with no prior
test coverage (none existed for this router before this session).

**Fixed**: both call sites corrected to the real method names/signatures.
**New test**: `tests/unit/test_cache_admin_router.py` — a small standalone
FastAPI app mounting only this router, `verify_token` overridden, a stub
Redis client — proves `set`→`get` round-trip, `delete`, `flush` (via
`delete_pattern`), and `health` all now work. **4/4 PASS.** Ruff and compile
pass. Docker image/container removed after verification.

## Re-proof against the exact original failure (same session, follow-up)

Unit tests prove the class; this re-proves the actual originally-broken
endpoint. Stood up a second, fresh ephemeral stack — Postgres migrated to
the current head, backend built from the now-fixed source, **Redis
intentionally not started at all** (`"cache":"unavailable"`,
`"redis":"unavailable"` on `/health`, reproducing report 62's exact failure
condition) — and drove the real HTTP flow with `curl` (register → login →
`GET /api/v1/identity/csrf-token` → create company → get company detail):

```text
POST /api/v1/identity/register            -> 201
POST /api/v1/identity/login                -> 200
GET  /api/v1/identity/csrf-token           -> 200
POST /api/v1/companies                     -> 201
GET  /api/v1/companies/{id}   (no Redis)   -> 200   (was 500 before this fix)
GET  /api/v1/companies/{id}   (again)      -> 200
```

Backend logs confirm the fix is doing exactly what it should — logging and
continuing, not crashing:

```text
WARNING sdk.cache: CacheService GET company:<tenant>:<id> failed: Timeout connecting to server
WARNING sdk.cache: CacheService SET company:<tenant>:<id> failed: Timeout connecting to server
WARNING app.common.middleware: GET /api/v1/companies/{id} 200 (4024.7ms)
```

**New observation, not fixed:** each request costs ~4 extra seconds when
Redis is completely absent (a failed `GET` then a failed `SET`, each paying
the `socket_connect_timeout=2`-second default). This is the honest cost of
graceful degradation under total Redis absence, not a bug this fix
introduces — a repeated-failure circuit breaker (stop trying to reach Redis
for N seconds after repeated timeouts) would remove this latency tax but is
a larger, separate change; noted for a future session, not attempted here
given today's scope was "don't crash," not "stay fast while crashed."

Ephemeral Postgres, backend, network, and image all removed after this
re-proof.

## Next code-reachable work

1. Consider whether `/api/v1/cache/*` should require an admin/owner
   permission rather than just `verify_token` (any authenticated user) —
   a raw cache-inspection/flush API is a wider blast radius than most
   per-tenant endpoints. Not changed this session (a permission-scope
   decision, not a correctness bug); flagged for a product/security call.
2. A repeated-failure circuit breaker in `CacheService`/`RedisCache` so a
   fully-down Redis stops costing ~4s per request instead of retrying the
   connection on every single call.
