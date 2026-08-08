# R2 — DevOps Lead | Enterprise Reconciliation Audit

## Role / Date

**Role:** DevOps Lead (deploy, compose, CI/staging, OPS-01 ops claims)  
**Date:** 2026-08-07  
**Mode:** READ ONLY — governance vs evidence contradictions only  
**Did not modify:** GA_STATUS, SIGN_HERE, OPS checklists, run reports, history  
**Validation:** light validated (docs + evidence inventory; no live redeploy)

---

## Claims examined (quote + path)

| ID | Quote / claim | Path |
|----|---------------|------|
| D1 | “Offsite backup … \| **OPEN / HUMAN**”; “WAL archive … \| **OPEN / HUMAN**”; “PITR … \| **OPEN / HUMAN**”; “Staging soak … \| **OPEN / HUMAN**” | `docs/ops/DR-GA-GAPS-CHECKLIST.md` checklist |
| D2 | “Rows 1–5 (launch) \| Still **OPEN / BLOCKED-HUMAN / UNSIGNED**”; “Offsite / staging soak / signatures \| **NOT done**” | `DR-GA-GAPS-CHECKLIST.md` §EAB-003 |
| D3 | “OPS01-01 … DONE\*”; “OPS01-02 … DONE\*”; “OPS01-03 … DONE\*”; “OPS01-04 … OPEN” | `…/OPS-01-CHECKLIST.md` |
| D4 | “Backup DR — offsite + WAL + PITR **DONE 2026-08-06**” | `GA_STATUS.md` #7 |
| D5 | “offsite S3/MinIO **OPEN**; primary `archive_mode=off`” | `SIGN_HERE.md` §Still open #7 |
| D6 | “GA / cutover gate: … rows 1–5 **OPEN** → **no Production GO**” | `docs/ops/DR_RUNBOOK.md` banner |
| D7 | “Local drills … ≠ offsite / WAL / staging soak” | `DR_RUNBOOK.md` banner |
| D8 | “Primary WAL \| Stock postgres has `archive_mode=off` — do not claim PITR from compose alone” | `COMPOSE-SOURCE-OF-TRUTH.md` footguns |
| D9 | “Railway staging exists … but **NOT production-parity** — 409 commits behind…” | `GA_STATUS.md` #1; `OPS-01-ADVANCEMENT.md` row 4 (2026-08-06) |
| D10 | “K1 now PASSES parity”; staging = prod baseline `4750038c` | `SOAK-GATE-CHECKLIST.md` 2026-08-07 UPDATE; `OPS01-ROW4-STATUS.md` |
| D11 | “Status: OPEN (parity achieved; soak not yet run)” / “soak **not started**” | `OPS01-ROW4-STATUS.md` §1 / §2 |
| D12 | “Soak window started 2026-08-07T14:10:06Z … PID 16044” | `OPS01-ROW4-STATUS.md` §5; `SOAK-GATE-CHECKLIST.md` §IN PROGRESS |
| D13 | “`soak_complete_claim`: **false**”; K2–K6 OPEN | `SOAK-GATE-CHECKLIST.md`; Wave11 claim docs |
| D14 | “48–72h soak NOT complete — **IN PROGRESS** (140 loops…)”; evidence `evidence/wave11-soak-48h-rerun/` | `SIGN_HERE.md` §Still open #1 |
| D15 | “No staging (cloud) deploy + rollback tabletop — 0 GitHub Environments…” | `SIGN_HERE.md` #2; `RELEASE-BACKLOG` item 4 **BLOCKED-HUMAN** |
| D16 | “CI/CD: repo secrets `RAILWAY_STAGING_*` set; `deploy-staging.yml` updated” | `OPS01-ROW4-STATUS.md` §1 |
| D17 | “deploy-staging.yml soft-skips (no `RAILWAY_STAGING_*` secrets)” | `GA_STATUS.md` #1 / OPS-01 advancement 2026-08-06 text |
| D18 | Production GA **NO-GO** | `GA_STATUS`, `SIGN_HERE`, EAB RUN-REPORT, cutover package |
| D19 | “MinIO `objectstore` profile … starting MinIO ≠ offsite DR closed” | `COMPOSE-SOURCE-OF-TRUTH.md` |
| D20 | Object key `2026/08/06/salesos_prod_…` vs evidence `2026/08/salesos_prod_…` | `OPS-01-ADVANCEMENT.md` vs `ops01-row1-evidence.md` |

---

## Evidence found / NOT VERIFIED

| Artifact | Present? | Notes |
|----------|:--------:|-------|
| `ops01-row1-offsite-restore.json` | Yes | Prod dump → S3 → disposable restore |
| `ops01-row2-wal-archiver.json` | Yes | Prod archive_mode=on path |
| `ops01-row3-pitr-restore.json` | Yes | PITR timestamp restore |
| `ops01-staging/gate-2026-08-07T140950Z.json` | Yes | Staging API/FE gate PASS; soak-complete denied |
| `ops01-staging/loop-*.json` | Yes — **23** files | Iterations `i00001` (14:10:06Z) … `i00023` (16:01:51Z); gate_pass true samples |
| PID 16044 still running / host process proof | **NOT VERIFIED** this review | Claimed in SOAK-GATE / ROW4; no process-status evidence file |
| GitHub Environments `total_count` re-probe 2026-08-07 | **NOT VERIFIED** | RELEASE-BACKLOG cites older 0 Environments |
| Post-isolation staging deploy secret hashes live re-check | **NOT VERIFIED** here | See SECURITY-SECRETS narrative 2026-08-07 |
| Checklist rows 1–3 flipped to CLOSED with ink | **NOT VERIFIED** / absent | Still OPEN in DR checklist |

