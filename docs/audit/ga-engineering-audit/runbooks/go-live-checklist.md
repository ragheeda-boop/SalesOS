# Go-Live Checklist (Waves 13–14 — PREPARE FOR HUMAN SIGNATURE)

**ID:** PROD-W13-001 / PROD-W14-001 (prep)  
**Status:** PREPARE ONLY — **no Production GO** and **no cutover executed**  
**Authority for current status:** [../GA_STATUS.md](../GA_STATUS.md) + [../00-EXECUTIVE-SUMMARY.md](../00-EXECUTIVE-SUMMARY.md) — **production no-go**  
**Program:** [../PRODUCTION_PLAN.md](../PRODUCTION_PLAN.md)  
**Ops spine (Sprint-26 prep):** [GO_LIVE_RUNBOOK.md](../../../ops/GO_LIVE_RUNBOOK.md) — **draft landed** (not executed / UNSIGNED)  
**Human-review summary:** [../PROGRESS-WAVE14-GO-LIVE.md](../PROGRESS-WAVE14-GO-LIVE.md)

> Complete every box with evidence links (CI run URL, screenshot, report path).  
> Blank or unchecked = not ready. Do not “ink” a GO from this template alone.  
> **Signatures below are UNSIGNED.** Do not forge names or dates as approved.

**Refreshed:** 2026-07-22 (local evidence Waves 0–13; short soak + **4h soak IN PROGRESS**; 48h plan ready / not started; local tabletop + gates/UI smoke; signatures still **UNSIGNED**).

**One-page sign pack:** [../SIGN_HERE.md](../SIGN_HERE.md) — **UNSIGNED**.

---

## Current evidence snapshot (2026-07-22)

| Item | Status | Evidence |
|------|--------|----------|
| FE rebuild (`/dashboard` in image) | **DONE** (local) | Image `salesos-frontend:local` `sha256:84ef1507c89e…` — [PROGRESS-WAVE13-UI-SMOKE.md](../PROGRESS-WAVE13-UI-SMOKE.md) |
| Playwright UI smoke | **PASS** (light) | [PROGRESS-WAVE13-UI-SMOKE.md](../PROGRESS-WAVE13-UI-SMOKE.md) — login, `/companies`, `/decisions`, `/copilot`, `/dashboard` HTTP 200 |
| Auth API smoke | **PASS** (13/13 local) | [PROGRESS-WAVE13-AUTH-SMOKE.md](../PROGRESS-WAVE13-AUTH-SMOKE.md) |
| Pre-deploy gates | **PASS** (local) | [PROGRESS-WAVE12-GATES.md](../PROGRESS-WAVE12-GATES.md) — alembic head **`0040`**, `/health` ok, `SALESOS_TESTING` unset; prior log `evidence/wave12-gates/gate-rerun-2026-07-22T1307Z.log` (0039-era) |
| Short soak (~0.2h / 5 iters) | **DONE** (not 48h) | [PROGRESS-WAVE11-SOAK.md](../PROGRESS-WAVE11-SOAK.md) + `evidence/wave11-soak/` (`soak_complete_claim=false`) |
| Extended local soak (4.0h) | **IN PROGRESS** (not 48h) | [PROGRESS-WAVE11-SOAK.md](../PROGRESS-WAVE11-SOAK.md) — PID 14884; iter 26 @ 12:38Z; ~20 PASS / 6 FAIL mid-run; do not kill |
| 48h local soak | **NOT started** | Plan + commands: [PROGRESS-WAVE11-SOAK-48H.md](../PROGRESS-WAVE11-SOAK-48H.md) → evidence dir `evidence/wave11-soak-48h/` (start after 4h ends) |
| Extended soak (48–72h + cloud) | **OPEN** | Cloud staging **UNVERIFIED**; `soak_complete_claim=false` |
| Local deploy/rollback tabletop | **DONE** | [PROGRESS-WAVE12-TABLETOP.md](../PROGRESS-WAVE12-TABLETOP.md) + `evidence/wave12-tabletop/` |
| Staging/cloud tabletop | **OPEN** / prep | Probe [PROGRESS-WAVE12-STAGING.md](../PROGRESS-WAVE12-STAGING.md); unblock [PROGRESS-WAVE12-STAGING-UNBLOCK.md](../PROGRESS-WAVE12-STAGING-UNBLOCK.md) |
| Local backup/restore drill | **DONE** | [PROGRESS-WAVE10-BACKUP.md](../PROGRESS-WAVE10-BACKUP.md) — pg_dump → `salesos_restore_drill` |
| WAL/PITR / offsite / Neo4j dump | **OPEN** | [PROGRESS-WAVE10-DR-GAPS.md](../PROGRESS-WAVE10-DR-GAPS.md) |
| CTO + Tech Lead signatures | **UNSIGNED** | [../SIGN_HERE.md](../SIGN_HERE.md) + signature blocks below |

