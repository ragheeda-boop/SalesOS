# 110 — The four G5 rules: real run and the G5 re-review (2026-09-25)

**Authority:** Ragheed Almadani (PO), 25/09/2026, reply "نعم" to the four proposals of report 109:
1. single-source domain corroboration;
2. out-of-market filter;
3. domain liveness;
4. re-run the spot check.

The G5 review was delegated to the agent (report 109).

**Still open:** batches 4–7 (report 109 §1) were **not** retried. "نعم" answered a two-option question without choosing an option.

**Scope:** `salesos_test` and public DNS/web only. No production writes, no Google Maps, Apollo or registry APIs. No commit.

## 1. Rules implemented

| # | Rule | Implementation |
|---|---|---|
| 1 | A single-source, domain-only identity is not enough for SRWR | Pipeline option `require_domain_corroboration`. SRWR becomes ENRICHMENT_REQUIRED when there is no CR, no Apollo ID, and fewer than 2 sources report the domain. The flag is recorded in the readiness basis. |
| 2 | Out of market | Usability blocker `OUT_OF_MARKET`: Apollo-only accounts whose city is not in `phase6/data/saudi_cities.txt` (curated reviewable gazetteer of ~170 English/Arabic spellings). Empty city is kept. A data-driven gazetteer was rejected: Apollo stores the foreign HQ city for Saudi branches. |
| 3 | Domain liveness | `scripts/phase6_domain_liveness.py` resolves each domain through public DNS (8.8.8.8/1.1.1.1). **DEAD = definitive NXDOMAIN in two attempts** (see note); 7 INVALID names count as dead; timeouts are never dead. Snapshot `phase6/data/domain_liveness.csv` (2026-09-25): 34,068 domains: 29,701 resolve, **4,087 dead**, 7 invalid, 273 unknown. |
| 4 | Re-run the spot check | §4 |

**Note on the liveness definition.** Two earlier versions were corrected before any use:
- The first treated "no address record" as dead, which flagged `nadec.com.sa` (only `www.` resolves).
- The second, using the OS resolver, could not tell NXDOMAIN from "no data", and flagged registered domains such as `gulfhygiene.com`.

The final version queries SOA via dnspython, so a domain that exists (MX-only, www-only) counts as alive.

## 2. Real run

| Item | Result |
|---|---|
| Backup | `scratchpad/phase6_derived_before_g5rules_20260925.dump` (161,373,527 bytes, sha256 `e7225bdb…163736e`) |
| First attempt | **Failed and rolled back**: the version string (37 characters) exceeded `varchar(32)`. Nothing was written (counts verified). The active-version switch was reverted. Fix: over-long names are compacted. The full rule set is `OPTION_C_1+NCNP+DS5+LV+CR`; existing version names are unchanged; unit test added. |
| Retry | Success. 296,746 rows; 40,123 candidates produced; 3,013 superseded (not deleted). Safety counters 0. |
| Invariants | Companies 296,746 · people 1,124 · source rows 909,967 · provenance 1,524,717 · Global-ID digest `98548a1e…cbf5` (unchanged) |

| Measure | `+EXCL_NCNP+DOMSH5` | `+NCNP+DS5+LV+CR` |
|---|---:|---:|
| SALES_READY | 5,845 | 5,863 |
| SALES_READY_WITH_REVIEW | 29,374 | **15,746** |
| ENRICHMENT_REQUIRED | 7,779 | 18,514 |
| P1 (corroboration/conflict/weak) | 6,344 (5,885/335/124) | 6,249 (5,903/234/112) |
| P2 | 36,418 | 33,654 |
| Ready accounts (usability) | 35,219 | 21,609 |
| OUT_OF_MARKET blocker | — | 2,867 |
| NON_COMMERCIAL blocker | 2,629 | 164 |
| Usable if G4 + G5(SRWR) closed | 32,440 | **18,430** |

## 3. Rebuilt workbooks

The previous set is archived in `superseded_OPTION_C_1+EXCL_NCNP+DOMSH5/`.

| File | Rows |
|---|---:|
| G3 | 5 |
| G4 field conflict / weak / corroboration 5% | 234 / 112 / 297 of 5,903 |
| G5 spot check (excludes non-commercial and out-of-market) | 51 (SFDA 25, Apollo 19, multi 6, engineering 1) |
| P2 sample v4 | 651 (472 SRWR + 179 enrichment) |

## 4. G5 re-review (agent, delegated)

| Result | Report 109 | Now |
|---|---:|---:|
| CORRECT | 23 (8 foreign) | **28** (2 foreign: China, Bangladesh; both had an empty city) |
| MATERIAL_ERROR | 6 | **2** |
| CANNOT_VERIFY | 22 | 21 |
| **Error rate** | 11.8% | **3.9%** (2/30 = 6.7% of verifiable accounts) |

- The rules worked: single-source contact-email domains no longer reach SRWR, and foreign Apollo accounts with a known city are blocked.
- **Still above 2%.** Both remaining errors share one pattern: an **SFDA registration contact domain** that belongs to another company (`selfstorage.sa`, `abdulrashid.com`). Their identity rests on the SFDA unified number, which is sound. The **displayed domain** is what is wrong.
- 51 is a small sample. The 95% interval for 2/51 spans roughly 0.5–13%, so the result alone cannot prove the stratum is below 2%.

### Remaining recommendations (need a PO decision)

- **E.** Do not populate the company `domain` field from a single-source SFDA contact domain. Keep it as evidence only. This would remove both remaining errors from this sample.
- **F.** Displayed-domain cleanup: `md_global_companies.domain` still shows excluded domains (agent, typo mail, placeholders; e.g. `whs.sa`, `gmaile.com`, `apps.bal`). Derive a cleaned display domain from the active rules.
- **G.** For an empty city, infer out-of-market from a clearly foreign ccTLD (`.com.bd`, `.cn`, …).
- **H.** A larger spot check (≥150) after E–G, to narrow the interval before accepting SRWR.

**G5 SRWR recommendation: not yet acceptable. Re-check after E–G.**

## 5. Verification

- Unit tests:
  - Phase 6 rules 9/9, usability 9/9.
  - Full suite 3,793 passed. One earlier run showed a single failure that did not reproduce and was not identified (possible intermittent test; noted, not claimed fixed).
- Phase 7 integration (`salesos_test`): 19/19, with expected counts updated to the new version.
- Capture dry run: G5 3.92%, `within_2pct_threshold: false`.

Gates G3/G4/G5 remain **OPEN**. Production is **NOT APPROVED**.
