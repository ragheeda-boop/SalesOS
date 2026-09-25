# 74 — AttributionEngine: a Real, Confirmed-Exploitable SQL Injection + 3 More Bugs (2026-09-24)

> **Scope:** Continues the manual raw-SQL review from reports 71-73 into
> `runtime/attribution/__init__.py`. Found and fixed a genuine SQL injection
> vulnerability — reproduced with a working exploit before the fix, not a
> theoretical claim — plus three more independent bugs in the same file,
> one of which was only reachable once the first three were fixed. This is
> the most severe finding of this session. Verified on a fresh ephemeral
> Postgres container; `salesos_test` was never touched. `AttributionEngine`
> is never instantiated anywhere in production (confirmed via repo-wide
> grep), so none of this was live-exploitable today — but it is fixed
> ahead of any future wiring decision, which matters more here than for
> prior reports' dead-code findings given bug #1's severity.

## 1. Bug 1: SQL injection — confirmed exploitable, not theoretical

`AttributionEngine.attribute_email()`'s four resolution steps
(explicit_reference, contact_match, company_match, domain_match) built raw
SQL via Python f-string interpolation of values sourced entirely from
external, attacker-controlled input:

- `opp_ref` — extracted via `re.finditer(pattern, subject + " " + body, ...)`
  directly from the raw email subject/body text. Anyone who can get an
  email delivered to a tenant's synced mailbox controls this value.
- `related_contact_ids` / `related_company_ids` — from synced email
  metadata, interpolated into `IN (...)` clauses.
- `domain` — the sender's email address domain
  (`from_addr.split("@")[-1]`), also fully attacker-controlled.

