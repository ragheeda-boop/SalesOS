# 94 — `salesos_test` restore, Global-ID instability on every re-ingest, and the test that kept wiping it (2026-09-24)

## Purpose

First step of Phase 7 implementation under PO decision A2 (report 91). A2
limits all Phase 7 DB work to `salesos_test`, and report 90 §3 found that
database emptied by test teardown. This session restored it, found why it
keeps being wiped, and found a more serious invariant violation in the
restore path itself.

## 1. Starting state (measured, before any write)

| table | rows |
|---|---:|
| `md_global_companies` | 180,000 (expected 296,746) |
| `md_source_rows` | 296,746 |
| `md_source_files` | 1 |
| `md_legacy_id_mappings` | 188,368 |
| `md_field_provenance` | 488,146 |
| `md_identity_classifications` / `md_review_candidates` | 0 / 0 |
| `md_review_queue_state` | 0 |
| `md_person_company_link_proposals` | 1,114 |

There were no connections to `salesos_test` and counts were stable across
20 s. This was an interrupted ingest from an earlier session, not one in
progress.

## 2. Restore performed (documented chain, AGENTS.md §34–36 + Phase 6 idempotency evidence)

| step | result |
|---|---|
| `scripts/muhide_ingest_real.py` | exit 0, 169.6 s |
| `scripts/muhide_v1_enrichment.py` | exit 0, 204.9 s |
| `scripts/fix_false_cr.py` | 0 concatenation artifacts; 15,419 CR mappings; 0 still-invalid. **Script crashed on this clean path** (passed the string `"none"` as a UUID when nothing needed fixing). Fixed and re-run: exit 0. |
| `Phase6Pipeline(dry_run=False)` | exit 0; `change_count` 0; `safety` {} |

**Final counts, all equal to the reference figures:**

| measure | value |
|---|---|
| companies | 296,746 |
| people | 1,124 |
| source rows | 862,775 |
| provenance | 1,524,717 |
| identity classifications | 296,746 |
| review candidates | 54,185 (P1 6,908 / P2 46,736 / P3 541) |
| industry normalization | 293,110 |
| quality history | 296,746 |
| readiness history | 296,746 |
| contact relationships | 1,102 |

Identity states: `STRONG_MULTI_SOURCE` 2,498, `GOVERNMENT_ANCHORED` 3,255.
CR classes: `SAFE` 15,419, `SUSPICIOUS_SHORT` 3,924, `SUSPICIOUS_MULTI` 36.

## 3. Finding: every re-ingest re-keys all Global IDs (invariant violation)

`muhide_ingest_real.py` generated each company's UUID with `uuid.uuid4()`
and each G-C/G-P slug with a random `_gen_id()`. The same applies to people
there and in `muhide_v1_enrichment.py`. So every restore gives all 296,746
companies new Global IDs. This breaks report 91 §4.5 ("existing G-C/G-P IDs
never change, regenerate, recycle, or reassign") and orphans every artifact
keyed by Global ID. Measured after the restore:

| artifact | Global IDs referenced | present in `salesos_test` now | present in the 2026-09-20 dump |
|---|---:|---:|---:|
| `PHASE6_P3_FULL_EVIDENCE.csv` (authoritative P3 pairs) | 1,565 | **0** | 1,565 |
| `md_person_company_link_proposals` (PROPOSED) | 792 | **0** | 792 |

The breakage predates this session's restore: the interrupted earlier ingest
in §1 had already truncated and re-keyed the companies. This session's
restore did not recover the original IDs either, because the script cannot.

**Recovery source:** `salesos_test_export/salesos_test_pre_repair_20260920.dump`
(AGENTS.md §47) holds the original IDs. Every evidence ID above resolves
against it. `md_global_companies`, `md_global_people` and
`md_legacy_id_mappings` were extracted from it into a scratch database on
the disposable `loop4h-pg` container (not `salesos_test`). Coverage there is
complete and unique: `LEGACY_MUHIDE_MA_ID` 296,746, `LEGACY_MUHIDE_CONTACT_ID`
1,102, `LEGACY_MUHIDE_V1_PERSON` 22.

**Delivered (code, not yet applied to the DB):**
- `salesos_test_export/muhide_global_id_pins_20260920.csv.gz`: 297,870 pins
  (legacy key → original UUID + slug), sha256
  `ebda2c81482532ef34a65a7e6a22a8994f6e1360ada0f8328205fe73171dbc38`.
- `scripts/_muhide_global_ids.py` (`GlobalIdResolver`): returns the pinned
  original ID where one exists, otherwise a deterministic `uuid5` plus slug.
  After this change, no re-ingest can re-key an account.
- `scripts/muhide_ingest_real.py`: companies (by MA ID) and the 1,102
  contacts (by Contact ID) now resolve through the resolver.

**Not done:**
- `muhide_v1_enrichment.py`'s 22 v1 people. The edit was refused by the
  session's automatic permission classifier ("Modify Shared Resources"). It
  was not worked around, and the partial import added alongside it was
  reverted.
- **A re-run of the restore with pins.** Until that runs, `salesos_test`
  keeps today's random IDs, and the evidence CSVs and link proposals remain
  unresolvable against it.

## 4. Root cause of the repeated wipes (FIXED)

`tests/integration/test_er_pipeline_db.py` pointed at `salesos_test` and, in
every test's setup, ran `TRUNCATE` over **every** `md_*` table (`CASCADE`).
That includes `md_review_queue_state` (recorded review captures) and
`md_person_company_link_proposals`. It is the only suite that truncates the
full `md_*` set.

**Fix:** the suite now uses its own disposable database
`salesos_test_er_pipeline`. It already created its own tables and does not
depend on anything that exists only in `salesos_test`.
- Result: 10/10 PASS.
- Immediately after the run, `salesos_test` still had 296,746 companies and
  1,114 link proposals.

## 5. What was deliberately NOT restored

`md_review_queue_state` stays at 0 rows. It held the 2026-09-22 capture
records (P1/P2/Fuzzy/MA, §96–98) and the pending P3/Short-CR queue items.
I did not replay the `phase7a_capture_*` or `phase7a_seed_*` scripts because:

- The seeds reference Global IDs that are currently unresolvable (§3).
- Report 91 records G2/G3 as open. Replaying machine-assisted captures
  would recreate records the current gate index does not count as human
  review.

Re-seeding the **pending** queue items (no decisions) is safe once the IDs
are pinned.

## 6. Phase 7 consequence

Phase 7 work that joins Global-ID-keyed evidence cannot be built or tested
honestly until the pinned restore runs. That covers the Review Queue UI, a
sales-usability segment API, and MA link promotion. Measured today under
A2/A3:
- Every `SALES_READY` account (5,710) is P1, which is gated by G4 (open).
- Every `SALES_READY_WITH_REVIEW` account (37,312) is P2, gated by A3
  (stratum acceptance pending).
- So zero accounts are sales-usable today.

## Deliberate non-claims

- All writes went only to `salesos_test` (authorized by A2) and to the
  disposable `loop4h-pg` container. No production, no Apollo, no external API.
- Source immutability: the restore re-inserts identical raw payloads from
  the same input files. No source file was modified.
- Global-ID stability is **not yet restored in the database**. Only the
  mechanism exists (pins file, resolver, ingest wiring).
- Register row 40 (Phase 7 review) is unchanged. G2/G3/G4 remain open.
  Production is **NOT APPROVED**.
