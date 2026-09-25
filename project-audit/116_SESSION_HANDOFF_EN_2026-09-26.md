# 116 — SESSION HANDOFF (English) for the next Claude instance

**Date:** 2026-09-26
**Branch:** `fix/login-and-keys`
**HEAD:** `d0e0859e`
**Database touched:** `salesos_test` ONLY
**Production:** `production_approved = false` — **NOT APPROVED**

This document is the single entry point. It states what exists, what was done,
what is verified, what is NOT done, and the exact next actions. Read it before
touching anything in Phase 6 / Phase 7.

---

## 0. Read this first — three rules that were violated before

1. **`status` is not a resolution flag.** Any predicate that infers "unresolved"
   from `md_review_queue_state.status` alone will silently release escalated
   work the moment a disposition is recorded. Only an affirmative resolution
   (`CONFIRM` / `SEPARATE`) clears a blocker. This caused a P0 — see §2.
2. **A `git stash` baseline proves nothing about database state.** It reverts
   code, not rows. Phase 6/7 regression isolation must reason about the *data*.
   This produced a wrong "pre-existing" verdict that hid the P0.
3. **`async with conn.transaction()` COMMITS on clean exit.** Any probe that
   must leave no trace needs an explicit `rollback()`. This leaked a junk row
   once; the QA gate caught it.

---

## 1. Current state at a glance

| Item | Value |
|---|---|
| `md_review_queue_state` rows | 3,342 |
| G2 (1,763 P3 pairs) | **BLOCKED** — source file never ingested |
| G4 (P1 review) | **OPEN** — 5,920 open (see §6) |
| G5 SALES_READY_WITH_REVIEW | CLOSED (registry-anchored) |
| G5 Apollo-only SRWR | OPEN |
| Production / G9–G16 | **NOT APPROVED** |
| Phase 7 unit tests | 56 passed, 2 skipped |
| Phase 7 integration tests | 28 passed, **0 failed** |
| Traceability QA gate | **8/8 PASS** |

---

## 2. The P0 that was found and fixed (commit `56f2ebc9`)

### 2.1 Mechanism

`usability._FACTS_SQL` decided "still awaiting human review" from
`status = 'pending'` alone:

```sql
-- BEFORE (defective)
WHERE queue_type = 'P3_PAIR' AND status = 'pending' AND global_company_id IS NOT NULL
```

`record_disposition` had moved all 2,661 P3 rows to `status = 'dispositioned'`
with `disposition = 'ESCALATE'`. The predicate matched nothing, the
`PENDING_P3_FUZZY_PAIR` blocker disappeared, and every account attached to an
unresolved P3 pair was reported as sales-usable.

`ESCALATE` means *"a human must adjudicate this"*. The code read it as
*"resolved"*.

### 2.2 Magnitude (the arithmetic closes exactly)

| Quantity | Value |
|---|---|
| P3-linked companies inside the ready population | **148** |
| Their `linkage_status` | `MISSING_SIDE_B` (the G2 population) |
| PO-asserted `usable_accounts` | 7,768 |
| 7,768 + 148 | **7,916** = the observed wrong value |
| Short-CR accounts also wrongly released | 1 (`UNRESOLVED_ESCALATE`) |

No drift, no rounding — a clean identity.

### 2.3 The fix

Block on `disposition`, not `status`:

- **P3 blocks** unless `disposition IN ('CONFIRM','SEPARATE')`.
  `ESCALATE`, `REVIEW`, `NULL` all block.
- **SHORT_CR blocks** while `status='pending'`, `disposition IS NULL`, or
  `disposition = 'UNRESOLVED_ESCALATE'`. `CONFIRMED_ARTIFACT` is a resolution
  and does not block.

Result: `usable_accounts` computes **7,768 by principle**. The number was NOT
fitted — the predicate was corrected and the PO figure fell out. Blockers are
visible again: `PENDING_P3_FUZZY_PAIR: 148`, `PENDING_SHORT_CR_ADJUDICATION: 1`.

---

## 3. What was DONE (all verified by executable evidence)

### 3.1 Commits

