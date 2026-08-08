# CTO-REQUIRED-HUMAN-DECISIONS.md

```
AUTHORITATIVE DECISION PACK

This document may only be changed by
an authorized human approver.

AI may propose recommendations only.

AI must never close,
approve,
reject,
or sign
any decision in this register.
```

**Pack:** SalesOS Production GA — Human Decision Register  
**Date:** 2026-08-07 · **Owner:** Project Owner (sole decision-maker; "CTO" in this register = Project Owner, per `RELEASE-GOVERNANCE-DECISION-2026-08-07.md`)  
**Inputs:** `reconciliation-2026-08-07/` (R1–R7 + Board Consensus) · EAB-2026-08-06-003 evidence · `PRODUCTION-CUTOVER-PACKAGE.md`  
**Arabic executive summary:** [`CEO-EXECUTIVE-BRIEF-AR.md`](./CEO-EXECUTIVE-BRIEF-AR.md)

---

## 1. Executive Summary

| Item | Status |
|------|--------|
| Technical Readiness | PASS |
| Governance Readiness | CONDITIONAL |
| Production Readiness | NO-GO (Until decisions complete) |
| Soak | IN PROGRESS |
| Remaining Human Decisions | 7 |

```text
This document contains every remaining decision that
cannot legally or operationally be made by AI.

Only authorized human approvers may close these items.
```

---

## 2. Decision Register

---

## RC-01

### Title

OPS-01 Rows 1–3 Disposition

### Current State

`GA_STATUS.md` #7 + OPS-01 checklist mark offsite/WAL/PITR **DONE (2026-08-06)**; `DR-GA-GAPS-CHECKLIST.md` rows 1–3 remain **OPEN**; `SIGN_HERE.md` lists them **OPEN**; EAB CEO/RUN/PROGRAM/FINDINGS call OPS-01 "still open / Deferred". DONE∩OPEN cannot both be current.

### Evidence

- OPS-01 advancement + checklist: `EAB-2026-08-06-003/OPS-01-ADVANCEMENT.md`, `OPS-01-CHECKLIST.md` (OPS01-01…03 DONE*)
- Offsite: `evidence/ops01-offsite/ops01-row1-offsite-restore.json` — pg_dump→S3 `salesos-backups-iwrweogrr`, restore drill exit 0, sha256 match, companies 141,221 = live, alembic `d1a8c35e7f09` match
- WAL: `evidence/ops01-pitr/ops01-row2-wal-archiver.json` + `prod-live-wal-archive-reverify-2026-08-07.json` — live prod `archive_mode=on`, archived **1240**, failed=0
- PITR: `evidence/ops01-pitr/ops01-row3-pitr-restore.json` — restore exit 0, promoted timeline 2, exact row match

### Options

**Option A** — Close checklist: CLOSE DR rows 1–3 with ink; update SIGN_HERE/EAB language to Partial/DONE-with-residuals (human CLOSE is authoritative).

**Option B** — Revert DONE*: qualify `GA_STATUS`/OPS DONE* until automation + sign-off meet checklist text.

### Risks

- A: checklist CLOSED but native `volumeInstancePITRRestore` remains not-authorized (RC-04) — residual must be labeled residual, not "fully closed".
- B: machine evidence (rows 1–3 drill facts) is real; wholesale revert falsely denies successful drills.

### Recommendation

**Option A** — CLOSE rows 1–3 as *drill facts done*, with explicit residual banner for the not-yet-authorized native PITR path (RC-04). Facts are evidence-verified; the DR checklist must reflect them instead of stale "archive off / not done".

### Human Decision

□ Approve

□ Reject

□ Defer

---

## RC-02

### Title

Accept WAL / PITR Evidence

### Current State

Board `RC-P0-02`: DR checklist EAB-003 block claims archive **Still off** / offsite **NOT done**, contradicting linked evidence JSON. Live prod reverify (2026-08-07) shows `archive_mode=on`, archived **1240**, failed=0.