**Proof, not assertion:** a crafted email subject
``[OPP-x' OR '1'='1' --]`` was tested against the pre-fix code on a fresh
ephemeral database seeded with one real, unrelated opportunity ("Unrelated
Deal"). The vulnerable query compiled to:

```sql
id LIKE '%x' OR '1'='1' --%' OR name ILIKE '%x' OR '1'='1' --%'
```

The trailing `--` comments out the rest of the line, and `'1'='1'` is a
genuine tautology — this returned the "Unrelated Deal" opportunity's real
UUID as a false positive match, captured directly in the test failure
output before the fix (`assert persisted[0]["opportunity_id"] == ""` failed
with the real opportunity's UUID). An earlier, less careful payload
(`[OPP-x%' OR '1'='1]`) was tried first and did **not** actually work due
to how the vulnerable template's trailing `'%'` breaks a naive tautology —
this is noted so the fix isn't credited against a payload that was never a
real threat; the working payload above is the one this report's claim
rests on.

### Fix

All 5 raw-SQL call sites in this file now use bound parameters instead of
string interpolation:

- `id LIKE :pattern OR name ILIKE :pattern` with `{"pattern": f"%{opp_ref}%"}`
- `contact_id IN (:cid0, :cid1, ...)` — dynamically named bind params per
  value (bounded to 10), not string-joined literals
- `company_id IN (:cid0, :cid1, ...)` — same pattern, bounded to 5
- `email ILIKE :pattern OR website ILIKE :pattern` for the domain lookup
- `company_id = :cid` for the resulting opportunity lookup

## 2. Bug 2: no tenant GUC pinning anywhere in the file

Every query in this file runs against RLS/FORCE-RLS-protected tables
(`commercial_opportunities`, `opportunity_contacts`, `companies`,
`activity_attributions`, `employee_email_events`) — `apply_tenant_guc()`
was never called anywhere. Under the real restricted `salesos_app` role
this fails closed to zero rows on every query — the engine could never
have matched anything at all, entirely independent of the injection bug.

**Fix:** `await apply_tenant_guc(session, tenant_id)` added at all 5
`async with self._session_factory() as session:` blocks (4 in
`attribute_email()`, 1 in `run_shadow_batch()`).

## 3. Bug 3: `run_shadow_batch()` never committed

Every `INSERT INTO activity_attributions` this method performs would be
silently discarded on normal `async with` exit — `AsyncSession.__aexit__`
closes the session, it does not commit. The method would run to
completion, report a nonzero `processed` count, and persist nothing.

**Fix:** `await session.commit()` added after the batch's processing loop,
inside the same session block.

## 4. Bug 4: a fourth bug, only reachable once 1–3 were fixed

With bugs 1–3 fixed, the code could finally reach its own
`activity_attributions` INSERT for the first time in this investigation —
which then raised a hard `PostgresSyntaxError: syntax error at or near ":"`
on every call. The INSERT used `:rc::jsonb`, `:ev::jsonb`, `:cb::jsonb`,
`:ac::jsonb`. Confirmed in complete isolation (a bare script, no test
framework, no ORM) that SQLAlchemy's `text()` bind-parameter scanner does
**not** recognize a parameter name immediately followed by `::` as a bind
parameter at all — it is left as literal, uncompiled text, while every
other named parameter in the same statement gets correctly compiled to
asyncpg's positional `$N` form, producing an invalid hybrid statement.
`CAST(:x AS jsonb)` was confirmed to work correctly in the same isolated
check.

**Fix:** all four occurrences changed from `:name::jsonb` to
`CAST(:name AS jsonb)`, matching the convention already used elsewhere in
this codebase (e.g. `sdk/events/store.py`).

This bug is a clean illustration of why fixing bugs in dead/unreached code
still matters: it was invisible until three unrelated fixes let execution
reach it for the first time.

## 5. Verification

New `tests/integration/test_attribution_engine_injection_and_isolation_db.py`
(3 tests) on a fresh ephemeral Postgres migrated to head, driven entirely
through `AttributionEngine.run_shadow_batch()` (not the query in
isolation):

- **Legitimate case**: a real `[OPP-ABC123]` reference correctly attributes
  and durably persists (`resolution_method="explicit_reference"`).
- **Injection case**: the confirmed-working exploit payload from §1 now
  produces only the engine's own honest "unresolved" fallthrough
  (`opportunity_id=""`, `resolution_state="unresolved"`) — proving the
  fix, not just the absence of a crash.
- **Cross-tenant case**: an identically-named opportunity in a different
  tenant is never matched — same honest "unresolved" fallthrough, not a
  leak.

**Genuine red→green for all four bugs, independently:**

- Bug 1: reverted the parameterization on the explicit_reference step only,
  re-ran the injection test — it failed with the real opportunity's UUID
  surfacing (the captured proof in §1). Restored, re-ran clean.
- Bug 2: removed the single GUC pin in `run_shadow_batch()`'s outer
  session, re-ran all 3 tests — all 3 failed with `processed == 0`
  (fail-closed RLS blocking the email query itself). Restored, re-ran
  clean.
- Bug 3: removed the `session.commit()`, re-ran the legitimate-case test —
  it failed with `processed == 1` but `0` rows actually persisted,
  reproducing the exact documented failure mode. Restored, re-ran clean.
- Bug 4: already reproduced live during initial verification (before any
  revert was needed) — confirmed via the isolated `CAST` vs `::` check and
  via the real test's own `PostgresSyntaxError` failure. Fixed, re-ran
  clean.

Combined regression, same ephemeral container, with reports 68/71/72/73's
suites: **26/26 PASS**. Full local `tests/unit/`: **3766 passed, 0
failed** (unchanged — all four bugs lived in code with zero live callers).

## 6. What this does not claim

- Does not claim `AttributionEngine` is now production-ready or should be
  wired in — that remains a separate product decision, same as report 73's
  `DealHealthComputer` finding.
- No production/staging migration; only an ephemeral, disposable Postgres
  container was used, torn down after. `salesos_test` was never touched.
- Does not claim an exhaustive audit of every raw-SQL block in `runtime/` —
  remaining unreviewed files from report 73's list:
  `event_runtime/persistent_dlq.py`, `knowledge_graph_runtime/connectors.py`,
  `knowledge_graph_runtime/hybrid_retrieval.py`, `search_runtime/__init__.py`,
  `context_runtime/__init__.py` (partial). `agent_runtime/{budget,preamble,
  queue,__init__}.py` were reviewed this session and found clean.
- Does not claim the capability register moved — these are correctness/
  security fixes to code with no current live caller, not a new capability.
- Phase 7 remains **BLOCKED**; production remains **NOT APPROVED**.

## 7. Files changed this session

- `runtime/attribution/__init__.py`
- `tests/integration/test_attribution_engine_injection_and_isolation_db.py` (new)