| SHA | Content |
|---|---|
| `72c0320c` | Persist Global Company linkage + structured evidence on disposition capture |
| `56f2ebc9` | **P0 fix** — escalated ≠ resolved; regression tests; QA gate; invariant snapshot; 38-row label stamp |
| `7cb16c2c` | FK enforcement; 52-row correction requirements; stub truth; `Body(...)`; report 115 |
| `d0e0859e` | Lint cleanup of `56f2ebc9` additions |

### 3.2 Files created

| Path | Purpose |
|---|---|
| `salesos/backend/scripts/phase7a_invariant_snapshot.py` | Read-only Phase 6 + queue fingerprint |
| `salesos/backend/scripts/phase7a_traceability_qa.py` | **8 hard gates**, all PASS |
| `salesos/backend/scripts/phase7a_fk_probe.py` | Proves FKs block dangling / accept legal |
| `salesos/backend/scripts/phase7a_stamp_remaining_labels.py` | Labels the last 38 rows (idempotent) |
| `salesos/backend/scripts/phase7a_material_error_plan.py` | Requirements plan + refusal gates for the 52 |
| `salesos/backend/tests/unit/test_phase7_unresolved_semantics.py` | 8 tests locking the resolution semantics |
| `project-audit/115_*.md` | Full P0 report |
| `project-audit/115_MATERIAL_ERROR_CORRECTION_REQUIREMENTS.csv` | **gitignored** (`*.csv`), regenerable via `--csv` |

### 3.3 Files modified

| Path | Change |
|---|---|
| `app/modules/master_data/phase7/usability.py` | P0 fix in `_FACTS_SQL` |
| `app/modules/master_data/phase7/review_router.py` | `Body(...)` + import |
| `scripts/phase7a_schema_gate.py` | 2 FK constraints, idempotent, asserted |
| `tests/integration/test_phase7_sales_usability_http.py` | stale 13 → 1 (see §7) |
| `tests/integration/test_phase7a_review_router_http.py` | stub truth (see §5) |
| `AGENTS.md` | §155 added |
| `project-audit/114_*.md` | removed stale "Nothing is committed" |

### 3.4 DB-level linkage enforcement (commit `7cb16c2c`)

`md_review_queue_state.global_company_id` / `_b` had **no foreign key** — the
dangling-link failure mode that produced the P0 was always reachable.

Added (idempotent via `pg_constraint` catalog check, `NO ACTION` on delete to
match the Phase 6 never-delete discipline):

- `fk_md_review_queue_state_company` → `md_global_companies(id)`
- `fk_md_review_queue_state_company_b` → `md_global_companies(id)`

Verified: 2,598 + 898 populated links, 0 dangling beforehand; dangling insert
rejected by both; legal link accepted; 0 probe rows persist. QA gate `Q8`
asserts both exist.

### 3.5 38 remaining rows labelled

- 36 `SHORT_CR` → `linkage_status = "RESOLVED"` (via legacy crosswalk)
- 2 `P2_SAMPLE` → `linkage_status = "SUBJECT_NOT_A_COMPANY"` + the v5
  crosswalk basis **transcribed verbatim from each row's own `notes`**, including
  `real_world_truth_verified: false` because the note says so.

38 written, **0 on re-run**.

---

## 4. The 52 MATERIAL_ERROR rows — NOT correctable from the record

| Field | Present |
|---|---|
| `error_type` | 52/52 (32 `WRONG_DOMAIN`, 20 `OTHER`) |
| `evidence_url` | **0/52** — no external corroboration |
| `exact_match_field` | **0/52** — no field-level agreement |
| authoritative replacement value | **0/52** |

A "wrong domain" verdict names the **defect** but not the **correct value**, so a
correction is *not computable*. Inventing one would fabricate Phase 6 canonical
data.

`phase7a_material_error_plan.py` emits **requirements, not corrections**:
- `--csv` → per-row ask (`authoritative_domain` or
  `defect_description_and_correct_value`)
- `--apply <csv>` → gated; verified to REFUSE: empty mapping, partial mapping
  (1 of 52), and `--commit` without `--i-have-approval`

**0 corrections applied.** The `--commit` path is intentionally not implemented:
MATERIAL_ERROR touches Phase 6 canonical data and needs a separately reviewed
migration.

