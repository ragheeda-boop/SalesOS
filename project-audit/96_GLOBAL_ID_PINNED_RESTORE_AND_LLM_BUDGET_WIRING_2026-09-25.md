# 96 — Global IDs restored to their original values; LLM budget enforcement wired (fail-open) (2026-09-25)

## Purpose

Executes the two decisions the owner approved after reports 93 and 94:

1. Restore `salesos_test` with the **original** Global IDs, and make future
   restores unable to re-key them.
2. Wire AI Foundation F2 budget enforcement into the running app, with
   **fail-open** on budget-store errors (rationale below).

Scope: `salesos_test` and the disposable `loop4h-pg` container only. No
production, no Apollo, no external API.

## Part 1 — Global-ID pinned restore

### Changes

| file | change |
|---|---|
| `scripts/_muhide_global_ids.py` | `GlobalIdResolver` (pinned original ID and slug, else deterministic `uuid5`) plus `require_loaded()`. A restore aborts if the pin file is missing, unless `MUHIDE_ALLOW_UNPINNED=1` is set for a genuinely new dataset. |
| `scripts/muhide_ingest_real.py` | Companies and the 1,102 contacts resolve through the resolver. The guard runs **before** the `TRUNCATE`. |
| `scripts/muhide_v1_enrichment.py` | The 22 v1 people resolve through the resolver, with the same guard. |
| `scripts/phase7a_seed_short_cr.py` | New. Seeds the 36 short-CR accounts as **pending** queue items from the G3 workbook, idempotently. No disposition, no reviewer. Aborts unless each MA ID resolves to exactly one real company. |
| `salesos_test_export/muhide_global_id_pins_20260920.csv.gz` | 297,870 pins recovered from the 2026-09-20 dump (report 94 §3). |
| `tests/unit/test_muhide_global_ids.py` | New. 4 tests: pinned wins, derived is deterministic, no cross-type collision, missing pins abort. |

### Execution

| step | result |
|---|---|
| Backup of all `md_*` tables before any write | 266,489,279 bytes, 31 tables, sha256 `b46bc9e1…ee11e` (session scratchpad) |
| Guard check, deliberately wrong pin path | aborted before connecting; `md_global_companies` unchanged |
| `muhide_ingest_real.py` | pinned=297,848, **derived=0** (296,746 companies + 1,102 contacts) |
| `muhide_v1_enrichment.py` → `fix_false_cr.py` → `Phase6Pipeline(dry_run=False)` | all exit 0. Same Phase 6 summary as report 94. |

### Orphan cleanup

The ingest `TRUNCATE` does not cover Phase 6 derived tables. Their rows from
report 94's run pointed at that run's random IDs, so each derived table held
exactly one extra, orphaned full set. I deleted the orphans in a single
transaction guarded by a `DO` block that raises (rolls back) unless every
table lands exactly on its reference count.

| table | orphan rows deleted | final count |
|---|---:|---:|
| `md_identity_classifications` | 296,746 | 296,746 |
| `md_review_candidates` | 54,185 | 54,185 |
| `md_industry_normalization` | 293,110 | 293,110 |
| `md_quality_score_history` | 296,746 | 296,746 |
| `md_sales_readiness_history` | 296,746 | 296,746 |
| `md_contact_relationships` | 1,102 | 1,102 |

Every deleted review candidate was `pending` with no decision. The
deletion filter itself required that. With stable IDs, this cannot recur.

### Verification (read-only)

| check | result |
|---|---|
| sha256 of every (legacy key, Global ID, slug): database vs pin file | identical (`a4eafbfc…f338`), 297,870 / 297,870 |
| `PHASE6_P3_FULL_EVIDENCE.csv` Global IDs present | **1,565 / 1,565** (report 94: 0) |
| MA link proposals (PROPOSED) resolvable | **792 / 792** (report 94: 0) |
| Reference counts | companies 296,746 · people 1,124 · source rows 862,775 · provenance 1,524,717 · candidates 54,185 (P1 6,908 / P2 46,736 / P3 541) |
| **Idempotency:** Phase 6 re-run on the restored DB | delta 0 on all 9 tables; Global-ID digest unchanged |

### Review queue re-seeded (pending only)

`phase7a_seed_p3.py` and the new `phase7a_seed_short_cr.py` restored the
pending queue:

| queue | rows | decisions | companies |
|---|---:|---:|---|
| P3 pairs | 2,661 | 0 | all 1,565 IDs real |
| Short-CR | 36 | 0 | each resolves to exactly one real company |

