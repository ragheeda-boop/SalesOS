# OPS-01 Row 4 — Staging Soak Status + Final Verdict

> **SUPERSEDED wording (2026-08-12):** §§1–2 “soak not yet run / not started” and mid-window “IN PROGRESS” are **Incorrect-as-current**.  
> **Current:** 72h wall-clock **finished** 2026-08-10 (`loop-summary-2026-08-10T141003Z.json`, 854 iters / 82 failures). Row 4 remains **OPEN** (`soak_complete_claim=false`) pending TL triage + K2–K6. See [SOAK-GATE-CHECKLIST.md](./SOAK-GATE-CHECKLIST.md) · [OPS01-DR-GATE-2026-08-12.md](../../../../../reports/OPS01-DR-GATE-2026-08-12.md).

**Run:** EAB-2026-08-06-003 · **Update:** 2026-08-07 (banner 2026-08-12) · **Mode:** EXECUTE + VERIFY
**Parent:** [OPS-01-CHECKLIST.md](./OPS-01-CHECKLIST.md) · [OPS-01-ADVANCEMENT.md](./OPS-01-ADVANCEMENT.md)

---

## 1. Status of OPS-01 Row 4 (staging soak 48–72h, staging parity, not local-only)

**Status: OPEN** (parity achieved; soak not yet run)

| Prior label | This run |
|-------------|----------|
| OPEN — staging parity | **OPEN — parity CLOSED; soak execution remains** |

Work completed this run (all verified):
- Staging redeployed to **prod baseline `4750038c`** from a clean worktree; `/openapi.json` byte-identical to prod (881,643 B).
- Staging DB migrated to **repo head `e5f9a32b0c08`** (was `b7e2f65a3f07`); RLS 71/71; all 11 new tables present.
- Env parity: `DEBUG=false`, `FRONTEND_URL`, `FEATURE_HTTPONLY_ACCESS_COOKIE=false`, staging-scoped `GOOGLE_REDIRECT_URI`.
- **Secrets isolated:** new `JWT_SECRET_KEY` (`BF9D04AA99`) and `SECRET_KEY` (`AB16182BED`) distinct from prod (was identical → security failure fixed).
- **Prod Neo4j repaired** (`deploymentRedeploy` mutation, user-approved) → prod `/health` `graph=connected`; staging graph also connected — no inversion.
- **celery-worker + celery-beat redeployed to `4750038c`** (`Dockerfile.railway`) — cleared staging Postgres connection saturation (was pre-existing 01:14 UTC; now active=12/100).
- CI/CD: repo secrets `RAILWAY_STAGING_SERVICE_ID`/`RAILWAY_STAGING_ENVIRONMENT_ID` set; `deploy-staging.yml` updated + YAML-validated (5 jobs).
- Soak gates K1 now PASS; K2–K6 still OPEN.

## 2. Final verdict (as requested)

| Question | Verdict | Basis |
|----------|---------|-------|
| **Production** | **READY with conditions — NOT GO** | `/health` 200, DB/cache/redis/graph all connected, CI path active. **Conditions:** prod DB is **11 revisions behind its own code** (`d1a8c35e7f09` vs `e5f9a32b0c08`) — needs human-approved migration; prod Neo4j has **no persistent volume**; GA audit remains **production no-go** (Security 48 / Production Readiness 38). |
| **Staging** | **SOAK-CAPABLE WITH CONDITIONS** | Code/config/secret parity with prod baseline; healthy; Postgres saturation cleared. Conditions: staging Google OAuth app (human), accept/close WAL+offsite-backup gap, optional `max_connections` bump (100 vs 500). |
| **OPS-01 Row 4** | **OPEN** | Parity done, but soak **not started** — requires ≥48h (prefer 72h) dated-UTC evidence + Project Owner review (K2–K6). |
| **Launch** | **NO-GO** | Row 4 OPEN, Row 5 UNSIGNED (Project Owner signed **NO-GO**), prod DB behind code, prod Neo4j volume risk, GA audit no-go. |

## 3. Honesty note

- Staging changes were executed under the authorized "non-destructive fixes" mandate; prod change was a **single user-approved redeploy** of the pre-existing `neo4j-prod` deployment record (no volume/config change).
- "SOAK-CAPABLE" is an environment-readiness claim; it does **not** equal soak-complete or GA GO. `soak_complete_claim` stays **false** until K2–K6 close.
- No SIGN_HERE added.

