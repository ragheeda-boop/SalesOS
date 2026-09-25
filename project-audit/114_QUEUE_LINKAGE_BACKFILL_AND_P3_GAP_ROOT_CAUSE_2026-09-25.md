# 114 — Queue linkage backfill + capture-path root fix; the G2 P3 gap is proven unrecoverable from the database (2026-09-25)

**Authority:** Ragheed Almadani (PO), 25/09/2026, in response to the traceability finding reported in chat: complete the crosswalk for `Portfolio Master v1 (existing draft)` to link the 1,762 unlinked P3 pairs, and normalize G4 onto the `global_company_id` column with structured evidence. Explicit approval given before any write.

**Scope:** `salesos_test` only. Writes go **exclusively** to `md_review_queue_state` (`global_company_id` and `evidence_ref` columns). No merge, no CR promotion, no classification change, no source-row edit, no production action. `disposition`, `status`, `reviewer`, `reviewed_at` and `notes` are never modified by this work.

---

## 1. Root cause of the traceability gap

`ReviewQueueService.record_disposition` (`app/modules/master_data/phase7/review_queue.py:315-402`) writes only `subject_key`, `status`, `disposition`, `reviewer`, `reviewed_at` and `notes`. It never populates `global_company_id` or `evidence_ref`.

`phase7a_capture_gate_workbooks.py:87` calls it with `subject_key=row["global_company_id"]`, so all 643 G4 rows carried a real Global Company UUID **in the `subject_key` column only**, with `evidence_ref = {}`. The rows were always traceable — the linkage simply lived in the wrong column, with no machine-readable evidence.

The P3 gap is different in kind. `phase7a_seed_p3.py:78-85` copies `company_a_global_id` / `company_b_global_id` straight out of the authoritative Phase 6 artifact `docs/data/phase6/implementation/PHASE6_P3_FULL_EVIDENCE.csv`. **The blanks originate in that CSV, not in the capture.**

## 2. The P3 linkage cannot be recovered from the database — four candidate paths tested and rejected

| # | Candidate path | Result | Verdict |
|---|---|---|---|
| 1 | `md_legacy_id_mappings` (`LEGACY_MUHIDE_MA_ID`, 296,746 rows) | The P3 `subject_key` numbers are **not** in the `MA-XXXXXXX` namespace. `subject_key "549:340719"` maps to stored Global ID `e5b2e88c…` = `MA-0000451`, but looking up `MA-0000549` returns `4ea2c067…`. | **Rejected — unsafe.** Applying it would have written **1,730 conflicting Global Company IDs**, silently corrupting correct links. |
| 2 | `md_source_rows.row_number` | `row_number` is per-source (909,967 rows, only 336,067 distinct values; every source restarts at 0). `row_a = 549` matches 7 different source rows. | **Rejected — ambiguous.** |
| 3 | `md_source_rows.global_entity_id` | **NULL for all 909,967 rows.** The column is unused. | **Rejected — empty.** |
| 4 | `md_entity_matches` (`source_a_id` / `source_b_id`) | **Table is empty (0 rows).** | **Rejected — empty.** |

Probing the raw index space settles it: `row_a` values `315216` / `318033` match `muhide_source_map.row_number` uniquely, but `566691` / `568213` / `340719` match **nothing** in any table (`muhide_source_map` tops out at 340,185). `row_a` / `row_b` are row indices into the external MUHIDE resolution-candidates file, **which was never ingested as a source file**. That index → Global Company translation does not exist anywhere in `salesos_test`.

Note that `md_field_provenance` *is* fully populated (1,524,717 rows, 520,117 distinct source rows, 100% with a `global_entity_id`), so the source-row → company link does exist — but there is no ingested row that corresponds to a `row_a` index, so provenance cannot be reached from it.

**Conclusion: the missing IDs are unrecoverable without re-ingesting the original candidates file as a source file and re-deriving the pair linkage upstream in Phase 6.** Fabricating them from a mismatched ID namespace is prohibited by the standing invariants (Global ID stability, no manufactured anchors, never auto-merge).

## 3. What was applied

New script `salesos/backend/scripts/phase7a_backfill_queue_linkage.py` (refuses without `--apply`, asserts `salesos_test`, single transaction, pre-flight asserts).

**3a. G4 / `P1_CANDIDATE` — 643 rows**

- `global_company_id` ← the already-validated `subject_key` UUID. Pre-flight proved 643/643 are real `md_global_companies` rows and that the workbook ID set and the database key set are **exactly equal** (0 drift either way). This asserts no new identity; it moves an existing, verified one into its proper column.
- `evidence_ref` rebuilt from the G4 workbooks: 14 fields — `workbook`, `review_set`, `reason`, `source_stratum`, `ma_id`, `cr_class`, `identity_state`, `sales_readiness`, `non_commercial`, `domain_relation`, `exact_match_field`, `error_type`, `evidence_url`, `workbook_decision`. PII-free (no contact names, emails or phone numbers).

