# Sprint 03 — 2026-08-31 → 2026-09-13

> **Phase:** 0 — Foundation & Security Hardening · **Prior:** [Sprint 02](Sprint-02.md) · **Next:** [Sprint 04](Sprint-04.md) · **Index:** [ENGINEERING_ROADMAP.md](../ENGINEERING_ROADMAP.md)

> ## ⚠️ PARTIALLY UNBLOCKED — STORY-02-01 still cannot start against Railway
>
> **R-14** (`docs/program/RISK_REGISTER.md`, score 25) and **DEC-013/DEC-014/DEC-015** (`docs/program/DECISION_LOG.md`): the application's DB role (`salesos`) is a Postgres superuser with BYPASSRLS — RLS policies, however correctly written and `FORCE`-enabled, provide **zero** actual protection under this role. Independently reproduced three times.
>
> **Local dev, CI, Staging, and the self-hosted Production Template: remediated and proven** (2026-07-31) — `salesos_app` (non-superuser, non-BYPASSRLS) provisioned via `infra/docker/postgres/init/02-app-role.sql` (auto-mounted by every compose file; an explicit CI step for GitHub Actions' non-compose ephemeral Postgres service), `app_database_url` wired in `app/config.py`/`app/database.py`, bypass-probe independently re-run against each environment's shape and confirmed isolating correctly, full regression suite re-checked with zero R-14-attributable regressions (29 pre-existing failures, all classified, none touch roles/RLS/permissions).
>
> **Railway: still unremediated, still blocked — by explicit choice, not oversight.** Railway's live role is `postgres` (not `salesos`), it provisions Postgres via a managed add-on rather than any compose file in this repo, and there is no init-script mount to rely on. Asked directly, the decision this session was to leave it **fully untouched**: no live connection, no `railway.json` edit. Applying R-14 there requires (a) explicit authorization to connect live and run the provisioning SQL + bypass-probe, or (b) a `railway.json`/deploy-process change that itself can't be verified without an actual deploy. See `OPERATIONS_MANUAL.md` §14 for the runbook. **STORY-02-02, STORY-02-03, and STORY-03-04 below are not affected by this block** and may proceed independently. STORY-02-01 may proceed against local dev/CI/staging/prod-template shapes; only a Railway-targeted run remains blocked.

**Sprint Goal:** RLS live everywhere; `middleware.ts` live; Phase 0 exit gate.

| Story | Owner | Priority | Risk | Acceptance Criteria |
|---|---|---|---|---|
| STORY-02-01 (RLS rollout, complete) | BE-Lead, BE1 | P0 | High | 100% of 72 tenant-scoped tables have an RLS policy; adversarial suite passes 100% |
| STORY-02-02 (middleware.ts) | FE-Lead | P0 | High | Client-side-only auth gating removed; server-side redirect verified |
| STORY-02-03 (JWT audience split, groundwork) | BE1 | P1 | Medium | Issuer/audience claim structure defined (not yet consumed — EPIC-04 consumes it) |
| STORY-02-04 (relabel 4 global tables) | BE2 | P2 | Low | `CANONICAL_ARCHITECTURE.md` §17.2 updated |
| STORY-03-04 (contract test framework) | DevOps/SRE* | P1 | Medium | Template merged, used by first real endpoint test |

*DevOps/SRE not yet hired — BE-Lead covers as stopgap.

**Expected Demo:** **Phase 0 Go/No-Go review.** Live demo of the adversarial cross-tenant test suite passing at 100%; green CI for 5 consecutive days shown via dashboard.

**Technical Debt Created:** None carried forward — Phase 0 exit is a hard "zero partial credit" gate per `PRODUCT_ROADMAP.md`.
