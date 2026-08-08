# Document Contradictions — Board Chair Register

**Pack:** Enterprise Reconciliation Audit — 2026-08-07  
**Mode:** READ ONLY synthesis of seven independent reviewers  
**Rule:** Evidence wins. Single-document claims are not authority.  
**Sources:** `reviewers/R1`…`R7` + direct re-read of cited paths. No existing governance rewritten.

---

## How this register was built

1. Collect contradictions from R1–R7.  
2. Merge duplicates that describe the **same Claim A vs Claim B**.  
3. Resolve reviewer severity disagreements (Chair ruling in notes).  
4. Drop non-contradictions (e.g., Production **NO-GO** agreement is a **Verified Truth**, not a contradiction).

**Reviewer raw totals (pre-dedupe):** R1 12 · R2 11 · R3 13 · R4 13 · R5 13 · R6 12 · R7 14  

**Board unique contradictions after merge:** **22** (P0: **4** · P1: **9** · P2: **6** · P3: **3**)

---

## P0 — Critical (cutover / integrity blockers)

| ID | Claim A | Claim B | Reviewers | Chair note |
|----|---------|---------|-----------|------------|
| **RC-P0-01** | `GA_STATUS.md` #7: offsite + WAL + PITR **DONE 2026-08-06**; `OPS-01-CHECKLIST` / `OPS-01-ADVANCEMENT`: OPS01-01…03 **DONE\*** with evidence JSON | `DR-GA-GAPS-CHECKLIST.md`: rows 1–3 **OPEN**; EAB-003 block “**NOT done** — do not claim”; `SIGN_HERE.md` #7 offsite/WAL/PITR **OPEN**; EAB CEO/RUN/PROGRAM/FINDINGS-RECHECK: OPS-01 / rows 1–5 still open / Deferred | R1–R7 | **CRITICAL CONTRADICTION** (special check). Gate CLOSED? vs statusboard DONE cannot both be current. |
| **RC-P0-02** | Same DR checklist EAB-003 block: primary `archive_mode` **Still off**; offsite **NOT done** | Linked OPS-01 pack + `ops01-row2-wal-archiver.json` / `ops01-row1-offsite-restore.json`: prod WAL on + offsite restore SHA-verified | R1–R3, R6–R7 | Gate document **self-inconsistent** with its own linked evidence tree. |
| **RC-P0-03** | Concurrent “current” Security scores: audit baseline **48**; `GA_STATUS` **~65**; APPENDIX/Principal lineage **72**; EAB-001 **~70**; EAB-002 **~78**; EAB-003 **~81**; ROW4 “Security **98%**” | No board-mandated supersession recorded onto `GA_STATUS` / SIGN_HERE | R1, R4–R5, R7 (R4=P0) | Chair **elevates to P0**: operators can shop any score. Same-run EAB-003 cites both **~81** and **48**. |
| **RC-P0-04** | DR row text / cutover expectation: **automated** offsite + retention; managed/native PITR path | OPS **DONE\*** with schedule / `volumeInstancePITRRestore` **BLOCKED-HUMAN** and empty human `signed_off_by` | R3 (P0), R1/R2 (P2) | Chair keeps **P0** for *cutover CLOSED* semantics: manual drill ≠ requirement CLOSED. Facts of drills remain separately true (see Verified Truths). |

---

## P1 — High (decision-affecting SoT forks)