**3b. G2 / `P3_PAIR` — 2,661 rows, annotation only**

`evidence_ref` gains `linkage_status`, `missing_side` and `linkage_source`. **No Global Company ID was invented.**

| `linkage_status` | Pairs |
|---|---:|
| `COMPLETE` (both sides linked) | 898 |
| `MISSING_SIDE_B` | 1,021 |
| `MISSING_BOTH` (all 742 from `Portfolio Master v1 (existing draft)`) | 742 |

## 4. Post-write verification (read-only re-query)

| Check | Result |
|---|---|
| P1 rows with `global_company_id` | **643 / 643** |
| P1 rows joining a real `md_global_companies` row | **643 / 643** |
| P1 `global_company_id` ≠ `subject_key` (mismatches) | **0** |
| P1 rows with populated `evidence_ref` | **643 / 643**, all 14 keys on all rows |
| P3 rows annotated | **2,661 / 2,661** |
| P3 rows still lacking an ID | 1,763 — **unchanged, by design** |
| Dispositions | Unchanged: 277 CONFIRM / 52 ESCALATE / 314 REVIEW; 2,661 ESCALATE; 29 / 7 SHORT_CR; 2 P2 |
| Phase 6 tables | Unchanged: 296,746 companies · 909,967 source rows · 54,754 review candidates · 314,413 legacy mappings · 1,524,717 provenance · 1,483,730 identity + 1,483,730 readiness rows (5 versions × 296,746) |

## 5. Honest effect on the gates

- **G4 moves from "recorded" to "traceable".** Every one of the 643 dispositions is now joinable to a real company with machine-readable evidence. The 52 `MATERIAL_ERROR` corrections are still **not applied** to `md_global_companies` — that remains a separate, explicitly unapproved step.
- **G2 does not move.** Its 1,763 unlinked pairs are now *labelled* as such instead of silently looking incomplete, but they remain un-actionable. Closing G2 requires re-ingesting the MUHIDE candidates file as a source file and re-deriving the pair → company linkage in Phase 6.
- No gate closed by this work. No production action taken or authorized.

### 5a. Correction — 643 is 10.3% of G4, not the whole of it

The 643 rows must not be read as a G4 closure:

| Sub-population | Reviewed | Total | Remaining |
|---|---:|---:|---:|
| `P1:CORROBORATION_REVIEW` (sampled 5%) | 297 | 5,903 | **5,606** |
| `P1:FIELD_CONFLICT_REVIEW` (full) | 234 | 234 | 0 |
| `P1:WEAK_IDENTITY_REVIEW` (full) | 112 | 112 | 0 |
| **Total P1** | **643** | **6,249** | **5,606** |

643 = a 5% sample of the corroboration stratum (297) + two fully-reviewed strata (346). G4 is therefore **10.3% reviewed, 89.7% outstanding.**

## 6. Root-cause fix in the capture path (items 1.1 + 1.3)

Section 3 was a one-off backfill. The defect that produced untraceable rows was in
`ReviewQueueService.record_disposition()` itself, so it is now fixed at source.

**1.1 — write-through.** `record_disposition` accepts an optional structured
`evidence` bag and resolves `global_company_id` from the *subject*, persisting
both into `md_review_queue_state`. The response now returns
`global_company_id` and `evidence_ref` so the API consumer sees what was stored.

**1.3 — refuse a dangling subject.** Resolution is queue-specific, because not
every subject is a company:

| Queue | Subject shape | Behaviour |
|---|---|---|
| `P1_CANDIDATE` | Global Company UUID | **Refused** unless the UUID is both a pending P1 candidate *and* a real `md_global_companies` row → writes the id, `linkage_status=RESOLVED` |
| `SHORT_CR` | `MA-XXXXXXX` | **Refused** unless the authoritative crosswalk `LEGACY_MUHIDE_MA_ID → global_entity_id` resolves → writes the id, `linkage_status=RESOLVED` |
| `P3_PAIR` | `rowA:rowB` | Not company-resolvable (report §2). Reuses any linkage a prior pass proved; otherwise `linkage_status=SOURCE_ROWS_UNRESOLVED` and **no id is invented** |
| `P2_SAMPLE` | stratum label | Not a company; never gated. `linkage_status=SUBJECT_NOT_A_COMPANY` |
| `MA_UNRESOLVED` | `GP-…` Global **Person** | Not a company; never gated |
| `TRIAGE` | review label | Not a company; never gated |

Two further properties are enforced:

- **PII-free evidence.** A free-form evidence bag on a shared review table could
  leak contact data, so `EVIDENCE_PII_FORBIDDEN_KEYS` rejects any
  name/email/phone/address key — nested too — at the API boundary.
- **Additive, non-destructive merge.** Re-capturing a row merges new evidence
  and never erases prior provenance; `linkage_status` is preserved from the
  existing row so a re-review cannot downgrade a precise P3 label
  (`MISSING_SIDE_B`) to a generic one.

