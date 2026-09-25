# 105 — NCNP rule (G3-2): implementation and dry run (2026-09-25)

**Authority:** PO decision record [report 104](104_PO_DECISION_RECORD_G3_G4_G5_2026-09-25.md), signed Ragheed Almadani, 25/09/2026. Approved scope: add the rule and run a dry run to measure its effect. **No real run was made.**
**Database:** `salesos_test`, one READ ONLY transaction. All 9 safety counters are 0 and nothing was written.

## 1. Implementation

- `app/modules/master_data/phase6/pipeline.py`:
  - New function `filter_cr_by_source()`. It drops a CR token only when an excluded source is the only source reporting it; a token another source also reports is kept. Accounts with no source attribution are left unchanged.
  - New constructor option `cr_excluded_sources`. **The default is empty, so current behaviour is unchanged.** When the option is set, the version becomes `OPTION_C_1+EXCL_NCNP`, so a new run never collides with the `OPTION_C_1` history.
  - NCNP is also removed from `cr_values_by_source` in the field-agreement check.
  - Summary counters: `cr_accounts_changed_by_source_rule` and `cr_tokens_excluded_by_source_rule`.
- `scripts/phase6_dry_run.py`: new `--exclude-cr-source NCNP` option.
- `scripts/phase6_compare_dry_run.py` (new): compares a dry run's staged changes, account by account, against the current state (read only).
- Tests: `tests/unit/test_phase6_cr_source_rule.py` (5). Phase 6/7/CR unit tests: 157 passed. Ruff clean.

Confirming evidence: in the source map, NCNP supplies the "CR" as sequential registry numbers (`'1'`, `'2'`, `'6'`, `'1000000300'`, `'1000000700'`…). They are not commercial registrations.

## 2. Dry-run results (296,746 accounts)

Artifacts: `docs/data/phase6/implementation/phase6_dry_run_ncnp_rule_20260925_{results.json,changes.csv}`, `PHASE6_DRY_RUN_NCNP_RULE_20260925_REPORT.md`, `phase6_ncnp_rule_20260925_comparison.json`.

| Measure | Current (OPTION_C_1) | With the rule |
|---|---:|---:|
| CR `SAFE` | 15,419 | 11,415 |
| `SUSPICIOUS_SHORT` | 3,924 | 104 |
| `SUSPICIOUS_MULTI` | 36 | **2** (the two SOCPA accounts) |
| SALES_READY | 5,710 | 5,689 |
| SALES_READY_WITH_REVIEW | 37,312 | 36,034 |
| ENRICHMENT_REQUIRED | 11,163 | 8,910 |
| P1 / P2 / P3 | 6,908 / 46,736 / 541 | 6,883 / 43,204 / 546 |

**3,656 accounts change (1.2%). All 3,656 include NCNP among their sources**, so the rule touches nothing else.

Main transitions:

| Count | Change |
|---:|---|
| 2,263 | ENRICHMENT_REQUIRED/P2 → INSUFFICIENT_DATA/P4. Their only identity was an NCNP number. |
| 1,272 | SALES_READY_WITH_REVIEW/P2 → INSUFFICIENT_DATA/P4 (same reason). |
| 40 | SALES_READY/P1 → SALES_READY_WITH_REVIEW/P2. They lose the government anchor and keep a domain. |
| 34 | **SALES_READY_WITH_REVIEW/P2 → SALES_READY/P1** (DETERMINISTIC_SINGLE_SOURCE → STRONG_MULTI_SOURCE). Once the truncated NCNP number is gone, the other sources agree. These are promotions, and they remain blocked by G4. |
| 14 + 3 | P1 → P4. Their identity rested only on the NCNP number. |
| Others | 11 GOVERNMENT_ANCHORED → STRONG_MULTI_SOURCE; small moves between REVIEW/WEAK. |

Review candidates: 3,576 P2 removed and 44 added; 58 P1 CORROBORATION removed and 34 added; 3 P1 FIELD_CONFLICT removed; 2 P1 WEAK added; **5 new P3 fuzzy pairs**.

## 3. What happens to the 36 accounts (G3)

- **33:** readiness is unchanged and they are no longer `SUSPICIOUS_MULTI`, because their short NCNP numbers were removed. That is G3-1 as approved.
- **3 accounts need human confirmation.** Examples: MA-0263479 (`7041460564; 621`), MA-0272304 (`7048819507; 5555`), MA-0269017 (`7028654585; 1111`). Once the NCNP short number is gone, a full SFDA number (7-series, not truncated) remains and becomes `SAFE`. That is a correct application of the rule, but in practice it promotes the SFDA number to a government anchor without a human decision. **Recommendation:** add these 3 to human review alongside the two SOCPA accounts (5 accounts in total) before accepting them.
- **2 SOCPA accounts:** stay `SUSPICIOUS_MULTI`, awaiting individual human review (G3-1).

## 4. Effect on G5 (P2 sample of 1,213)

| Stratum | Unchanged | → INSUFFICIENT_DATA | Other |
|---|---:|---:|---:|
| SALES_READY_WITH_REVIEW (1,119) | 1,077 | 41 | 1 → ENRICHMENT |
| ENRICHMENT_REQUIRED (94) | 62 | 32 | — |

Of the 114 NCNP-only SRWR accounts in the sample, 41 drop out. The other 73 keep a real domain, so under OPTION C they remain single-source SRWR, but no longer anchored on a CR. The sample therefore needs a redraw under the new version before the real-world spot check (G5-1).

## 5. Prerequisites before any real run (a new decision is needed)

1. **Versioned reads:** `phase7/usability.py` (`_FACTS_SQL`) and `review_queue.py` read `md_identity_classifications` without a version filter. Writing `OPTION_C_1+EXCL_NCNP` alongside the old rows would count every account twice. They must read only the active version.
2. **Obsolete review candidates:** `md_review_candidates` is keyed by (entity, type, reason) with no version. A real run adds the new candidates but does not close the 3,637 obsolete ones. That needs a supersession method with an audit trail, not a delete.
3. The 3 + 2 accounts in §3 go to human review.
4. Redraw the P2 sample under the new version, then run the spot check.

## 6. Status

Rule implemented and measured. **No real run.** Gates G3/G4/G5 remain OPEN. Production is **NOT APPROVED**.
