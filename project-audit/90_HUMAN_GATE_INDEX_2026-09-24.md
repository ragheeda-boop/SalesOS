# 90 — Human Gate Index: all human-owned gates currently blocking progress, with owners, evidence, and next concrete step (2026-09-24)

## Purpose

A single, current index of every human-owned gate standing between the audit state and Phase 7 / production. This is a read-only inventory; it opens no gate and changes no code or database. It exists so the PO and owners can see at a glance what is open, what evidence exists for it, where that evidence lives, and what the immediate next step is. Data state re-verified this session where noted.

Nothing in this report is a closure, a promotion, or an approval. Phase 7 remains BLOCKED; production remains NOT APPROVED. This report's own sign-off section does not lift either.

---

## 1. Gate inventory (summary)

| # | Gate | Status | Owner | Evidence of status |
|---|---|---|---|---|
| G1 | Register methodology acceptance (report 57) | **ACCEPTED 2026-09-24 (PO)** | PO | `project-audit/57_...md` §4 + `project-audit/91_PO_PHASE_A_DECISION_RECORD_2026-09-24.md` |
| G2 | P3 fuzzy pairs — full human review (2,661) | OPEN | Data / review queue | `PHASE6_P3_FULL_EVIDENCE.csv` (all `final_review_required=YES`) |
| G3 | 36 suspicious short-CR adjudication | OPEN | Data + PO / registry access | `PHASE6_P0_RECONCILIATION.md`; workbook `docs/data/phase6/review/REVIEW_36_SUSPICIOUS_SHORT_CR.csv` (NEW 2026-09-24) |
| G4 | P1 review (6,908) — Tier A conflicts then Tier B spot-check | OPEN | Data + PO | `PHASE6_HUMAN_REVIEW_PO_GATE.md` §4/§5; decision record §2.2 |
| G5 | P2 review (46,736) — stratified sampling, thresholds PO-set | **PARAMS ACCEPTED 2026-09-24 (3%/1%)** | PO | `PHASE6_PO_DECISION_RECORD.md` §2.3 + report 91 §3 |
| G6 | DI P1/P2 enrichment-priority terminology | DECIDED 2026-08-29 | PO | decision record §3 (retired, historical only) |
| G7 | Phase 7 scope gate | **IMPLEMENTATION RELEASED 2026-09-24 (PO), risk-tracked** — supersedes Option B | PO | report 91 §2 (invariants §3 hold: no auto-merge, no auto-CR, no production) |
| G8 | Production-readiness gate | NOT OPEN | PO + DevOps | explicitly never assessed; decision record §5; not part of A1–A3 |
| G9 | Staging Google OAuth app | OPEN (P1) | DevOps | `docs/ops/OAUTH-STAGING-SETUP-2026-08-22.md`; runbook `staging-oauth-setup.md` |
| G10 | Railway managed backup schedule | OPEN (P1) | Platform / Railway Owner | OPS-01 signature pack rows 1–3 signed 2026-08-24; schedule itself not enabled |
| G11 | Live `preDeployCommand` vs `railway.json` drift | OPEN (P1) | DevOps | `HUMAN-GATE-CLOSURE-SUMMARY-2026-08-21.md` (repo says `alembic upgrade head`; live used custom `init_db()`) |
| G12 | SSO Microsoft / GitHub (row 53) | OPEN | PO + DevOps | product decision + external registration + credentials |
| G13 | PDPL compliance statement (row 59) | OPEN | Legal | sign-off |
| G14 | SOC2 Type I (row 60) | OPEN | External auditor | engagement |
| G15 | CS health lifecycle product+data (row 132) | OPEN | PO + Data | real usage/support data |
| G16 | Learning / adaptive ICP (row 131) | OPEN | PO + Data | product decision + real customer usage |

Sources: 132-row register (report 57 §2), PO decision record 2026-08-29, OPS/A09 docs under `docs/ops/`, AGENTS.md BLOCKED-row lists.

## 2. Gates that are NOT human — closed or environment-pinned

| Item | Status |
|---|---|
| Alembic single head `f2e3d4c5b6a7`, 129 migrations | VERIFIED (this session, report 89) |
| RLS coverage 211 tables / 139 policies / 139 FORCE / 0 gaps | VERIFIED (fresh ephemeral DB, report 89) |
| Feature flags (5 `feature_*` = False, enforcement = True) | VERIFIED (report 89) |
| v3=49 / legacy=78 routes | VERIFIED (report 89) |
| Backend scoped tests | PASS (reports 68/70–88 54/54 this run) |
| DB safety 12/12 (Phase 6 test-DB) | PASS (PHASE6_FINAL_DB_SAFETY_VALIDATION) |
| DEC-157 RLS closure (14 tables) | CLOSED (report 68) |
| FORCE RLS account_funnel/score_observations | CLOSED (report 58) |

