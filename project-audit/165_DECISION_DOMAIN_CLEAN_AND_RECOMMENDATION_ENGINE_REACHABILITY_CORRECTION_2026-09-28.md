# 165 — `domains/decision` (context + recommendation) fully clean; clarifies report 168's reachability scope — the engine is live even though its repository is dead

**Read-only.** No database or container needed — pure source-code review, since `RecommendationEngine.evaluate()` is a stateless, side-effect-free computation with no persistence involved on its live call paths.

## 1. Scope

Continuing the `domains/` sweep. `domains/decision` turned out to be the CONTRACT/domain-model layer that `domains/commercial/infrastructure/postgres_repositories.py`'s `PostgresContextRepository`/`PostgresRecommendationRepository` (already fixed in reports 167/168) implement against — confirmed directly: that file imports `DecisionContext`/`DecisionFactor`/`Policy`/`Recommendation`/etc. straight from `domains.decision.context.models`/`domains.decision.recommendation.models`. The parts of this domain not yet directly reviewed were the service layer (`domains/decision/context/service.py`) and the recommendation engine (`domains/decision/recommendation/engine.py`), plus their real callers.

## 2. `DecisionService` — clean, one known fix already applied

Read the full file. `build_context()`/`build_contexts()` construct `DecisionContext` objects with real, matching fields and correctly persist via `save_context()`/`save_contexts()` (already verified field-mapping-clean in report 167). `add_policy()` already contains report 167's fix (`policy.tenant_id = tenant_id` is applied before persisting — confirmed present, not re-broken). `add_factor()`'s fetch-mutate-save flow doesn't introduce a new gap: `context.policies` not surviving a round trip through `get_context()` is the same, already-documented gap from report 167 (`DecisionContextModel` has no `policies` column at all) — observed again here from the service-layer angle, not a new finding.

## 3. `RecommendationEngine.evaluate()` — clean, and genuinely live (correcting report 168's framing)

Read the full file (`domains/decision/recommendation/engine.py`). Every `Recommendation`/`Alternative`/`RecommendationEvidence` constructor call matches the real dataclasses' fields exactly (`id`, `tenant_id`, `context_id`, `title`, `description`, `reasoning`, `confidence`, `risk`, `expected_impact`, `evidence`, `alternatives`, `target_id`, `target_type` — all verified directly against `domains/decision/recommendation/models.py`).

**Reachability clarification**: report 168 stated "`RecommendationEngine.evaluate()`... is a pure computation — it never calls any repository's `save()`" while establishing that `PostgresRecommendationRepository` has zero callers. That's accurate but easy to misread as "the engine itself is unreached" — it is not. This codebase has (at least) three unrelated classes named `RecommendationEngine` in different packages (`domains.decision.recommendation.engine`, `runtime.recommendation_runtime`, `intelligence.recommendation_engine`); a naive grep for the class name alone conflates them. Checked each real import statement individually:

- `app/routers/commercial.py` — **2 live call sites**, both importing `domains.decision.recommendation.engine.RecommendationEngine` specifically. `GET .../recommendation` (line ~1505) computes one recommendation for a given `context_id` and returns it directly as JSON; the workspace dashboard endpoint (line ~1674) batches this across all open opportunities via `asyncio.gather()`. Both are pure compute-and-return — `Recommendation.save()` is never called on either path, so report 168's 3 fixed-but-dead repository bugs are correctly never exercised here, by design, not by accident.
- `app/application/dashboard/router.py` — 1 live call site, via `DashboardDecisionProvider`/`RecommendationEngineAdapter`, also compute-and-return (an ephemeral `InMemoryDecisionRepository` backs the accompanying `DecisionService`, deliberately not the durable Postgres one, since dashboard recommendations are recomputed per-request).
- `app/boot/startup.py`'s `app.state.recommendation_engine` and `app/modules/gtm/recommendation_router.py` use the **other two**, unrelated `RecommendationEngine` classes — not this one.

## 4. `DecisionServiceAdapter`/`RecommendationEngineAdapter` — clean

`app/application/dashboard/services/decision_platform_adapter.py` bridges the domain types to `sdk.scoring.interfaces`' SDK-facing types. Every field constructed on both sides (`DomainDecisionFactor`, `SDKDecisionContext`, `SDKRecommendation`, `SDKRecommendationEvidence`) verified directly against both dataclass definitions — all match.

## 5. Verdict

**No bug found anywhere in `domains/decision`.** The domain-model layer, service layer, recommendation engine, and its SDK-facing adapter are all internally consistent and correctly wired for their actual (compute-on-demand, not persist) live usage pattern.

## 6. Scope and safety

- No files changed — no bug found. No database or container needed.
- No gate closed. No auto-merge, auto-resolution, or cluster-certify attempted.

## 7. Loop status

Continuing the standing 24-hour continuous-loop authorization. Remaining `domains/` subdirectories not yet reviewed: `domains/ai`, `domains/copilot`, `domains/marketplace`, `domains/rag` (`domains/ubom` remains deferred, explicitly marked DEPRECATED).
