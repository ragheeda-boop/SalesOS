# Authoritative Document Map

**Pack:** Enterprise Reconciliation Audit — 2026-08-07  
**Rule:** For each topic, **ONE** authoritative document (or evidence class). Others are Derived / Deprecated / Historical / Incorrect-as-current.  
**Chair decides** mapping; reviewers proposed candidates only.

Legend: **Authoritative** · **Derived** · **Historical** · **Incorrect-as-current** · **Evidence (facts)** · **UNSIGNED / OPEN gate**

---

## 1. Production GA decision (GO / NO-GO)

| Role | Document |
|------|----------|
| **Authoritative** | `docs/audit/ga-engineering-audit/SIGN_HERE.md` — CTO Decision **NO-GO** (2026-08-06) |
| **Authoritative (board)** | Latest EAB `CEO-SUMMARY.md` / `RUN-REPORT.md` (EAB-2026-08-06-003) — Production GA **NO-GO** |
| Derived | `GA_STATUS.md` decision header (must track SIGN_HERE + latest EAB) |
| Incorrect-as-current | `OPS01-ROW4-STATUS.md` “READY with conditions” / “Verification 100%” / “~96%” as GA posture |
| Historical / superseded | `docs/vnext/reports/GO_NO_GO_DECISION.md`, `GA_CHECKLIST.md` (explicitly superseded) |

---

## 2. Cutover gate CLOSED? (OPS-01 / DR rows 1–5)

| Role | Document |
|------|----------|
| **Authoritative (CLOSED?)** | `docs/ops/DR-GA-GAPS-CHECKLIST.md` + human ink / explicit CLOSE |
| **UNSIGNED / OPEN gate** | `SIGN_HERE.md` Tech Lead block; RPO acceptance |
| Derived (ops narrative) | `OPS-01-ADVANCEMENT.md`, `OPS-01-CHECKLIST.md` — useful but **not** cutover CLOSED until DR checklist updated |
| Incorrect-as-current for CLOSED | `GA_STATUS.md` #7 “DONE” treated as cutover-closed without checklist CLOSE |
| Program disposition | `REMEDIATION-PROGRAM-STATUS.md` — Deferred until reconciled |

---

## 3. Executable DR drill facts (offsite / WAL / PITR)

| Role | Document |
|------|----------|
| **Authoritative (facts)** | `…/EAB-2026-08-06-003/evidence/ops01-offsite/*`, `…/evidence/ops01-pitr/*` — incl. **live** `prod-live-wal-archive-reverify-2026-08-07.json` (`archive_mode=on`, archived **1240**, failed=0, 2026-08-07) |
| Derived narrative | `OPS-01-ADVANCEMENT.md` §§2–3 |
| Historical / local-only | `PROGRESS-WAVE10-BACKUP.md`, Wave10 local WAL drills |
| Incorrect-as-current | DR checklist EAB-003 lines claiming archive **Still off** / offsite **NOT done** *as denial of these JSON facts* |

---

## 4. Staging soak (Row 4) completeness

| Role | Document |
|------|----------|
| **Authoritative (complete?)** | `SOAK-GATE-CHECKLIST.md` K1–K6 + explicit `soak_complete_claim` |
| **Evidence (progress)** | `…/evidence/ops01-staging/loop-*.json`, `gate-*.json` |
| Derived status | `OPS01-ROW4-STATUS.md` (**OPEN** is correct; discard “not started” once soak UTC exists) |
| Incorrect-as-current as cloud soak SoT | `SIGN_HERE.md` **140-loop** local `wave11-soak-48h-rerun` narrative for cloud Row 4 close |
| Historical staging gap snapshot | `STAGING-VERIFICATION.md` / `SOAK-READINESS.md` (2026-08-06) — banner as superseded for parity claims after 2026-08-07 ROW4 |

---

## 5. Staging parity / CI wiring (current)

| Role | Document |
|------|----------|
| **Authoritative (current)** | `STAGING-vs-PRODUCTION-DIFF.md` + dated `OPS01-ROW4-STATUS.md` (2026-08-07) |
| Incorrect-as-current | Unbannered `GA_STATUS.md` #1 “409 commits behind / DEBUG=true / shared JWT” as present tense |
| Historical | `STAGING-VERIFICATION.md` (2026-08-06 pre-parity) |

---

## 6. Security score (current board)