Incidental Phase 6 observations (NOT corrected, out of scope): stored domains
include the malformed `gmail.com.com` alongside plausible large entities such as
`coca-cola.com.sa` and `naqel.com.sa`.

---

## 5. Test-honesty defects that were fixed

- **`_StubService`** in `test_phase7a_review_router_http.py` claimed triage
  counts `5,753` / `46,736` — matching no query. Real strata:
  **5,903** `CORROBORATION_REVIEW` and **33,654** `PRIORITIZATION_PP2` out of
  **53,644** total. It also returned `{"id": "x"}` where a `P3PairRow` was
  expected. A stub that lies about the population lets a data assertion pass
  against fiction.
- **`body: ReviewQueueDisposition = ...`** worked only by inference; normalized
  to `Body(...)`.

---

## 6. Open backlog (human-bound, not code-bound)

### 6.1 G4 — P1 candidate review

| Population | Count |
|---|---|
| Total P1 rows in queue | 6,249 |
| Reviewed | 643 |
| — terminal (`CORRECT` → `CONFIRM`) | 277 |
| — terminal (`MATERIAL_ERROR` → `ESCALATE`) | 52 |
| — **`CANNOT_VERIFY` → `REVIEW` (NOT resolved)** | **314** |
| Never reviewed | 5,606 |
| **Actually still open** | **5,920** |

**Correction to earlier reporting:** "5,606 remaining" understated the backlog.
`REVIEW` = "could not verify", not a resolution. Of the 643 reviewed rows only
**329 are terminal**.

**230 of the 346 "fully reviewed" strata rows are `CANNOT_VERIFY` (66%)** — so
further account-by-account review of that strata is not expected to close it.
The evidence that would decide those rows was never captured.

### 6.2 Cluster-and-certify was TESTED AND FALSIFIED

Do not re-attempt it as originally conceived. The 5,903
`CORROBORATION_REVIEW` rows collapse into **14 evidence-signature clusters**
(6 cover 98.9%), but **verdicts are mixed inside each cluster**:

| Cluster signature | CONFIRM | REVIEW | ESCALATE |
|---|---|---|---|
| `(MATCHED, SAFE, False, real_domain=True, apollo=False)` | 48 | 28 | 11 |
| `(MATCHED, SAFE, False, real_domain=False, apollo=False)` | 53 | — | 1 |
| `(LIKELY MATCH, AMBIGUOUS, False, real_domain=True, apollo=True)` | 70 | 1 | — |

And **591 of 643 rows carry no `error_type` at all**. The information needed to
decide was never captured, so no deterministic rule can replace the review.
**The lever is capturing the reason, not shortcutting the work.**

### 6.3 G2 — 1,763 P3 pairs

**BLOCKED.** Pairs reference an external candidates file that was never
ingested, so side B's Global Company ID is unrecoverable from the database.
- 898 `COMPLETE` · 1,021 `MISSING_SIDE_B` · 742 `MISSING_BOTH`
- Of 2,661 rows, 1,919 have at least one linked side; **0 dangling**
- Requires the original `MUHIDE resolution-candidates` file, then re-ingest /
  re-derivation in Phase 6

---

## 7. Requires PO ratification

`test_summary_and_listing_over_http` asserted
`PENDING_SHORT_CR_ADJUDICATION total == 13`, written when all 13 short-CR
accounts were `pending`.

12 have since been adjudicated `CONFIRMED_ARTIFACT` — a resolution. The PO
headline `7,768` **already required** them released; keeping them blocked yields
7,756. **The two PO-asserted figures were mutually inconsistent.**

Decision taken: keep the headline commercial figure, set the listing count to
**1**, document the conflict rather than silently reconcile it. **This is a
PO-level call and is awaiting ratification.**

---

## 8. NOT DONE — the remaining work

### 8.1 W1 — Mandatory typed evidence model (HIGHEST VALUE, NOT STARTED)

Current state is a free-form `evidence: dict` with a **key-name-only** PII
blocklist (`EVIDENCE_PII_FORBIDDEN_KEYS`, recursive on keys).

Known gaps to close:
1. **Key-only filtering misses values.** An email in a *value* or in the
   pre-existing `notes` TEXT column passes.
