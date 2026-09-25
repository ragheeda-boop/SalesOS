# Correction: The 14 "Dead Table" Candidates Are Live — RLS Gap Documented, Not Closed — 2026-09-23

## What this report is

A correction of report 57 §3 and report 58's "next code-reachable work"
item 1, produced at the user's explicit request to verify before touching
any code ("تحقق فقط أولًا" — verify only, first). The verification found the
original classification was wrong, and the corrected finding is
**deliberately left undone** this session per the user's own choice (stop
and document; no code change). No file under `salesos/` was touched by this
report. No migration, test, or application code was written or run.

## The error being corrected

Report 57 §3 classified 15 tenant_id-bearing tables with no RLS as mostly
"confirmed-dead legacy tables (hygiene, not security)," based on a grep
scoped only to `salesos/backend/app/`. That scope was too narrow: none of
this project's raw-SQL "orphan" tables live under `app/` — they live under
`runtime/` and `sdk/`, which the original grep never searched. Re-running the
search against the correct scope reverses the conclusion for 14 of the 15
tables.

## What the corrected verification actually found

### 1. An existing, accepted architecture decision already governs 13 of these tables

`docs/program/decisions/DEC-130f-DB-05-SLICE-5F-ORPHAN-KEEP-REGISTER.md`
(Status: **Accepted**, dated 2026-08-01) explicitly classifies
`company_funding_events`, `company_payments`, `company_job_postings`,
`company_intent_contacts`, `company_intent_visits`, `company_intent_rfps`,
`company_intent_content`, `company_products`, `company_deals`,
`company_policies`, `decisions`, and `decision_feedback_loop` (plus
`rag_documents`, `rag_document_chunks`, `graph_nodes`, which are out of scope
here — RAG already has RLS via a dedicated later migration, and `graph_nodes`
is the already-documented Neo4j-adjacent dormant case) as **"KEEP — live
enrichment / decision / RAG / graph paths"** and records, verbatim: *"(a)
DROP the 15 orphan tables — Rejected — live enrichment / decision / RAG /
graph paths; no dedicated DROP DEC."* Per-table annotations in that decision
are explicit: `company_policies` = "KEEP (policy_runtime raw SQL)",
`decisions` = "KEEP (decision_runtime raw SQL)", `decision_feedback_loop` =
"KEEP (feedback raw SQL)". `app/db05_orphan_keep.py` implements this decision
by registering Core `Table` stubs on `Base.metadata` so `alembic check` stops
proposing a `remove_table` autogenerate diff for them — it is a
tooling-quieting mechanism, not evidence the tables are dead.

**This means report 57/58's recommendation to "confirm dead, then drop" was
not just unverified — it would have contradicted a standing, accepted
architecture decision had it been acted on.**

### 2. All 14 are live, confirmed by direct code reference (not by ORM model absence)

| Table | Live call site | Operation |
|---|---|---|
| `company_funding_events` | `runtime/feature_store/features.py` | `SELECT ... FROM public.company_funding_events` |
| `company_job_postings` | same | `SELECT ... FROM public.company_job_postings` |
| `company_intent_rfps` | same | `SELECT COUNT(*) FROM public.company_intent_rfps` |
| `company_intent_visits` | same | `SELECT COUNT(*) FROM public.company_intent_visits` |
| `company_intent_content` | same | `SELECT COUNT(*) FROM public.company_intent_content` |
| `company_intent_contacts` | same | `SELECT COUNT(*) FROM public.company_intent_contacts` |
| `company_products` | same | `SELECT DISTINCT ... FROM public.company_products` |
| `company_deals` | same | `SELECT SUM(amount) FROM public.company_deals` |
| `company_payments` | same | `SELECT COUNT(*) FROM public.company_payments` (×2 queries) |
| `company_policies` | `runtime/policy_runtime/__init__.py` | `SELECT policy_name, action, reason, severity FROM company_policies` |
| `decisions` | `runtime/decision_runtime/__init__.py` | `SELECT`/`INSERT`/`UPDATE` on `decisions` |
| `decision_feedback_loop` | `runtime/decision_runtime/feedback_loop.py` (`DecisionFeedbackLoop.record_feedback`) | `INSERT INTO decision_feedback_loop` |
| `domain_events` | `sdk/events/store.py` (`PostgresEventStore`), instantiated by `runtime/event_runtime/__init__.py` | Full CRUD via SQLAlchemy Core `Table` |
| `activity_records` | `runtime/activity_runtime/__init__.py` (`ActivityRuntime`) | `INSERT`/`SELECT` via SQLAlchemy Core `Table` |

Every one of these runtime engines is listed as **Live** in
`11_CAPABILITY_MATRIX.md` §1.8 and carried forward as COMPLETE in this
session's own reconciled register (report 57, rows 41 EventBus, 72 Activity
Runtime, 75 Decision Runtime — Feature Store and Policy Runtime are folded
into row 76/existing rows). **The register itself already told me these were
live; report 57 §3 should have cross-checked against its own §2 before
concluding "dead."**

### 3. The more serious finding: most of these tables carry tenant data through code that never pins the RLS session GUC

