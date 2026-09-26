# 123 — ContractService.sign() never recorded who/when a contract was signed; PostgresContractRepository.kpis() returned fake numbers

**Read-only in scope of production/salesos_test.** Verification ran against a disposable, ephemeral `pgvector/pgvector:pg16` container migrated to head, torn down after use. No write to `salesos_test` or production.

## 1. First clean class in this file — the 3-for-3 streak breaks

Continuing the same-file sweep after reports 120/121/122 (StageEntry, Quote, Proposal — all guaranteed-crash bugs from a domain-contract/DB-model field mismatch), `PostgresContractRepository`'s core CRUD (`save()`/`get()`/`get_by_opportunity()`/`get_by_quote()`/`list_by_tenant()`/`_to_domain()`) was checked field-by-field against the real `Contract`/`ContractParty`/`ContractObligation`/`RenewalRule` dataclasses and found **correct** — every field used matches a real contract field. This is not a crash-bug report; the two bugs found here are a silent data-loss bug in a live endpoint and a set of fake/wrong metrics in unreached code, both found by tracing the service layer rather than from mypy or a field-name diff.

## 2. Bug 1 — `ContractService.sign()` never touched the fields it exists to set

`Contract.signed_by_provider`/`signed_by_customer` are `datetime | None` — timestamps of *when* each party signed. `ContractService.sign(contract_id, signed_by_provider: str, signed_by_customer: str)` takes the *signer's name* as a string, but its old body only forwarded these strings into the emitted event's `extra` payload (`{"provider": ..., "customer": ...}`) and called the shared `_transition()` helper, which only ever sets `status`/`updated_at` — **nothing ever wrote to `Contract.signed_by_provider`/`signed_by_customer`, regardless of what was passed.**

Live and reachable: `POST /contracts/{contract_id}/sign` (`app/routers/commercial.py`) calls exactly this method, and its own response handler (`_contract_response`) serializes `signed_by_provider`/`signed_by_customer` back to the caller — every real signing request returned `null` for both fields, no matter what signer name was submitted.

**Fix**: `sign()` now fetches the contract itself, sets `signed_by_provider`/`signed_by_customer` to the current timestamp when the corresponding name argument is truthy (recording *that* and *when* each party signed — the name itself has no field to live in and remains available only in the emitted event, unchanged from before), sets `status=SIGNED`, and saves. No `_transition()` double-fetch risk here — `sign()` no longer routes through it.

## 3. Bug 2 — `PostgresContractRepository.kpis()`: 3 of 5 fields fake, 1 mislabeled, 1 correct

`ContractKPIs` has 5 real fields: `total_contracts`, `active_contracts`, `signed_rate`, `renewal_rate`, `expiring_soon`, `total_contract_value` (6, corrected count). The Postgres implementation:
- Set `renewal_rate=0.85` — a **hardcoded constant**, never computed from any data.
- Never set `signed_rate` at all — silently always its dataclass default `0.0`.
- Computed `expiring_soon` as the count of contracts with `status == "expired"` — i.e. *already expired*, not *expiring soon* (the in-memory reference defines it as signed contracts whose `expiry_date` falls within the next 90 days — a materially different, and correct, business meaning).
- Set `total_contract_value=0.0` unconditionally, **ignoring the `quote_values` parameter entirely** — the one piece of external data the method was explicitly given to compute this figure from.

Checked reachability: `ContractService.kpis()` exists and delegates correctly, but is called only by a domain-level unit test (`test_contract.py`) — **no live router endpoint calls it today**. Fixed anyway, for the same reason reports 121/122 fixed their zero-caller `revenue_kpis()`/`kpis()` methods: mirroring the in-memory reference repository's exact formulas keeps both implementations contract-aligned, and the fake `0.85` in particular is the kind of stub value that becomes a real incident the day someone wires this method into a dashboard without re-checking it first.

**Fix**: rewrote `kpis()` to load contracts via `list_by_tenant()` and compute all five figures with the identical formulas as `contract/in_memory_repo.py`.

## 4. Verification — genuine red→green, both bugs independently

New `tests/integration/test_contract_repository_persistence_db.py` (2 tests) drives the real `ContractService`→`PostgresContractRepository` flow against a fresh, fully-migrated, RLS-enforced disposable database.

- `test_sign_persists_signed_at_timestamps_and_status`: creates a contract, calls `sign()`, asserts `signed_by_provider`/`signed_by_customer` are non-null both on the returned object and in the raw table row.
- `test_kpis_mirrors_in_memory_reference_formulas`: seeds 3 contracts (one signed and expiring within 90 days, one signed-then-renewed, one still draft) and asserts all 5 KPI figures against hand-derived expected values. One test-authoring mistake was caught and corrected during this same verification pass: the test initially assumed a signed-then-renewed contract still counts toward `signed_rate` — it does not, since `Contract.is_signed` only covers `SIGNED`/`ACTIVE`/`COMPLETED`, not `RENEWED`. Caught by the test's own first failed run (`0.33 == 0.67`), traced to the real `is_signed` property definition (not guessed at), and the test's assertions corrected to match — the production formula itself was not touched or worked around.

Reverting exactly the 2 changed files (scoped `git stash`): both tests fail — `signed_by_provider` is `None` (exact predicted gap), and `kpis()` returns the old hardcoded values (`renewal_rate=0.85`, `signed_rate=0.0`, `expiring_soon=0`, `total_contract_value=0.0`, `signed_rate` computed as `0.0` against an expected `0.33`). Restored: both PASS.

Regression: `domains/commercial/contract/tests/test_contract.py` + both new tests: **12/12 PASS**. Ruff (`E4,E7,E9,F,I`): confirmed via scoped stash/pop that the 2-file baseline is unchanged at 58 findings (0 new; all pre-existing, unrelated to this change — the `EvidenceItem`/`Insight` `F821` findings live in `PostgresEvidenceRepository`, a different, not-yet-reviewed class). New test file Ruff-clean on its own. `compileall` and `git diff --check` clean.

## 5. Scope and safety

- Files changed: `salesos/backend/domains/commercial/infrastructure/postgres_repositories.py` (`kpis()` rewrite + `timedelta` import), `salesos/backend/domains/commercial/contract/service.py` (`sign()` rewrite), `salesos/backend/tests/integration/test_contract_repository_persistence_db.py` (new, includes the report 118/121 `current_database()` safety guard from the outset).
- `salesos_test` and production: untouched. Only the disposable container was written to; every env-var export was kept in the same Bash call as the command needing it throughout.
- No gate closed by this report. No auto-merge, auto-resolution, or cluster-certify attempted.

## 6. Loop status

Continuing the standing "6 hours, all approvals" authorization. `PostgresEvidenceRepository`'s `F821` findings (`Insight`/`InsightCategory`/`EvidenceItem` referenced but seemingly not imported at module scope) are a concrete, specific lead for the next iteration — a genuinely different kind of defect (missing import, not a contract/model mismatch) from the pattern this file has shown 3 times so far. Remaining unreviewed classes: `Forecast`, `Analytics`, `Decision`, `Recommendation`, `Meeting`, `Email`, `OpportunityContact`, `Review`, `Quota`, `Territory`, `Evidence`.
