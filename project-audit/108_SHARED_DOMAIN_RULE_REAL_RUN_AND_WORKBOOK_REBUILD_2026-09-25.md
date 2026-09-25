# 108 — Shared-domain rule: real run and workbook rebuild (2026-09-25)

**Authority:** Ragheed Almadani (PO), 25/09/2026, reply "يلا" to report 107 option 1. It approves the threshold-5 shared-domain rule with a group allowlist, a real run by the report 106 method, and regeneration of the workbooks and the P2 sample.
**Scope:** `salesos_test` only. No production, no external calls, no commit.

## 1. Group-domain allowlist

- File: `app/modules/master_data/phase6/data/shared_domain_allowlist.csv`, 139 domains, sha256 `1debae78…275e90`.
- Selection: shared by 5 or more accounts, not matching junk patterns (free/typo/disposable mail, social, placeholders, platforms, telco, `.gov.sa`), and at least 60% of the sharing accounts have one distinctive name token in common. Examples: `nadec.com.sa`, `herfy.com`, `kudu.com.sa`, `aldrees.com`, `coca-cola.com.sa`. The site builder `app.site123.com` was removed.
- Conservative by design: keeping a domain preserves the pre-rule behaviour.
- Status `CANDIDATE_KEEP_PENDING_HUMAN_CONFIRMATION`. Removing a domain is a later human decision.

## 2. Code

- `pipeline.py`:
  - `load_shared_domain_allowlist()` is loaded by the rule.
  - `ACTIVE_CLASSIFICATION_VERSION` = `OPTION_C_1+EXCL_NCNP+DOMSH5`.
- `scripts/phase6_apply_ncnp_rule.py`: new `--shared-domain-threshold` option.
- New scripts:
  - `scripts/phase7a_build_gate_workbooks.py`: reproducible workbook build from the active version.
  - `scripts/phase7a_enrich_gate_workbooks.py` and `scripts/phase7a_capture_gate_workbooks.py` (report 107).
- Tests:
  - 2 new unit tests (allowlist and entity-domain).
  - Phase 7 integration expected counts updated to the new state.

## 3. Real run

| Item | Result |
|---|---|
| Backup | `scratchpad/phase6_derived_before_domsh5_20260925.dump` (116,144,766 bytes, sha256 `0b2a548e…b20e5a`) |
| First attempt | **Stalled** in the `md_quality_score_history` insert: the server was waiting on the client (`ClientRead`) and the client was idle. The session was terminated; one transaction meant a **full rollback**, verified by counts. The retry completed normally. Recorded here as an operational note. |
| Version | `OPTION_C_1+EXCL_NCNP+DOMSH5`, 296,746 rows. The previous two versions are kept. |
| Domains | 494 shared → 139 allowlisted, 355 excluded; 9,468 domain choices changed. Safety counters 0. |
| Candidates | 42,998 produced; 7,981 newly superseded (not deleted). |
| Invariants | Companies 296,746 · people 1,124 · source rows 909,967 · provenance 1,524,717 · Global-ID digest `98548a1e…cbf5` (unchanged) |

State of the active version:

| Measure | `+EXCL_NCNP` | `+EXCL_NCNP+DOMSH5` |
|---|---:|---:|
| SALES_READY | 5,689 | 5,845 |
| SALES_READY_WITH_REVIEW | 36,034 | 29,374 |
| P1 (corroboration / conflict / weak) | 6,883 (5,729/663/491) | 6,344 (5,885/**335**/**124**) |
| P2 | 43,204 | 36,418 |
| P3 account candidates | 546 | 236 |
| Ready accounts (usability) | 41,723 | 35,219 |
| Non-commercial blocker | 2,844 | 2,629 |
| Usable if G4 + G5(SRWR) closed | 38,729 | **32,440** |

## 4. Rebuilt workbooks

In `docs/data/phase7/gate_review_20260925/` (README updated; the earlier set is archived in `superseded_OPTION_C_1+EXCL_NCNP/`):

| File | Rows | Machine suggestion (not a decision) |
|---|---:|---|
| G3 | 5 | — |
| G4 field conflict (full) | 335 | 30 likely correct / 305 needs human |
| G4 weak identity (full) | 124 | 124 needs human |
| G4 corroboration 5% sample | 296 of 5,885 | 99 / 197 |
| G5 real-world spot check | 51 | 15 / 36 |
| P2 sample v3 | 951 (881 SRWR + 70 enrichment) | — |

**Total human review:** G3 5 + G4 755 + G5 51 = **811 accounts**, down from 1,497 before the rule.

## 5. Verification

- Unit: **3,789 passed**, 0 failed.
- Phase 7 integration (`salesos_test`): **19/19**.
- Capture tool dry run: 0 to record (nothing filled yet).
- Ruff clean.

## 6. Next

1. Human reviewers fill G3 (5) and G5 (51) first, then G4.
2. Human confirmation of the allowlist.
3. Capture with `--apply` after PO acceptance, then a closure report per gate.

Gates remain **OPEN**. Production is **NOT APPROVED**.