## 4. Next required human actions (in order)

1. Create staging Google OAuth app → set `SSO_GOOGLE_CLIENT_ID`/`SSO_GOOGLE_CLIENT_SECRET` on staging.
2. Decide prod DB migration to `e5f9a32b0c08` (prod change — requires approval).
3. Decide prod Neo4j persistent volume; add `deploymentRedeploy` runbook note.
4. Accept or close staging WAL/offsite-backup gap; optionally bump staging `max_connections`/seed data.
5. Start soak: `python salesos/scripts/wave11-soak-gate.py --target https://salesos-staging.up.railway.app` ≥48h; evidence under `evidence/ops01-staging/`.
6. Project Owner review → `soak_complete_claim: true` + OPS-01 Row 4 → DONE.
7. Rotate the staging Postgres password (`VPGcEjKY…` exposed in a transcript once).

## 5. Project Owner decision record (2026-08-07)

The Project Owner reviewed the **Pre-Production Migration Risk Assessment** and decided:

- **Approved verdict:** `REQUIRES MAINTENANCE WINDOW` (NOT `SAFE TO EXECUTE`). Highest risk: revision `a4f7c29e1b80` creates **37 indexes without CONCURRENTLY** on live tables → write-lock risk during build.
- **Phase 1 (now):** start the **72h staging soak** — it validates runtime/stability/workers/memory/health and is independent of the DB migration.
- **Soak window started 2026-08-07T14:10:06Z** (see [SOAK-GATE-CHECKLIST.md](./SOAK-GATE-CHECKLIST.md)), PID 16044, evidence → `evidence/ops01-staging/`.
- **Phase 2 (after soak):** open a **Maintenance Window**: final backup → verify restore → pause/reduce writes → run the 15 migrations → smoke tests → performance monitoring.
- **New recommendation — Migration Dress Rehearsal:** restore a Production copy to a separate env, run the 15 migrations, measure time/lock/errors/resource usage; if clean, the maintenance window becomes more predictable.
- **Order:** Google OAuth for staging → 72h soak → finish Row 4 → Project Owner review → maintenance window → 15 migrations → prod smoke test → update EAB → Row 5 acceptance → re-evaluate Production GA.
- **Explicit guardrail:** do **not** execute the production DB migration outside a maintenance window.

## 6. Parallel-track directive (Project Owner 2026-08-07)

- **Path A (running):** continue the 72h soak, collect evidence, monitor for any P0 / regression. Evidence → `evidence/ops01-staging/` (iterations every 5 min; i1–i5 PASS as of 14:30Z).
- **Path B (started):** prepare the **Maintenance Window Package** + **Migration Dress Rehearsal** + **Index impact analysis** + execution/rollback docs.
- Path B deliverables this session:
  - [MAINTENANCE-WINDOW-PACKAGE.md](../../../MAINTENANCE-WINDOW-PACKAGE.md) — window playbook, preconditions, migrate runner pattern, rollback, dress-rehearsal runbook.
  - Read-only prod probe (evidence `evidence/ops01-staging/prod-index-probe.json`): **0/37 target indexes exist**; `companies` 141,221 rows / 345 MB is the dominant hot table; remaining hot tables ≈ empty → **window estimate ~2–10 min**, not 45+.
  - Migrate runner (`Dockerfile.migrate` + `salesos-migrate-4750038c`) proven on staging → reusable for the window.
- **Soak exit → window entry:** if soak finishes clean with no new P0, the team is ready to enter the maintenance window immediately, then re-evaluate Production GA per the Enterprise Audit Board.

## 7. Cutover package directive (Project Owner 2026-08-07)

- **Project Owner verdict:** the dress rehearsal was a **major milestone** — replaced theoretical estimates with **actual measurement**: dropped the biggest technical risk (`a4f7c29e1b80`, 37 non-CONCURRENTLY indexes ≈ **20 s** measured), turned the maintenance window into a measured window (with safety margin), and touched **no production** — preserving certification integrity.
- **Project Owner decisions:** ✅ continue soak · ✅ complete the **Production Cutover Package** · ✅ **do not execute anything on Production until the soak finishes** · ✅ after soak → review evidence → execute the window per the package → then Row 5 (human acceptance).
- **Deliverable:** single authoritative [PRODUCTION-CUTOVER-PACKAGE.md](../../../PRODUCTION-CUTOVER-PACKAGE.md) containing: T-0 checklist, minute-by-minute runbook (T-30→T+30), abort matrix, rollback runbook (restore vs forward-fix, decider, point-of-no-return), evidence matrix, and sign-off packet (Project Owner/ops + final GO/NO-GO). Supporting docs remain references only.
- **Progress estimate (Project Owner):** Engineering 100% · Verification 100% · Security 98% · OPS-01 Rows 1–3 100% · Row 4 ~15% (soak running) · Row 5 0% · Production Readiness ~96%.
- **Non-negotiable:** the **72h soak must actually complete** — it depends on elapsed time, not work volume.