### Evidence

- `evidence/ops01-pitr/prod-live-wal-archive-reverify-2026-08-07.json` (live, 2026-08-07)
- `evidence/ops01-pitr/ops01-row2-wal-archiver.json` (2026-08-06 drill)
- `evidence/ops01-pitr/ops01-row3-pitr-restore.json` (PITR restore drill, exit 0)
- `evidence/ops01-offsite/ops01-row1-offsite-restore.json` (offsite restore drill)

### Options

**Option A** — Accept evidence: stale `archive_mode=off` claim is a local-compose scoping error (see `COMPOSE-SOURCE-OF-TRUTH.md`); prod WAL/PITR facts stand.

**Option B** — Reject/ignore: require fresh full re-drill before treating rows 1–3 as evidenced.

### Risks

- A: if bucket retention lifecycle is later found inadequate, "evidenced" overstates durability — mitigation: RC-04 + retention note.
- B: wasted re-drills; evidence chain of custody already verified (sha256, exact row counts).

### Recommendation

**Option A** — Accept. The stale claim's source is local compose scope, not production. Evidence is machine-verified.

### Human Decision

□ Approve

□ Reject

□ Defer

---

## RC-03

### Title

Official Security Score

### Current State

Concurrent "current" scores without supersession: audit baseline **48** · `GA_STATUS` **~65** · APPENDIX lineage **72** · EAB-001 **~70** · EAB-002 **~78** · EAB-003 **~81** · ROW4 "Security **98%**". Operators can shop any score.

### Evidence

- `EAB-2026-08-06-003/SCORECARD.md` — Security **~81** (production no-go cap)
- `00-EXECUTIVE-SUMMARY.md` — audit baseline **48** (historical 2026-07-22)
- `GA_STATUS.md`, `OPS01-ROW4-STATUS.md` §7 (98%), APPENDIX-B (72)

### Options

**Option A** — Publish **EAB-003 ~81** as the single board Security SoT on GA_STATUS; fence 48/72/98% as non-current (historical / non-board).

**Option B** — Keep audit **48** as official and label all newer scores as soft.

**Option C** — No single score; publish the numeric range with labels.

### Risks

- A: ~81 still carries the production no-go cap — cannot be read as "secure enough to launch".
- B: understates verified hardening work (secrets isolated, CSP, RBAC, RLS 71/71).
- C: leaves the shopping problem unresolved (board RC-P0-03).

### Recommendation

**Option A** — Publish **EAB-003 ~81** (board axis, production-no-go-capped) as official; annotate 48 as historical baseline and 98% as a row-level status, not the board Security score.

### Human Decision

□ Approve

□ Reject

□ Defer

---

## RC-04

### Title

RPO / RTO Acceptance + Managed Backup

### Current State

Offsite/WAL/PITR drills pass, but: native Railway `volumeInstancePITRRestore` mutation returned **Not Authorized** (plan/permission gating, `BLOCKED-HUMAN`); RPO/RTO **UNSIGNED**; managed backup schedule / bucket lifecycle retention under review.

### Evidence

- `evidence/ops01-pitr/ops01-row3-pitr-restore.json` (`railway_native_pitr.result = "Not Authorized"`, fallback = pgBackRest restore against same archive)
- `evidence/ops01-offsite/ops01-row1-offsite-restore.json` (retention note)
- `DR-GA-GAPS-CHECKLIST.md` (OPS01-04 OPEN)

### Options

**Option A** — Accept documented RPO/RTO with residual: RPO = managed pgBackRest archive (archived WAL) → restore via drill-proven path; RTO = ~5–10 min measured (259s restore + boot). Note native PITR permission as open follow-up.

**Option B** — Block until native `volumeInstancePITRRestore` is authorized and tested.

**Option C** — Accept drill fallback only; waive native PITR requirement.

### Risks

