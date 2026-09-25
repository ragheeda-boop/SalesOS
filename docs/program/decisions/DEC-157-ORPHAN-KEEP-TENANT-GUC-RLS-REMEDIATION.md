# DEC-157 — Tenant GUC pinning + RLS for the 14 live orphan-keep tables (Accepted — CLOSED)

> **Status:** **Accepted — CLOSED 2026-09-23.** Steps 1-4 all executed and verified this session; see §8 for the closure evidence and §3 for the rulings that unblocked Accept.
> **Date:** 2026-09-23
> **Board:** Backend Platform / Database (SalesOS)
> **Finding:** `project-audit/59_ORPHAN_KEEP_TABLES_RLS_GAP_2026-09-23.md` (capability register mechanical audit)
> **Authority:** DEC-085 (`set_config` / canonical tenant-isolation RLS pattern) · DEC-130b/DEC-130f (orphan KEEP register — no DROP without a dedicated DEC) · DEC-156 (adjacent, still-unaccepted proposal to merge some of the same tables' `MetaData()` onto `Base.metadata` — related but distinct concern, see §5)
> **Out of scope (unchanged even after this Accept):** DROP or reshape any table · production/staging migration · `feature_ai_copilot` or any unrelated flag. **Now in scope and executed:** the Alembic head bump (`e1d1c1225d00`) and all code changes in §2/§8 — both were explicitly out of scope for the *proposal* draft but are exactly what accepting a DEC authorizes.

---

## 1. Decision (Accepted 2026-09-23 — all 4 steps executed)

Authorized and executed, **in this order**:

1. An explicit ruling (this DEC, on Accept) on two specific semantics questions
   (§3) for `activity_records` and `domain_events`, since both currently
   allow — possibly by original design, not by omission — reads that are not
   scoped to a single tenant.
2. Adding `app.tenant_id` session-GUC pinning (the same
   `set_config('app.tenant_id', :tenant_id, true)` / `apply_tenant_guc(...)`
   convention already used by `runtime/decision_runtime/__init__.py` and
   every DEC-085-pattern table) to the five call sites listed in §2 that
   currently have none.
3. Full regression proof for all five affected modules (§4) with the GUC
   pinning in place but **before** any RLS is enabled — to separately verify
   the pinning itself introduces no behavior change.
4. Only then, a single additive migration enabling
   `ENABLE`/`FORCE ROW LEVEL SECURITY` + the canonical
   `tenant_isolation_<table>` policy (via `app.alembic.lib.rls.generate_policy_sql`,
   the same helper used by migrations `y8z9a0b1c2d3`, `z9a0b1c2d3e4`,
   `u1v2w3x4y5z6`, `70193187420d`) on all 14 tables, with regression proof
   re-run against the RLS-enabled schema.

This DEC's acceptance and execution happened in the same session; §8 is the
closure evidence.

| Pin | Value |
|---|---|
| Tables in scope | **14** (see §2) — excludes `rag_documents`/`rag_document_chunks` (already RLS-protected) and `graph_nodes` (dormant per ADR-108) from DEC-130f's 15-table KEEP register |
| Tables with existing GUC pinning before this DEC | **1 of 14** (`decisions`, via `apply_tenant_guc`) — now **14 of 14** |
| Call sites given new GUC pinning | **5** modules (§2) — done |
| Semantics rulings | **2**, both ruled in §3 (`activity_records.tenant_id` nullability → no carve-out; `domain_events.read_by_type()` → dead code, now tenant-scoped) |
| Alembic head | **`e1d1c1225d00`** (was `70193187420d`) |
| DEC-130f | **Unaffected** — this DEC adds RLS only; it does not drop, rename, or reshape any of the 15 KEEP tables, so it does not conflict with DEC-130f's "no DROP without a dedicated DEC" constraint |
| Report 58 precedent | The `account_funnel`/`score_observations` FORCE-RLS fix was **not** a template for this case — those two tables already had a policy and were already implicitly GUC-compatible; these 14 were not, and needed the pinning step first |

### Alternatives considered

| Option | Result |
|---|---|
| (a) Add RLS now, without GUC pinning, matching report 58's pattern | **Rejected** — report 59 confirms this would break five live, routed runtime engines (every unpinned session would see zero rows on read and a `WITH CHECK` failure on write) |
| (b) Leave as-is indefinitely (status quo) | **Rejected as a permanent position** — these are real tenant-scoped tables with zero database-level isolation, relying solely on hand-written `WHERE tenant_id` clauses scattered across five modules; that is exactly the anti-pattern DEC-085's RLS program exists to close everywhere else. Acceptable only as a *temporary* hold pending this DEC's review, not as the final answer. |
| (c) Rule on semantics + add GUC pinning + regression-prove + then RLS, as one reviewed sequence (this proposal) | **Approved for proposal; awaiting Accept** |

---

## 2. The 14 tables, their live call site, and current isolation mechanism

| # | Table | Live call site | GUC pinned today? | Current isolation |
|--:|---|---|:---:|---|
| 1 | `company_funding_events` | `runtime/feature_store/features.py` | No | Manual `WHERE tenant_id = :tid` |
| 2 | `company_job_postings` | same | No | same |
| 3 | `company_intent_rfps` | same | No | same |
| 4 | `company_intent_visits` | same | No | same |
| 5 | `company_intent_content` | same | No | same |
| 6 | `company_intent_contacts` | same | No | same |
| 7 | `company_products` | same | No | same |
| 8 | `company_deals` | same | No | same |
| 9 | `company_payments` | same | No | same |
| 10 | `company_policies` | `runtime/policy_runtime/__init__.py` | No | Manual `WHERE tenant_id = :tid AND is_active = true` |
| 11 | `decisions` | `runtime/decision_runtime/__init__.py` | **Yes** (`apply_tenant_guc`) | GUC + manual filter (RLS itself still absent today) |
| 12 | `decision_feedback_loop` | `runtime/decision_runtime/feedback_loop.py` (`DecisionFeedbackLoop.record_feedback`) | No | Manual `tenant_id` bind on INSERT only |
| 13 | `domain_events` | `sdk/events/store.py` (`PostgresEventStore`), used by `runtime/event_runtime/__init__.py` | No | Manual `tenant_id` column on INSERT; **no filter at all** on `read_by_type()` |
| 14 | `activity_records` | `runtime/activity_runtime/__init__.py` (`ActivityRuntime`) | No | **Nullable** `tenant_id`; filter applied **conditionally** (`if tenant_id is not None`) |

Five distinct call sites need new GUC pinning: `runtime/feature_store/features.py`
(covers 9 tables), `runtime/policy_runtime/__init__.py` (1 table),
`runtime/decision_runtime/feedback_loop.py` (1 table), `sdk/events/store.py`
(1 table, invoked from `runtime/event_runtime/__init__.py`), and
`runtime/activity_runtime/__init__.py` (1 table).

---

## 3. Semantics rulings (RULED — this Accept)

1. **`activity_records.tenant_id` is nullable and its query builder applies
   the tenant filter only when a caller supplies one. Is there a real,
   intentional cross-tenant/tenant-less use case?**

   **Ruling: no.** Exhaustive grep of every production caller of
   `ActivityRuntime.query()` / `get_by_entity()` / `get_by_actor()` /
   `get_by_action()` (`app/modules/company/service.py`,
   `app/modules/employee_360/service.py`,
   `app/modules/work_intelligence/service.py`, `domains/employee/signals.py`)
   shows every single call site passes a concrete `tenant_id` sourced from
   the authenticated request/router boundary (`get_current_tenant_id`, which
   itself 400s on a missing tenant). There is no admin/observability caller
   that intentionally queries `tenant_id=None`. The *nullability* itself is
   real and load-bearing at the write path — `ActivityRuntime.on_domain_event()`
   can construct a record with `tenant_id=None` when the inbound domain event
   carries none — but that is a write-time edge case, not a read-time
   cross-tenant need.

   Given that, and following the **already-accepted precedent** in migration
   `d1a8c35e7f09` (`admin_ai_costs`/`admin_jobs`, also nullable `tenant_id`)
   and the explicit rejection of an `OR tenant_id IS NULL` bypass in
   `b7e2f65a3f07`: **no carve-out.** The standard fail-closed
   `generate_policy_sql()` policy applies to `activity_records` exactly as to
   every other Category A table. A NULL-tenant row is invisible under any
   tenant GUC, and a future INSERT of a NULL-tenant row will now be rejected
   by `WITH CHECK` unless the caller supplies a real tenant — this is a
   deliberate tightening, not an oversight, and matches this repo's one
   existing precedent for the identical shape of problem rather than
   inventing a second, inconsistent answer.

2. **`sdk/events/store.py`'s `PostgresEventStore.read_by_type()` reads across
   all tenants by event type, with no tenant filter at all. Is this
   intentional?**

   **Ruling: not intentional — dead code, closed by construction.**
   Exhaustive grep (`grep -rn "read_stream\|read_by_type"`) across the entire
   repository, tests included, finds **zero callers** of either
   `EventStore.read_stream()` or `read_by_type()` anywhere — the interface
   methods have never been invoked in production or by any test. There is no
   live cross-tenant replay use case to preserve. `sdk/events/base.py`'s
   abstract signatures now require a `tenant_id: str` parameter on both
   methods (no longer optional), and `sdk/events/store.py`'s
   `PostgresEventStore` implementation pins the tenant GUC before every read
   and filters both queries by `tenant_id`. Same fail-closed policy as every
   other table — `domain_events`' nullable `tenant_id` gets the identical
   no-carve-out treatment as `activity_records` (ruling 1 above), for the
   identical reason.

Both rulings resolve to the same answer: apply the standard, uniform
`generate_policy_sql()` fail-closed policy to all 14 tables with no
exceptions. This is the simplest, most consistent choice, and it matches
existing accepted precedent rather than creating a new policy shape.

### Sequencing / scope questions (§7, answered)

- **Pin all five modules first, then one RLS migration for all 14 tables**
  (as originally proposed) — confirmed as the executed sequence. Landing
  GUC pinning and RLS table-by-table would have meant repeatedly running the
  full migration chain; batching was strictly less work with no loss of
  rigor, since step 3's regression proof (GUC pinning, RLS still off) and
  step 4's isolation proof (RLS on) are independently verifiable either way.
- **Split `company_policies`/`decisions`/`decision_feedback_loop` into their
  own DEC, separate from the nine Feature Store tables?** Not split. All 14
  tables share one root cause (DEC-130f orphan-keep tables with zero
  database-level isolation) and one fix shape (GUC pin + standard RLS
  policy); splitting would have meant re-deriving the same migration
  mechanics twice for no independent value, and this Accept closes all 14 in
  one verified pass.

---

## 4. Validation plan (EXECUTED this session — all rows closed)

| Check | When | Result |
|---|---|---|
| Existing regression suite green with GUC pinning added, RLS still off | After §1 step 2 | **PASS** — `tests/unit/` full local run: 3763 passed, 4 skipped, 7 xfailed, 3 xpassed, 1 pre-existing unrelated failure (`test_db05_slice4_deferred_8_rls_authority.py`, a stale `ALL_TENANT_TABLES` count assertion predating this session, unrelated to any of the 5 touched modules). `test_event_runtime_subscriber_bounds.py` updated (await_count 1→2 + GUC-call assertion) via genuine red→green; a new `test_activity_runtime_router_tenant_injection.py` (2 tests) added after finding and fixing a real cross-tenant injection bug in `runtime/activity_runtime/router.py`'s `ingest-batch` endpoint along the way, also red→green verified |
| Fresh ephemeral `pgvector/pgvector:pg16`, full migration chain, RLS added, `salesos_app` (non-superuser, `NOBYPASSRLS`) proves cross-tenant isolation on all 14 tables | After §1 step 4 | **PASS** — `tests/integration/test_dec157_orphan_keep_rls_db.py` (9 tests, new): RLS/FORCE/policy shape for all 14 tables; `FundingScoreComputer`/`HiringScoreComputer`/`ExpansionScoreComputer`/`RevenueScoreComputer` (covering all 9 Feature Store tables) each see only their own tenant's rows on a same-`company_id` cross-tenant probe; `PolicyEngine.evaluate()` isolates `company_policies`; `DecisionFeedbackLoop.record_feedback()` isolates `decision_feedback_loop`; `decisions` isolates via raw-SQL GUC-pinned read; `ActivityRuntime` isolates `activity_records` (tenant-A/tenant-B) **and** a NULL-tenant insert is rejected by `WITH CHECK` (fail-closed, no bypass — ruling 1); `PostgresEventStore.append/read_stream/read_by_type` isolates `domain_events`. Adjacent suites re-run in the same container with no regression: `test_effectiveness_force_rls.py`, `test_relationships_rls.py`, `test_feature_store_licenses_table_db.py` (10 tests, all PASS) |
| Downgrade → upgrade round trip on the new migration | After §1 step 4 | **PASS** — migration `e1d1c1225d00`: full chain from zero (single head confirmed before and after), `alembic downgrade -1` removes RLS/FORCE/policy from all 14 tables (verified via `pg_class`/`pg_policy`), `alembic upgrade head` restores identical state |
| No change to `alembic check` / DEC-130f's KEEP-register posture | Throughout | **PASS** — RLS DDL only; no `CREATE TABLE`/`DROP TABLE`/column changes; `app/db05_orphan_keep.py`'s `ORPHAN_KEEP_TABLES` stubs untouched |

---

## 5. Relationship to DEC-156

DEC-156 (2026-08-13, still **Proposed — not Accepted**) separately proposes
merging six residual private `MetaData()` islands — including
`activity_records`, `domain_events`, and `db05_orphan_keep`'s own KEEP
register — onto the canonical `sdk.database.Base.metadata`, for a different
reason (DRIFT-01 metadata-island freeze ceiling, not RLS). That proposal and
this one overlap in table scope but not in concern: DEC-156 is about where
the `Table()` objects live in Python; this DEC is about tenant isolation at
the database layer. They can be accepted independently and in either order;
implementers should check DEC-156's status before touching the same files
this DEC's future implementation would touch, to avoid a merge conflict
between two agents working the two DECs in parallel.

---

## 6. Records

- Finding: `project-audit/59_ORPHAN_KEEP_TABLES_RLS_GAP_2026-09-23.md`
- Correction trail: `project-audit/57_CAPABILITY_REGISTER_RECONCILIATION_2026-09-23.md` §3 (superseded characterization), `project-audit/58_EFFECTIVENESS_FORCE_RLS_CLOSURE_2026-09-23.md` (unaffected — different tables, already GUC-compatible)
- `DECISION_LOG.md` entry: this DEC, filed above DEC-156
- **Not claimed:** Accepted status, any code change, production readiness, Phase 7 progress, or that cross-tenant data has actually leaked in any live environment

## 7. Architecture reviewer — resolved this Accept

1. Answers to §3's two semantics questions — see §3 rulings.
2. Sequencing (pin-all-five-then-one-migration vs. table-by-table) — see §3
   "Sequencing / scope questions".
3. Whether to split `company_policies`/`decisions`/`decision_feedback_loop`
   into their own DEC — see §3 "Sequencing / scope questions" (not split).

## 8. Closure evidence (2026-09-23)

- **Code:** `sdk/events/base.py` (required `tenant_id` on both read methods),
  `sdk/events/store.py` (`_pin_tenant_guc()` local helper — duplicated, not
  imported, to avoid a `sdk` → `app.database` circular import discovered
  while implementing this), `runtime/feature_store/features.py` (5 pin
  sites), `runtime/policy_runtime/__init__.py` (1 pin site),
  `runtime/decision_runtime/feedback_loop.py` (1 pin site),
  `runtime/activity_runtime/__init__.py` (4 pin sites).
- **Side-effect fix:** `runtime/activity_runtime/router.py`'s
  `ingest-batch` endpoint let a client-supplied `tenant_id` in the request
  body override the authenticated caller's tenant — a real cross-tenant
  injection bug found while tracing this module's call sites, fixed and
  covered by a new red→green-verified regression test
  (`tests/unit/test_activity_runtime_router_tenant_injection.py`).
- **Migration:** `app/alembic/versions/e1d1c1225d00_dec157_orphan_keep_rls.py`
  (new alembic head, down_revision `70193187420d`), plus
  `DEC_157_ORPHAN_KEEP_TENANT_TABLES` added to `app/alembic/lib/rls.py`.
- **Tests:** `tests/unit/test_event_runtime_subscriber_bounds.py` (updated),
  `tests/unit/test_activity_runtime_router_tenant_injection.py` (new, 2
  tests), `tests/integration/test_dec157_orphan_keep_rls_db.py` (new, 9
  tests) — all verified on a fresh ephemeral `pgvector/pgvector:pg16`
  container built from current source, torn down after verification. No
  write to `salesos_test` or any shared/persistent database.
- **Report:** `project-audit/68_DEC157_ORPHAN_KEEP_RLS_CLOSURE_2026-09-23.md`.
- **Not claimed:** production/staging migration, capability-census movement
  beyond what report 68 states, or anything about the pre-existing,
  unrelated `test_db05_slice4_deferred_8_rls_authority.py` failure (a stale
  count assertion predating this session — flagged, not fixed, out of
  scope for this DEC).