## 3. Data-state re-check (new this session, directly measured)

The Phase 6 review population lives **only** in the checked-in evidence CSVs right now. Direct read of `salesos_test` this session:
`md_review_candidates` = 0 rows · `md_identity_classifications` = 0 · `md_source_rows` = 0 · `md_global_companies` = 180,000 (expected 296,746) · `md_p0_dispositions` = 0 · `md_entity_conflicts` = 0 · `md_entity_matches` = 0.

Root cause: integration-test teardowns truncate `md_*` tables; restore is documented (`AGENTS.md` §34/35) via `muhide_ingest_real.py` + `muhide_v1_enrichment.py` re-runs. **Consequence for gates G2/G3/G4/G5:** human review must proceed from the evidence CSVs (authoritative, reconciled) until a re-ingestion restores the DB. Review workbooks were produced from those CSVs this session (see §4).

## 4. Deliverables produced this session (human-gate enablement, read-only)

- `docs/data/phase6/review/REVIEW_36_SUSPICIOUS_SHORT_CR.csv` — G3 workbook, 36 rows, empty adjudication columns.
- `docs/data/phase6/review/REVIEW_P3_PAIRS_2661.csv` — G2 workbook, 2,661 pairs, empty adjudication columns.
- `docs/data/phase6/review/README.md` — order, counts, non-claims, restore note.
- `project-audit/89_BOOKKEEPING_RECONCILIATION_2026-09-24.md` — register + mechanical re-verification (signed section added 2026-09-24).
- This report (90).

No code changed, no migration, no DB write, no Apollo/external call, no production access.

## 5. Deliberate non-claims

- **This index opened no gate originally, and the Phase-A decisions (report 91) are PO decisions recorded, not additional closures by this workstream.** G1/G5 params/G7 were decided by the PO on 2026-09-24 and are reflected above; this report merely records them. G2/G3/G4 remain open.
- **A2 (Phase 7 released) does not authorize production, merging, or CR adjudication.** Report 91 §3 invariants bind: no auto-merge of any P3 pair; no auto-adjudication of the 36 short-CR; no production DB/write/external call; `salesos_test` only.
- **The 36-short-CR workbook does not adjudicate.** Each needs a human with registry/business knowledge; no auto rule per the government-ID hard veto.
- **The P3 workbook does not merge anything.** All 2,661 pairs stay `RETAINED`, `final_review_required=YES`, none auto-merged.
- **P2 acceptance threshold (error %) remains PO-set** (3%/1% sample fractions accepted; the threshold value is a separate PO number).
- Re-ingestion to restore `salesos_test` is **not** performed by this report (it is a DB-write action outside read-only scope and requires owner/PO awareness).

## 6. Immediate next action per gate (for owners)

| Gate | Immediate next step | Est. effort |
|---|---|---|
| G1 | ~~PO/TL accept report 57 methodology~~ **DONE 2026-09-24** | — |
| G2 | Open `REVIEW_P3_PAIRS_2661.csv`; staff reviewer tier; fill adjudication | depends on staff |
| G3 | Open `REVIEW_36_SUSPICIOUS_SHORT_CR.csv`; lookup each short CR vs Saudi registry or MUHIDE conventions | ~1 day for one reviewer |
| G4 | Extract Tier A conflict subset from classifications CSV; run 5% Tier B sample | ~2 days |
| G5 | ~~PO set sample fractions~~ **DONE 2026-09-24 (3%/1%)**; remaining: set acceptance threshold + stratify | PO: 30 min |
| G7 | ~~Planning-only~~ **RELEASED 2026-09-24**; Phase 7 work may start under report 91 invariants | — |
| G9 | Follow `OAUTH-STAGING-SETUP-2026-08-22.md` (Google Cloud Console) | 15–30 min |
| G10 | Railway Owner/Admin enable managed backup | platform access |
| G11 | Align Railway live `preDeployCommand` to `railway.json` | deploy fix |
| G12/G13/G14/G15/G16 | Product/legal/auditor/data grooming | business-dependent |

## Sign-off (inventory review only)

| Field | Value |
|---|---|
| Prepared by | Audit workstream (report 90) |
| Prepared at | 2026-09-24 |
| Nature | Read-only index; no gate opened; no DB/code/production change |
| Owner action | PO + gate owners review and act on §6 rows |