## 8. Reconciliation evidence deposits (2026-08-07)

Addressing the reconciliation board (`reconciliation-2026-08-07`) without editing `GA_STATUS`/`SIGN_HERE` (per board constraint). New durable artifacts under `evidence/`:

| Board item | Deposit | Status |
|------------|---------|--------|
| **Missing Evidence #1** — post-repair prod `/health` JSON (graph=connected) | `evidence/ops01-prod-health/prod-health-2026-08-07T1623Z.json` (HTTP 200, `graph=connected`, uptime 42.84h) + `prod-health-detailed-2026-08-07T1623Z.json` (HTTP 200, all connected, SLA healthy) | **CLOSED** |
| **RC-P0-02 / DB-P0-2 / DO-P0-2 / EA-P0-2** — DR checklist "archive still off" vs evidence | `evidence/ops01-pitr/prod-live-wal-archive-reverify-2026-08-07.json`: live prod `archive_mode=on`, `archived_count` **1240** (grew 6→1240 since 2026-08-06 drill), `failed=0`, alembic `d1a8c35e7f09` | **RESOLVED** (stale claim references local compose, not prod) |
| **Soak progress** (board saw 24 loops) | Now **i00026** PASS (2026-08-07T16:16:59Z), 7 PASS / 0 FAIL, staging `/health` `graph=connected`; PID 16044 alive; ends 2026-08-10T14:10:06Z | **OPEN (in progress)** |
| **Auth & RBAC on prod (NEW audit)** | `evidence/ops01-prod-health/prod-auth-rbac-audit-2026-08-07.json` + [`PRODUCTION-AUTH-ROLE-AUDIT-2026-08-07.md`](../../PRODUCTION-AUTH-ROLE-AUDIT-2026-08-07.md) — **READ-ONLY**. AuthN PASS (login 200, unauth gates 401, CSRF enforced). Tenant-admin RBAC PASS (admin 200 / user 403 on all 4 runtime admin paths). Owner Platform admin routes deployed but **unreachable**: `/owner/login` NOT deployed (404 ×3, absent from prod openapi) → 401 for all owner routes (functional gap, not security breach). **Roles swapped vs assumption:** `muhide.com`=role user (unverified), `ratlfintech.com`=role admin; **both share tenant** `326e0825-1834-4399-8cca-77c2679f172b` → cross-tenant test inconclusive with these creds. | **COMPLETE (light validated)** — action items → Row 5 / maintenance window |
| **Owner-login deploy package (NEW)** | `OWNER-LOGIN-DEPLOY-PACKAGE-2026-08-07.md` (this dir) — scoped 3-file commit to enable Owner Console in the RC-06 maintenance window. Root cause confirmed: prod baseline `4750038c` has owner token machinery but **not** the `owner/login` route (uncommitted on `master`). Strict-minimum set: `identity/router.py` + `common/middleware.py` CSRF path + `tenant_lifecycle_guard.py` skip prefix. Rollback + risk register included. Registered as **RC-08** (BLOCKED until soak + RC-06). | **PREPARED — NOT EXECUTED** |

**Still NOT VERIFIED (human/board):** human CLOSE of DR rows 1–3 · single Security/PR score SoT · Project Owner acceptance · RPO/RTO acceptance · SSRF/KG pentest closure · prod Neo4j persistent volume decision. These remain `signed_off_by: ""` and require board/human action.

**Single source for decisions:** [`CTO-REQUIRED-HUMAN-DECISIONS.md`](../../../CTO-REQUIRED-HUMAN-DECISIONS.md) — Executive Decision Packet (RC-01…08; "CTO" = Project Owner per `RELEASE-GOVERNANCE-DECISION-2026-08-07.md`). AI recommendations only; decisions close only with human ink.