Both scripts, re-run, add 0 rows.

`ReviewQueueService` reads the seeded queue back: P3 2,661, short-CR 36
(36 linked to a company), and full triage counts.

**No machine-assisted captures were replayed.** G2, G3 and G4 remain open
(report 91).

### P3 evidence completeness (verified, not a gap)

Only 898 of the 2,661 P3 pairs name both companies in the evidence CSV;
742 name neither.

- The CSV's `row_a`/`row_b` values are `muhide_source_map` row numbers.
  Looking those rows up reproduces **all 2,817** known company links, with
  0 disagreements.
- The 2,505 empty sides are source rows that were never linked to any
  master account.

So the evidence is complete relative to the data. Nothing was filled in or
guessed.

### Update — v0.7 contacts restored (owner-approved)

After the owner approved it, `stage_master_contacts_v07 --apply` was run:

| check | result |
|---|---|
| rows staged | 47,192 new |
| tenant visibility | visible to `salesos_app` in its own tenant; 0 visible from another tenant |
| canonical people / mappings / relationships changed | 0 |
| re-run | 0 new rows |
| `md_source_rows` / `md_source_files` | 909,967 / 7, matching the AGENTS.md §42/§49 reference exactly |
| `test_phase7a_review_queue_db.py` + unit | 27/27 PASS, including the MA-unresolved capture test |
| review queue | 2,697 rows, 0 decisions, unchanged |

Full unit suite after all report-96 changes: **3,773 passed, 0 failed**
(4 skipped, 7 xfailed, 3 xpassed).

### Originally blocked (resolved by the update above)

The v0.7 contacts source (`muhide_contacts_v07`, 47,192 rows) was staged on
2026-09-22 and was wiped by the old test truncation. Its staging script
(`scripts/stage_master_contacts_v07.py`):

- is source-rows only, with deterministic IDs;
- verifies the input file hashes;
- passes its **dry run**: 47,192 rows, and every MA→company link matches v10.

The `--apply` run was **refused by the session's permission classifier**
and was not worked around.

Until it runs, one existing test fails:
`test_phase7a_review_queue_db.py::test_ma_unresolved_capture_is_record_only`
needs that source. The other 36 tests in that group pass.

## Part 2 — LLM budget enforcement wired, fail-open

### Decision and rationale (owner-approved)

On a budget-store error the call is **allowed**, with a warning and a
structured `budget_check_failed_open` log event. Four reasons:

1. No budgets are configured yet (`tenant_llm_budgets` is empty).
2. Independent cost controls remain: `ai_tokens` quota metering and the
   provider spend-reservation gate (report 30).
3. The budget is a cost control, not a security boundary. Security paths
   (RLS, RBAC) stay fail-closed.
4. Fail-closed would turn an outage of a cost-monitoring table into a full
   outage of AI features.

If budgets later become contractual or prepaid caps, switching to
fail-closed is a one-line change in `_check_budget_fail_open`.

### Changes

- `intelligence/agents/llm.py`: new `_check_budget_fail_open()`, used at all
  3 budget-check sites (`chat`, `chat_stream`, `embed`). An exceeded budget
  still blocks. Post-call recording was already wrapped in `try` at all 3
  sites (verified).
- `app/boot/startup.py`: new `_init_llm_cost_tracker()`, which calls
  `init_cost_tracker(async_session)`. It is registered in Phase 3 of
  startup, so every per-request `LLMService` now gets a tracker.

### Verification

New `tests/unit/test_llm_cost_tracker_wiring.py` (3 tests):
- a budget-store outage does not block the call;
- an exceeded budget still blocks, and nothing is recorded;
- boot initialises the process-wide tracker, and a fresh `LLMService()`
  picks it up.

**Red→green** (reverted in the container copy only):
- Fail-open reverted → `ConnectionError: db down` fails the test.
- Boot init removed → the boot test fails.
- Both restored → 3/3 PASS.

**Regression:**
- F2 + quota unit tests: 37/37.
- Combined integration regression, now including reports 93 and 95:
  **60/60**.

## Deliberate non-claims

- The budget path is wired but not exercised over HTTP against a live
  provider. No tenant has a budget configured, so no call is currently
  blocked by it.
- `muhide_contacts_v07` is not restored (permission). The MA-unresolved
  capture path and its one test depend on it.
- No review decision was recorded, replayed or inferred. Register row 40
  is unchanged. Production is **NOT APPROVED**.