2. **No reason is required.** 591/643 rows have no `error_type` (§6.2).
3. **Backdoor:** `review_queue._resolve_company_link` returns early for
   `subject_key.startswith("test:")` — in **production code**.
4. **No size/depth limit** on the evidence bag.

Target design:
- Replace the free-form dict with a **typed Pydantic model**, fixed whitelisted
  fields with strict types → PII becomes **impossible by construction** because
  no field can hold an address or phone number.
- Make `reason` / `error_type` **required** so the §6.2 gap closes going forward.
- Remove the `test:` backdoor; use an explicit dependency-injected test flag.
- Decide how to handle the existing `notes` channel (it predates this work).

### 8.2 W2 — Real end-to-end test (NOT STARTED)

`test_phase7a_review_router_http.py` uses a **stub service**, so router →
service → DB is never exercised together. Needed: real `ReviewQueueService` on
`salesos_test`, a real P1 UUID, full path, with cleanup.

Also missing:
- Unit tests proving `TRIAGE` / `MA_UNRESOLVED` are deliberately **not**
  company-gated (they are, by design — needs locking in)
- Concurrent-capture idempotency test

### 8.3 W7b — 14-cluster verdict dispersion report (LOW, NOT STARTED)

The §6.2 analysis exists only in console output. Worth persisting for the PO as
evidence that cluster-certification is not viable.

---

## 9. Invariants you must not break

```
md_source_rows                909,967   (unchanged)
md_global_companies           296,746   (unchanged — no CRUD, ever)
md_identity_classifications   1,483,730 (unchanged)
md_review_candidates            54,754   (unchanged)
md_legacy_id_mappings          314,413   (unchanged)
md_field_provenance          1,524,717   (unchanged)
md_review_queue_state             3,342 (the ONLY writable table)
```

- Write to `salesos_test` ONLY. Never `salesos` (production).
- No `md_global_companies` CRUD. No merges. No CR promotion. No
  classification changes. No external enrichment.
- `status='dispositioned'` never means resolved — see §0 rule 1.
- Verify with:
  ```
  python scripts/phase7a_traceability_qa.py       # must be 8/8 PASS
  python scripts/phase7a_invariant_snapshot.py     # counts must match above
  ```

---

## 10. Blocked on humans, not code

| # | Item | Owner | Status |
|---|---|---|---|
| 1 | Ratify SHORT_CR listing 13 → 1 | PO | **needs decision** |
| 2 | Authoritative domains for the 32 `WRONG_DOMAIN` rows | PO + Data | **blocking the 52** |
| 3 | Defect description + correct value for the 20 `OTHER` rows | PO + Data | **blocking the 52** |
| 4 | Sign off the 2 FK constraints before any production promotion | PO + DevOps | done on test, needs sign-off |
| 5 | G2: 1,763 P3 pairs | Data | **blocked** on the candidates file |
| 6 | G4: 5,920 open P1 | PO + Data | open, human-bound |
| 7 | Production G9–G16 | DevOps + PO | **NOT APPROVED** |
| 8 | Token rotation for the known-leaked `3de118a5` | DevOps | not done |

---

## 11. Suggested next actions for Claude

1. **Do W1 (typed evidence model).** Highest value: it closes the PII-by-value
   gap, makes `reason` mandatory (unlocking the §6.2 analysis), and removes the
   `test:` backdoor. It is an API change — state that in the commit.
2. **Then W2 (real e2e).** Locks W1 in.
3. **Then W7b** to persist the falsification evidence for the PO.
4. Do **not** attempt cluster-and-certify, auto-merge, or any auto-resolution of
   the 5,606 / 1,763. Each was tested and is not viable without new evidence.

### Working rules
- Heavy commands (`npm run build`, full `pytest`, installs) need explicit
  approval per `AGENTS.md` §3. Scoped runs are fine.
- The git tree is **dirty with unrelated changes**. Stage explicit paths only.
  Never `git add -A`.
- Git identity is not configured; commits used
  `-c user.name="ragheed-AQLIYA" -c user.email="ragheed@aqliya.com"`.
- Report executable evidence (command + output). Never claim a gate closed.
