# 124 — PostgresEvidenceRepository: type annotations referencing names never imported at module scope (genuinely different bug shape from reports 120-123)

**Read-only in scope of production/salesos_test.** Verification used a scoped `git stash`/`pop` and direct Python introspection (`typing.get_type_hints`) — no database container was needed for this specific defect class. No write to `salesos_test` or production.

## 1. A different bug shape from the last 4 reports

Reports 120-123 were all "domain contract fields don't match DB model columns" bugs in this same file. This one is structurally different: `PostgresEvidenceRepository`'s method **signatures** reference `Insight`, `InsightCategory`, `EvidenceItem` as type annotations (`async def save_insight(self, insight: Insight) -> Insight:`, `category: InsightCategory | None = None`, etc.), but **none of these names were ever imported at module scope** — only inside two OTHER methods' own function bodies (`_to_domain()` and `_evidence_to_domain()`, each with its own local `from domains.commercial.evidence.contracts.models import ...`).

Because this file has `from __future__ import annotations` active, Python never evaluates these signature annotations eagerly — ordinary calls to `save_insight()`, `list_insights()`, etc. work fine at runtime, since their bodies only access attributes on already-passed-in objects and never need to resolve `Insight`/`EvidenceItem` themselves. This is why the class's one existing caller (`tests/unit/test_evidence_scoring_adr0113.py`, which only exercises `save_evidence()`/`_evidence_to_domain()` — both of which *do* correctly import what they need) has always passed. The annotations are genuinely broken, though: any code that calls `typing.get_type_hints()` on these methods — a real, if not-yet-exercised, risk for anything that introspects this class (dataclass/Pydantic tooling, API doc generators, static analyzers) — hits a hard `NameError`, confirmed directly below.

## 2. Reachability

`PostgresEvidenceRepository` is referenced only by that one unit test, not by any router or service in `app/` (confirmed via a scoped grep of `app/` and `domains/`). Not live in production traffic today, but the annotation defect is real and independent of reachability — it is a property of the class definition itself, triggered the moment anyone introspects it, not by a particular caller.

## 3. Fix

Moved the module names actually needed (`Insight`, `InsightCategory`, `ConfidenceLevel`, `EvidenceItem`, `EvidenceType`, `EvidenceSource`, `EvidenceKind` from `domains.commercial.evidence.contracts.models`; `InsightModel`, `EvidenceItemModel` from the existing `.models` import block) to the top of the file, matching every other repository class in it. Removed the now-redundant local imports inside `save_insight`, `get_insight`, `list_insights`, `list_insights_by_confidence`, `save_evidence`, `list_evidence`, `count_by_category`, `count_by_confidence`, `_to_domain`, and `_evidence_to_domain` (all of which were either fully redundant with the new module-level import, or — for `select`/`func` — already available from this file's existing top-level `sqlalchemy` import). Checked for a circular-import risk before making the change (a common reason to keep imports local); confirmed clean via a direct fresh import of the module.

## 4. Verification — genuine red→green via runtime introspection, not a DB test

`typing.get_type_hints(PostgresEvidenceRepository.save_insight)` raised `NameError: name 'Insight' is not defined` before the fix (reproduced by reverting exactly this one file via a scoped `git stash`) and resolves correctly after (`{'insight': <class '...Insight'>, 'return': <class '...Insight'>}`), confirmed for both `save_insight` and `list_insights`. Restored the fix and reconfirmed the same successful resolution.

Regression: `tests/unit/test_evidence_scoring_adr0113.py` (the only existing caller of this class) + the domain test suites already touched this session (`test_quote.py`, `test_pipeline.py`, `test_proposal.py`, `test_contract.py`): **69/69 PASS**, no change in behavior for any exercised path. Ruff (`E4,E7,E9,F,I`): confirmed via scoped stash/pop that the file's finding count dropped from 47 to 26 (all removed findings were the `F821` undefined-name errors this fix targets, plus their associated now-unneeded local-import `I001` sort warnings) — 0 new findings introduced. `compileall` and `git diff --check` clean.

## 5. Scope and safety

- Files changed: `salesos/backend/domains/commercial/infrastructure/postgres_repositories.py` only (import reorganization; no behavior change to any method body).
- `salesos_test` and production: untouched — no database container was needed for this fix's verification.
- No gate closed by this report. No auto-merge, auto-resolution, or cluster-certify attempted.

## 6. Loop status

Continuing the standing "6 hours, all approvals" authorization. The remaining Ruff findings in this file (26, down from 58 at the start of today's sweep of it) are a mix of pre-existing, low-priority style issues (`E402` module-level-imports-not-at-top from later `from .models import ...` blocks deeper in the file, `E741` ambiguous variable name `l`, a couple of genuinely-unused `dataclass`/`ActivityModel` imports) — none currently look like another crash-bug lead of the report 120-123 shape. Remaining unreviewed repository classes in this file: `Forecast`, `Analytics`, `Decision`, `Recommendation`, `Meeting`, `Email`, `OpportunityContact`, `Review`, `Quota`, `Territory`.
