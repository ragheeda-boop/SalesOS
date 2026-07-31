# Sprint 03 — 2026-08-31 → 2026-09-13

> **Phase:** 0 — Foundation & Security Hardening · **Prior:** [Sprint 02](Sprint-02.md) · **Next:** [Sprint 04](Sprint-04.md) · **Index:** [ENGINEERING_ROADMAP.md](../ENGINEERING_ROADMAP.md)

> ## ⚠️ STORY-02-01 PARTIAL / STOPPED — pending architecture decision
>
> **Database Team Alpha STOPPED** (2026-08-01) on STORY-02-01 with inventory evidence — **no further RLS migration shipped**. Live policies: **46** (`ALL_TENANT_TABLES` / `0afbf3e6ae53`). Sprint AC target **72** → gap **26**. ORM tables with `tenant_id`: **55**; **9** missing from RLS list; only **`company_features`** is additive-safe; **8** blocked on R-09 (no CREATE TABLE). Remainder is Category B join policies (Sprint 04); canonical “exactly 72” inventory is **not pinned** (55+14≈69). Decision package: [`docs/program/decisions/DEC-DRAFT-STORY-02-01-RLS-72.md`](../decisions/DEC-DRAFT-STORY-02-01-RLS-72.md) — **DRAFT**, recommends **Option B** (close at 46+`company_features`=47 with revised AC; Category B → Sprint 04; R-09 tables wait on DB-05). **Not Accepted.**
>
> **R-14** (`docs/program/RISK_REGISTER.md`, score 25) and **DEC-013/DEC-014/DEC-015** (`docs/program/DECISION_LOG.md`): the application's DB role (`salesos`) is a Postgres superuser with BYPASSRLS — RLS policies, however correctly written and `FORCE`-enabled, provide **zero** actual protection under this role. Independently reproduced three times.
>
> **Local dev, CI, Staging, and the self-hosted Production Template: remediated and proven** (2026-07-31) — `salesos_app` (non-superuser, non-BYPASSRLS) provisioned via `infra/docker/postgres/init/02-app-role.sql` (auto-mounted by every compose file; an explicit CI step for GitHub Actions' non-compose ephemeral Postgres service), `app_database_url` wired in `app/config.py`/`app/database.py`, bypass-probe independently re-run against each environment's shape and confirmed isolating correctly, full regression suite re-checked with zero R-14-attributable regressions (29 pre-existing failures, all classified, none touch roles/RLS/permissions).
>
> **Railway: still unremediated, still blocked — by explicit choice, not oversight.** Railway's live role is `postgres` (not `salesos`), it provisions Postgres via a managed add-on rather than any compose file in this repo, and there is no init-script mount to rely on. Asked directly, the decision this session was to leave it **fully untouched**: no live connection, no `railway.json` edit. Applying R-14 there requires (a) explicit authorization to connect live and run the provisioning SQL + bypass-probe, or (b) a `railway.json`/deploy-process change that itself can't be verified without an actual deploy. See `OPERATIONS_MANUAL.md` §14 for the runbook. **STORY-02-02, STORY-02-03, and STORY-03-04 below are not affected by the RLS inventory stop** and may proceed independently. Further STORY-02-01 DDL waits on DEC-DRAFT-STORY-02-01-RLS-72; Railway-targeted run remains blocked on R-14.

**Sprint Goal:** RLS live everywhere; `middleware.ts` live; Phase 0 exit gate.

| Story | Owner | Priority | Risk | Status | Acceptance Criteria | Landing notes |
|---|---|---|---|---|---|---|
| STORY-02-01 (RLS rollout, complete) | BE-Lead, BE1 | P0 | High | **PARTIAL / STOPPED** | Original AC: 100% of 72 tenant-scoped tables + adversarial 100% — **unachievable as written** without Category B design + inventory pin (see DRAFT). Evidence: 46 live; +1 safe (`company_features`); 8× R-09; Category B → Sprint 04 | **STOPPED** pending [`DEC-DRAFT-STORY-02-01-RLS-72`](../decisions/DEC-DRAFT-STORY-02-01-RLS-72.md) (recommends B → revised AC at 47). Railway R-14 still open. Phase 0 exit **NO-GO** |
| STORY-02-02 (middleware.ts) | FE-Lead | P0 | High | **PARTIAL** | Client-side-only auth gating removed; server-side redirect verified | Commit `3f4b3c8` on master — `middleware.ts` + cookie session sync + unit tests for redirect helpers. Client-only dashboard gate removed. Browser/E2E redirect: **not validated**. No browser-pass claim |
| STORY-02-03 (JWT audience split, groundwork) | BE1 | P1 | Medium | **DONE** | Issuer/audience claim structure defined (not yet consumed — EPIC-04 consumes it) | Commit `2379e5f` — `jwt_audience` / `jwt_owner_audience`, owner mint/verify helpers, unit tests. Consumption deferred to EPIC-04 / Sprint 04. Test run: **light validated** — commit `deae7de` / [`SWARM_VALIDATION_2026-08-01.md`](../../salesos/docs/audit/ga-engineering-audit/SWARM_VALIDATION_2026-08-01.md) (Docker pytest **15 passed** / 0 failed, including JWT suite + write-protection) |
| STORY-02-04 (relabel 4 global tables) | BE2 | P2 | Low | **DONE** | `CANONICAL_ARCHITECTURE.md` §17.2 updated | Commit `932f722` already on master — four tables relabeled Owner-Platform-scoped by design; scorecard updated |
| STORY-03-04 (contract test framework) | DevOps/SRE* | P1 | Medium | **DONE** | Template merged, used by first real endpoint test | Commit `623077c` — `tests/contract/` framework + first real endpoint (`GET /api/v1/identity/csrf-token`). Contract pytest execution: **not validated** at records close |

*DevOps/SRE not yet hired — BE-Lead covers as stopgap.

### Phase 0 exit (as of 2026-08-01)

**NO-GO.** Reasons (honest, evidence-governed):

1. **R-14 / Railway** still open — S04-04 blocked on credentials/authorization.
2. **STORY-02-01** **PARTIAL / STOPPED** — 46 policies live; original 72 AC unmet; architecture DRAFT pending (recommend revise AC to 47 + defer Category B). Incomplete 72 unless AC revised; Phase 0 still **NO-GO** either way until Railway + completeness criteria clear.
3. **CI GREEN not met** — overall CI workflow remains red (MyPy/CI-20, pip-audit/CI-16, npm audit/CI-14, Jest debt, Trivy fs, etc.).
4. STORY-02-02 is **PARTIAL** (middleware landed; browser redirect verification absent).

See DEC-040, `DEC-DRAFT-STORY-02-01-RLS-72`, and `docs/program/EXECUTION_DAG.md`.

**Expected Demo:** **Phase 0 Go/No-Go review.** Live demo of the adversarial cross-tenant test suite passing at 100%; green CI for 5 consecutive days shown via dashboard.

**Technical Debt Created:** None carried forward as Phase 0 exit credit — Phase 0 exit remains a hard "zero partial credit" gate per `PRODUCT_ROADMAP.md`. Landed groundwork (JWT split, contract framework, middleware) does not unlock Phase 0 GO.
