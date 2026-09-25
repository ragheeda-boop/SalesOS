# 87 — action_outcomes idempotency: NULL idempotency_key defeats dedup entirely (documented, not fixed) (2026-09-24)

## Summary

While reviewing `app/modules/signal_actions/hitl_service.py::OutcomeService.record()`
(live: called from `app/modules/signal_actions/hitl_router.py`'s
`POST /outcomes`), found that the `ON CONFLICT (tenant_id, action_id,
idempotency_key) DO NOTHING` idempotency guarantee silently does nothing
whenever `idempotency_key` is `NULL` — which the API's own contract
(`idempotency_key: str | None = Field(default=None, ...)`) explicitly
allows a caller to send.

Confirmed directly: two identical INSERTs with `idempotency_key = NULL`
for the same `(tenant_id, action_id)` pair both succeeded — Postgres
treats every `NULL` in a unique constraint as distinct from every other
`NULL`, so the constraint provides no deduplication at all in this case.
A network retry, a double-click, or any caller (mobile app, future
frontend refactor, retry middleware) that omits the key would silently
create duplicate `action_outcomes` rows and duplicate auto-generated
follow-ups (`FollowupService.generate()` runs once per successful
`record()` call, so a duplicate outcome row means a duplicate follow-up
task too).

## Why this is documented, not fixed

Two things make the "obvious" fix (substitute a sentinel value like `''`
for `NULL` so the constraint actually dedupes) genuinely risky rather
than a narrow, safe patch:

1. **Zero current real-world exposure.** The one live frontend caller
   (`company-nba-tab.tsx`) always generates a real
   `crypto.randomUUID()` idempotency key via a stable `useState`
   initializer — confirmed via grep. No currently-shipping code path
   ever calls this endpoint with an omitted key.
2. **The correct fix depends on a product decision this session should
   not make unilaterally.** If a caller omits the key because they
   genuinely want to log a *second, real* outcome for the same action
   (e.g., "no_answer" logged for two separate real call attempts against
   the same `action_id`), forcing all no-key submissions to collapse to
   one shared sentinel value would silently drop legitimate repeated
   outcomes instead of fixing an accidental-duplicate problem — a
   behavior change with real product consequences, not obviously correct
   either way without knowing the intended semantics of "no idempotency
   key supplied."

Matching this session's established practice for genuinely ambiguous
architecture/product questions (reports 59/60/84), this is documented
with the exact reproduction and impact, rather than silently choosing a
dedup semantics that could just as easily be wrong.

## Recommended resolution paths (not implemented)

- **Option A — require the key.** Make `idempotency_key` a required field
  on `OutcomeRequest` (matches how the one real caller already behaves)
  and reject requests that omit it. Simplest, closes the gap completely,
  but is a breaking API contract change for any future caller.
- **Option B — sentinel-per-request.** Server-generates a fresh UUID for
  the row's dedup key whenever the caller omits one — equivalent to "no
  idempotency requested," explicitly not deduplicating that submission
  (matches Postgres's current behavior exactly, just states it as
  intentional rather than an accidental foot-gun) — i.e., document the
  current behavior as correct-by-design and simply clarify the API
  contract/docstring instead of changing code.
- **Option C — partial index.** A `WHERE idempotency_key IS NOT NULL`
  partial unique index would not help, since it wouldn't apply when the
  key is absent — the actual gap remains for that case by construction.

Given the current zero-exposure state, this is not urgent, but should be
resolved with an explicit product decision before any new caller of this
endpoint is added (mobile app, integrations, etc.).

## Verification

Direct reproduction on a fresh ephemeral `pgvector/pgvector:pg16`
container, `salesos_app` restricted role: two INSERTs with identical
`(tenant_id, action_id)` and `idempotency_key = NULL` both succeeded,
confirmed via a `COUNT(*) = 2` read-back. No code was changed as part of
this finding.

## Production / Phase 7

No production or `salesos_test` write; only a disposable, ephemeral
Postgres container was used for reproduction, destroyed after. No source
code changed. Phase 7 remains BLOCKED; production remains **NOT
APPROVED**.
