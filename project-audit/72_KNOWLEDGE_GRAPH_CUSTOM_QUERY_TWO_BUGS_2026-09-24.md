# 72 — GET /graph/query/custom Was Broken for Every Supported entity_type, Two Independent Bugs (2026-09-24)

> **Scope:** Continues the systematic raw-SQL audit from report 71 into
> other REST routers with raw SQL (`knowledge_graph_runtime`, `identity`,
> `signal_actions`). Found and fixed two independent, always-reproducible
> bugs in the same endpoint. Verified on a fresh ephemeral Postgres
> container; `salesos_test` was never touched.

## 1. What was checked

Report 71's table-existence sweep only checked table *names*. This session
extended the review to the 4 `router.py` files across the repo that embed
raw SQL (`runtime/knowledge_graph_runtime/router.py`,
`runtime/pipeline_analytics/router.py` — already covered in report 71,
`app/modules/identity/router.py`, `app/modules/signal_actions/router.py`),
reading each raw-SQL block by hand for column-name and type correctness
(not just table existence). `runtime/knowledge_graph_runtime/router.py`'s
`GET /graph/query/custom` (registered live at `/api/v1/graph/query/custom`,
`app/boot/routers.py:217`) had two separate, independent bugs — one per
mechanism — leaving all 3 of its supported `entity_type` values broken.

## 2. Bug 1: `UnboundLocalError` in the `opportunity`/`contract` branches

`custom_graph_query()`'s `opportunity` and `contract` branches each do
`result["items"] = [...]` then `result["total"] = len(items)` — but `items`
is a bare local variable never assigned in either branch (only the
`company` branch, earlier in the same `if/elif` chain, happens to assign
`items` before using it). Since the route has no `try/except` at all, every
real call with `entity_type=opportunity` or `entity_type=contract` raised
an unhandled `UnboundLocalError`, an unhandled 500. Zero prior test
coverage for this endpoint at all.

**Fix:** both occurrences changed to `result["total"] = len(result["items"])`.

## 3. Bug 2: `varchar = uuid` type mismatch in the `company` branch's subquery

The `company` branch's correlated subquery
`(SELECT COUNT(*) FROM commercial_opportunities WHERE company_id = c.id)`
compares `commercial_opportunities.company_id` (`character varying(36)`)
directly against `companies.id` (`uuid`) with no cast. Reproduced in
complete isolation — a bare Python script against a fresh ephemeral
database, no pytest, no FastAPI, no TestClient involved — before
attributing it to the router, specifically to rule out a test-harness
artifact:

```
asyncpg.exceptions.UndefinedFunctionError: operator does not exist: character varying = uuid
HINT: No operator matches the given name and argument types. You might need to add explicit type casts.
```

The sibling correlated subquery in the same SELECT,
`(SELECT COUNT(*) FROM contacts WHERE company_id = c.id)`, needed no change
— `contacts.company_id` is itself `uuid`, matching `companies.id` cleanly.
A repo-wide grep for the same `company_id = c.id`/`companies.id` join
pattern found two other occurrences (`app/routers/revenue.py`,
`runtime/context_runtime/__init__.py`) — both checked and confirmed safe:
`company_signals.company_id` and `licenses.company_id` are both `uuid`,
matching `companies.id` correctly.

**Fix:** cast the varchar side to text on the comparison:
`WHERE company_id = c.id::text` — this matches the existing convention
already established in this codebase's RLS policies themselves (e.g.
`companies`' own FK-adjacent RLS predicate casts `tenant_id::text = ...`
rather than casting the parameter side).

## 4. Verification

New `tests/integration/test_knowledge_graph_custom_query_db.py` (3 tests),
run through the real HTTP router (not the query in isolation) on a fresh
ephemeral Postgres migrated to head, seeding a tenant with one company, one
opportunity, and one contract:

- `entity_type=opportunity`: asserts HTTP 200 (was always `UnboundLocalError`
  → 500) and `total == 1`.
- `entity_type=contract`: same assertion, same prior failure mode.
- `entity_type=company`: asserts HTTP 200 (was always `UndefinedFunctionError`
  → 500) and `total == 1`.

**Genuine red→green for both bugs independently**: reverted each fix in
turn, re-ran, confirmed the exact predicted failure each time (the
`UnboundLocalError`-shaped 500 for bug 1 was already confirmed via the
isolated script before router changes; bug 2's revert reproduced the
identical `UndefinedFunctionError: operator does not exist: character
varying = uuid` traceback, at both the isolated-script level and the full
router/TestClient level) — then restored both fixes and re-confirmed all
3 tests pass.

Same `TestClient`-vs-async-engine event-loop conflict from report 71
recurred and was resolved the same way (dispose the shared engine between
the seed phase and entering the `TestClient` block).

Adjacent regression, same ephemeral container: combined with reports 68/71's
suites (`test_dec157_orphan_keep_rls_db.py`,
`test_effectiveness_force_rls.py`, `test_relationships_rls.py`,
`test_pipeline_analytics_score_deal_db.py`) — **22/22 PASS**. Full local
`tests/unit/`: **3766 passed, 0 failed** (unchanged — this bug lived
entirely in a previously-uncovered integration path).

## 5. What this does not claim

- No production/staging migration; only an ephemeral, disposable Postgres
  container was used, torn down after. `salesos_test` was never touched.
- Does not claim an exhaustive audit of every raw-SQL column reference in
  the repository — this reviewed the 4 `router.py` files with embedded raw
  SQL plus a targeted grep for the specific `company_id = ...id` join
  shape that caused bug 2; `app/modules/identity/router.py` and
  `app/modules/signal_actions/router.py` were read but had no comparable
  issues found in this pass.
- Does not claim the capability register moved — this is a correctness fix
  to an already-existing, already-counted feature, not a new capability.
- Phase 7 remains **BLOCKED**; production remains **NOT APPROVED**.

## 6. Files changed this session

- `runtime/knowledge_graph_runtime/router.py`
- `tests/integration/test_knowledge_graph_custom_query_db.py` (new)
