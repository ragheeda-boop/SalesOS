# R5 — QA Director | Enterprise Reconciliation Audit

## Role / Date

**Role:** QA Director (suite claims, soak evidence integrity, readiness vocabulary, NO-GO honesty)  
**Date:** 2026-08-07  
**Mode:** READ ONLY — governance contradictions only  
**Did not modify:** GA_STATUS, SIGN_HERE, OPS checklists, run reports, history  
**Validation:** light validated (evidence file inventory; suites not re-executed)

---

## Claims examined (quote + path)

| ID | Quote / claim | Path |
|----|---------------|------|
| Q1 | “B7 — Pytest suite logged … **1548 passed, 0 failed**” | `SIGN_HERE.md` Closed table |
| Q2 | “BE pytest (**1548/0**)”; “FE lint/tsc/build green (0/0/74 routes)” | `SIGN_HERE.md` TL notes |
| Q3 | Backend `tests/unit` **2009 pass / 0 fail**; FE `npm test` **2492 pass / 0 fail** | `EAB-2026-08-06-003/EVIDENCE-LOG.md`; `RUN-REPORT.md` |
| Q4 | “frontend `npm test` **2492 pass**”; BE unit 0 failures | `CEO-SUMMARY.md` |
| Q5 | “Testing \| **~99+**” (scoreboard) | `GA_STATUS.md` Wave columns |
| Q6 | “48–72h soak NOT complete — **IN PROGRESS** (140 loops, ~12.4h…)”; `soak_complete_claim: false` | `SIGN_HERE.md` #1 |
| Q7 | “No 48–72h soak claim — harness running; claim still **false**” | `GA_STATUS.md` #1 |
| Q8 | “Status: OPEN … soak not yet run” / “soak **not started**” | `OPS01-ROW4-STATUS.md` §1–2 |
| Q9 | “Soak window started 2026-08-07T14:10:06Z”; “iterations every 5 min; i1–i5 PASS” | `OPS01-ROW4-STATUS.md` §5–6 |
| Q10 | K2–K6 OPEN; `soak_complete_claim` **false**; IN PROGRESS table PID 16044 | `SOAK-GATE-CHECKLIST.md` |
| Q11 | Gate classification: “not Production GO; not 48–72h soak complete” | `gate-2026-08-07T140950Z.json` |
| Q12 | Wave11 local soak: hard fails historically; claim false | `PROGRESS-WAVE11-SOAK*.md` |
| Q13 | Production GA **NO-GO** | `GA_STATUS`, `SIGN_HERE`, EAB |
| Q14 | “READY with conditions — NOT GO”; Progress Readiness ~**96%**; Verification **100%** | `OPS01-ROW4-STATUS.md` §2 / §7 |
| Q15 | EAB Prod Readiness **~53**; Overall **~54** | EAB-003 SCORECARD / RUN-REPORT |
| Q16 | Audit Production Readiness **38** | README / `00-EXECUTIVE-SUMMARY` / ROW4 citation |
| Q17 | Security scoreboard **~65** vs EAB **~81** vs cited **48** | `GA_STATUS` / EAB / ROW4 |
| Q18 | Backup DR rows 1–3 **DONE** (`GA_STATUS`) vs DR checklist **OPEN** | `GA_STATUS` #7 vs `DR-GA-GAPS-CHECKLIST` |
| Q19 | “UI crawl 49/49 PASS”; Auth 13/14 | `SIGN_HERE.md` closed evidence |
| Q20 | Staging SSRF pentest **OPEN** | `GA_STATUS` #4; `SIGN_HERE` #4 |
| Q21 | DEC-093 mint DONE light; browser pass **not** claimed | `DEC-093-OWNER-LOGIN-FOLLOWUP-CLOSED.md` |
| Q22 | Neo4j repaired / connected vs OFFLINE docs | `ROOTCAUSE-NEO4J` vs `PRODUCTION-VERIFICATION` |

---

## Evidence found / NOT VERIFIED

| Artifact | Present? | Notes |
|----------|:--------:|-------|
| EAB-003 EVIDENCE-LOG citing 2009/0 and 2492/0 | Yes | Board run evidence log |
| `evidence/wave3-pytest/` path cited for 1548 | Cited in SIGN_HERE | Contents **not re-opened** this review — treat as historical claim; consistency vs 2009 is documentary |
| `ops01-staging/loop-*.json` | Yes — **23** loops | i00001@14:10:06Z … i00023@16:01:51Z; sampled gate_pass true |
| `ops01-staging/gate-2026-08-07T140950Z.json` | Yes | PASS 7/0; soak-complete denied in classification |
| `evidence/wave11-soak-48h-rerun/` 140 JSONs | Cited | Inventory **NOT VERIFIED** file-count this review |
| 48–72h wall-clock completion artifact | **No** | Consistent with claim false |
| Browser E2E / owner mint success | **NOT VERIFIED** | Explicitly not claimed |
| Staging pentest report | **NOT VERIFIED** / OPEN | |

