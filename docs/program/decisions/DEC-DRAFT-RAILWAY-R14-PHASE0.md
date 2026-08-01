# DEC-DRAFT — Railway R-14 / Phase 0 Exit Gate

> **Status:** **SUPERSEDED** by [`DEC-016-RAILWAY-R14-OPTION-A.md`](DEC-016-RAILWAY-R14-OPTION-A.md)  
> **Date:** 2026-08-01 (draft); Accepted Option A executed 2026-08-01  
> **Board:** Architecture Review Board + Risk Manager (SalesOS / AQLIYA program)  
> **Stop condition:** Cleared — S04-04 **CLOSED** under DEC-016 (Railway staging + production §14 + bypass-probe + health evidence).  
> **Authority chain:** `RISK_REGISTER.md` R-14 → DEC-013 / DEC-014 / DEC-015 → DEC-008 → this package → human accept Option A → **DEC-016**.

---

## 1. Decision required

Human owners must choose how the program treats the **sole remaining open R-14 environment** — Railway managed Postgres — relative to the **Phase 0 Go/No-Go** gate.

| Fact | Evidence |
|---|---|
| R-14: app DB role is superuser / BYPASSRLS → RLS is a no-op under that role | Confirmed; score **25** (L5×I5); highest in register |
| Local / CI / Staging / self-hosted Production Template | Remediated + bypass-probe verified (DEC-014, DEC-015) |
| Railway | **Untouched by explicit prior choice** — no live connect, no `railway.json` edit (DEC-015) |
| Live Railway role shape | Diverges from templates (`postgres` vs `salesos`); unresolved without authorized live check |
| Remediation runbook | Exists, unexecuted: `OPERATIONS_MANUAL.md` §14 |
| Phase 0 rule | DEC-008: security / tenant isolation is **non-skippable, zero partial credit** |
| Stop item | S04-04 BLOCKED; Phase 0 exit **cannot GO** until this package is resolved |

**Out of scope for this package:** executing Railway provisioning, editing `railway.json`, connecting live, rotating secrets, or claiming GO/NO-GO without human accept.

---

## 2. Options

### Option A — Authorize Railway remediation now

Authorize DevOps-SRE / Chief Architect (or named production owner) to execute `OPERATIONS_MANUAL.md` §14 against Railway (staging first if dual-env, then production as separately named):

1. Live connect with owner/migration role.  
2. Idempotent provision of `salesos_app` (`NOSUPERUSER NOBYPASSRLS …`) + grants / default privileges (adapt `02-app-role.sql` for managed Postgres; no compose init mount).  
3. Set `APP_POSTGRES_USER` / `APP_POSTGRES_PASSWORD` via Railway secrets.  
4. Redeploy / reconnect request path through `app_database_url`.  
5. Re-run bypass-probe; require isolate-under-`salesos_app` / leak-under-owner.  
6. Record evidence; close S04-04; update R-14 Status toward full close for Railway.

**Does not authorize:** blind `railway.json` edits without a verification deploy; use of saved credential files without this explicit go-ahead.

### Option B — Formally accept Phase 0 exit without Railway coverage (residual risk)

Declare Phase 0 **GO** with Railway R-14 **open**, documenting residual risk: live managed Postgres may still serve as a BYPASSRLS (or equivalent privileged) role, so RLS on Railway provides no enforceable isolation until remediated later.

Requires **explicit supersession or carve-out of DEC-008** for the Railway environment (zero-partial-credit cannot silently mean “all environments except the live one”).

### Option C — Defer Phase 0 GO indefinitely; continue local / CI / non-Railway work

Keep Phase 0 exit **NO-GO / deferred**. Do not authorize Railway changes. Continue Sprint 03 remainder and approved parallel local/CI work. S04-04 stays BLOCKED. R-14 stays **PARTIALLY CLOSED** (Railway OPEN). No false GO claim.

This was the **operating posture** until human accepted Option A.

---

## 3. Pros / cons and R-14 score impact

Historical register score for R-14 remains **25** (confirmed fact at discovery). Status — not retroactive score softening — reflects environment coverage. Below: **effective residual** for the Railway slice and Phase 0 gate honesty.

| | Option A | Option B | Option C |
|---|---|---|---|
| **Pros** | Closes last R-14 gap; enables honest Phase 0 GO under DEC-008; aligns live prod with remediated shapes; uses existing runbook | Unblocks calendar / Phase 1 labeling without waiting on ops; engineering velocity preserved | Honest NO-GO; no live-prod risk from unauthorized ops; preserves DEC-008; parallel eng continues |
| **Cons** | Requires human auth + live change window; short outage/misconfig risk; needs probe evidence before close | **Conflicts with DEC-008** unless formally carved; false sense of security on live target; audit/GO claim fragile | Phase 0 / M1 date slips; Sprint 04 Phase-1 stories remain under governance tension; S04-04 stays blocked |
| **R-14 residual (Railway)** | → **Closed** if probe passes (target effective residual **0** for Railway) | → **Accepted residual** — treat as Open/Accepted-Risk; **score 25 retained** as record; gate falsely green | → **Unchanged** — PARTIALLY CLOSED; Railway OPEN; score **25** retained; gate correctly blocked |
| **Phase 0 exit** | Eligible for GO after evidence | GO only if DEC-008 superseded/carved | **Cannot GO** (correct) |

**Risk Manager note:** Option B does not reduce likelihood or impact of R-14 on Railway; it only relabels the gate. That is residual-risk **acceptance**, not mitigation.

