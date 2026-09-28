# 171 — Master-data append-only test-baseline defect: per-table DELETE resets aborted against the committed append-only trigger, leaving salesos_test in nondeterministic partial states; fixed (12 errors + 8 order-dependent failures → all green)

**Read-only in scope of production.** Restore/reset operations confined to `salesos_test` only; no `salesos` (production) write, no DDL on production, no Apollo/external APIs, no auto-merge.

## 1. Scope

The master-data integration suites share `salesos_test` (296,746-company MUHIDE evidence database) and reset `md_*` fixtures on setup. Several suites reset via a per-table `DELETE FROM` loop reading `pg_tables` WITHOUT `ORDER BY`. Postgres returns those rows in catalog order (by table OID ≈ creation order), which is **nondeterministic across migrations/schemas**. The committed append-only trigger `md_guard_source_immutability` (phase-0 master-data foundation, migrations `j4k5l6m7n8o9`/`4adee846`) raises on ANY `DELETE` against `md_source_files`/`md_source_rows`, so whichever table the loop hit last aborted the whole reset — leaving `salesos_test` in a **random partial state** (e.g. `md_global_companies` 296,746 intact but `md_global_people`/`md_legacy_id_mappings`/`md_field_provenance` wiped, review queue/candidates zeroed).

Observed symptom: `test_master_data_db` ran with 12 errors in the forensic combined run, and subsequent suites ("fifty" self-heal) failed 8 further assertions because their self-heal trigger keys were wrong.

## 2. Root cause

1. **DELETE-based reset vs. append-only trigger.** The trigger protects source rows by rejecting `DELETE` unconditionally. `TRUNCATE` is the sanctioned test reset (established precedent in `muhide_ingest_real.py` and `test_er_pipeline_db.py`).
2. **Nondeterministic table ordering.** `SELECT tablename FROM pg_tables ... LIKE 'md_%'` without `ORDER BY` → reset aborts at a different point per run → different partial wipe each time.
3. **Order-dependent self-heal keys.** `test_muhide_rehousing_db` self-healed only when `md_global_companies < 1000` and only ran `muhide_ingest_real.py`; `test_cr_normalization_safety_db` self-healed only when the *whole* `md_legacy_id_mappings` table was empty. Both assumptions break when a prior suite leaves non-zero scenario residue.

## 3. Fix — 4 files

1. `salesos/backend/tests/integration/test_master_data_db.py` — replaced the DELETE loop with a single deterministic `TRUNCATE TABLE <all md_% ORDER BY tablename> RESTART IDENTITY CASCADE`. Eliminates the 12 errors; every test resets the full `md_*` fixture deterministically.
2. `salesos/backend/tests/integration/test_muhide_ingestion_db.py` — same TRUNCATE reset (it had the identical broken DELETE loop).
3. `salesos/backend/tests/integration/test_muhide_rehousing_db.py` — module-level `_restore_baseline()` now runs BOTH `muhide_ingest_real.py` + `muhide_v1_enrichment.py` (the population contract — 1,124 people incl. 22 v1-unlinked, 6 source files, 1,524,717 provenance — requires both); all 6 `_run_ingestion` fixtures delegate to it, and the trigger now fires when ANY of the three core tables (companies/people/mappings) is below its baseline threshold instead of `companies<1000`.
4. `salesos/backend/tests/integration/test_cr_normalization_safety_db.py` — self-heal now keyed on the actual `LEGACY_MUHIDE_CR` baseline band (15,000–16,000) instead of "mappings table == 0", so it fires even when a prior suite leaves non-zero scenario mappings but zero CR anchors.

## 4. Verification — order-independence matrix (all green)

| Sequence | Result | Note |
|----------|:------:|------|
| `master_data` + `rehousing` | **49/49** (ran twice) | 633s then 554s |
| `muhide_ingestion` + `cr_normalization` | **23/23** | cr self-heals after a scenario-populated `md_legacy_id_mappings` |
| `muhide_ingestion` + `rehousing` | **53/53** | rehousing-after-scenario (the case the old `companies<1000` key would miss if scenario leaves ≥1000 companies) |
| `muhide_ingestion` + `cr` + `er_manual_merge` + `er_pipeline` (the worst-case sequence that previously returned 32 passed + 2 failed) | **34/34** | 360s |
| `er_pipeline` standalone (dedicated `salesos_test_er_pipeline` database) | **10/10** | 6.4s |
| Phase 7 suites (`test_phase7a_review_queue_db` + `test_phase7a_review_router_http` + `test_phase7_sales_usability_http`) | **23/28** | the 5 remaining failures are unchanged governance gates, not code regressions (see §5) |

## 5. Residual failures — governance gates, deliberately NOT closed unilaterally

1. `test_p1_triage_count` — pipeline produced P1=6,908 vs DI report-110 figure 6,249 (DI P1/P2 methodology flagged NOT RECONCILED per AGENTS §37; humans decide).
2. `test_p2_triage_count` — 46,736 vs 33,654 (same gate).
3. `test_ma_unresolved_capture_is_record_only` — needs `MA_UNRESOLVED` queue entries seeded from the G4 workbooks (PO-accepted capture step).
4. `test_p3_recapture_preserves_precise_linkage_status` — needs `linkage_status` backfill (blocked on P1_CANDIDATE seeding + HITL capture flow, README gate).
5. `test_summary_and_listing_over_http` — `usable_accounts` 0 vs expected 7,768 (DI usable-accounts methodology).

No test constants changed; no `--apply` run on capture scripts; Phase 7 remains BLOCKED per the standing gate.

## 6. Restored final state of `salesos_test` (exact contract, AGENTS §35/§37)

- `md_global_companies` 296,746 · `md_global_people` 1,124 · `md_legacy_id_mappings` 314,413 · `md_source_rows` 862,775 · `md_source_files` 6 · `md_field_provenance` 1,524,717
- Phase 6: `md_identity_classifications` 296,746 · `md_review_candidates` 54,185 · `md_industry_normalization` 293,110 · `md_quality_score_history` 296,746 · `md_sales_readiness_history` 296,746 · `md_contact_relationships` 1,102
- Review queue: `md_review_queue_state` 2,697 = 2,661 P3 + 36 short-CR (via `phase7a_seed_p3.py` + `phase7a_seed_short_cr.py`)
- Removed 2 leftover test companies (`Target Co`/`Source Co`) left by `er_manual_merge` residue without any legacy mapping → exact contract counts restored.
- Note: the 2026-09-24 header's data-state check ("review_candidates/identity 0 rows, 180,000/296,746 companies") is superseded — the full contract evidence is restored.

Restore chain used: `muhide_ingest_real.py` → `muhide_v1_enrichment.py` → `scripts/phase6_apply.py` (no-transaction, idempotent batched apply, safety counters `{}`) → the two Phase-7a seeds.

## 7. Invariants respected

- Append-only trigger protects SOURCE rows only (`md_source_files`/`md_source_rows`); derived tables stay deletable; resets use `TRUNCATE ... RESTART IDENTITY CASCADE`; no `salesos` (production) write.
- Global-ID stability: no re-generation/recycling; source immutability untouched; Phase 6 safety counters all `{}`.
- Concurrent-agent hazard: `app/modules/master_data/phase6/pipeline.py` carries another in-flight agent's uncommitted batched-apply fix — not touched, not committed. `git add -A` avoided; only the 4 test files are this session's own changes, all uncommitted.