---

## Contradictions only (Claim A vs Claim B, P0/P1/P2/P3)

### P0

| ID | Claim A | Claim B |
|----|---------|---------|
| **QA-P0-1** | `GA_STATUS` #7: offsite+WAL+PITR **DONE** (and OPS DONE\*) | Cutover SoT `DR-GA-GAPS-CHECKLIST` + `SIGN_HERE` #7 + EAB CEO/RUN: still **OPEN** / **NOT done** — QA cannot certify DR closed |
| **QA-P0-2** | “Verification **100%**” / Production Readiness ~**96%** (`OPS01-ROW4` §7) | Audit PR **38**, EAB PR **~53**, soak claim **false**, TL UNSIGNED, pentest OPEN — “100%/96%” overclaims verification completeness |

### P1

| ID | Claim A | Claim B |
|----|---------|---------|
| **QA-P1-1** | Suite SoT: **1548/0** (`SIGN_HERE` closed + TL draft) | Suite SoT: **2009/0** unit + **2492/0** jest (EAB-003) — three green numbers without dated supersession on SIGN_HERE |
| **QA-P1-2** | ROW4 §1–2: soak **not started** / not yet run | §5–6 + SOAK-GATE + **23** loop JSON: soak **started**; Row 4 OPEN is correct for incomplete duration, wording is not |
| **QA-P1-3** | SIGN_HERE open soak = **140 loops** local path | Staging path **23** loops / ~hours — dual soak stories as if one gate |
| **QA-P1-4** | “READY with conditions” language | Mandatory **production no-go** classification across GA_STATUS / SIGN_HERE / EAB |
| **QA-P1-5** | TL draft: FE green 0/0/74; P0/P1 closed | EAB: FE lint ~528; Partials; pentest OPEN |

### P2

| ID | Claim A | Claim B |
|----|---------|---------|
| **QA-P2-1** | Testing scoreboard **~99+** | Different suite populations (1548 vs 2009) and FE lint red — scoreboard not tied to EAB evidence log |
| **QA-P2-2** | Security **48** cited beside Verification 100% | EAB Security **~81** / GA **~65** — score shopping undermines QA scoreboard honesty |
| **QA-P2-3** | Neo4j “connected” after repair (ROW4) | PRODUCTION-VERIFICATION OFFLINE; post-repair health JSON **NOT VERIFIED** |
| **QA-P2-4** | DEC-093 CLOSED | RELEASE-BACKLOG IN_PROGRESS; browser not claimed |

### P3

| ID | Claim A | Claim B |
|----|---------|---------|
| **QA-P3-1** | UI crawl 49/49 / auth 13/14 closed as GO-supporting evidence | Still NO-GO — fine if dated, but packs can over-weight closed B-items |
| **QA-P3-2** | Gate JSON PASS 7/0 | SKIP alembic/flags via `--skip-*` — gate green ≠ full soak contract |

---

## Topic → candidate authoritative source

| Topic | Candidate SoT | Deprioritize |
|-------|---------------|--------------|
| Production GA | `SIGN_HERE` CTO NO-GO + EAB CEO | READY/~96%/Verification 100% |
| BE unit suite (latest board) | EAB-003 EVIDENCE-LOG **2009/0** | Undated **1548/0** as “current” |
| FE jest (latest board) | EAB-003 **2492/0** | — |
| Historical Wave3 pytest | SIGN_HERE B7 **1548** labeled historical | Equating to EAB-003 unit run |
| Soak complete? | `SOAK-GATE-CHECKLIST` K1–K6 + `soak_complete_claim` | Loop count; “not started” once loops exist |
| Staging soak evidence | `evidence/ops01-staging/loop-*.json` (**23**) | Local 140-loop narrative as cloud close |
| DR cutover closed? | `DR-GA-GAPS-CHECKLIST` | GA_STATUS DONE bullets |
| Pentest | OPEN until report linked | Code Fixed ≠ pentest PASS |

---

## Summary counts by severity

| Severity | Count |
|----------|------:|
| P0 | 2 |
| P1 | 5 |
| P2 | 4 |
| P3 | 2 |
| **Total contradictions** | **13** |

**Production NO-GO:** **Agreed.**  
**Suite consistency 1548 / 2009 / 2492:** **QA-P1-1** (must date-fence; not proof of failure—proof of SoT collapse).  
**Soak:** claim false consistent; “not started” vs 23 loops = **QA-P1-2**.  
**Rows 1–3 DONE vs DR OPEN:** **QA-P0-1 CRITICAL.**

---

*R5-QA-DIRECTOR — reconciliation-2026-08-07 — contradictions only*
