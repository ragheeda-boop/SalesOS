# Sprint 03 — 2026-08-31 → 2026-09-13

> **Phase:** 0 — Foundation & Security Hardening · **Prior:** [Sprint 02](Sprint-02.md) · **Next:** [Sprint 04](Sprint-04.md) · **Index:** [ENGINEERING_ROADMAP.md](../ENGINEERING_ROADMAP.md)

> ## STORY-02-01 DONE under revised AC (DEC-044 Option B)
>
> **Human accepted Option B** (2026-08-01, “الخيار B”) — [`DEC-044`](../decisions/DEC-044-STORY-02-01-RLS-OPTION-B.md) supersedes [`DEC-DRAFT-STORY-02-01-RLS-72`](../decisions/DEC-DRAFT-STORY-02-01-RLS-72.md).
>
> **Revised AC:** all Category A tenant-scoped tables with a CREATE TABLE migration in the governed inventory (`ALL_TENANT_TABLES`) have RLS. Close at **47** policies (46 + `company_features`) — **not** the original literal **72**. Migration `065d1d3a466b` enables RLS on `company_features` only. Category B join policies → Sprint 04. Eight R-09 tables wait on DB-05. Original “100% of 72” AC is **retired** for this story.
>
> **R-14** (`docs/program/RISK_REGISTER.md`, score 25) and **DEC-013/DEC-014/DEC-015** (`docs/program/DECISION_LOG.md`): the application's DB role (`salesos`) is a Postgres superuser with BYPASSRLS — RLS policies, however correctly written and `FORCE`-enabled, provide **zero** actual protection under this role. Independently reproduced three times.
>
> **Local dev, CI, Staging, and the self-hosted Production Template: remediated and proven** (2026-07-31) — `salesos_app` (non-superuser, non-BYPASSRLS) provisioned via `infra/docker/postgres/init/02-app-role.sql` (auto-mounted by every compose file; an explicit CI step for GitHub Actions' non-compose ephemeral Postgres service), `app_database_url` wired in `app/config.py`/`app/database.py`, bypass-probe independently re-run against each environment's shape and confirmed isolating correctly, full regression suite re-checked with zero R-14-attributable regressions (29 pre-existing failures, all classified, none touch roles/RLS/permissions).
>
> **Railway: still unremediated, still blocked — by explicit choice, not oversight.** Railway's live role is `postgres` (not `salesos`), it provisions Postgres via a managed add-on rather than any compose file in this repo, and there is no init-script mount to rely on. Asked directly, the decision this session was to leave it **fully untouched**: no live connection, no `railway.json` edit. Applying R-14 there requires (a) explicit authorization to connect live and run the provisioning SQL + bypass-probe, or (b) a `railway.json`/deploy-process change that itself can't be verified without an actual deploy. See `OPERATIONS_MANUAL.md` §14 for the runbook. **STORY-02-01 is DONE (DEC-044) — do not reopen.** **STORY-02-02, STORY-02-03, and STORY-03-04 below may proceed independently.** Railway-targeted run remains blocked on R-14 (**S04-04**). **Phase 0 exit critical path = S04-04 only; Phase 0 remains NO-GO.**

**Sprint Goal:** RLS live (STORY-02-01 DONE @ 47 under DEC-044); `middleware.ts` live; Phase 0 exit gated on S04-04.

| Story | Owner | Priority | Risk | Status | Acceptance Criteria | Landing notes |
|---|---|---|---|---|---|---|
| STORY-02-01 (RLS rollout, complete) | BE-Lead, BE1 | P0 | High | **DONE** (revised AC) | **Revised (DEC-044):** Category A + migrated inventory RLS complete at **47** policies (46 + `company_features`). Original “100% of 72” **retired**. Category B → Sprint 04; 8× R-09 → DB-05 | DEC-044 Option B. Migration `065d1d3a466b`. Generator + `POLICY_COUNT` → 47. Railway R-14 still open. Phase 0 exit **NO-GO** |
| STORY-02-02 (middleware.ts) | FE-Lead | P0 | High | **PARTIAL** | Client-side-only auth gating removed; server-side redirect verified | Commit `3f4b3c8` on master — `middleware.ts` + cookie session sync + unit tests for redirect helpers. Client-only dashboard gate removed. QA verify **DEC-088** (tip `f2c7587`): Jest middleware/session **14/14 PASS** (**light validated**); Playwright harness present but browser/E2E redirect **not executed** (FE `node_modules` broken; compose FE/BE down). **No browser-pass claim.** Remains: live Next redirect probe + optional `smoke-ui.ps1` |
| STORY-02-03 (JWT audience split, groundwork) | BE1 | P1 | Medium | **DONE** | Issuer/audience claim structure defined (not yet consumed — EPIC-04 consumes it) | Commit `2379e5f` — `jwt_audience` / `jwt_owner_audience`, owner mint/verify helpers, unit tests. Consumption deferred to EPIC-04 / Sprint 04. Test run: **light validated** — commit `deae7de` / [`SWARM_VALIDATION_2026-08-01.md`](../../salesos/docs/audit/ga-engineering-audit/SWARM_VALIDATION_2026-08-01.md) (Docker pytest **15 passed** / 0 failed, including JWT suite + write-protection) |
| STORY-02-04 (relabel 4 global tables) | BE2 | P2 | Low | **DONE** | `CANONICAL_ARCHITECTURE.md` §17.2 updated | Commit `932f722` already on master — four tables relabeled Owner-Platform-scoped by design; scorecard updated |
| STORY-03-04 (contract test framework) | DevOps/SRE* | P1 | Medium | **DONE** | Template merged, used by first real endpoint test | Commit `623077c` — `tests/contract/` framework + first real endpoint (`GET /api/v1/identity/csrf-token`). Contract pytest execution: **not validated** at records close |

*DevOps/SRE not yet hired — BE-Lead covers as stopgap.

### Phase 0 exit (as of 2026-08-01)

**NO-GO.** **Critical path = S04-04 Railway R-14 only** (Human Gate — independent of parallel Sprint 05/06 READY work).

1. **R-14 / Railway (S04-04)** still open — **sole remaining Phase 0 exit critical-path gate**; blocked on credentials/authorization. Do not execute Railway without human auth.
2. **STORY-02-01** **DONE under revised AC (DEC-044)** at 47 policies — original literal 72 **retired**; Category B + R-09 gaps remain explicit Sprint 04 / DB-05 work. **Do not reopen.** Story close ≠ Phase 0 GO.
3. **Parallel (not critical path):** **CI GREEN not met** (MyPy/CI-20, pip-audit residual, npm audit/CI-14, Trivy fs, etc.; Jest-debt CLOSED DEC-077); STORY-02-02 **PARTIAL** (DEC-088 — units light-validated; browser redirect still absent). Continue READY tracks.

See DEC-040, **DEC-044**, and `docs/program/EXECUTION_DAG.md`.

**Expected Demo:** **Phase 0 Go/No-Go review.** Live demo of the adversarial cross-tenant test suite passing at 100%; green CI for 5 consecutive days shown via dashboard.

**Technical Debt Created:** None carried forward as Phase 0 exit credit — Phase 0 exit remains a hard "zero partial credit" gate per `PRODUCT_ROADMAP.md`. Landed groundwork (JWT split, contract framework, middleware) does not unlock Phase 0 GO. Category B RLS + R-09 CREATE TABLE remain deferred (Sprint 04 / DB-05), not absorbed as Phase 0 credit.
