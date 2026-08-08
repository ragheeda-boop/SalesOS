# R6 — Site Reliability | Enterprise Reconciliation Audit

## Role / Date

**Role:** Site Reliability (soak runtime, Neo4j availability, DR ops truth, prod health)  
**Date:** 2026-08-07  
**Mode:** READ ONLY — contradictions vs evidence only  
**Did not modify:** GA_STATUS, SIGN_HERE, OPS checklists, run reports, history  
**Validation:** light validated (evidence inventory; no live `/health` re-probe this review)

---

## Claims examined (quote + path)

| ID | Quote / claim | Path |
|----|---------------|------|
| R1 | Prod health: `"graph":"unavailable"`; Neo4j OFFLINE | `PRODUCTION-VERIFICATION.md` §1 / §7 |
| R2 | “2026-08-06 live probe: `neo4j-prod` is OFFLINE (`graph=unavailable`)” | `GA_STATUS.md` #10 |
| R3 | “Prod Neo4j repaired … `/health` `graph=connected`” | `ROOTCAUSE-NEO4J.md` §3; `OPS01-ROW4-STATUS.md` §1 |
| R4 | “No volume attached to prod `neo4j-prod` → data is ephemeral” | `ROOTCAUSE-NEO4J.md` §4 |
| R5 | Staging soak Row 4 **OPEN**; “soak not yet run” / “not started” | `OPS01-ROW4-STATUS.md` §1–2; `OPS-01-CHECKLIST` OPS01-04 |
| R6 | Soak started `2026-08-07T14:10:06Z`, PID **16044**, evidence `ops01-staging/` | `SOAK-GATE-CHECKLIST.md`; `OPS01-ROW4` §5 |
| R7 | K2 ≥48h OPEN; `soak_complete_claim` **false** | `SOAK-GATE-CHECKLIST.md` |
| R8 | Gate/loop health bodies show staging `"graph":"connected"` | `gate-2026-08-07T140950Z.json`; loop samples |
| R9 | Offsite+WAL+PITR **DONE** (`GA_STATUS` / OPS DONE\*) | `GA_STATUS.md` #7; `OPS-01-CHECKLIST` |
| R10 | DR rows 1–3 **OPEN** / NOT done; `archive_mode` still off (checklist) | `DR-GA-GAPS-CHECKLIST.md`; `DR_RUNBOOK.md` |
| R11 | RPO table: “No PITR”; “Up to 24 hours (daily snapshot)” | `DR_RUNBOOK.md` §1 (body) |
| R12 | Advancement honesty: Primary WAL/PITR proven **TRUE** (2026-08-06) | `OPS-01-ADVANCEMENT.md` §6 |
| R13 | SIGN_HERE: 140 loops soak IN PROGRESS; Docker instability | `SIGN_HERE.md` #1 |
| R14 | Production **READY with conditions**; Launch **NO-GO** | `OPS01-ROW4-STATUS.md` §2 |
| R15 | kafka=`in_memory` residual | `GA_STATUS` #10; health payloads |
| R16 | Staging was 409 commits behind / empty DB (2026-08-06) | `GA_STATUS` #1; STAGING-VERIFICATION era |
| R17 | Staging parity CLOSED / K1 PASS (2026-08-07) | `SOAK-GATE` / ROW4 |
| R18 | Production GA **NO-GO** | SIGN_HERE / GA_STATUS / EAB |
| R19 | Security 48 cited with PR 38 beside connected health | ROW4 / PRODUCTION-VERIFICATION |
| R20 | EAB Security ~81 / PR ~53 | EAB-003 |

---

## Evidence found / NOT VERIFIED

| Artifact | Present? | Notes |
|----------|:--------:|-------|
| `ops01-row1/2/3` JSON + md | Yes | Manual DR drills on prod path |
| `ops01-staging/loop-*.json` | **23** files | ~5 min cadence from i1→i23 (~1h50m elapsed sampled) |
| `gate-2026-08-07T140950Z.json` | Yes | Staging graph connected; soak-complete denied |
| Live prod `/health` post-repair JSON in evidence/ | **No** | Neo4j connected **NOT VERIFIED** as artifact |
| Process evidence that PID 16044 still alive | **NOT VERIFIED** | Claim only |
| Full 48h/72h end UTC evidence | **No** | Consistent OPEN |
| Continuous WAL schedule automation | BLOCKED-HUMAN per OPS pack | Not closed |

**Soak loop count (this review):** `Get-ChildItem …/ops01-staging/loop-*.json` → **23**.

---