- A: native PITR untested → recovery depends on the pgBackRest manual path (proven, but not the managed UI).
- B: indefinite blocker; engineering evidence already demonstrates recoverability.
- C: operational risk if bucket lifecycle misconfigured — must pin retention.

### Recommendation

**Option A** — Accept RPO/RTO with documented residual (native PITR authorization as a follow-up ops item, not a launch blocker for drill-proven recoverability).

### Human Decision

□ Approve

□ Reject

□ Defer

---

## RC-05

### Title

Neo4j Production Volume

### Current State

Prod `/health` `graph=connected` (evidence deposited 2026-08-07), but prod `neo4j-prod` has **no attached persistent volume** — graph data is ephemeral; redeploy/restart can lose it. Staging has `neo4j-volume`; prod parity not restored.

### Evidence

- `evidence/ops01-prod-health/prod-health-2026-08-07T1623Z.json` (HTTP 200, `graph=connected`)
- `ROOTCAUSE-NEO4J.md` §3–4 (repair via `deploymentRedeploy`; volume residual P1)
- `STAGING-vs-PRODUCTION-DIFF.md`

### Options

**Option A** — Attach persistent volume to prod `neo4j-prod` (match staging) + data migration; restores parity.

**Option B** — Accept risk: keep ephemeral graph in prod, document data-loss window, restore graph by re-import.

### Risks

- A: volume attach requires a maintenance/prod change; brief graph downtime or re-seed.
- B: graph data loss on any redeploy; acceptable only if graph is re-derivable from DB within RTO.

### Recommendation

**Option A** — Attach a persistent volume (recommended by root-cause action items). If a near-term launch is required, **Option B is acceptable only with written acceptance** that graph is re-importable from the relational DB within RTO.

### Human Decision

□ Approve

□ Reject

□ Defer

---

## RC-06

### Title

Maintenance Window Authorization

### Current State

`PROD-MIGRATION-RISK.md` verdict: **REQUIRES MAINTENANCE WINDOW**. Dress rehearsal (2026-08-07): 15-revision migration measured **~60.6 s total** (a4f7 index build ≈ 20 s); scratch DB fully verified. **Window is PREPARED — NOT EXECUTED.** Project Owner guardrail: do not execute outside a maintenance window; do not execute before soak completes.

### Evidence

- `PRODUCTION-CUTOVER-PACKAGE.md` (T-0 checklist, T-30→T+30 runbook, abort matrix, rollback, sign-off packet)
- `MAINTENANCE-WINDOW-PACKAGE.md` (preconditions, migrate runner, rollback, rehearsal runbook)
- `evidence/ops01-staging/migration-dress-rehearsal.json` (timing: rev1 22.8s, a4f7 19.7s, rest 18.1s)
- `evidence/ops01-staging/prod-index-probe.json` (0/37 indexes exist; companies 141,221/345MB dominant)
- **2026-08-07 addition:** `enterprise-audit-board/history/EAB-2026-08-06-003/OWNER-LOGIN-DEPLOY-PACKAGE-2026-08-07.md` — owner/admin console currently **deployed but unreachable** (owner-login endpoint missing in prod; read-only audit evidence in `PRODUCTION-AUTH-ROLE-AUDIT-2026-08-07.md`). The 3-file owner-login commit is scoped for execution inside this same maintenance window (strict-minimum set: `identity/router.py` + `common/middleware.py` CSRF path + `tenant_lifecycle_guard.py` skip prefix). **Do not bundle EAB-001 security fixups in the same commit.**
- **P0-01 (owner-assigned 2026-08-07, see `RELEASE-GOVERNANCE-DECISION-2026-08-07.md` §1A):** tenant isolation/roles unverified on prod (both accounts share tenant `326e0825`; cross-tenant test INCONCLUSIVE; roles swapped `muhide.com`=user, `ratlfintech.com`=admin). **Must be resolved inside this window** (or explicitly accepted-with-residual by the Project Owner): confirm role intent, decide tenant topology, provision a cross-tenant test account if topology is split, and re-run the cross-tenant isolation test (audit §5 actions 1/2/5). GA blocked until closed.
- **2026-08-08 addition (owner decision):** the window scope is **expanded to deploy frontend HEAD `2538a7d`** (4 commits past prod baseline `4750038`: ADR-102 hardening, UX Phase 1 unified shell + locale fix, Company 360 enrichment, AI Copilot activation). Rationale: closes prod-vs-repo drift and ships locale/UX fixes. **Do not bundle i18n hardcoded-English fixes for pipeline/revenue in the same commit** — those remain a separate post-GA backlog item (owner decision).
- **2026-08-08 addition (owner decision):** honesty banners ("Not Production GO / RAG GO") are **restricted to admin-only rendering** — hidden from end-user pages, still visible to admin/owner console. Implementation is a **P1 window task**, not a GA blocker (banners are intentional transparency, not a bug).