**Still blocks Production GO:** see [GA_STATUS.md](../GA_STATUS.md) § Remaining NO-GO blockers and Wave 14 summary.

---

## Evidence map (Waves 0–14 prep vs still open)

| Wave / item | Progress / runbook | Prep | Cutover / ops proof |
|-------------|-------------------|------|---------------------|
| 0 FE lint/tsc/build | [PROGRESS-WAVE0-FE.md](../PROGRESS-WAVE0-FE.md) | **DONE** | CI/Linux standalone caveat **OPEN** |
| 1 Alembic local head | [PROGRESS-WAVE1-3-5-PLATFORM.md](../PROGRESS-WAVE1-3-5-PLATFORM.md), [PROGRESS-WAVE12-PROD-MIGRATE-PREP.md](../PROGRESS-WAVE12-PROD-MIGRATE-PREP.md) | **DONE** (local **0040**) | Staging/prod migrate **EXECUTION BLOCKED** (must include 0040) |
| 2 Security P0 code | [PROGRESS-WAVE2-SEC.md](../PROGRESS-WAVE2-SEC.md) | **DONE** (light) | Soak / residual SSRF/KG review **OPEN** |
| 3 Unit tests | [PROGRESS-CONTINUATION.md](../PROGRESS-CONTINUATION.md) | **DONE** (~1542 passed local) | Coverage gate / full e2e **OPEN** |
| 4 FE image routes | [PROGRESS-WAVE4-FE-IMAGE.md](../PROGRESS-WAVE4-FE-IMAGE.md), Wave 13 FE rebuild | **DONE** (`/copilot` `/analytics` `/dashboard` 200) | Auth UI deep e2e **OPEN** |
| 4/8/9 Infra/obs/secrets | [PROGRESS-WAVE4-8-9-INFRA.md](../PROGRESS-WAVE4-8-9-INFRA.md) | **DONE** (config) | Live matrix **OPEN** |
| 5 Auth probes | Wave 1/3/5 progress | **DONE** (local) | Prod soak **OPEN** |
| 6–7 Docs / AI honesty | [PROGRESS-WAVE6-7-DOCS.md](../PROGRESS-WAVE6-7-DOCS.md), [AI_HONESTY.md](../AI_HONESTY.md) | **DONE** | — |
| 10 Backup drill | [PROGRESS-WAVE10-BACKUP.md](../PROGRESS-WAVE10-BACKUP.md), [backup-restore-drill.md](./backup-restore-drill.md) | **DONE** (local pg_dump) | WAL/PITR / S3 / Neo4j **OPEN** |
| 11 Staging soak | [PROGRESS-WAVE11-SOAK.md](../PROGRESS-WAVE11-SOAK.md), [PROGRESS-WAVE11-SOAK-48H.md](../PROGRESS-WAVE11-SOAK-48H.md), [staging-soak.md](./staging-soak.md) | Gate + short **DONE**; **4h IN PROGRESS**; 48h plan ready | **48–72h + cloud staging OPEN** |
| 12 Deploy gates | [PROGRESS-WAVE12-GATES.md](../PROGRESS-WAVE12-GATES.md), [deploy-rollback.md](./deploy-rollback.md) | Script **PASS** local | Prod deploy **OPEN** |
| 12 Local tabletop | [PROGRESS-WAVE12-TABLETOP.md](../PROGRESS-WAVE12-TABLETOP.md) | **DONE** (compose) | Staging tabletop **OPEN** |
| 12 Backend image | [PROGRESS-WAVE12-IMAGE.md](../PROGRESS-WAVE12-IMAGE.md) | **DONE** (`jsonschema` 4.26.0) | — |
| 13 Auth / UI smoke | [PROGRESS-WAVE13-AUTH-SMOKE.md](../PROGRESS-WAVE13-AUTH-SMOKE.md), [PROGRESS-WAVE13-UI-SMOKE.md](../PROGRESS-WAVE13-UI-SMOKE.md) | API+UI **PASS** (light) | CTO/TL signatures **UNSIGNED** |
| 14 Hypercare / GO review | [PROGRESS-WAVE14-GO-LIVE.md](../PROGRESS-WAVE14-GO-LIVE.md), [hypercare-14d.md](./hypercare-14d.md) | Forms **PREPARE** | Hypercare **OPEN** (post-GO only) |
| Scoreboard | [GA_STATUS.md](../GA_STATUS.md) | **NO-GO** | — |

