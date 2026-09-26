# 126 — PostgresDecisionRepository: guaranteed crash on every real call, plus a genuinely stale Policy schema

**Read-only in scope of production/salesos_test.** Verification ran against a disposable, ephemeral `pgvector/pgvector:pg16` container migrated to head, torn down after use. No write to `salesos_test` or production.

## 1. Reachability — live, same wiring pattern as reports 120-123, 125

`PostgresDecisionRepository` is instantiated by `app/routers/commercial.py`'s `_get_context(db)` factory (`DecisionService(PostgresDecisionRepository(db))`), used by real, mounted decision/recommendation endpoints. `DecisionService.build_context()`/`build_contexts()` — the entry points for every one of those endpoints — call `save_context()`/`save_contexts()` unconditionally.

## 2. Bug 1 (live, guaranteed crash) — `DecisionContext.confidence` doesn't exist

`DecisionContext` (`domains/decision/context/models.py`) has `factors: list[DecisionFactor]`, `policies: list[Policy]`, `generated_at` — no top-level `confidence` field at all. `DecisionContextModel` (table `commercial_decision_contexts`, FORCE RLS) has a flat `confidence: float` column and treats `factors` as a plain JSON dict, not a list of typed objects. `save_context()`/`save_contexts()` read `context.confidence`/`ctx.confidence` directly — `AttributeError` on every call, confirmed as the actual crash below.

**Fix**: `save_context()`/`save_contexts()` now serialize `factors` properly (each `DecisionFactor`'s `source_layer`/`source_domain`/`key`/`value`/`label`/`severity` as a dict) and omit `confidence` entirely — there is no domain source of truth for it, so it is left at the column's own default rather than fabricated.

## 3. Bug 2 (live, found only after fixing bug 1) — `get_context()`/`get_latest_for_target()` also used the wrong field name

Once bug 1's fix let execution reach the reload path for the first time, a second, independent, pre-existing bug surfaced: both methods constructed `DecisionContext(..., created_at=model.created_at)` — but the dataclass's field is `generated_at`, not `created_at`. This was masked the entire time by bug 1 (nothing could ever be saved, so nothing could ever be reloaded to hit this line). Fixed to `generated_at=model.created_at`.

## 4. Bug 3 (unreached, zero live callers) — `Policy`'s schema is stale, not renamed

`save_policy()`/`list_policies()` used `policy.rules`/`policy.outcome`/`policy.priority`/`policy.enabled` — none of which exist on `Policy` (real fields: `id`/`name`/`description`/`rule` [singular]/`category`) — and `policy.tenant_id`, which also didn't exist despite `PolicyModel.tenant_id` being a required column on this FORCE-RLS table (the same gap StageEntry and Proposal needed fixed in reports 120/122). Searched the codebase for any other class matching `PolicyModel`'s shape (`rules: list` / `outcome: str` / `priority: int` / `enabled: bool`) — found none; this looks like a genuinely stale table from an earlier, since-abandoned "Policy" design, not a simple field rename.

Checked reachability: `add_policy()`/`list_policies()` are **never called from any router endpoint** (confirmed via grep — only `build_context()`/`get_context()` are reachable). Fixed anyway with a documented, best-effort, lossy mapping, since this method would otherwise still crash the moment anyone does wire it up:
- `rules=[policy.rule] if policy.rule else []` — the single `rule` string preserved as the sole list entry.
- `outcome=policy.category` — the closest existing concept standing in for a column that has no domain equivalent at all; **explicitly documented as a stand-in, not a true semantic match**.
- `priority`/`enabled` — omitted from the constructor, left at the column's own defaults (`0`/`True`) rather than fabricated.
- Added `tenant_id: str = ""` to `Policy` (additive; the sole existing construction call site, in `test_context.py`, uses keyword arguments only). Fixed `DecisionService.add_policy(tenant_id, policy)` — which already received `tenant_id` as a parameter but never applied it to the object — to set `policy.tenant_id = tenant_id` before saving, matching the report 123 Contract `sign()` precedent of threading an already-available parameter through.

**Not fixed, disclosed**: `DecisionContext.policies` has no column on `DecisionContextModel` at all — not persisted, same category as report 122's Proposal.sections gap.

## 5. Verification — genuine red→green, all bugs together

New `tests/integration/test_decision_repository_persistence_db.py` (2 tests) drives the real `DecisionService`→`PostgresDecisionRepository` flow against a fresh, fully-migrated, RLS-enforced disposable database.

- `test_build_context_persists_and_reloads_factors_correctly`: builds a context with a critical `DecisionFactor`, reloads it via `get_context()` and `get_latest_context()`, and asserts the factor's `key`/`value`/`severity` all round-trip correctly and `has_critical()` still evaluates correctly on the reloaded object.
- `test_add_policy_persists_and_reloads_with_lossy_mapping`: adds a policy through the real service (thereby exercising the `tenant_id` threading fix), reloads it via `list_policies()`, and asserts the raw table row's `rules`/`outcome`/`priority`/`enabled` values match the documented mapping exactly.

Reverting exactly the 3 changed files (scoped `git stash`): `AttributeError: 'DecisionContext' object has no attribute 'confidence'` and `AttributeError: 'Policy' object has no attribute 'tenant_id'` — both exact predicted failures. Restored: both tests PASS. The `generated_at`/`created_at` bug (§3) was caught organically during this same red→green cycle — the first test run with bug 1 already fixed still failed, with the new, different, exact error `TypeError: DecisionContext.__init__() got an unexpected keyword argument 'created_at'`, which was then fixed and reconfirmed.

Regression: `domains/decision/context/tests/test_context.py` + both new tests: **9/9 PASS**. Ruff (`E4,E7,E9,F,I`): confirmed via scoped stash/pop that the combined 3-file baseline is unchanged at 27 findings (0 new). New test file Ruff-clean on its own. `compileall` and `git diff --check` clean.

## 6. Scope and safety

- Files changed: `salesos/backend/domains/commercial/infrastructure/postgres_repositories.py`, `salesos/backend/domains/decision/context/models.py` (`Policy.tenant_id` addition), `salesos/backend/domains/decision/context/service.py` (`add_policy()` fix), `salesos/backend/tests/integration/test_decision_repository_persistence_db.py` (new, includes the report 118/121 `current_database()` safety guard from the outset).
- `salesos_test` and production: untouched. Only the disposable container was written to; every env-var export was kept in the same Bash call as the command needing it.
- No gate closed by this report. No auto-merge, auto-resolution, or cluster-certify attempted.

## 7. Loop status

Continuing the standing 24-hour continuous-loop authorization ("stop only on completion, or something requiring heavy-weight human intervention"). This is the 4th live, guaranteed-crash bug found in this file (StageEntry, Quote, Proposal, now Decision) — Contract, Forecast, and Analytics' core CRUD were all clean, so the pattern is real but not universal; each remaining class is checked on its own merits. Remaining unreviewed classes: `Recommendation`, `Meeting`, `Email`, `OpportunityContact`, `Review`, `Quota`, `Territory`.