### Options

**Option A** — Authorize the maintenance window **after soak completes clean** (schedule date, window start/end, named operator).

**Option B** — Require another rehearsal / dry run before window.

**Option C** — Defer window indefinitely (stay NO-GO on migrations).

### Risks

- A: concurrent writes during index builds could still contend — mitigate via T-0 write-pause + abort matrix.
- B: extra latency; rehearsal already measured on a byte-identical prod copy.
- C: prod DB stays 11 revisions behind code — divergence risk grows.

### Recommendation

**Option A** — Pre-authorize the window subject to **soak-complete + Project Owner evidence review**; do not execute before then (per Project Owner guardrail).

### Human Decision

□ Approve

□ Reject

□ Defer

---

## RC-07

### Title

Final Production GO

### Current State

BLOCKED by all of the above. Soak ends **2026-08-10T14:10:06Z**; K1 PASS, K2–K6 OPEN; Project Owner acceptance pending; previously signed **NO-GO**.

### Evidence

- `SOAK-GATE-CHECKLIST.md` + `evidence/ops01-staging/loop-*.json` (i00028 as of 2026-08-07)
- `SIGN_HERE.md` (Project Owner NO-GO; acceptance pending)
- Board Consensus — NO-GO

### Options

**Option A** — GO after: soak completes clean → Project Owner review (K2–K6) → RC-01…05 resolved → maintenance window executed (RC-06) → Row 5 acceptance → re-evaluate EAB.

**Option B** — NO-GO until next full EAB re-run after window.

### Risks

- A: GO without board re-certification repeats the governance-integrity failure the reconciliation flagged.
- B: extended NO-GO with prod DB 11 revisions behind — accumulation risk.

### Recommendation

**Option A** — Condition GO on: soak complete + Project Owner acceptance + RC-01…05 approvals + RC-06 window executed + a dated EAB re-evaluation. **Never signed by AI.**

### Human Decision

□ Approve

□ Reject

□ Defer

---

## RC-08

### Title

Enable Owner Console admin — deploy `owner/login` to Production

### Current State

Owner Platform admin routes (`/api/v1/admin/{tenants,users,roles,permissions,plans,feature-flags,audit/logs,health/detailed}`) are **deployed on prod but unreachable**: the owner-audience JWT mint endpoint `POST /api/v1/identity/owner/login` is missing (404 ×3; absent from prod `openapi.json`). Every owner route returns 401 for all callers. Token-minting machinery (`create_owner_*`, `owner_auth.py`, admin router `require_owner_role_dep("admin")`) already exists in deployed baseline `4750038c`. Evidence: read-only audit 2026-08-07.

### Evidence

- `PRODUCTION-AUTH-ROLE-AUDIT-2026-08-07.md` (read-only audit, 38 PASS / 18 FAIL, all fails trace to missing owner-login)
- `evidence/ops01-prod-health/prod-auth-rbac-audit-2026-08-07.json`
- `enterprise-audit-board/history/EAB-2026-08-06-003/OWNER-LOGIN-DEPLOY-PACKAGE-2026-08-07.md` (full execution + rollback package)