---

## 4. Explicit recommendation

### Recommend: **Option A**

**Rationale (ARB + Risk):**

1. **DEC-008 is Accepted** — Phase 0 is zero partial credit. Railway is the documented live production target (`railway.json` / deploy history). Exiting Phase 0 while that target remains BYPASSRLS-class is the failure mode DEC-013 named: “correct-looking policies that silently do nothing.”  
2. **Mitigation is ready** — local/CI/staging/prod-template already prove the pattern; only authorization + live execution remain (DEC-015 deferred deliberately, not for lack of a plan).  
3. **Option B is architecturally incoherent** without a new Accepted decision that supersedes or carves DEC-008. ARB does not recommend that carve-out while Railway remains the live path.  
4. **Option C is the correct interim** if A cannot be authorized in this session — but it is a **hold**, not a GO path.

**If A is refused or delayed:** operate under **Option C** (not B). Do not mark Phase 0 GO. Do not close S04-04. Do not soften R-14.

**Acceptance of A should mint:** DEC-016 (Authorize Railway R-14 remediation per §14) with named owner, environment order (e.g. Railway staging → Railway production), and evidence bar (bypass-probe + role flags).

---

## 5. What engineering MAY continue in parallel

Applies until human accept of A or B. Default = **Option C parallel rules**.

### Shared tension: D-S4-002 vs DEC-008

| Decision | Stance |
|---|---|
| **DEC-008** | Phase 1 does **not** start until Phase 0 RLS/security exit is met — no partial credit |
| **D-S4-002** | Sprint 04 feature stories may proceed **in parallel with CI remediation**; CI is not yet a reliable merge gate |

**ARB reading:** D-S4-002 authorizes parallel **CI debt work** and limited Sprint 04 **local/dev** feature scaffolding; it does **not** authorize claiming Phase 0 GO, nor shipping Phase 1 tenant-adjacent tables to an unremediated Railway as “production-ready.” New commercial tables (`subscriptions`, `usage_meters`, provisioning status fields) inherit the same isolation class DEC-008 was written to protect.

### Under Option A (once authorized)

| May continue | Must wait / constrain |
|---|---|
| Execute §14 on Railway (authorized owners only) | Phase 0 GO until probe evidence lands |
| Sprint 03 remainder on non-Railway shapes (STORY-02-01 completion evidence, middleware/JWT/contract work already in flight) | Closing R-14 / S04-04 before probe |
| CI remediation stories (CI-08, CI-09, registered backlog) per D-S4-002 | Blind `railway.json` changes without verification deploy |
| Sprint 04 **design / local migrations / tests** against remediated local/CI DB | Treating Railway deploy as Phase 0 exit proof before A completes |

### Under Option B (only if formally Accepted + DEC-008 carve-out)

| May continue | Must document |
|---|---|
| Label Phase 0 GO with **explicit residual**: Railway R-14 Open/Accepted | Superseding/carving DEC-008 entry in `DECISION_LOG.md` |
| Sprint 04 Phase 1 features under D-S4-002 | Residual risk owner, review date, ban on “RLS proven in production” marketing |
| CI / local hardening | That adversarial suite green ≠ Railway isolation |

**ARB does not recommend B.** If chosen, treat as Program Director + Chief Architect joint gate exception under `RISK_REGISTER.md` Escalation Rule (score ≥15).

### Under Option C (recommended interim if A not yet authorized — **current stop**)

| May continue | Must not |
|---|---|
| **Sprint 03 remaining** non-Railway: finish/verify STORY-02-01 on local/CI/staging/prod-template; STORY-02-02 / 02-03 / 02-04 / 03-04 as scheduled | Claim Phase 0 GO or M1 “Foundation Secure” |
| **CI / pipeline / security gates** (blocked ops items CI-08/CI-09 remain ops-blocked) | Execute Railway R-14 / edit live Railway secrets |
| **Sprint 04 features under D-S4-002 tension:** local implementation + tests for STORY-04-01 / 04-02 / JWT consume **only** against remediated environments; no production GO narrative | Add tenant-adjacent commercial tables to Railway as “GA path” while R-14 Railway OPEN |
| Adversarial suite expansion (S04-05 / S04-06) on local/CI | Close S04-04 or R-14 without A |

**Stop preserved:** S04-04 BLOCKED; Phase 0 exit **NO-GO** until A completes or B is formally Accepted.

---

## 6. Decision record (human fill-in)

| Field | Value |
|---|---|
| Chosen option | ☑ **A**  ☐ B  ☐ C |
| Authorizing role(s) | Program Director / Ops — Arabic standing approval (Option A) |
| Date | 2026-08-01 |
| If A: environments + order | Railway staging → Railway production (env/role only; no app image promote) |
| If B: DEC-008 carve-out ID | n/a |
| Follow-on DEC ID when Accepted | **DEC-016** |
| Evidence pointer (post-A) | [`DEC-016-RAILWAY-R14-OPTION-A.md`](DEC-016-RAILWAY-R14-OPTION-A.md) |

---

## 7. Immediate program effects (post-Acceptance)

- `SPRINT_05_DELIVERY_BOARD.md` — S04-04 **CLOSED** (DEC-016).  
- `RISK_REGISTER.md` R-14 — Railway **Closed** (full environment coverage).  
- This file — **SUPERSEDED** by DEC-016.

**Validation status:** Option A **executed** via Railway CLI; bypass-probe + health evidence recorded in DEC-016 (secrets redacted).
