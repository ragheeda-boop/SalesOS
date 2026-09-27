# 144 — app/modules/facts/apply_service.py (the canonical CRM-write boundary): confirmed clean, zero prior real-DB coverage closed

**Ephemeral, disposable Postgres container only (`sweep-pg17`, `pgvector/pgvector:pg16`, destroyed after use).** No `salesos_test` or production contact.

## 1. Scope — pivoting methodology per report 138's suggestion

Report 138 suggested pivoting to a raw-SQL/table-existence sweep restricted to files added since report 98 (fact ledger, provider spend, Agent Reach, MA-proposal-staging — none swept this way before). Checked `app/modules/billing/provider_spend.py` first (`ProviderSpendCoordinator`): its 5 raw-SQL calls to Postgres functions (`reserve_provider_spend`, `mark_provider_spend_in_flight`, `mark_provider_spend_unknown`, `settle_provider_spend`, `release_provider_spend`) were compared parameter-by-parameter and return-column-by-column against the exact `CREATE OR REPLACE FUNCTION` definitions in `app/alembic/versions/t3u4v5w6x7_provider_spend_reservations.py` — every call matches exactly. Consistent with report 86's own "2/2 PASS" integration-test claim for this file; no dedicated report needed for a file already covered.

Moved to `app/modules/facts/apply_service.py` (`FactApplyService`) — the **canonical CRM-write boundary**: the only code path in the entire codebase that ever writes a Phase 7 human-approved fact into the live `Company`/`Contact` tables (per `docs/adr/0114-canonical-write-boundary.md`).

## 2. Static verification — every allowlisted field is a real column; every type is compatible

`CRM_APPLY_FIELDS` allowlists 16 `company` fields and 6 `contact` fields. Checked each against `Company.__table__.columns`/`Contact.__table__.columns` via direct Python introspection: **all 22 exist exactly as named** — no drift between the allowlist and the real schema (this session's most commonly recurring bug class, e.g. reports 71/72/74/85/142/143's field-name mismatches, does **not** occur here).

`CanonicalFact.subject_id`/`tenant_id` and `Company.id`/`tenant_id` are all `UUID`-typed — no uuid-vs-varchar comparison risk (the second most commonly recurring bug class this session, e.g. reports 71/72/74/85).

`FactApplyService.apply()` verifies (does not itself pin) `current_setting('app.tenant_id', true)` against the caller's claimed `tenant_id` — correct, since the live router endpoint (`app/modules/facts/router.py:372`, `POST /facts/{fact_id}/apply`, gated by `require_permission_dep("master-data-review", PermissionAction.UPDATE)`) supplies `db: AsyncSession = Depends(get_db_session)`, the codebase's standard GUC-pinning DI chain already established correct dozens of times this session.

## 3. The coverage gap — a highly consequential path with zero real database exercise

`tests/unit/test_fact_apply_service.py` (the only existing test coverage) uses a hand-rolled fake `_Session`/`SimpleNamespace` in place of a real `AsyncSession`/`Company`/`CanonicalFact` — it has never actually inserted a row, executed real SQL, or verified a real database round trip. This is exactly the shape of test that let reports 142/143's real bugs slip through undetected for as long as they did. Given this file's severity (it is the *only* path that ever mutates canonical CRM data from an approved fact), this gap was worth closing even without a bug to fix.

## 4. New coverage — genuine, real database round trips

New `tests/integration/test_fact_apply_service_crm_write_db.py` (4 tests) against a fresh, disposable, fully-migrated Postgres container:

- `test_every_allowlisted_field_is_a_real_company_or_contact_column`: a static guard against future schema drift (fails loudly if a future migration renames/removes an allowlisted column).
- `test_apply_updates_the_real_company_row_and_writes_an_audit_event`: creates a real `Tenant`/`Company`/`CanonicalFact` (pre-approved), calls `FactApplyService.apply()` through the real GUC-pinned session path, then re-reads via a **genuinely separate session** (no identity-map shortcut — the exact trap that hid report 143's bug) to confirm the `Company.city` row and the `CanonicalFactEvent` audit row are both really persisted.
- `test_apply_rejects_a_field_not_on_the_allowlist`: confirms `cr_number` (an identity/control field, deliberately excluded per the ADR) is rejected even with a fully approved fact.
- `test_apply_is_idempotent_on_an_already_applied_fact`: confirms a second `apply()` call on an already-`APPLIED` fact returns `changed=False` without creating a duplicate audit event.

All 4 PASS. Combined regression with the existing mocked unit suite: **7/7 PASS**. Ruff (`E4,E7,E9,F,I`), `compileall`, and `git diff --check` all clean on the new file.

## 5. Scope and safety

- Files added: `salesos/backend/tests/integration/test_fact_apply_service_crm_write_db.py` (new). No source file changed — no bug found in `apply_service.py`.
- One disposable, ephemeral Postgres container (`sweep-pg17`) used for verification; destroyed after (`docker rm -f`). No `salesos_test` or production contact.
- No gate closed by this report (this does **not** touch Phase 7's human-review gates — `FactApplyService` only applies *already-approved* facts through the *existing*, already-governed review pipeline). No auto-merge, auto-resolution, or cluster-certify attempted.

## 6. Loop status

Continuing the standing 24-hour continuous-loop authorization. This is a genuine methodology pivot per report 138's suggestion (raw-SQL/table-existence sweep on newer modules) that yielded a clean result with a meaningful coverage gap closed, rather than a bug. Remaining candidates in the same newer-module family: `app/modules/agent_reach/persistence.py`/`fact_proposals.py` (already extensively covered across reports 61-65, 82-87 — lower priority for re-sweep), `app/modules/facts/review_service.py` (partially covered by report 72's reviewer-transition work — worth a dedicated static/coverage check), MA-proposal-staging (`report 100`'s `md_person_company_link_proposals` module).