**Tests:** 39 pass across `tests/unit/test_phase7a_review_queue.py`,
`tests/integration/test_phase7a_review_queue_db.py` (11 new cases) and
`tests/integration/test_phase7a_review_router_http.py`. Ruff is at or below the
pre-change baseline on every rule.

**Applied (same session, on PO go-ahead):** `scripts/phase7a_stamp_p1_linkage_status.py`
stamps `linkage_status = RESOLVED` on the 643 P1 rows — the only P1 rows in the table that
predated the fix. 643 writes, single transaction, `salesos_test` only.

Pre-flight refuses the whole run unless every target row already has a non-null
`global_company_id`, that id equals `subject_key` (no drift), and it is a real
`md_global_companies` row — `RESOLVED` is the only label that could be truthful.
Re-running stamps **0 rows** (verified idempotent). Independent re-query: 643/643
labelled, 643/643 linked, 643/643 joining a real company, dispositions unchanged,
Phase 6 fingerprint unchanged.

**Deliberately not stamped:** 36 `SHORT_CR` and 2 `P2_SAMPLE` rows still carry no
`linkage_status`. Both queues are fully resolvable by the new code and will be labelled
on next capture; extending the stamp to them is a separate, unapproved write. `P2_SAMPLE`
in particular is `{}` by design — its subject is a sampling stratum, not a company, and
the seeded row is asserted as `{}` in the integration tests.

**Pre-existing, unrelated failures** (fail identically with these changes
stashed, confirmed by `git stash`): `test_phase7_sales_usability_db.py::
test_p1_fully_blocked_p2_registry_anchored_srwr_accepted` and
`test_phase7_sales_usability_http.py::test_summary_and_listing_over_http`, the
latter asserting a hard-coded `usable_accounts == 7_768` against an actual
7,916. Population drift, not a regression from this work.

## 7. Data-integrity verification after the code fix

Re-queried `salesos_test` read-only after running the new suite (which writes
and restores rows), to prove the tests did not pollute the seeded population.

| Check | Expected | Actual |
|---|---:|---:|
| `md_review_queue_state` total rows | 3,342 | **3,342** |
| `P1_CANDIDATE` rows / linked | 643 / 643 | **643 / 643** |
| `P3_PAIR` rows / linked | 2,661 / 1,919 | **2,661 / 1,919** |
| `SHORT_CR` rows / linked | 36 / 36 | **36 / 36** |
| `P2_SAMPLE` rows | 2 | **2** |
| Dispositions (P1 277/52/314 · P3 2,661 · CR 29/7 · P2 2) | unchanged | **unchanged** |
| P3 `linkage_status` (898 / 1,021 / 742) | unchanged | **unchanged** |
| Leftover `test:%` or synthetic state rows | 0 | **0** |
| Leftover synthetic `md_review_candidates` | 0 | **0** |
| Seeded P2 row `evidence_ref` | `{}` | **`{}`** |

### Defect found in the test harness while verifying this

`_cleanup_test_rows` in `test_phase7a_review_queue_db.py` restored only
`status / disposition / reviewer / reviewed_at / notes`. It did **not** restore
`global_company_id`, `global_company_id_b` or `evidence_ref` — so any test using
`preserve=` against a seeded row would have permanently written the new linkage
columns into it. The helper now snapshots and restores all eight columns, and
the two `preserve=` SELECTs were widened to read them.

## 8. Files changed

Code (Phase 7-A, the only area touched):

- `salesos/backend/app/modules/master_data/phase7/review_queue.py` —
  `_resolve_company_link` (`:315`), `record_disposition` write-through
  (`:399`), additive merge (`:460`)
- `salesos/backend/app/modules/master_data/phase7/schemas.py` — `evidence`
  field, `EVIDENCE_PII_FORBIDDEN_KEYS` (`:67`), `_assert_evidence_pii_free`,
  `ReviewQueueDispositionResponse` linkage fields
- `salesos/backend/app/modules/master_data/phase7/review_router.py` — pass
  `evidence` through
- `salesos/backend/tests/unit/test_phase7a_review_queue.py` — contract + PII tests
- `salesos/backend/tests/integration/test_phase7a_review_queue_db.py` — 11 new
  linkage/guard tests; helper restores all columns (`:509`)
- `salesos/backend/tests/integration/test_phase7a_review_router_http.py` — stub accepts `evidence`
- `salesos/backend/scripts/phase7a_backfill_queue_linkage.py` — NEW (§3 backfill)
- `salesos/backend/scripts/phase7a_stamp_p1_linkage_status.py` — NEW (§6 label stamp)

Docs:

- `project-audit/114_QUEUE_LINKAGE_BACKFILL_AND_P3_GAP_ROOT_CAUSE_2026-09-25.md` — this file
- `AGENTS.md` §154

**Nothing is committed.** The working tree carries these changes uncommitted,
alongside pre-existing unrelated modifications; stage explicit paths only, never
`git add -A`. Production remains **NOT APPROVED**.

