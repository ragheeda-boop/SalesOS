# 111 — Rules E–G applied and the 151-account G5 review (2026-09-25)

**Authority:** Ragheed Almadani (PO), 25/09/2026, reply "نوافق" to recommendations E–H of report 110. The G5 review was delegated to the agent (report 109).

**Still open:** commit batches 4–7 were **not** retried: the answer did not choose between the two options offered.

**Scope:** `salesos_test` only. Public web and DNS only; no Google Maps, Apollo, registry APIs or production.

## 1. Rules implemented

| # | Rule | Implementation |
|---|---|---|
| E + F | Verified display domain | Pipeline option `display_domain_rule` writes `signals.display_domain` into the identity row. It is the entity domain after the shared-domain and dead-domain exclusions, and is **null when only SFDA reports it** (SFDA registration contact). Canonical `md_global_companies.domain` is not modified. Sales Usability and the workbooks show `display_domain`. 2,968 SFDA-only contact domains were suppressed. |
| G | Foreign ccTLD when the city is empty | `usability.foreign_cctld()`: a 2-letter TLD that is not `.sa` and not a generic-use ccTLD (`.co .io .me .ai .tv`…). It is used only when an Apollo-only account has no city. +9 OUT_OF_MARKET accounts. |
| H | Larger spot check | `G5_SPOT_SIZE = 150` in the workbook builder (§3) |

- The version name for the full rule set is `OPTION_C_1+NCNP+DS5+LV+CR+ED`; the compact-name mapping was extended with `EDOM → ED`.
- Tests: Phase 6/7 unit tests 138 passed (incl. new version-name and ccTLD tests). Phase 7 integration 19/19.

## 2. Real run

- Backup: `scratchpad/phase6_derived_before_edom_20260925.dump` (206,550,243 bytes, sha256 `b2765e40…62efc3`).
- Result: 296,746 rows; 40,123 candidates produced; **0 superseded** (rule E does not change readiness).
- Invariants unchanged (companies 296,746, source rows 909,967, Global-ID digest `98548a1e…cbf5`).

Usability:
- ready 21,609;
- OUT_OF_MARKET 2,876;
- **18,421 usable once G4 + G5(SRWR) close**.

P2 sample v5 is unchanged in population (33,654; 651 sampled).

## 3. G5 review (151 accounts, agent-delegated)

| Source stratum | Correct | Material error | Cannot verify | Error rate |
|---|---:|---:|---:|---:|
| Apollo-only (54) | 41 | **4** | 9 | **7.4%** |
| SFDA (81) | 34 | 1 | 46 | 1.2% |
| Multi-source (15) | 8 | 0 | 7 | 0% |
| Engineering (1) | 0 | 0 | 1 | 0% |
| **Total (151)** | **83** | **5** | **63** | **3.3%** (5/88 = 5.7% of verifiable) |

- **Method:** website fetch for accounts with a display domain; web search by name for the rest. Nine very well-known companies (Nahdi, Lulu, Aujan, Sawani, Al Safi Danone, Bin Zagr, Berain, Forsan, Mayar) were marked correct from public knowledge, **and the note says so**.
- **The search tool hit its weekly quota once mid-review.** It recovered on retry and no account was skipped.

### Errors

| # | Account | Error |
|---|---|---|
| 8 | Al Zawahed security (Apollo) | `fajr.com.sa` belongs to Fajr Al-Sharq Security |
| 12 | Nawa, Jeddah (Apollo) | `nawa.live` is a Thai restaurant in the USA |
| 52 | Al Rahma Hospital, Medina (Apollo) | `rahmahospital.org` is Rahma Hospital, Lebanon |
| 54 | MALAMA, Dammam (Apollo) | `heymalama.co` is a US Medicaid provider |
| 131 | SFDA | Name is the placeholder `FeedLicMigrationAccountNameAr` |

### Findings

1. **Apollo name collisions.** In 4 of 54 Apollo-only accounts, Apollo attached the domain of a same-name foreign company. The ccTLD rule cannot catch these (`.org`, `.co`, `.live`).
2. **Placeholder names.** The master data contains **22** accounts named `FeedLicMigrationAccountNameAr`. This is a source/migration artifact.
3. **SFDA and multi-source strata are within the 2% threshold** in this sample (1.2%, 0%).
4. **Many small establishments can't be verified.** 57% of SFDA accounts have no web presence found; their identity rests on the SFDA unified number.

## 4. Recommendations (need a PO decision)

- **I.** Split SRWR for acceptance by identity basis:
  - accept the registry-anchored part (SFDA unified number / multi-source) at 1.2% / 0%;
  - keep **Apollo-only** SRWR under review, or require a second signal for it (the same logic as rule 1).
- **J.** Placeholder-name rule: a name matching known migration placeholders counts as an identity error (blocker). 22 accounts.
- **K.** An optional Apollo-collision check: an Apollo-only account whose website names a different city or country goes to ENRICHMENT. This needs page fetching, so it is a larger change.
- **Statistical note.** 5/151: the 95% interval for the whole stratum is roughly 1.1%–7.6%. For SFDA, 1/81 gives roughly 0.03%–6.7%. The small sample leaves the upper bound above 2%. Acceptance is a PO judgement on this evidence.

## 5. Status

Gates G3/G4/G5 remain **OPEN**. G5(SRWR) is **not acceptable as a whole**; a split acceptance (recommendation I) is possible on PO decision. Production is **NOT APPROVED**. No commit.