| Role | Document |
|------|----------|
| **Authoritative (board axis)** | `EAB-2026-08-06-003/SCORECARD.md` — Security **~81** (with **production no-go** cap) |
| Historical baseline | `00-EXECUTIVE-SUMMARY.md` / audit **48** — label **historical 2026-07-22** |
| Derived / lagging | `GA_STATUS.md` Security **~65** until explicitly refreshed to EAB-003 |
| Incorrect-as-current | Mixing **48** next to “Verification 100%”; ROW4 “Security **98%**”; orphan APPENDIX “Use **72**” as EAB score |

---

## 7. Production Readiness score (current board)

| Role | Document |
|------|----------|
| **Authoritative** | EAB-003 SCORECARD / RUN-REPORT — PR **~53**, Overall **~54**, **production no-go** |
| Historical | Audit baseline PR **38** |
| Lagging / alternate | `GA_STATUS` Wave24 **~78** (engineering scoreboard — not EAB axis SoT) |
| Incorrect-as-current | ROW4 “Production Readiness ~**96%**” |

---

## 8. Test suite claims

| Role | Document |
|------|----------|
| **Authoritative (EAB Verification Run)** | EAB-003 `EVIDENCE-LOG` / RUN-REPORT — BE **2009/0**, FE **2492/0**, e2e critical **42/42** (dated to that run) |
| Historical signature packet | `SIGN_HERE.md` **1548/0** — fence as older wave evidence unless re-run linked |
| Derived | `GA_STATUS` Testing **~99+** — not a suite census |

---

## 9. Prod Alembic / migration risk

| Role | Document |
|------|----------|
| **Authoritative (current revision)** | `prod-index-probe.json` / restore JSON / `PRODUCTION-VERIFICATION.md` → **`d1a8c35e7f09`** |
| **Authoritative (risk class)** | `PROD-MIGRATION-RISK.md` — **REQUIRES MAINTENANCE WINDOW** |
| **Authoritative (window playbook)** | `PRODUCTION-CUTOVER-PACKAGE.md` — PREPARED, **NOT EXECUTED** |
| Evidence (rehearsal) | `migration-dress-rehearsal.json` |
| Incorrect-as-current | `GA_STATUS` “Alembic **0051**”; `SIGN_HERE` “head **0040**” as live identity |

---

## 10. Neo4j / graph availability

| Role | Document |
|------|----------|
| **Authoritative (current, durable)** | `…/evidence/ops01-prod-health/prod-health-2026-08-07T1623Z.json` + `prod-health-detailed-2026-08-07T1623Z.json` — **post-repair** prod `/health` JSON: HTTP 200, `graph=connected`, uptime 42.84h (captured 2026-08-07T16:23Z) |
| Narrative (secondary) | `ROOTCAUSE-NEO4J.md`, ROW4 "repaired / connected" — now corroborated by durable health JSON above |
| Historical / pre-repair | `PRODUCTION-VERIFICATION.md` OFFLINE (2026-08-06 pre-fix snapshot) — no longer current |
| Policy | OPS01-06 PARTIAL; Neo4j backup policy still OPEN on DR checklist; prod `neo4j-prod` **no persistent volume** (P1 human decision — connected ≠ durable) |

---

## 11. Compose / local stack SoT

| Role | Document |
|------|----------|
| **Authoritative** | `docs/ops/COMPOSE-SOURCE-OF-TRUTH.md` → `salesos/docker-compose.yml` |
| Deprecated for cutover | Root `docker-compose.yml` as production path |

---

## 12. AI marketing / honesty

| Role | Document |
|------|----------|
| **Authoritative** | `docs/audit/ga-engineering-audit/AI_HONESTY.md` |
| Derived | EAB axis 43 / AIGOV Partial dispositions |
| Incorrect-as-current | Any reading of Security/Readiness percentages as AI GA |

---

## 13. Credential / secret isolation (staging)

| Role | Document |
|------|----------|
| **Authoritative (current)** | `SECURITY-SECRETS.md` + dated ROW4 (2026-08-07 isolation claims) |
| Historical failure state | `PRODUCTION-VERIFICATION` / GA_STATUS shared JWT/SECRET (2026-08-06) — must be bannered Historical |
| OPEN residuals | Credential rotation items still listed on GA_STATUS / SIGN_HERE notes |

---

## 14. Release / ops backlog tracking

