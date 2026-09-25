# 106 — NCNP rule real run, non-commercial segment, and gate review workbooks (2026-09-25)

**Authority:** Ragheed Almadani (PO), 25/09/2026, in the session chat: "يلا ولك الموافقة على التشغيل الفعلي للخطوة 4 كذالك". It approves the plan in the previous turn: steps 1–7, the non-commercial segment proposal (G5-3), and the real run (step 4).
**Scope:** `salesos_test` only. No production writes, no external APIs, no commit.

## 1. Decisions recorded

| # | Decision |
|---|---|
| G5-3 | Non-profits (NCNP register) and government bodies (`.gov.sa`) form a separate **non-commercial** segment, excluded from sales-usable. It is a blocker, not a deletion, and is reversible via `EXCLUDE_NON_COMMERCIAL`. |
| Step 4 | Real Phase 6 run with the NCNP CR rule (report 105), written under a new version, with obsolete candidates superseded. |

## 2. Code changes

- `phase6/pipeline.py`: `ACTIVE_CLASSIFICATION_VERSION`, now `OPTION_C_1+EXCL_NCNP`. It is the single version Phase 7 readers use.
- `phase7/usability.py`:
  - Readers filter by the active version, which prevents double counting.
  - New blocker `NON_COMMERCIAL_SEGMENT`: an NCNP source-map row, or a `.gov.sa` domain.
- `phase7/review_queue.py`: triage list, counts, and P1 capture check exclude `status='superseded'` and join the active version.
- `scripts/phase7a_p2_sample.py`: filters by version and excludes superseded rows. New seed `PHASE7A-P2-2026-09-25-v2-EXCL_NCNP` with the new expected population.
- `scripts/phase6_apply_ncnp_rule.py` (new): requires `--apply` and asserts `salesos_test`. Everything runs in one transaction:
  1. The pipeline writes the new version.
  2. Pending, undecided candidates the new version no longer produces are set to `superseded`, with `superseded_by_version`, `superseded_at` and `superseded_reason` added to `evidence`. Nothing is deleted, and no human decision is touched.
- Frontend: Arabic label for the new blocker on `/v3/sales-usability`.
- Tests:
  - New unit test for the non-commercial blocker.
  - The Phase 7 integration tests' expected counts were updated to the new state (43,022→41,723; P1 6,908→6,883 = 5,729 + 663 + 491; P2 46,736→43,204; short-CR in ready 29→32).

## 3. Real run

| Item | Result |
|---|---|
| Backup before the run | `scratchpad/phase6_derived_before_ncnp_20260925.dump` (5 derived tables, 71,050,301 bytes, sha256 `05c285e8…f502e3`) |
| New version rows | 296,746 (`OPTION_C_1` history kept: 296,746) |
| Result versus the dry run | **Identical**: SAFE 11,415, SUSPICIOUS_MULTI 2, P1/P2/P3 6,883/43,204/546. Safety counters 0. |
| Candidates superseded | 3,637 (P1 61, P2 3,576). This matches the dry-run delta. |
| Active candidates | 50,633 |
| Invariants | Companies 296,746, people 1,124, source rows 909,967, provenance 1,524,717. The pipeline writes only derived tables (identity, candidates, industry, quality, readiness, relationships). Global IDs and `raw_payload` are unchanged. |
| Review queue | Unchanged: P3_PAIR 2,661 pending, SHORT_CR 36 pending. |

**Rollback:**
1. Set `ACTIVE_CLASSIFICATION_VERSION` back to `OPTION_C_1`.
2. Set candidates with `evidence->>'superseded_by_version' = 'OPTION_C_1+EXCL_NCNP'` back to `pending`.
3. Or restore the backup.

## 4. Sales Usability after the run

| Measure | Value |
|---|---:|
| Ready accounts | 41,723 (SALES_READY 5,689, SRWR 36,034) |
| Usable now | 0 |
| P1_REVIEW_GATE_OPEN / P2_STRATUM_NOT_ACCEPTED | 5,689 / 36,034 |
| NON_COMMERCIAL_SEGMENT | 2,844 |
| PENDING_P3_FUZZY_PAIR / PENDING_SHORT_CR / CR_SUSPICIOUS_MULTI | 148 / 32 / 2 |
| If G4 + G5(SRWR) closed | **38,729 usable** |

## 5. Human review workbooks

Location: `docs/data/phase7/gate_review_20260925/` (with a README).

| File | Rows |
|---|---:|
| G3 — 5 accounts (3 NCNP associations with an SFDA number, 2 SOCPA firms). All five numbers are 10 digits beginning with `7`, the unified-number series; the reviewer should confirm whether that series is a CR. | 5 |
| G4 — field conflicts (full) | 663 |
| G4 — weak identity (full) | 491 |
| G4 — corroboration sample, 5% stratified by source (MULTI 163, SFDA 111, SOCPA 13, Engineering 1) | 288 of 5,729 |
| G5 — real-world spot check, commercial SRWR only, stratified (Directory 14, Apollo 11, SFDA 9, Contractors 6, Suppliers 4, Balady 2, Multi 2, Engineering 1, SOCPA 1) | 50 |
| G5 — redrawn A3 sample v2 | 1,153 (1,081 + 72) |

## 6. Verification

- Unit suite: **3,787 passed**, 0 failed.
- Phase 7 integration (DB + HTTP, `salesos_test`): **19/19**.
- Ruff clean on changed files.

## 7. Still open

- Human reviews in §5 (G3: 5, G4: 1,442, G5: 50).
- A capture step to record the reviewers' decisions, after PO acceptance of the filled workbooks.
- A closure report per gate.
- Frontend label: TypeScript PASS and Jest sales-usability 2/2. Not browser-verified.

Gates G2/G3/G4/G5 remain **OPEN**. Production is **NOT APPROVED**.