| Table / module | Pins `app.tenant_id` via `set_config`/`apply_tenant_guc`? | Isolation mechanism today |
|---|---|---|
| `decisions` (`runtime/decision_runtime/__init__.py`) | **Yes** — `apply_tenant_guc(session, decision.tenant_id)` before every query | GUC + manual `WHERE tenant_id` (RLS itself still absent at the DB level, so the GUC is currently pinned for nothing) |
| `decision_feedback_loop` (`feedback_loop.py`) | **No** | Manual `tenant_id` bind parameter on INSERT only |
| `company_*` × 9 (`feature_store/features.py`) | **No** | Manual `WHERE tenant_id = :tid` per query |
| `company_policies` (`policy_runtime/__init__.py`) | **No** | Manual `WHERE tenant_id = :tid AND is_active = true` |
| `domain_events` (`sdk/events/store.py`) | **No** | Manual `tenant_id` column value on INSERT; **no tenant filter at all on `read_by_type()`**, which reads across all tenants by event type |
| `activity_records` (`runtime/activity_runtime/__init__.py`) | **No** | `tenant_id` column is **nullable**, and the query builder applies the tenant filter **conditionally** (`if tenant_id is not None`) — some call sites can legitimately query with no tenant scoping at all |

**Consequence:** enabling `ENABLE`/`FORCE ROW LEVEL SECURITY` on these tables
today, using the same one-line pattern applied in report 58, would silently
break every one of these five runtime engines — `current_setting('app.tenant_id', true)`
returns `NULL` for any session that never called `set_config`, so a standard
`tenant_id::text = current_setting(...)` policy would make every unpinned
`SELECT` return zero rows and every unpinned `INSERT`/`UPDATE` fail its
`WITH CHECK`. This is not a 2-line fix like `account_funnel`/
`score_observations` (report 58) — those two already had a policy and were
already effectively governed by the same GUC convention used everywhere else;
these 14 have never been wired into that convention at all.

## Why this is not classified CODE-CLOSABLE this session

Closing this properly requires, in order:
1. A product/architecture decision on `activity_records.tenant_id`'s
   nullability and the `domain_events.read_by_type()` cross-tenant read path
   — both may be **intentionally** cross-tenant today (e.g. a global event
   replay or an internal admin activity feed) and turning that into
   forced tenant isolation could be a functional regression, not a fix,
   without a decision on intended behavior first.
2. Adding `apply_tenant_guc`-equivalent GUC pinning to five call sites across
   five different runtime engines (`activity_runtime`, `event_runtime` /
   `sdk/events/store.py`, `feature_store/features.py`, `policy_runtime`,
   `decision_runtime/feedback_loop.py`) — a real, non-trivial code change to
   live, routed engines.
3. Running the full existing regression scope for all five modules
   (`tests/unit/test_feature_store.py`, `test_feature_store_cache.py`,
   `test_scoring.py`, `test_event_runtime_subscriber_bounds.py`,
   `test_dashboard_mappers.py`, `test_deal_health.py`, `test_nba_pipeline.py`,
   plus any activity/policy-runtime suites) after the GUC-pinning change,
   before an RLS migration is even attempted.
4. Only then adding the RLS/FORCE RLS migration itself, following the
   canonical DEC-085 pattern — which, per DEC-130f, does **not** require
   dropping or reshaping these tables; RLS is pure additive DDL and is fully
   compatible with DEC-130f's "no DROP" constraint.
5. Given DEC-130f is itself a formally accepted decision record for this
   exact table set, the project's own established practice suggests this
   remediation should be proposed as its own dedicated DEC (a "DEC-130h" or
   similarly-numbered follow-on), not folded silently into an unrelated
   migration.

This is a materially different risk profile from report 58's fix (which
touched zero application code, only a DDL flag on two tables already
following the standard convention). Per the user's explicit decision this
session, **no code was changed**; this report exists to make sure the
finding is not lost and is scoped correctly for whoever picks it up next.

## Register effect

**None.** Report 57's reconciled register total (124/132) is unchanged by
this report — it was never an assertion about these 14 tables' RLS status;
it correctly listed the "21 tables with tenant_id, no RLS" as a documented,
not-closed finding. Only the *characterization* of 14 of those 21 tables
(as dead vs. live) is corrected here. Rows 41 (EventBus), 72 (Activity
Runtime), 75 (Decision Runtime) remain COMPLETE as before — their code-scope
completeness was never in question; what this report adds is that their
*tenant isolation at the database layer* has a real, newly-precise gap that
their own COMPLETE status does not capture (a nuance worth carrying forward
if the register is ever refined further).

## Deliberate non-claims

- No migration, test, or application code was written or executed this
  round. No ephemeral database was created.
- This is not a claim that cross-tenant data has actually leaked in
  production — that would require auditing actual production traffic
  patterns and data, which is out of this session's scope and authority.
- `rag_documents`/`rag_document_chunks` (also in DEC-130f's KEEP register)
  are explicitly excluded from this gap — they already have RLS via
  `h1i2j3k4l5m7_phase4a_rag_rls`, confirmed present in this session's own
  ephemeral-DB policy count (report 57 §1).
- Production remains **NOT APPROVED**; Phase 7 remains **BLOCKED**. Neither
  status is affected by this report.

## Recommended next step (drafted, not yet accepted)

Open a dedicated DEC (following the DEC-130f precedent and numbering
convention) proposing: (a) an explicit ruling on `activity_records`'
nullable-tenant and `domain_events`' cross-tenant-read semantics, (b) GUC
pinning added to the five identified call sites, (c) full regression proof,
(d) the RLS/FORCE RLS migration itself — scoped and reviewed as one unit,
given the live-engine blast radius, before any of it is implemented.

**Update, same day:** this proposal is now drafted as
`docs/program/decisions/DEC-157-ORPHAN-KEEP-TENANT-GUC-RLS-REMEDIATION.md`
and logged in `docs/program/DECISION_LOG.md`. Status is **Proposed — not
Accepted**; no code implementing any of its four steps has been written.
Do not begin implementation until an architecture reviewer accepts it and
rules on the two semantics questions in its §3.
