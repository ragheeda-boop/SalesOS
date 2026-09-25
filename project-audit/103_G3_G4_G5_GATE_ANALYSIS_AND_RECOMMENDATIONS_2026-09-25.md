# 103 — Analysis of gates G3, G4 and G5 with recommendations (2026-09-25)

**Type:** read-only analysis. No decision was recorded, no gate was opened, and no CR was adjudicated.
**Sources:**
- `~/Downloads/MUHIDE_extracted/01_Master_Accounts.csv` (296,746 rows; source file, not modified).
- `docs/data/phase6/review/REVIEW_36_SUSPICIOUS_SHORT_CR.csv`.
- `docs/data/phase7/p2_sample_20260920/PHASE7A_P2_MASTER_COMPARISON_20260920.csv` (1,213-row sample).
- Snapshot `PHASE7A_REVIEW_SNAPSHOT_20260922.json`.

`salesos_test` was not queried: Docker was not running during this analysis.

## 1. Main finding: the NCNP source feeds `CR_Numbers` with values that are not commercial registrations

| Measurement (full file) | Value |
|---|---|
| Accounts with a `CR_Numbers` value | 19,380 |
| 10-digit tokens | 15,192 |
| Of these, ending in `00` | **3,891 (25.6%)**. The expected rate for random digits is about 1%. The next most common endings are only about 140 each. |
| NCNP 10-digit tokens ending in `00` | **3,784 of 3,788 (99.9%)** |
| Every other source | 0.0%–8.7% |
| Short tokens (<8 digits) from NCNP | 4,110 of 4,383 |
| Accounts with a CR that include NCNP / come only from NCNP | 7,863 / 7,650 |
| 10-digit values shared by more than one account | **0**, so truncation has not caused false government-anchor collisions |

**Interpretation:** NCNP is the register for non-profits and associations, and these entities do not hold commercial registrations. Two things are happening in the field mapped to `CR_Numbers`:
1. Short registration or licence numbers (3–4 digits).
2. 10-digit numbers truncated to 8 significant digits, probably through float or Excel scientific-notation conversion.

In both cases the value is not a verifiable commercial registration. Phase 5/6 nevertheless counts the 10-digit values as `SAFE` CRs, which are government anchors.

## 2. G3: the 36 short-CR accounts

- 34 of 36 come from NCNP (19 NCNP-only, 15 NCNP combined with other sources). The other 2 come from SOCPA.
- Token patterns:
  - 11 accounts contain only short numbers.
  - 25 accounts contain one "valid" 10-digit number plus short numbers. **Every one of those 25 "valid" numbers ends in `00`**, so all are truncated.
- Domains are mostly `.org.sa` and `.gov.sa`, which fits associations and government bodies.

**Recommendation G3-1:** do not adjudicate these 36 as "real short CR vs artifact". Adopt a clearer rule: an NCNP number is not a CR. The 34 NCNP accounts lose the CR anchor (as a derived value; the source stays unchanged) and keep the number as an `NCNP registration` identifier. The two SOCPA accounts are reviewed individually by a human.
**Why:**
- The "valid" 10-digit numbers are truncated and cannot be verified.
- Accepting any of them would violate the government-ID veto (report 91 §4.2).
- The rule settles 34 cases with one decision and prevents the problem from recurring on re-ingest.

**Recommendation G3-2 (wider than the 36):** add a source-aware rule to derived classification that excludes NCNP tokens from CR anchors. Then run a Phase 6 dry run to measure its effect on identity states and readiness before any real run.
**Why:** 3,784 truncated values are currently counted as government anchors. Report 91 invariants hold: `raw_payload` stays immutable and Global IDs stay stable, because only derived values change.

## 3. G4: P1 (6,908)

Current breakdown: 5,753 `CORROBORATION_REVIEW`, 666 `FIELD_CONFLICT_REVIEW`, 489 `WEAK_IDENTITY_REVIEW`.

**Recommendation G4-1:** endorse the B2 order (full review of the 666 + 489, and a 5% sample of the 5,753, about 288 accounts) with two changes:
1. Stratify the 5% sample by source, including NCNP explicitly, instead of drawing it at random.
2. Move any P1 account whose identity anchor is an NCNP-only CR into the full-review group, or wait until G3-2 is applied.

**Why:** errors cluster in conflicts and weak identity. Corroboration is lower risk, but only if it does not rest on a truncated anchor. The number of P1 accounts that depend on NCNP could not be measured without the database, so it is the first query once Docker is back up.

**Acceptance rule:** if the error rate in the 5% sample exceeds 2%, expand to a full review of the 5,753.

## 4. G5: P2 (46,736)

The "0.00%" recorded in reports 37/46 measured **internal consistency**: the sample was compared against the same master it was derived from. That comparison cannot detect a wrong source value.

P2 sample profile (1,213 accounts):

| Stratum | Observation |
|---|---|
| SALES_READY_WITH_REVIEW (1,119) | **114 (10.2%) come only from NCNP and have a truncated "CR"**. Most of the rest are single-source with a domain and no CR (Directory 272, Apollo 239, Contractors 127, Suppliers 81, Balady 43). |
| ENRICHMENT_REQUIRED (94) | 32 are NCNP-only with a CR and no domain. |

**Recommendation G5-1:** do not accept either stratum on the current 0% figure. Redefine the error as real-world error, in line with B1, and run the ~50-account spot check stratified by the sources above.
**Recommendation G5-2:** apply G3-2 first. If NCNP-only accounts are counted as errors today, the SRWR error rate is about 10% (well above 2%) and the stratum would fail for a known root cause.
**Recommendation G5-3 (product decision):** decide whether non-profits and government bodies are part of the sales ICP at all. If they are not, excluding them from "sales-ready" removes the largest single source of error.

## 5. Proposed order

1. PO decision on G3-1 and G3-2 (source rule + dry run).
2. Implement G3-2 on `salesos_test` (derived values only), then measure.
3. G4 per G4-1, and G5 spot check per G5-1.
4. The PO accepts or rejects each stratum/gate, with a closure report.

Gates G3/G4/G5 remain **OPEN**. Production is **NOT APPROVED**.