| ID | Claim A | Claim B | Reviewers | Chair note |
|----|---------|---------|-----------|------------|
| **RC-P1-01** | Neo4j **OFFLINE** / `graph=unavailable` (`PRODUCTION-VERIFICATION`, `GA_STATUS` #10) | Neo4j **repaired** / `graph=connected` (`ROOTCAUSE-NEO4J`, `OPS01-ROW4`); residual **no persistent volume** | R1, R3, R5–R7 | Post-repair prod `/health` JSON under evidence/ → **NOT VERIFIED**. Connected narrative not durable artifact. |
| **RC-P1-02** | `OPS01-ROW4` §1–2: soak **not started** / not yet run | Same file §5–6 + SOAK-GATE + `evidence/ops01-staging/loop-*.json` (**24** loops observed 2026-08-07; e.g. i00022 at 15:56:48Z) — soak **started**; Row 4 status **OPEN** still correct for incomplete 48–72h | R2, R5–R7 | Status OPEN OK; wording “not started” false. |
| **RC-P1-03** | `SIGN_HERE` open soak = **140** local loops (`wave11-soak-48h-rerun`) | Staging cloud soak SoT = `ops01-staging/` (hours, not 48–72h; `soak_complete_claim` false) | R2, R5–R6 | Dual soak stories without handoff banner. |
| **RC-P1-04** | Suite SoT: BE **1548/0** (`SIGN_HERE` closed + TL draft) | Suite SoT: BE **2009/0** + FE **2492/0** (EAB-003 evidence/CEO/RUN) | R4–R5, R7 | Three greens without dated supersession on signature packet. |
| **RC-P1-05** | `OPS01-ROW4`: Production **READY with conditions**; Verification **100%**; Readiness **~96%** | Mandatory **production no-go**; EAB PR **~53** / Overall **~54**; audit PR **38**; soak false; TL UNSIGNED | R1, R3, R5–R7 | Vocabulary conflict — not a GO claim, but integrity-damaging. |
| **RC-P1-06** | Prod Alembic **0051** (`GA_STATUS`); head **0040** (`SIGN_HERE`) | Probe/risk/restore evidence: current **`d1a8c35e7f09`**, tip **`e5f9a32b0c08`**; migrations **NONE** on prod | R1, R3 | Identity SoT = evidence JSON / PRODUCTION-VERIFICATION. |
| **RC-P1-07** | `GA_STATUS` #1 present-tense: staging **NOT parity**, soft-skip CI, shared JWT/SECRET | `OPS01-ROW4` / DIFF 2026-08-07: parity CLOSED, secrets isolated, K1 PASS | R2, R4, R6 | Temporal staleness without SUPERSEDED banner on GA_STATUS. |
| **RC-P1-08** | EAB CEO/RUN/FINDINGS-RECHECK: “no WAL/offsite” / Checklist 1–5 OPEN as if drills absent | OPS-01 machine table DONE\* ×3 + JSON on same EAB-003 tree | R1, R3, R7 | Disposition lag / undifferentiated “OPS-01 open”. |
| **RC-P1-09** | `RELEASE-BACKLOG`: Backup DR **PARTIAL**; DONE count **0** for items 4–10; DEC-093 may remain **IN_PROGRESS** | `GA_STATUS` DONE for DR drills; `DEC-093-*-CLOSED` closed narrative | R4–R5, R7 | Backlog vs statusboard vs closeout docs. |

---

## P2 — Medium

| ID | Claim A | Claim B | Reviewers |
|----|---------|---------|-----------|
| **RC-P2-01** | `PROD-MIGRATION-RISK` downtime **5–45+ min** / validation class weak | Dress rehearsal ~**60.6 s**; a4f7 ≈20 s measured (`PRODUCTION-CUTOVER-PACKAGE` / rehearsal JSON) | R1, R3 |
| **RC-P2-02** | Health PASS with `kafka=in_memory` | “All connected” / READY rhetoric that implies production event-bus parity | R6 |
| **RC-P2-03** | Advancement object key path `2026/08/06/…` | Evidence JSON object_key `2026/08/…` | R2, R3 |
| **RC-P2-04** | TL draft: FE green 0/0/74; P0/P1 closed | EAB: FE lint ~528; Partials; staging pentest **OPEN** | R4–R5, R7 |
| **RC-P2-05** | Compose/local `archive_mode=off` footgun language | Prod WAL evidence `archive_mode=on` — scopes bleed into checklist “Still off” | R2, R6 |
| **RC-P2-06** | Gate JSON PASS 7/0 with SKIP alembic/flags | Over-read as full soak/contract green | R5–R6 |

---

## P3 — Low / hygiene

| ID | Claim A | Claim B | Reviewers |
|----|---------|---------|-----------|
| **RC-P3-01** | Offsite restore ~96 tables vs local restore ~134 | Env difference; mis-citation risk | R3 |
| **RC-P3-02** | Wave10 local DR still OPEN docs | Prod-path DONE narratives — scope unlabeled skim risk | R1, R3 |
| **RC-P3-03** | EAB README / index “latest run” pointer lag risk | Index hygiene | R7 |

---

## Explicit non-contradictions (do not escalate)

| Topic | Finding |
|-------|---------|
| Production GA decision | **NO-GO** agreed across `GA_STATUS`, `SIGN_HERE` (CTO), EAB-001/002/003 CEO, cutover/risk packages, `AI_HONESTY` |
| OPS-01 Row 4 status value | **OPEN** is consistent with incomplete 48–72h soak (loops ≠ claim complete) |
| Cutover package execution | **PREPARED — NOT EXECUTED** consistent with NO-GO / no prod migrate |

---

## Counts

| Severity | Board unique |
|----------|-------------:|
| P0 | 4 |
| P1 | 9 |
| P2 | 6 |
| P3 | 3 |
| **Total** | **22** |

---

## Post-register evidence updates (2026-08-07, executor deposits)

Rule: evidence wins. These new durable artifacts change the *evidence basis* (not governance files, which remain board/human-controlled):

| ID | Deposit | Effect |
|----|---------|--------|
| **RC-P0-02** | `evidence/ops01-pitr/prod-live-wal-archive-reverify-2026-08-07.json` — live prod `archive_mode=on`, archived **1240** (6→1240 since 08-06), failed=0 | Claim B ("archive Still off") **refuted for prod**; checklist text refers to local compose scope (see also RC-P2-05). Facts side now verified live. |
| **RC-P1-01** | `evidence/ops01-prod-health/prod-health-2026-08-07T1623Z.json` + `prod-health-detailed-2026-08-07T1623Z.json` — HTTP 200, `graph=connected`, uptime 42.84h | **NOT VERIFIED → VERIFIED** for current runtime state. Residual stands: prod Neo4j **no persistent volume** (connected ≠ durable). |
| **RC-P2-05** | Same WAL reverify artifact above | Scopes confirmed separate: prod `archive_mode=on` vs compose-local `off`. |
| **RC-P2-06 / soak progress** | `evidence/ops01-staging/loop-*` now **i00026** (2026-08-07T16:16:59Z), 7 PASS/0 FAIL, PID 16044 alive | Progress advances; completeness still gated by K2–K6 + `soak_complete_claim`. |
| **NEW — Prod auth/RBAC audit** | `evidence/ops01-prod-health/prod-auth-rbac-audit-2026-08-07.json` + `PRODUCTION-AUTH-ROLE-AUDIT-2026-08-07.md` (read-only) | AuthN PASS; tenant-admin RBAC PASS. **New facts for board:** roles are **swapped vs operator assumption** (`muhide.com`=user/unverified, `ratlfintech.com`=admin); both accounts share **same tenant** `326e0825…` (cross-tenant test inconclusive with these creds); Owner Platform admin routes deployed but **unreachable** — `/owner/login` **not deployed** (404 ×3, absent from prod openapi.json, baseline `4750038c`) → all owner routes 401. No security regression (denied 401/404); deployment gap only. |

**Unchanged:** RC-P0-01 (needs human CLOSE/ink), RC-P0-03 (score SoT), RC-P0-04 (BLOCKED-HUMAN automation), RC-P1-03/04 (SoT handoff), RC-P1-05 (vocabulary) remain open for board/human.

**Governance packets added (not editable by agents):** `CTO-REQUIRED-HUMAN-DECISIONS.md` (authoritative human decision register RC-01…08; AI recommends only) + `CEO-EXECUTIVE-BRIEF-AR.md` (Arabic executive summary for management).

**2026-08-07 release decision:** `RELEASE-GOVERNANCE-DECISION-2026-08-07.md` — Engineering **CLOSED**, Release **ACTIVE**, Change Freeze until 2026-08-10T14:10Z. Terminology rule: in current operational docs, "CTO"/"Tech Lead" where it meant the owner's personal decision is now **Project Owner Decision / Acceptance**; `history/EAB-*` archives keep original labels (records). Immutable archive created: `docs/releases/v1.0.0-ga/` (frozen at GA; never edited after deposit).

*Executor addendum — reconciliation-2026-08-07*

---

*Chair synthesis — DOCUMENT-CONTRADICTIONS — reconciliation-2026-08-07*
