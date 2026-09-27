# 139 — domains/decision_center/postgres_repo.py: fully clean; live but zero downstream consumers

**Read-only in scope of production/salesos_test.** Pure source-code review; no database container needed.

## 1. Scope of this check

Starting a new systematic pass: checking `domains/*/postgres_repo.py` files (outside the already-fully-swept `domains/commercial/infrastructure/postgres_repositories.py`, whose 17 classes were checked across earlier reports — 8 had real contract/DB-model field-mismatch bugs, 9 were clean) for the same bug class. `domains/decision_center/postgres_repo.py` (439 lines, `PostgresDecisionCenterRepository`) was checked first, since Decision Center is called out repeatedly in this project's own history as a preferred live feature over stub decision engines.

## 2. Field-mapping check — every class pair is correct

Checked all four persisted dataclass/model pairs and every read/write method against them, line by line:

- **`Decision`/`DecisionModel`** (`save_decision`/`get_decision`/`update_decision_status`/`_decision_from_row`): `decision_type=decision.type.value`, `decision_metadata=decision.metadata`, `ensemble_votes` correctly serialized/deserialized as a list of `EnsembleVote` objects, `status=decision.status.value` — all correct both directions. `tenant_id` is derived from inside `decision.metadata` (the dataclass has no direct `tenant_id` field) — a harmless duplication (also stored whole in `decision_metadata`), not a bug.
- **`DecisionAudit`/`DecisionAuditModel`** (`save_audit`/`get_audit`/`_audit_from_row`): `input_context`, `reasoning_steps`, `confidence_breakdown`, `provider_used`, `alternatives_considered`, `timestamp`, `ensemble_metadata` — every field name matches exactly in both directions, confirmed by reading the actual method bodies (not just the column/field names).
- **`DecisionFeedback`/`DecisionFeedbackModel`** (`save_feedback`/`get_feedback_for_decision`/`_feedback_from_row`): `id`, `decision_id`, `rating.value` (stores `"up"`/`"down"`, matching `FeedbackRating(str, Enum)`'s exact values), `comment`, `actor_id`, `created_at` — correct both directions.
- **`FeedbackAggregate`** (`get_feedback_by_type`): joins `DecisionModel` to `DecisionFeedbackModel` via `func.cast(DecisionModel.id, sa_String) == DecisionFeedbackModel.decision_id` — the cast is already present (avoiding the uuid=varchar mismatch bug class found repeatedly elsewhere this session, e.g. reports 71/72/74/85), and `rating == "up"`/`"down"` string-literal comparisons match `save_feedback`'s stored values exactly.
- **`DecisionTemplate`/`DecisionTemplateModel`** (`save_template`/`get_template`/`list_templates`/`delete_template`/`update_template`/`_template_from_row`): `template_type=template.type.value`, `tenant_id`, `config`, `created_at` — all correct both directions, including the nullable-tenant-id (global template) `OR tenant_id IS NULL` read pattern used consistently across all three read methods.

**No bug found anywhere in this file.**

## 3. GUC pinning and reachability — live wiring, but no downstream consumer

Checked whether this class's real (non-test) construction site pins tenant GUC, since that is the second bug class this session found repeatedly (reports 129-131):

- **`app/startup.py:248`** (`dc_repo = PostgresDecisionCenterRepository(async_session())`) — confirmed dead code (this file, distinct from the live `app/boot/startup.py`, is never imported anywhere in `app/`, `runtime/`, or `domains/`; matches report 132's prior finding about this exact file).
- **`app/boot/startup.py:198-201`** (the LIVE boot path) — `repo = FactoryBoundRepository(PostgresDecisionCenterRepository, async_session)`; `app.state.decision_center_service = DecisionCenterService(repository=repo)`. Read `FactoryBoundRepository.__getattr__` (`app/database.py:124-160`) in full: every proxied async method call is wrapped in `tenant_scoped_session(self._session_factory)`, which itself calls `await apply_tenant_guc(session)` (no explicit `tenant_id` — falls back to the request-scoped `ContextVar`, the same established pattern `get_db()` uses) before yielding the session, and commits automatically on success / rolls back on exception. **This wiring is correct.**

However: `grep -rln "decision_center_service"` across the entire `app/` tree returns only `app/startup.py` (dead) and `app/boot/startup.py` (the assignment itself) — **zero routers, GraphQL resolvers, or any other code path ever reads `app.state.decision_center_service`**. The service is constructed correctly at boot, wired correctly end-to-end (GUC pinning, session lifecycle, field mapping), but has no caller — it is reachable from nowhere in an actual HTTP request today. This is a distinct shape from this session's usual findings: not a bug, not even reachable-but-broken dead code — it is **correctly-built, unreached code**, the mirror image of report 133's `graph_nodes` finding (a real gap that was fixed) and reports 73/74's "dead code fixed ahead of any future wiring decision" precedent (here there is nothing to fix).

## 4. Scope and safety

- No files changed. No test added (no bug to reproduce, and the wiring correctness was confirmed by direct code reading against the established `FactoryBoundRepository`/`tenant_scoped_session`/`apply_tenant_guc` contract already proven correct and tested elsewhere in this codebase).
- No database, container, or migration involved.
- No gate closed by this report. No auto-merge, auto-resolution, or cluster-certify attempted.

## 5. Loop status

Continuing the standing 24-hour continuous-loop authorization. This is the first file checked in the new "`domains/*/postgres_repo.py` field-mismatch sweep" pass (outside the already-fully-swept `domains/commercial/infrastructure/postgres_repositories.py`) — a clean result. Remaining candidates from the same pass: `domains/revenue/analytics/postgres_repo.py`, `domains/feature_store/postgres_repo.py`, `domains/workflow/postgres_repo.py`, `domains/timeline/engine/postgres_repo.py`, `domains/notifications/postgres_repo.py`, `domains/employee/postgres_repo.py`, `domains/search/engine/postgres_repo.py` (the latter already had 2 independent bugs found and fixed under a different methodology in reports 79-81, so it is skipped as already covered).
