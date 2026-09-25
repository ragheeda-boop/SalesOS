# 73 — DealHealthComputer: Third Occurrence of the varchar/uuid Bug + UTC-Date Bug, and It's Unregistered (2026-09-24)

> **Scope:** Continues the manual raw-SQL review from reports 71/72 into
> `runtime/` files not yet checked. Found and fixed two more real bugs in
> `runtime/nba_engine/engine/risk/deal_health.py::DealHealthComputer` — a
> third occurrence of report 72's `varchar = uuid` join-type mismatch, and a
> third occurrence of report 70's UTC/local calendar-boundary bug. Also
> documents, but does not act on, a separate finding: this computer is not
> currently wired into the live Feature Store registry at all. Verified on
> a fresh ephemeral Postgres container; `salesos_test` was never touched.

## 1. Bug 1 (third occurrence): `varchar = uuid` join mismatch

`DealHealthComputer.compute()`'s signal-detection query:

```sql
SELECT COUNT(*) as cnt FROM company_signals s
JOIN commercial_opportunities o ON o.company_id = s.company_id
WHERE o.id = :oid AND s.created_at >= :d30
```

compares `commercial_opportunities.company_id` (`varchar(36)`) directly
against `company_signals.company_id` (`uuid`) — the identical bug class
found twice already this session (report 72,
`runtime/knowledge_graph_runtime/router.py`). Confirmed the column types
directly against the live schema before touching anything. A repo-wide
grep for both join directions (`X.company_id = companies.id` and
`X.company_id = Y.company_id`) found no further occurrences beyond what
reports 72 and this report already fix.

**Fix:** `o.company_id = s.company_id` → `o.company_id = s.company_id::text`,
matching the identical cast convention used in report 72's fix.

## 2. Bug 2 (third occurrence): UTC/local calendar-boundary bug

The timeline-pressure calculation used
`days_to_close = (close_date - datetime.now(timezone.utc).date()).days`
against `commercial_opportunities.expected_close_date` (a plain `Date`
column) — the identical bug class fixed twice already this session (report
70: `app/modules/signal_actions/actions.py`,
`app/modules/company/repositories.py`). The file's other `datetime.now(timezone.utc)`
usages (measuring `days_since_last_activity` against a full
`timestamptz` column) were left untouched — those compare two UTC-aware
timestamps consistently and have no date-only truncation, so they carry
none of this bug's risk.

**Fix:** `date.today()` instead of `datetime.now(timezone.utc).date()`.

## 3. Separate finding, not acted on: this computer is unregistered

Unlike reports 67/71/72's bugs (all in code reachable from a registered
router or the live Feature Store boot wiring), `DealHealthComputer` is
**not currently invoked anywhere in production**. A repo-wide grep for
`DealHealthComputer` finds only its own definition file and its (fully
mocked) unit test file — it is absent from
`app/boot/startup.py::_init_feature_store()`'s `FeatureStore(computers=[...])`
list, which registers the other 7 computers (`IcpComputer`,
`FundingScoreComputer`, `HiringScoreComputer`, `GrowthScoreComputer`,
`IntentScoreComputer`, `ExpansionScoreComputer`, `RevenueScoreComputer`).
This looks like an integration gap (a class written to the same contract,
with its own dedicated test file, that was never wired in) rather than
deliberately dead code, but wiring a new computer into the live scoring
pipeline is a product/scope decision this report does not make — fixing
its two confirmed bugs ahead of any future wiring decision is still
correct and low-risk; registering it is not attempted here.

## 4. Verification

New `tests/integration/test_deal_health_computer_db.py` (1 test) on a
fresh ephemeral Postgres migrated to head: seeds a tenant, company,
opportunity (`expected_close_date` = today + 10 days), and one
`company_signals` row, then calls `DealHealthComputer.compute()` directly
(this is a pure computer, no HTTP layer to drive — no `TestClient`
complications this time). Asserts `signal_count == 1` (the join found the
seeded signal; the old bug raised `UndefinedFunctionError` before this
line was ever reached) and `timeline_risk == 0.2` (the `<30-day` tier for
a deal closing 10 days out).

**Genuine red→green for the join fix**: reverted the cast, re-ran, got the
exact predicted `UndefinedFunctionError: operator does not exist: character
varying = uuid` traceback. Restored, re-ran clean.

Existing mocked unit suite (`tests/unit/test_deal_health.py`, 16 tests,
predates this session) still passes unchanged — mocks don't exercise real
column types or real UTC-offset timing, which is exactly why neither bug
was ever caught by it.

Adjacent regression, same ephemeral container, combined with reports
68/71/72's suites: **15/15 PASS**. Full local `tests/unit/`: **3766
passed, 0 failed** (unchanged — both bugs lived in code with zero live
callers).

## 5. What this does not claim

- Does not register `DealHealthComputer` into the live Feature Store
  pipeline — that is a separate product decision (§3), not addressed here.
- No production/staging migration; only an ephemeral, disposable Postgres
  container was used, torn down after. `salesos_test` was never touched.
- Does not claim an exhaustive audit of every raw-SQL block in `runtime/` —
  this reviewed one additional file (`deal_health.py`) plus a targeted
  repo-wide grep for the two exact bug shapes already found this session;
  it does not claim every remaining unreviewed `runtime/` file (there are
  still several with raw SQL not yet manually checked: `agent_runtime/*`,
  `attribution/__init__.py`, `event_runtime/persistent_dlq.py`,
  `knowledge_graph_runtime/connectors.py`,
  `knowledge_graph_runtime/hybrid_retrieval.py`, `search_runtime/__init__.py`)
  is clean.
- Does not claim the capability register moved — these are correctness
  fixes to code with no current live caller, not a new capability.
- Phase 7 remains **BLOCKED**; production remains **NOT APPROVED**.

## 6. Files changed this session

- `runtime/nba_engine/engine/risk/deal_health.py`
- `tests/integration/test_deal_health_computer_db.py` (new)