| Role | Document |
|------|----------|
| **Authoritative for backlog state** | `RELEASE-BACKLOG-2026-08-06.md` (as backlog, not scoreboard) |
| Must reconcile against | OPS-01 evidence + DR checklist — currently conflicts on Backup DR PARTIAL vs DONE |

---

## 15. Production auth & RBAC posture (2026-08-07)

| Role | Document |
|------|----------|
| **Authoritative (current)** | [`docs/audit/ga-engineering-audit/PRODUCTION-AUTH-ROLE-AUDIT-2026-08-07.md`](../../PRODUCTION-AUTH-ROLE-AUDIT-2026-08-07.md) + `EAB-2026-08-06-003/evidence/ops01-prod-health/prod-auth-rbac-audit-2026-08-07.json` |
| Status | AuthN PASS · tenant-admin RBAC PASS · Owner Platform admin unreachable (owner-login not deployed) · roles swapped vs operator assumption · both accounts same tenant |
| OPEN action items | Confirm roles/tenants · deploy owner-login (Row 5 / maintenance window) · re-run cross-tenant isolation with a second tenant |
| Not security regression | All owner routes denied 401/404 — functional deployment gap only |

---

## 16. Owner Console enablement plan (2026-08-07)

| Role | Document |
|------|----------|
| **Authoritative (plan)** | `EAB-2026-08-06-003/OWNER-LOGIN-DEPLOY-PACKAGE-2026-08-07.md` — scoped 3-file commit for RC-06 window |
| **Evidence (facts)** | `PRODUCTION-AUTH-ROLE-AUDIT-2026-08-07.md` + `evidence/ops01-prod-health/prod-auth-rbac-audit-2026-08-07.json` |
| **Decision gate** | RC-08 in `CTO-REQUIRED-HUMAN-DECISIONS.md` — BLOCKED until soak complete + RC-06 window |
| Status | Owner routes deployed-but-unreachable (401 all) — functional gap, no security bypass; NOT executed |

---

## 17. Release governance decision + archive (2026-08-07)

| Role | Document |
|------|----------|
| **Authoritative** | `RELEASE-GOVERNANCE-DECISION-2026-08-07.md` — Engineering **CLOSED** / Release **ACTIVE** / Change Freeze until 2026-08-10T14:10Z |
| **Authoritative (decisions)** | `CTO-REQUIRED-HUMAN-DECISIONS.md` — RC-01…08; "CTO" = **Project Owner** (sole decision-maker) |
| **Archive (immutable)** | `docs/releases/v1.0.0-ga/` — frozen Release Record; populated at GA; never mutated after deposit |
| **Terminology rule** | CTO/Tech Lead references in current operational docs → **Project Owner Decision / Acceptance** (single-owner reality); historical `history/EAB-*` archives keep original labels |

---

## 18. Addendum — Completion Program + human GO (2026-08-08)

| Role | Document |
|------|----------|
| **Authoritative (human Decision ink)** | `SIGN_HERE.md` — CTO+TL **SIGNED GO** 2026-08-08 (رغيد المدني; dual-role P1). Prior NO-GO 2026-08-06 **preserved** with supersession. |
| **Honesty companion** | `reconciliation-2026-08-07/HUMAN-GO-DECLARATION-2026-08-08.md` — human-declared GO ≠ evidence-based readiness |
| **Authoritative (board engineering posture)** | EAB-003 CEO/RUN — still **production no-go** / residual until soak etc. — ink does not rewrite evidence |
| **Authoritative (cutover CLOSED?)** | `docs/ops/DR-GA-GAPS-CHECKLIST.md` — rows 1–3 **OPEN** for CLOSE; facts **DONE\*** (see §3) |
| **Living program** | `docs/audit/ga-engineering-audit/COMPLETION-PROGRAM.md` + `completion/PROGRAM-BOARD.md` |
| **Human actions** | `completion/HUMAN-GATE-CARD.md` |
| **Label alignment (RC-P0-01…03)** | `completion/GOVERNANCE-LABEL-ALIGNMENT.md` |

**Rule:** Do not shop human GO as evidence-based Production GO. Do not deny DONE\* drill JSON. Do not CLOSE cutover without human ink.

---

*Chair synthesis — AUTHORITATIVE-DOCUMENT-MAP — reconciliation-2026-08-07 · Completion addendum 2026-08-08*