---

## Contradictions only (Claim A vs Claim B, P0/P1/P2/P3)

### P0

| ID | Claim A | Claim B |
|----|---------|---------|
| **DO-P0-1** | `GA_STATUS` #7 + OPS-01 checklist: Rows 1–3 **DONE** (machine verified) | `DR-GA-GAPS-CHECKLIST` + `DR_RUNBOOK` + `SIGN_HERE` #7 + EAB CEO/RUN-REPORT: offsite/WAL/PITR / rows 1–5 **OPEN** / **NOT done** |
| **DO-P0-2** | DR EAB-003 block: primary `archive_mode` **Still off**; offsite **NOT done** | OPS-01 evidence JSON + advancement: prod WAL on + offsite restore done — checklist contradicts its own linked pack |

### P1

| ID | Claim A | Claim B |
|----|---------|---------|
| **DO-P1-1** | `OPS01-ROW4` §1–2: soak **not yet run** / **not started** | Same file §5–6 + `SOAK-GATE` IN PROGRESS + **23** loop JSON under `evidence/ops01-staging/` — soak **started**; Row 4 remains OPEN (incomplete) but “not started” is false |
| **DO-P1-2** | `GA_STATUS` / OPS-01 advancement (2026-08-06): staging **NOT parity**, `deploy-staging.yml` soft-skips, no secrets | `OPS01-ROW4` / `SOAK-GATE` (2026-08-07): K1 PASS, secrets wired, parity CLOSED — stale present-tense on GA_STATUS without SUPERSEDED banner |
| **DO-P1-3** | `SIGN_HERE` soak story: **140 loops** local `wave11-soak-48h-rerun` as the open soak blocker narrative | Staging cloud soak evidence path is `ops01-staging/` (**23** loops, ~hours not 48–72h) — two soak narratives without clear SoT handoff |
| **DO-P1-4** | `RELEASE-BACKLOG` / `SIGN_HERE`: staging cloud deploy tabletop **BLOCKED-HUMAN** / 0 Environments | ROW4 claims CI secrets + workflow updated — Environments/tabletop vs Railway staging reachability mixed without reconciliation |

### P2

| ID | Claim A | Claim B |
|----|---------|---------|
| **DO-P2-1** | Compose footgun: local `archive_mode=off` — do not claim PITR from compose | Prod path evidence claims WAL/PITR DONE\* — local vs prod scopes conflated in DR checklist “Still off” |
| **DO-P2-2** | Advancement cites object key under `2026/08/06/` | Evidence md/json use `2026/08/` — path mismatch |
| **DO-P2-3** | `DONE\*` with scheduled automation **BLOCKED-HUMAN** | Operators may treat DONE\* as cutover-closed automation |

### P3

| ID | Claim A | Claim B |
|----|---------|---------|
| **DO-P3-1** | MinIO profile exists for drills | Starting MinIO ≠ offsite closed — honesty OK; risk if backlog cites MinIO as progress toward DONE |
| **DO-P3-2** | Production NO-GO agreed | Soft staging “SOAK-CAPABLE” language adjacent to cutover prep packages |

---

## Topic → candidate authoritative source

| Topic | Candidate SoT | Deprioritize |
|-------|---------------|--------------|
| Cutover CLOSED for offsite/WAL/PITR | `DR-GA-GAPS-CHECKLIST.md` + human close | `GA_STATUS` DONE until checklist updated |
| Drill executable facts | `evidence/ops01-offsite/*`, `evidence/ops01-pitr/*` | Wave10 local-only progress |
| Staging parity (current) | `STAGING-vs-PRODUCTION-DIFF.md` + `OPS01-ROW4` (2026-08-07) | Unbannered `GA_STATUS` #1 409-behind clause |
| Soak completeness | `SOAK-GATE-CHECKLIST.md` K1–K6 + `soak_complete_claim` | Loop count alone; SIGN_HERE 140-loop local story as cloud close |
| Compose SoT | `COMPOSE-SOURCE-OF-TRUTH.md` | Root compose |
| Staging CI wiring | Dated ROW4 / workflow files | SIGN_HERE “0 secrets” without date fence |
| Production GA | `SIGN_HERE` CTO NO-GO | Cutover package “PREPARED” |

---

## Summary counts by severity

| Severity | Count |
|----------|------:|
| P0 | 2 |
| P1 | 4 |
| P2 | 3 |
| P3 | 2 |
| **Total contradictions** | **11** |

**Production NO-GO:** **Agreed.**  
**Rows 1–3 DONE vs DR OPEN:** **CRITICAL (DO-P0-1).**  
**Row 4:** status **OPEN** consistent with incomplete 48–72h; contradiction is “not started” vs **23** loop evidence + PID claim (**DO-P1-1**).  
**Neo4j / security scores / pytest triple counts:** noted as cross-cutting; DevOps cites Neo4j only insofar as staging/prod graph inversion claimed fixed in ROW4 vs PRODUCTION-VERIFICATION OFFLINE (see SRE).

---

*R2-DEVOPS-LEAD — reconciliation-2026-08-07 — contradictions only*
