# 85 — GET /api/v1/meetings/{id}/brief: live 500 on every real call (2026-09-24)

## Summary

`domains/commercial/meeting/intelligence.py`'s
`MeetingIntelligenceService.generate_brief()` is genuinely live: called
from `app/routers/meetings.py`'s `GET /meetings/{opportunity_id}/brief`,
mounted at boot. Its "recent signals" query compared
`company_signals.company_id` (`uuid`) directly against a subquery
returning `commercial_opportunities.company_id` (`varchar(36)`) with no
cast — the same `uuid`/`varchar` type-mismatch bug class found repeatedly
this session (reports 71, 72, 74). Confirmed via direct reproduction:

```
ERROR:  operator does not exist: uuid = character varying
```

Every real call to this endpoint raised this error; the router's own
broad `except Exception` caught it, logged it, and returned an unhandled
**500 Internal Server Error** to every caller — the pre-meeting brief
feature has likely never worked. The existing unit test
(`tests/unit/test_meeting_intelligence.py`) mocks the session entirely
(`AsyncMock()`), so this had never been caught by any test.

## Fix

**`domains/commercial/meeting/intelligence.py`**: cast the subquery's
result to `uuid` (`SELECT company_id::uuid FROM commercial_opportunities
...`), matching `company_signals.company_id`'s real column type.

## Verification

Fresh ephemeral `pgvector/pgvector:pg16` container, `salesos_app`
restricted role.

**New file**: `tests/integration/test_meeting_intelligence_signals_db.py`
(1 test): seeds a company, an opportunity, and a company signal; calls
`generate_brief()` end to end and confirms the signal is correctly
returned in `recent_signals`.

**Genuine red→green**: reverted the `::uuid` cast, re-ran, confirmed the
exact predicted `UndefinedFunctionError: operator does not exist: uuid =
character varying`. Restored, re-confirmed passing.

**Existing unit regression** (`tests/unit/test_meeting_intelligence.py`):
**34/34 PASS**, unaffected (all mock the session).

**Combined session regression** (all integration tests from reports
68/70–85 run together in the same container): **52/52 PASS**, no
cross-fix regressions.

**Full local unit suite** (`tests/unit/`): **3766 passed, 0 failed** (4
skipped, 7 xfailed, 3 xpassed — all pre-existing categories) — clean
baseline reconfirmed.

## Production / Phase 7

This is a live-bug fix: `GET /api/v1/meetings/{opportunity_id}/brief` was
returning an unhandled 500 on every real call with any persisted company
signals. No production or `salesos_test` write; only a disposable,
ephemeral Postgres container was used, destroyed after verification.
Phase 7 remains BLOCKED; production remains **NOT APPROVED**.
