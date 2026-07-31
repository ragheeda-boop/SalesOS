# Sprint 05 — Enterprise Delivery Board (Program)

> **Canonical living board** for the Sprint 05 program entry package delivered under the Enterprise Delivery Mode governance (Sprint 04 → Sprint 05 transition package). Each story follows the governed cycle: pre-task package → executive approval → Phase 1 (implement + validate + local commit) → Phase 2 (controlled push/CI evidence) → executive close → record updates (DECISION_LOG / RISK_REGISTER).
> Status values: `PENDING`, `IN PROGRESS`, `BLOCKED` (with reason), `REGISTERED` (standalone story created by executive decision), `COMPLETE`.

| ID | Story | Priority | Status | Blocked on / Notes |
|---|---|---|---|---|
| CI-01 | Deploy Production branch guard (`deploy.yml`) | P0 | COMPLETE | Closed DEC-017; commit `61e08d4`, run `30648063788`; R-16 closed |
| CI-08 | GHCR 403 (staging image push) | P0 | BLOCKED | Org-level GHCR access, outside repo scope; R-17 |
| CI-11 | npm audit remediation (patch-only) | P0 | COMPLETE | Closed DEC-019; commit `060c946`, run `30649799993`; residual 30 high → CI-14 |
| S04-04 | Railway R-14 closure (DEC-016) | P0 | BLOCKED | Requires authorization/credentials |
| S04-01 | Adversarial RLS suite `tests/integration/test_adversarial_rls.py` | P0 | COMPLETE | 7/7 PASS after CI-15 (07e3ec4084fc); closed DEC-021; uncommitted fixes committed with CI-15 |
| CI-02 | pip-audit (Poetry) in CI | P0 | PENDING | |
| CI-03 | docker-smoke env var (`GF_SECURITY_ADMIN_PASSWORD`) | P0 | PENDING | |
| CI-07 | MyPy/Ruff `cli/` path in CI | P1 | PENDING | |
| CI-04 | Workflow fix (triage) | P1 | PENDING | |
| CI-05 | Workflow fix (triage) | P1 | PENDING | |
| CI-06 | Workflow fix (triage) | P1 | PENDING | |
| CI-13 | Jest suite baseline | P1 | PENDING | Dependency for CI-14 |
| S04-05 | Adversarial write-protection tests | P1 | PENDING | |
| S04-06 | Adversarial suite (remaining) | P2 | PENDING | |
| CI-12 | Workflow fix (triage) | P2 | PENDING | |
| CI-09 | VPS SSH/secrets provisioning | P2 | BLOCKED | Ops-side secret provisioning; R-17 |
| CI-10 | Workflow fix (triage) | P2 | PENDING | |
| compose prod name fix | docker-compose production service name | P2 | PENDING | |
| CI-14 | Frontend Dependency Modernization | P1 | REGISTERED | Standalone, Sprint 06 (DEC-018); dep CI-13; R-18 |
| CI-15 | Analytics Schema Reconciliation (add `metrics`, `dimensions`, `filters`, `visualization_type`, `created_by` to `analytics_reports` via Alembic) | P0 | CLOSED | Closed DEC-022; migration `07e3ec4084fc`; Phase 1 validation PASS + Phase 2 push `4793b08` → CI run `30652813475` (matrix identical to baseline `30649799993`; only delta = 10 new Ruff style violations from the migration file in the pre-existing red Backend Lint gate, transferred to the lint backlog, not fixed in CI-15); R-19 closed |
| DB-05 | Repository Schema Reconciliation Program — systemic ORM↔DB drift (R-20) | P1 | BACKLOG | Program story, multi-sprint (R-20); created by CI-15 Phase 1 decision; NOT part of CI-15; placed in backlog per DEC-022 |

## Progress
- Complete/Closed: 4/19 (CI-01, CI-11, S04-01, CI-15). Blocked: CI-08, S04-04, CI-09. Registered: CI-14. Backlog: DB-05.
- S04-01 status detail (CLOSED): RC1 (`:id::uuid` bind bug) and RC2 (cross-loop pool reuse) fixed and proven; 7th test was blocked on R-19 (analytics ORM↔DB drift), resolved by CI-15 migration `07e3ec4084fc`; suite now 7/7 PASS — see DEC-020/DEC-021/DEC-022.
- CI-15 Phase 1 (approved ACs, DEC-021): analytics-only scope; systemic drift OUT of scope, registered as R-20 with Program Story DB-05. Principle: **Local Story fixes Local Drift. Systemic Drift becomes a Program Initiative.** Phase 2 (DEC-022): pushed `4793b08`, CI run `30652813475` — job matrix identical to baseline, no functional/test/RLS/integration regression; 10 new Ruff style violations from the migration file disclosed and transferred to the lint backlog (not fixed within CI-15).
