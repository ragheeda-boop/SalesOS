# 127 — PostgresRecommendationRepository: three independent, stacked crashes, dead code

**Read-only in scope of production/salesos_test.** Verification ran against a disposable, ephemeral `pgvector/pgvector:pg16` container (`sweep-pg8`) migrated to head `f2e3d4c5b6a7`, torn down after use. No write to `salesos_test` or production.

## 1. Reachability — dead code, confirmed via grep, unlike Decision (report 126)

`PostgresRecommendationRepository` has zero references anywhere in `app/` (no router wiring) and zero references anywhere in `domains/` outside its own definition. `RecommendationEngine.evaluate()` (`domains/decision/recommendation/engine.py`) — the only production producer of a `Recommendation` — is a pure computation: it builds and returns a `Recommendation` object but never calls any repository's `save()` at all. There is no `RecommendationService` in this domain (unlike Decision's `DecisionService`). Fixed anyway, matching the established practice from reports 121/123/126 of correcting dead code ahead of any future wiring decision, since the crash is real and unconditional the instant a caller is added.

## 2. Bug 1 (identified by field-by-field comparison, masked by bug 2 in a real run) — `RecommendationEvidence` field names don't match

`RecommendationEvidence`'s real fields are `source_layer`/`source_domain`/`key`/`value`/`narrative` (`domains/decision/recommendation/models.py`). The original `save()` serialized using `e.factor`/`e.label`/`e.source_id`/`e.source_type` — none of which exist. This line is never reached in a real run because `save()` raises on `recommendation.recommendation_type` (bug 2, below) first — confirmed by field-by-field comparison against the dataclass, not by a separate isolated run.

**Fix**: serialize using the real field names (`source_layer`, `source_domain`, `key`, `value`, `narrative`).

## 3. Bug 2 (the first crash actually hit in the red run) — `recommendation.recommendation_type` doesn't exist on the domain at all

`Recommendation`'s real fields are `id`/`tenant_id`/`context_id`/`title`/`description`/`reasoning`/`confidence`/`risk`/`expected_impact`/`status`/`evidence`/`alternatives`/`created_at`/`target_id`/`target_type` — there is no `recommendation_type` field. `RecommendationModel.recommendation_type` is `String(100)`, `NOT NULL`, with **no column default**, so some value must be supplied. There is no domain concept this could stand in for (unlike Decision's `Policy.category`↔`outcome` mapping) — persisted as `""` and explicitly documented in-source, rather than fabricated.

`_to_domain()`'s `recommendation_type=model.recommendation_type` kwarg was also invalid — `Recommendation`'s constructor has no such parameter, an independent `TypeError` on every reload.

## 4. Bug 3 (found only via a byte-exact re-read of the dataclass, before writing the fix) — `applied_at`/`dismissed_at` don't exist on the domain

`RecommendationModel` has nullable `applied_at`/`dismissed_at` timestamp columns; `Recommendation` tracks only `status` (`PROPOSED`/`ACCEPTED`/`REJECTED`/`OVERRIDDEN`), with no field for when a transition happened. `_to_domain()`'s `applied_at=model.applied_at, dismissed_at=model.dismissed_at` kwargs are invalid — a third, independent `TypeError` that would have fired immediately after fixing bugs 1 and 2, undiscovered until this session's now-standard practice of re-verifying every field via a fresh read of both sides before writing any fix.

**Fix**: dropped from `_to_domain()`'s constructor call; left unset on `save()` (no domain source of truth exists), documented in-source.

## 5. Data-loss finding (not a crash) — `Alternative.expected_outcome`/`risk` were silently dropped

`Alternative`'s real fields include `expected_outcome`/`risk` in addition to `title`/`description`/`confidence`; `save()` only captured the latter three. Fixed to serialize all five fields; `_to_domain()`'s `Alternative(**a)` reconstruction already round-trips correctly once `save()` writes the complete dict.

## 6. No schema home (documented, not migrated) — `context_id`/`reasoning`/`risk`/`expected_impact`

`Recommendation.context_id` is **required** (no default) but `RecommendationModel` has no `context_id` column at all — same category as report 122's `Proposal.sections` gap. `reasoning`/`risk`/`expected_impact` are likewise real, populated domain fields with no corresponding column. `_to_domain()` uses `context_id=""` as an explicit placeholder (required to satisfy the constructor); the other three are simply omitted, defaulting to `""`. All four documented in a class-level docstring rather than fabricated or migrated.

## 7. Verification — genuine red→green

New `tests/integration/test_recommendation_repository_persistence_db.py` (1 test) drives the raw `PostgresRecommendationRepository` directly (no service layer exists for this domain), saving a `Recommendation` with one `RecommendationEvidence` and one `Alternative`, then reloading via `get()`, `list_by_target()`, and `list_by_tenant()`, asserting every field round-trips and that the raw `recommendation_type`/`applied_at`/`dismissed_at` columns hold the documented placeholder/unset values.

Reverting exactly the fixed file (scoped `git stash push -- domains/commercial/infrastructure/postgres_repositories.py`): `AttributeError: 'Recommendation' object has no attribute 'recommendation_type'` — the exact predicted first crash. Restored: test PASSES.

Regression: `domains/decision/recommendation/tests/test_recommendation.py` (9 tests, pure in-memory, unaffected) + this session's four persistence integration tests (Contract, Forecast, Decision, Recommendation): **16/16 PASS**. Ruff (`E4,E7,E9,F,I`) on the changed file: 25 findings before the fix (scoped stash) → 24 after — a net **improvement** of 1 (removing the now-redundant local `_to_domain()` import cleared an `I001` finding), zero new findings introduced. `compileall` and `git diff --check` clean.

## 8. Scope and safety

- Files changed: `salesos/backend/domains/commercial/infrastructure/postgres_repositories.py` (top-level import widened to include `Alternative`/`RecommendationEvidence`; `save()`/`_to_domain()` rewritten; class-level docstring added documenting all schema gaps), `salesos/backend/tests/integration/test_recommendation_repository_persistence_db.py` (new, includes the report 118/121 `current_database()` safety guard from the outset).
- `salesos_test` and production: untouched. Only the disposable container was written to; every env-var export was kept in the same Bash call as the command needing it.
- No gate closed by this report. No auto-merge, auto-resolution, or cluster-certify attempted.

## 9. Loop status

Continuing the standing 24-hour continuous-loop authorization ("stop only on completion, or something requiring heavy-weight human intervention"). This is the 5th class in `postgres_repositories.py` found with at least one guaranteed crash (StageEntry, Quote, Proposal, Decision, now Recommendation) — Contract, Forecast, and Analytics' core CRUD were clean (each had a *different*, non-crash bug instead, already fixed in reports 123/125). Recommendation is notable as the first class in this file confirmed to have **zero live callers at any layer** (not even a service wrapping it) — fixed on the same "correct dead code ahead of wiring" principle as reports 121/123/126, since every prior "unreached" sub-finding in this file (Decision's Policy methods, Contract's `kpis()`) turned out to be either partially reachable or trivially wireable. Remaining unreviewed classes in this file: `Meeting`, `Email`, `OpportunityContact`, `Review`, `Quota`, `Territory`.