**Pre-deploy automation:** `salesos/scripts/pre-deploy-gates.ps1` (alembic drift, `/health`, `SALESOS_TESTING` trap; optional `-RunUnitTests`).

---

## Scope reminder

- **In scope:** SalesOS Production GA candidate  
- **Out of scope:** AQLIYA multi-product GA; marketing AI as production-ready while flags/stubs say otherwise ([AI_HONESTY.md](../AI_HONESTY.md))

---

## T-7 (calendar week before)

| # | Item | Owner | Evidence | Done |
|---|------|-------|----------|------|
| 1 | All PRODUCTION_PLAN P0 items closed | TL | [APPENDIX-C](../APPENDIX-C-FINDINGS-REGISTER.md) + [GA_STATUS.md](../GA_STATUS.md) blockers + CI | ☑ security P0/P1 (8/8, 10/10 closed); ☐ PRODUCTION_PLAN P0 (blockers remain) |
| 2 | Feature freeze for non-GA work | Product | Change log freeze note | ☐ |
| 3 | Dependency / security scans re-run (Wave 9) | Security | Scan report; config prep in [PROGRESS-WAVE4-8-9-INFRA.md](../PROGRESS-WAVE4-8-9-INFRA.md) | ☑ pip-audit (python-multipart upgraded); npm audit (next.js — deferred) |
| 4 | Backup/restore drill report filed (Wave 10) | DevOps | [PROGRESS-WAVE10-BACKUP.md](../PROGRESS-WAVE10-BACKUP.md) (local **DONE**); WAL/offsite still **OPEN** per [PROGRESS-WAVE10-DR-GAPS.md](../PROGRESS-WAVE10-DR-GAPS.md) | ☑ local / ☐ DR gaps |
| 5 | RPO acceptance (24h vs WAL) signed | CTO | PRC note — [PROGRESS-WAVE10-DR-GAPS.md](../PROGRESS-WAVE10-DR-GAPS.md) | ☐ **UNSIGNED** |
| 6 | AI honesty reviewed; no “AI-native GA” in launch notes | Product | [AI_HONESTY.md](../AI_HONESTY.md) + release draft | ☑ prep (feature_ai_copilot=False; stubs labeled) / ☐ launch notes |
| 7 | Stakeholder awareness: SalesOS-only scope | CTO | Email/meeting note | ☐ |
| 8 | Prior GO docs confirmed SUPERSEDED | Docs | Wave 7 banners; [PROGRESS-WAVE6-7-DOCS.md](../PROGRESS-WAVE6-7-DOCS.md) | ☑ **DONE** (docs + AGENTS.md present) |

---

## T-3

| # | Item | Owner | Evidence | Done |
|---|------|-------|----------|------|
| 1 | Release candidate images on staging | DevOps | Digests | ☐ **OPEN** (local images only) |
| 2 | Soak in progress (≥24h already) | DevOps | [PROGRESS-WAVE11-SOAK.md](../PROGRESS-WAVE11-SOAK.md) — short ~0.2h + **4h in progress**; 48h plan [PROGRESS-WAVE11-SOAK-48H.md](../PROGRESS-WAVE11-SOAK-48H.md); 48–72h **OPEN** | ☐ **OPEN** |
| 3 | Feature flags reviewed (`feature_ai_copilot=False`) | Backend | Soak gate PASS flags; [AI_HONESTY.md](../AI_HONESTY.md) | ☑ local (feature_ai_copilot=False; stubs labeled) / ☐ staging env dump |
| 4 | Alembic staging `current == heads` | Backend | Local gates expect **`0040`**; staging ☐ — [PROGRESS-WAVE12-GATES.md](../PROGRESS-WAVE12-GATES.md), [PROGRESS-WAVE12-PROD-MIGRATE-PREP.md](../PROGRESS-WAVE12-PROD-MIGRATE-PREP.md) | ☐ staging **OPEN** |
| 5 | Smoke GA routes 200 on staging (Wave 4 + 13 list) | FE/DevOps | Local FE: [PROGRESS-WAVE4-FE-IMAGE.md](../PROGRESS-WAVE4-FE-IMAGE.md) + [PROGRESS-WAVE13-UI-SMOKE.md](../PROGRESS-WAVE13-UI-SMOKE.md) (`84ef1507`); staging ☐ | ☐ staging **OPEN** |

---

## T-1

