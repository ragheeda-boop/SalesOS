# 115 — Escalated ≠ Resolved: P0 fix, DB-level linkage enforcement, and correction requirements for the 52

**Date:** 2026-09-26
**Branch:** `fix/login-and-keys`
**Commits:** `72c0320c` (capture-path linkage + structured evidence) · `56f2ebc9` (this report's P0 fix)
**Scope:** `salesos_test` + `md_review_queue_state` only. Phase 6 and Production untouched.

---

## 1. Headline

A 4-hour hardening loop found a **P0 in its first 15 minutes**: 148 sales-usable
accounts were being reported as usable on a false premise. The two integration
test failures previously dismissed as "pre-existing" were in fact **correct
regression detectors** for a real defect.

**No gate closed.** G2 and G4 remain blocked, and Production remains NOT
APPROVED. What changed is that the numbers are now true and the invariant is
now enforced by the database.

---

## 2. The P0

### 2.1 Mechanism

`usability._FACTS_SQL` decided "still awaiting human review" from
`status = 'pending'` **alone**, never consulting `disposition`:

```sql
-- before
WHERE queue_type = 'P3_PAIR' AND status = 'pending' AND global_company_id IS NOT NULL
```

`record_disposition` had moved all 2,661 P3 rows to `status = 'dispositioned'`
with `disposition = 'ESCALATE'`. The predicate therefore matched **nothing**,
the `PENDING_P3_FUZZY_PAIR` blocker silently disappeared, and every account
attached to an unresolved P3 pair was released as usable.

`ESCALATE` means *"a human must adjudicate this"*. The code read it as
*"resolved"*.

### 2.2 Magnitude — the arithmetic closes exactly

| Quantity | Value |
|---|---|
| P3-linked companies inside the ready population | **148** |
| Their `linkage_status` | `MISSING_SIDE_B` (side B unrecoverable — the G2 population) |
| PO-asserted `usable_accounts` | 7,768 |
| 7,768 + 148 | **7,916** — the observed value |
| Short-CR accounts also released | 1 (`UNRESOLVED_ESCALATE`) |

`usable_accounts` was overstated by exactly the number of unresolved P3 pairs.
No drift, no rounding — a clean identity.

### 2.3 Correction of a prior misdiagnosis

An earlier session recorded these two failures as **pre-existing**, justified by
a `git stash` check. That check was invalid: `git stash` reverts *code*, but the
database writes from the P3 backfill had already been applied, so the check
exonerated the wrong layer. The failures were introduced by the P3 stamping and
were correctly reporting a live defect.

**Lesson recorded:** a stash-based baseline comparison proves nothing about
database state. Phase 6/7 regressions must be isolated by restoring or
reasoning about the *data*, not the working tree.

### 2.4 The fix

Block on `disposition`, not `status`:

- A P3 pair blocks unless it carries an affirmative resolution
  (`CONFIRM` / `SEPARATE`). `ESCALATE`, `REVIEW` and `NULL` all block.
- A SHORT_CR row blocks while `pending`, `NULL`, or `UNRESOLVED_ESCALATE`.
  `CONFIRMED_ARTIFACT` is a resolution and does not block.

`usable_accounts` now computes **7,768 by principle**. The number was not fitted
— the predicate was corrected and the PO figure fell out. The blockers are
visible again: `PENDING_P3_FUZZY_PAIR: 148`, `PENDING_SHORT_CR_ADJUDICATION: 1`.

---

## 3. One PO assertion corrected — requires ratification

`test_summary_and_listing_over_http` asserted
`PENDING_SHORT_CR_ADJUDICATION total == 13`, written when all 13 short-CR
accounts were `pending`.

12 have since been adjudicated `CONFIRMED_ARTIFACT` — a resolution. The PO
headline `7,768` **already required** them to be released; keeping them blocked
yields 7,756. The two PO-asserted figures were therefore **mutually
inconsistent**.

Decision taken: keep the headline commercial figure, set the listing count to
**1**, and document the conflict rather than silently reconcile it.

**This is a PO-level call and is flagged for ratification.**

---

## 4. DB-level linkage enforcement (was application-only)

`md_review_queue_state.global_company_id` / `_b` had **no foreign key**. The
only protection was application code, so any bug or direct SQL write could
create a dangling link — and a dangling link is exactly the failure mode that
produced §2.

Added (idempotently, `NO ACTION` on delete to match the Phase 6 never-delete
discipline):

- `fk_md_review_queue_state_company` → `md_global_companies(id)`
- `fk_md_review_queue_state_company_b` → `md_global_companies(id)`

Verified: 2,598 + 898 populated links, **0 dangling** beforehand; a probe insert
of a dangling link is now rejected by both constraints; a legal link is still
accepted; no probe row persists.

---

## 5. The 52 MATERIAL_ERROR rows are not correctable from the record

| Field | Present |
|---|---|
| `error_type` | 52/52 (32 `WRONG_DOMAIN`, 20 `OTHER`) |
| `evidence_url` | **0/52** — no external corroboration |
| `exact_match_field` | **0/52** — no field-level agreement |
| authoritative replacement value | **0/52** |

A "wrong domain" verdict names the defect but **not the correct value**. A
correction is therefore *not computable* from the record. Inventing a
replacement would fabricate Phase 6 canonical data.

`phase7a_material_error_plan.py` accordingly emits a **requirements plan**
(per-row ask: authoritative domain, or defect description + correct value) plus
a machine-readable CSV (`115_MATERIAL_ERROR_CORRECTION_REQUIREMENTS.csv`).
The CSV is **not committed** — `*.csv` is ignored by `.gitignore:62` — and is
regenerable at any time with `--csv`. Its apply path is gated and
verified to refuse: an empty mapping, a partial mapping (1 of 52), and
`--commit` without `--i-have-approval`. **No correction was applied.**

Incidental data observations (not corrected — Phase 6 is out of scope): stored
domains include the malformed `gmail.com.com`, alongside plausible large
entities such as `coca-cola.com.sa` and `naqel.com.sa`.

---

## 6. New guard rails

| Artefact | Purpose |
|---|---|
| `tests/unit/test_phase7_unresolved_semantics.py` | 8 tests locking the resolution semantics at the SQL-predicate level, so flipping `status` can never again read as resolution |
| `scripts/phase7a_traceability_qa.py` | 8 hard gates — all PASS |
| `scripts/phase7a_invariant_snapshot.py` | read-only Phase 6 + queue fingerprint |
| `scripts/phase7a_fk_probe.py` | proves the FKs block dangling and accept legal links |
| `scripts/phase7a_stamp_remaining_labels.py` | labelled the last 38 rows |

QA gates: Q1 evidence well-formed · Q2 no dangling links · Q3 P1 linkage ·
Q4 P3 `linkage_status` vs actual NULL-ness · Q5 SHORT_CR states · Q6 escalation
blocks · Q7 Phase 6 population floors · Q8 FKs present. **All PASS.**

The gate earned its keep immediately: on first run it failed Q1/Q3 and
independently rediscovered the 2 empty `P2_SAMPLE` evidence rows.

**38 rows labelled** (36 SHORT_CR → `RESOLVED` via the legacy crosswalk;
2 P2_SAMPLE → `SUBJECT_NOT_A_COMPANY` with the v5 crosswalk basis transcribed
verbatim from each row's own `notes`, including
`real_world_truth_verified: false` because the note says so). 38 written, **0 on
re-run**.

---

## 7. Test-honesty defect corrected

`_StubService` in `test_phase7a_review_router_http.py` asserted triage counts of
`5,753` / `46,736`, which matched no query — the true strata are **5,903**
`CORROBORATION_REVIEW` and **33,654** `PRIORITIZATION_PP2` out of 53,644 total.
The stub also returned `{"id": "x"}` where the response model expects a
`P3PairRow`. A stub that lies about the population lets a future data assertion
pass against fiction. Replaced with verified real figures and real shapes.

Also normalized `body: ReviewQueueDisposition = ...` to `Body(...)`; the former
worked only by inference.

---

## 8. A mistake I made and the gate caught

While proving the FKs, I wrote a probe whose "legal link accepted" case ran
inside `async with c.transaction():` — which **commits** on clean exit, despite
my comment claiming rollback. It persisted one junk queue row. The new QA gate
failed Q1 and Q3 on the very next run, which is how it was found. The probe was
corrected to roll back explicitly, the row was removed, and the queue returned
to 3,342. Recorded because the failure mode — a test helper that lies about its
own transaction semantics — is the same class of defect as §7.

---

## 9. Evidence

```
Phase 7 unit         : 56 passed, 2 skipped
Phase 7 integration  : 28 passed, 0 failed   (was 26 passed, 2 failed)
Traceability QA gate : 8/8 PASS
Schema gate          : PASS, idempotent, md_ table delta 0
FK probe             : 2 blocked, 1 accepted, 0 persisted
Label stamp          : 38 written, 0 on re-run
```

Phase 6 row counts byte-identical:

```
md_source_rows               909,967
md_global_companies          296,746
md_identity_classifications  1,483,730
md_review_candidates          54,754
md_legacy_id_mappings         314,413
md_field_provenance         1,524,717
md_review_queue_state          3,342
```

No disposition, company, classification, merge, or Production value was altered.

---

## 10. Open items for the PO

| # | Item | Status |
|---|---|---|
| 1 | **Ratify** the `PENDING_SHORT_CR_ADJUDICATION` 13 → 1 correction | **needs decision** |
| 2 | Supply authoritative values for the 32 `WRONG_DOMAIN` rows | **blocking** — the 52 cannot be corrected without them |
| 3 | Supply defect descriptions for the 20 `OTHER` rows | **blocking** |
| 4 | FK constraints added to `salesos_test` — confirm before production | done here, needs sign-off |
| 5 | W1 typed evidence model / PII-by-construction | **not started** |
| 6 | W2 real end-to-end test (router + service + DB) | **not started** |
| 7 | G2: 1,763 P3 pairs | **blocked** — original candidates file never ingested |
| 8 | G4: 5,920 open P1 (5,606 unreviewed + 314 `CANNOT_VERIFY`) | open, human-bound |
| 9 | Production / G9–G16 | **NOT APPROVED** |

On item 8: of the 643 reviewed P1 rows only **329 are terminal**
(277 `CORRECT` + 52 `MATERIAL_ERROR`); **314 are `CANNOT_VERIFY`**, i.e. a
recorded failure to verify, not a resolution. 230 of the 346 "fully reviewed"
strata rows are `CANNOT_VERIFY` (66%), so further account-by-account review of
that strata is not expected to close it. The evidence that would decide those
rows was never captured.