### Options

**Option A** — Deploy the strict-minimum 3-file commit (`identity/router.py` + `common/middleware.py` CSRF path + `tenant_lifecycle_guard.py` skip prefix) inside the RC-06 maintenance window. Owner Console becomes usable.

**Option B** — Keep owner routes unreachable (401) until a dedicated UI/console release.

**Option C** — Defer indefinitely (Owner Console stays dormant).

### Risks

- A: needs owner account with `role=admin` + active — current roles **swapped** (`muhide.com`=user, `ratlfintech.com`=admin) — decide owner account first; owner_login is fail-safe (only `role=admin` mints).
- B: admin automation/debugging via Owner Console impossible; UI console stays broken.
- C: divergence persists; no impact on tenant security (routes remain denied).

### Recommendation

**Option A** — Deploy inside RC-06 window, as a **standalone release** (its own commit, own tag), separate from EAB-001 security fixups and any other work. Validate with post-deploy probe matrix.

### Human Decision

**Owner Decision** (project owner is final decision-maker for this deploy)

□ YES — approve owner-login release inside RC-06 window

□ NO — keep owner routes unreachable (401) for now

□ DEFER — revisit after RC-06 window / next review

---

## 4. Required Human Decisions (summary)

| Decision | Owner | Deadline | Impact | Recommendation |
|----------|-------|----------|--------|----------------|
| **RC-01** OPS-01 Rows 1–3 | Project Owner | Before RC-07 / Row 5 | Removes DONE∩OPEN integrity block | A — CLOSE with residuals |
| **RC-02** Accept WAL/PITR evidence | Project Owner | Before RC-01 | Settles stale "archive off" claim | A — Accept |
| **RC-03** Official Security Score | Project Owner (+ EAB) | Before RC-07 | Ends score shopping | A — EAB-003 ~81 |
| **RC-04** RPO/RTO + managed backup | Project Owner | Before RC-07 | Closes OPS01-04 residual | A — Accept w/ residual |
| **RC-05** Neo4j production volume | Project Owner (+ ops) | Before RC-06 window | Prod graph durability | A — persistent volume |
| **RC-06** Maintenance window | Project Owner | After soak (08-10 14:10Z) | Executes 15 migrations + resolves **P0-01** + deploy frontend HEAD `2538a7d` + owner-login + admin-only honesty banners (P1) | A — authorize post-soak |
| **RC-07** Final Production GO | Project Owner + EAB | After all above | Launch decision | A — conditional GO |
| **RC-08** Enable Owner Console admin (`owner/login`) | Project Owner (+ ops) | In RC-06 window | Unlocks deployed-but-unreachable `/api/v1/admin/*` owner routes | A — standalone owner-login release inside window |

**Required Signature:** RC-01…05 — Project Owner. RC-06 — Project Owner + named operator. RC-07 — Project Owner + EAB Chair acknowledgement. RC-08 — Project Owner (final decision-maker), with named operator (same window as RC-06).

---

## 5. Decision Status

| Decision | Status |
|----------|--------|
| RC-01 | OPEN |
| RC-02 | OPEN |
| RC-03 | OPEN |
| RC-04 | OPEN |
| RC-05 | OPEN |
| RC-06 | BLOCKED (until Soak complete) |
| RC-07 | BLOCKED (until RC-01~06 complete) |
| RC-08 | BLOCKED (until Soak complete + RC-06 window) — RC manifest prepared; **commit created at window time from actual repo state** (not pre-staged) |

---

*CTO-REQUIRED-HUMAN-DECISIONS — AUTHORITATIVE DECISION PACK — 2026-08-07 — Project Owner decisions (sole decision-maker; "CTO" = Project Owner). AI recommendations only, no decisions closed.*