| # | Item | Owner | Evidence | Done |
|---|------|-------|----------|------|
| 1 | Code freeze (hotfix-only) | TL | Branch protection | ☑ local verification (FE lint 0 errors; tsc 0 errors; build 74 routes; BE 1548 passed; alembic head 0040; DB schema verified) |
| 2 | Production backup taken (if data exists) | DevOps | Backup object id | ☐ |
| 3 | Final Go/No-Go review vs PRODUCTION_PLAN §16 | CTO + TL | Meeting notes + [GA_STATUS.md](../GA_STATUS.md) | ☐ **current: NO-GO** |
| 4 | On-call primary + secondary named | DevOps | Roster | ☐ |
| 5 | Rollback tabletop completed | DevOps | Local: [PROGRESS-WAVE12-TABLETOP.md](../PROGRESS-WAVE12-TABLETOP.md) **DONE**; staging ☐ **OPEN** | ☑ local / ☐ staging |
| 6 | Comms draft (internal) ready | Product | Doc link | ☐ |
| 7 | Secrets checklist (Wave 9) complete | Security | Checklist; prep in Wave 4/8/9 progress | ☐ |

---

## T-0 (launch day)

| # | Item | Owner | Evidence | Done |
|---|------|-------|----------|------|
| 1 | **Human GO signature** (CTO + Tech Lead) | CTO/TL | Signed blocks below — currently **UNSIGNED** | ☐ |
| 2 | `pre-deploy-gates.ps1` green + `alembic upgrade head` then verify `current` | DevOps | Local gates **PASS**; prod migrate **FORBIDDEN** while NO-GO | ☐ prod |
| 3 | Deploy images via `deploy-production.yml` | DevOps | Actions run URL | ☐ **do not run while NO-GO** |
| 4 | Automated smoke green | DevOps | Workflow job | ☐ |
| 5 | Manual smoke: login, company list, opportunity critical path | QA/TL | Local light: Wave 13; prod ☐ | ☐ |
| 6 | Gradual traffic / DNS as planned | DevOps | Change ticket | ☐ |
| 7 | Intensified monitoring first 60 minutes | On-call | Dashboard link | ☐ |
| 8 | Rollback authority online | On-call | Ack in Slack | ☐ |

**If any P0 appears → automatic NO-GO / rollback.**

---

## T+1

| # | Item | Owner | Evidence | Done |
|---|------|-------|----------|------|
| 1 | Incident review (any S1/S2) | On-call | IR notes | ☐ |
| 2 | Continue vs rollback decision | CTO | Written | ☐ |
| 3 | Hypercare window officially starts | DevOps | [hypercare-14d.md](./hypercare-14d.md) | ☐ |
| 4 | Customer/partner comms (if any) | Product | Sent | ☐ |

---

## Sign-off blocks — **UNSIGNED** (humans only)

> Leave blank until a real Go/No-Go meeting with evidence review.  
> **Agents must not fill names, dates, or Decision=GO.**  
> Scoreboard remains **NO-GO** until humans explicitly change it: [GA_STATUS.md](../GA_STATUS.md).  
> Shortcut one-pager (same blanks): [../SIGN_HERE.md](../SIGN_HERE.md).  
> Open blockers listed truthfully on SIGN_HERE + GA_STATUS (soak 48–72h, staging cloud, DR/RPO, security residuals, AI honesty).

### CTO — **UNSIGNED**

```
Status:     UNSIGNED
Name:       _______________________________
Title:      CTO
Date:       __________ (YYYY-MM-DD)
Decision:   [ ] GO    [ ] NO-GO    [ ] CONDITIONAL (list conditions)
Conditions / notes:
_________________________________________________________________
_________________________________________________________________
Signature / ack: _______________________________________________
```

### Tech Lead — **UNSIGNED**

```
Status:     UNSIGNED
Name:       _______________________________
Title:      Tech Lead
Date:       __________ (YYYY-MM-DD)
Decision:   [ ] GO    [ ] NO-GO    [ ] CONDITIONAL (list conditions)
Confirms evidence reviewed (gates, soak, backup, smoke): [ ] Yes  [ ] No
Conditions / notes:
_________________________________________________________________
_________________________________________________________________
Signature / ack: _______________________________________________
```

### DevOps (optional witness) — **UNSIGNED**

```
Status:     UNSIGNED
Name:       _______________________________
Date:       __________
Ack rollback authority + on-call roster ready: [ ] Yes  [ ] No
Signature / ack: _______________________________________________
```

### Security (optional witness) — **UNSIGNED**

```
Status:     UNSIGNED
Name:       _______________________________
Date:       __________
Ack Wave 9 scans + residual SSRF/KG policy reviewed: [ ] Yes  [ ] No
Signature / ack: _______________________________________________
```

**Current documentation pass: forms prepared only. No signatures. No Production GO. Scoreboard: [GA_STATUS.md](../GA_STATUS.md).**