## Contradictions only (Claim A vs Claim B, P0/P1/P2/P3)

### P0

| ID | Claim A | Claim B |
|----|---------|---------|
| **SR-P0-1** | `GA_STATUS` / OPS-01: Rows 1–3 **DONE** (WAL/offsite/PITR machine verified) | `DR-GA-GAPS-CHECKLIST` / `DR_RUNBOOK` / `SIGN_HERE` #7: **OPEN**; EAB CEO still “OPS-01 … remains open” as launch blocker undifferentiated |
| **SR-P0-2** | `DR_RUNBOOK` §1 body still: “**No PITR**”; RPO up to 24h snapshot; checklist EAB-003 “archive **Still off**” | OPS-01 evidence + advancement §6: WAL/PITR proven **TRUE** on prod path — runbook body **contradicts** banner-linked evidence pack |

### P1

| ID | Claim A | Claim B |
|----|---------|---------|
| **SR-P1-1** | Neo4j OFFLINE / `graph=unavailable` (PRODUCTION-VERIFICATION, GA_STATUS #10) | Neo4j repaired / `graph=connected` (ROOTCAUSE, ROW4); **no** post-repair prod health JSON → **NOT VERIFIED**; residual **no volume** = availability ≠ durability |
| **SR-P1-2** | ROW4: soak **not started** | SOAK-GATE + PID claim + **23** loop JSON: soak **in progress**; Row 4 correctly OPEN for duration, incorrectly “not started” |
| **SR-P1-3** | SIGN_HERE soak = 140 local loops / Docker instability narrative | Staging cloud soak = `ops01-staging` 23 loops — SRE cannot operate two soak SoTs |
| **SR-P1-4** | “READY with conditions” for Production | Audit/EAB **production no-go**; Neo4j volume risk; migrate behind; soak incomplete |

### P2

| ID | Claim A | Claim B |
|----|---------|---------|
| **SR-P2-1** | Staging NOT parity / soft-skip CI (GA_STATUS present tense) | K1 PASS / secrets wired / parity CLOSED (2026-08-07 packs) |
| **SR-P2-2** | Health `kafka=in_memory` accepted in PASS health | Event-bus honesty vs “all connected” READY language |
| **SR-P2-3** | DONE\* without managed schedule / native PITR API | Automated DR expectation in checklist text |
| **SR-P2-4** | Security/PR 48/38 cited next to healthy env | EAB 81/53 — reliability scoreboard shopping |

### P3

| ID | Claim A | Claim B |
|----|---------|---------|
| **SR-P3-1** | Gate skips alembic/flags | Soak monitors runtime only — OK if labeled; easy to over-read as full contract |
| **SR-P3-2** | Compose local archive_mode=off footgun | Prod WAL on — scope bleed into checklist “Still off” |

---

## Topic → candidate authoritative source

| Topic | Candidate SoT | Deprioritize |
|-------|---------------|--------------|
| Prod Neo4j **now** | Fresh dated `/health` JSON artifact + ROOTCAUSE residual (no volume) | Stale PRODUCTION-VERIFICATION alone; unreplicated “connected” narrative alone |
| Soak complete? | K2–K6 + `soak_complete_claim` | “not started” after loops exist; local 140-loop as cloud close |
| Staging soak evidence | `evidence/ops01-staging/` (**23** loops + gate) | Wave11 local dirs |
| DR cutover CLOSED | `DR-GA-GAPS-CHECKLIST` + ink | `GA_STATUS` DONE; OPS DONE\* |
| DR executable facts | `evidence/ops01-offsite/*`, `ops01-pitr/*` | `DR_RUNBOOK` §1 body until rewritten |
| RPO capability | Must recompute after WAL evidence; currently body vs evidence conflict | Snapshot-only table as current truth |
| Production GA | SIGN_HERE NO-GO | READY with conditions |

---

## Summary counts by severity

| Severity | Count |
|----------|------:|
| P0 | 2 |
| P1 | 4 |
| P2 | 4 |
| P3 | 2 |
| **Total contradictions** | **12** |

**Production NO-GO:** **Agreed.**  
**Rows 1–3 DONE vs DR OPEN:** **SR-P0-1 CRITICAL.**  
**Row 4 OPEN vs soak evidence:** OPEN status OK; contradiction = “not started” vs **23** iterations + start UTC (**SR-P1-2**).  
**Neo4j fixed vs health:** **SR-P1-1** (artifact gap + volume residual).

---

*R6-SITE-RELIABILITY — reconciliation-2026-08-07 — contradictions only*
