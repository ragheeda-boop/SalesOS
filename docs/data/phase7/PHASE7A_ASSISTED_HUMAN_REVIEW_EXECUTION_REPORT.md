# Phase 7-A — Assisted Human Review: Execution Report

**Date:** 2026-08-31
**Actor:** Claude Code, acting as Human Review Assistant/Auditor
**Method:** Direct DB (`salesos_test`) + repository files only. No browser UI, no frontend, no Apollo/external API.
**Final status:** **ASSISTED_REVIEW_CONDITIONAL**
**Production:** **NOT APPROVED** (unchanged; this record does not authorize production).

---

## 0. Environment verified before any action

- `docker ps`: `salesos-postgres-1` (pgvector/pg16) up and healthy, `salesos-backend-1` up and healthy.
- `SELECT current_database()` via both `psql` and the app's own `ReviewQueueService` → `salesos_test` in every case. No connection to `salesos` (app/prod DB) was made.
- `md_review_queue_state` exists (created by `phase7a_schema_gate.py`), unique on `(queue_type, subject_key)`, capture-only per its own docstring.

---

## 1. Short-CR (36 accounts) — EXECUTED, VERIFIED

**Finding:** the 36 dispositions already existed in `md_review_queue_state` at the start of this pass (`reviewed_at = 2026-08-31 17:42:06 UTC`, `reviewer = system_auto`), i.e. this rule had already been executed against the DB. Rather than blindly re-run writes, I recomputed the rule independently from source data and verified every row **1:1**.

### 1.1 Independent recomputation

Ran `ReviewQueueService.list_short_cr()` (the app's own read path: `md_source_rows` for `source_id='muhide_master_accounts'` with `CR_Numbers LIKE '%;%'`, joined to `md_legacy_id_mappings`) — read-only, connected DB confirmed `salesos_test`, transaction rolled back.

- **Total short-CR candidates:** 36 (matches task spec exactly)
- **`valid_cr_count >= 1`:** 25 accounts
- **`valid_cr_count = 0`:** 11 accounts

### 1.2 Disposition rule verification (existing DB rows vs. recomputed rule)

Joined the recomputed rule output against `md_review_queue_state WHERE queue_type='SHORT_CR'` row-by-row (`subject_key = master_account_id`):

| Rule branch | Expected disposition | Expected note | DB rows matching | Mismatches |
|---|---|---|---|---|
| `valid_cr_count >= 1` | `CONFIRMED_ARTIFACT` | "Short token treated as artifact because a valid long CR exists." | 25/25 | 0 |
| `valid_cr_count = 0` | `UNRESOLVED_ESCALATE` | "No valid long CR present; requires escalation." | 11/11 | 0 |
| — | `CONFIRMED_VALID_SHORT_CR` | (not used — no trusted source present) | 0 | — |

**Result: 36/36 rows correct, 0 mismatches, 0 uses of `CONFIRMED_VALID_SHORT_CR`** (correctly withheld — no internal trusted source corroborates any rejected short token as a genuine CR).

### Required proof — Short-CR

| Metric | Count |
|---|---:|
| Total reviewed | 36 |
| `CONFIRMED_ARTIFACT` | 25 |
| `UNRESOLVED_ESCALATE` | 11 |
| `CONFIRMED_VALID_SHORT_CR` | 0 |

No further writes were made in this pass for Short-CR — the existing rows are already correct and the write is idempotent (`ON CONFLICT (queue_type, subject_key) DO UPDATE`), so re-issuing them would be a no-op.

---

## 2. Write-scope proof

### 2.1 Writes made by this pass

**Zero.** Every DB operation performed in this pass was read-only (`SELECT`, including via the app's `ReviewQueueService`, whose queries all end in `ROLLBACK`). This report is the only artifact produced.

### 2.2 Phase 6 table counts — before vs. after this pass

| Table | Before | After | Δ |
|---|---:|---:|---:|
| `md_global_companies` | 296,746 | 296,746 | 0 |
| `md_identity_classifications` | 296,746 | 296,746 | 0 |
| `md_sales_readiness_history` | 296,746 | 296,746 | 0 |
| `md_source_rows` | 862,775 | 862,775 | 0 |
| `md_legacy_id_mappings` | 314,413 | 314,413 | 0 |
| `md_industry_normalization` | 293,110 | 293,110 | 0 |
| `md_contact_relationships` | 1,102 | 1,102 | 0 |
| `md_review_candidates` | 54,185 | 54,185 | 0 |
| `md_entity_matches` | 0 | 0 | 0 |
| `md_entity_merge_history` | 0 | 0 | 0 |
| `md_quality_scores` | 0 | 0 | 0 |
| `md_p0_dispositions` | 0 | 0 | 0 |
| `md_review_queue_state` (Phase 7-A, permitted) | 2,697 | 2,697 | 0 |

**No Phase 6 table changed. `md_review_queue_state` (the one permitted Phase 7-A table) also did not change, because this pass made no writes** — the Short-CR rows it contains were already correct (§1).

---

## 3. P3 fuzzy pairs (2,661) — ANALYZED, NOT AUTO-DISPOSITIONED

### 3.1 Baseline evidence in `md_review_queue_state`

All 2,661 rows carry identical evidence: `reason = "FUZZY_NAME_SIMILARITY only; FUZZY_ONLY=NEVER_AUTO_MERGE"`, `exact_match_field = "company_name (fuzzy)"` (from the authoritative source, `docs/data/phase6/implementation/PHASE6_P3_FULL_EVIDENCE.csv`, 2,661 rows). **No row carries a deterministic corroborating field** (no CR/domain/phone exact-match flag) in the seeded evidence itself — every pair's own generation-time evidence is name-similarity only, by design (`FUZZY_ONLY=NEVER_AUTO_MERGE`).

Per instruction, I went beyond the seeded `evidence_ref` and cross-checked against live `md_global_companies` for both sides of each pair (still internal data, still read-only) to look for real deterministic corroboration (CR number, domain, VAT).

### 3.2 Grouping (evidence-based, from existing internal data only)

| Group | Count | Basis |
|---|---:|---|
| Both sides unresolved to a comparable company (`global_company_id_b` NULL) | 1,763 | 66.2% of the queue — one side of the pair never resolved to a Global Company record, so there is nothing to compare a "same vs. different company" judgment against. |
| Both sides resolved, **CR numbers differ** (non-null on both sides) | 9 | See §3.3 — **not** classified as a safe SEPARATE call. |
| Both sides resolved, **domains equal** (non-null) | 114 | Best positive signal available anywhere in the queue. |
| Both sides resolved, no CR/domain/VAT corroboration either way | 775 | Fuzzy name only — genuinely undecidable from data alone. |
| **Total** | **2,661** | 1,763 + 9 + 114 + 775 |

### 3.3 Why 0 pairs were classified `HIGH_MATCH_CANDIDATE`/`HIGH_SEPARATE_CANDIDATE` as final, and why the 9 CR-differ pairs are **not** a safe auto-SEPARATE

I initially treated "two different non-empty CR numbers" as a plausible deterministic SEPARATE signal, then pulled the actual 9 rows before writing anything:

| Pair | Name A | CR A | Name B | CR B |
|---|---|---|---|---|
| 286401:286407 | شركة عبدالرحمن العمودي للاعاشة والتموين شركة شخص واحد | 7009016069 | *(identical name)* | 7007770378 |
| 287268:287970 | شركة مصنع العمره للمياه المحدوده | 7001380257 | شركة مصنع العمرة للمياه المحدودة *(near-identical)* | 7004014952 |
| 288401:298731 | شركة الصالحية التجارية مساهمة مقفلة | 7011931347 | *(identical name)* | 7014816818 |
| 290347:290348 | شركة سقالة الرعاية الصحية | 7007980688 | *(identical name)* | 7013984518 |
| 292483:292518 | FoodProductsMigrationAccNameAR *(placeholder/migration artifact, not a real name)* | 7001988687 | *(identical placeholder)* | 7031739217 |
| 299671:299673 | شركة سلاسل الامداد للخدمات اللوجستية | 7018040613 | *(identical name)* | 7023560753 |
| 303251:303254 | فرع الشركة الاهلية للصناعات الغذائية ("branch of...") | 7003554446 | *(identical name)* | 7016772159 |
| 303251:303255 | فرع الشركة الاهلية للصناعات الغذائية | 7003554446 | فرع الشركة الاهلية للصناعت الغذائية *(typo variant)* | 7002597073 |
| 303254:303255 | فرع الشركة الاهلية للصناعات الغذائية | 7016772159 | فرع الشركة الاهلية للصناعت الغذائية | 7002597073 |

Every one of these 9 pairs has an **identical or near-identical name and a different CR**. In the Saudi CR system a *branch* of a company is issued its own distinct CR number while remaining the same legal entity as its parent/other branches — three of these nine rows (`303251:303254`, `303251:303255`, `303254:303255`) are literally a 3-way cluster on "**فرع** الشركة الاهلية للصناعات الغذائية" ("**branch of** National Food Industries Co."). Auto-writing `SEPARATE` here on the strength of "CR differs" would very plausibly have been **wrong** — this pattern is at least as consistent with "same company, different registered branch" as with "two different companies." This is exactly the "government identifier (CR number) ambiguity you cannot resolve" case the job aid tells reviewers to escalate (`docs/data/phase7/PHASE7A_REVIEWER_JOB_AID.md` §3), so these route to **ESCALATE**, not `HIGH_SEPARATE_CANDIDATE`.

**Revised, evidence-honest grouping (final):**

| Bucket | Count | Disposition this pass |
|---|---:|---|
| `HIGH_MATCH_CANDIDATE` | 114 | Not written. Domain-equal — strongest positive signal in the queue; recommended as the first human-review batch. |
| `HIGH_SEPARATE_CANDIDATE` | 0 | None met a genuinely deterministic bar; forcing 9 pairs into this bucket would have risked a false SEPARATE on same-company/multi-branch pairs. |
| `UNSURE` | 775 | Not written. Both sides resolved, no corroborating identifier either way — needs a human eye, no shortcut. |
| `ESCALATE` | 1,772 | Not written. 1,763 with an unresolved counterpart (data-readiness gap, not a reviewer judgment) + 9 CR-ambiguity/branch-pattern pairs (§3.3, needs a PO policy call on branch handling). |

Sample of the strongest positive (`HIGH_MATCH_CANDIDATE`) evidence, for calibration:

| Pair | Name A | Name B | Shared domain |
|---|---|---|---|
| 315273:318090 | مكتب المعمار المتطور للإستشارات الهندسية | *(identical)* | ihcc.sa |
| 325763:338617 | Orient Provision & Trading Company | Orient Provision and Trading Company | optcl.net |
| 324646:325479 | Raneen Medical Co. | Raneen Medical | raneenmed.com |

### 3.4 Recommended next executable batch (P3)

1. **9 CR-ambiguity pairs** → route to PO/Data Owner now as a named policy question: *"same/near-identical name + different CR — is this a multi-branch same-entity pattern (`MATCH` for CRM purposes) or two distinct legal entities (`SEPARATE`)?"* Small (9), high-signal, cheap for a human to resolve once policy is set — do this first.
2. **114 domain-equal pairs** → first full-review human batch; highest hit-rate expected of any subset in the 2,661.
3. **775 no-corroboration pairs** → the bulk of genuine one-at-a-time fuzzy review the job aid describes; no shortcut available.
4. **1,763 missing-counterpart pairs** → **not a reviewer task as-is**. Recommend routing back to data engineering to either resolve `row_b` to a Global Company or drop it from the P3 queue; asking a human reviewer to judge "same vs. different company" against a record that was never resolved risks manufacturing a decision from absent data.

### 3.5 Scope note (not actioned)

`md_review_candidates` also contains 541 rows with `candidate_type='P3', reason='FUZZY_CANDIDATE_REVIEW'` — a queue distinct from the 2,661 `P3_PAIR` rows in `md_review_queue_state` and **not** one of the 6 queues named in this task's scope. Flagging for awareness only; no action taken.

---

## 4. P1 / P2 — ANALYZED AND PRIORITIZED

No writes made (none were authorized for this section — task explicitly says "ANALYZE AND PRIORITIZE" / "P2 must remain sampling-only" / "Do not mark all P2 reviewed"). All `md_review_candidates` rows remain `status='pending'`, `decision=NULL` — confirmed via direct query.

### 4.1 FIELD_CONFLICT_REVIEW (666) — prioritized first per policy

| Sub-batch | Count | conflict_fields |
|---|---:|---|
| **CR-number conflicts (highest stakes)** | 4 | `["cr_number"]` ×3, `["cr_number","domain"]` ×1 |
| Domain-only conflicts | 662 | `["domain"]` |

**Cross-queue finding:** all 4 CR-number-conflict `global_entity_id`s (`a68fe4f6…`, `eeb94268…`, `490bcf8d…`, `48777b92…`) are the **same companies** already dispositioned `CONFIRMED_ARTIFACT` in the Short-CR queue (§1) — `MA-0259345`, `MA-0263479`, `MA-0269017`, `MA-0272304` respectively. Their "field conflict" is the identical short-token-vs-long-CR pattern the Short-CR rule already adjudicated. **Recommended first P1 batch:** these 4, with `CONFIRM` and a note citing the Short-CR resolution — the fastest, best-evidenced batch available anywhere in P1/P2, but left for explicit sign-off rather than auto-written here since only Short-CR was authorized to execute.

**Second batch:** the 662 domain-only conflicts, full review per policy (§2 of the ops decision record calls for FULL review of this queue).

### 4.2 CORROBORATION_REVIEW (5,753) — targeted/full, recommended ordering

| Confidence tier | Count |
|---|---:|
| `LIKELY MATCH` (weaker — review first) | 1,860 |
| `MATCHED` (stronger) | 3,893 |

Recommend reviewing the 1,860 `LIKELY MATCH` items first — they are the ones most likely to actually need a decision or escalation; the 3,893 `MATCHED` items are lower-risk and can follow.

### 4.3 WEAK_IDENTITY_REVIEW (489) — 5% sample per policy, expand if error > 2%

| cr_class | Count |
|---|---:|
| `AMBIGUOUS` | 488 |
| `SUSPICIOUS_SHORT` | 1 |

Recommend the single `SUSPICIOUS_SHORT` item as a quick first look (same CR-integrity theme as §1/§4.1), then a 5% (≈24-25 item) random sample of the 488 `AMBIGUOUS` items per the operations decision record.

### 4.4 P2 PRIORITIZATION_PP2 (46,736) — sampling only, not reviewed in bulk

Stratum sizes (joined to `md_sales_readiness_history.sales_readiness`):

| Stratum | Population | Sample rule | Recommended sample size |
|---|---:|---|---:|
| `SALES_READY_WITH_REVIEW` | 37,312 | 3% random | ≈1,119 |
| `ENRICHMENT_REQUIRED` | 9,424 | 1% random | ≈94 |
| **Total P2** | **46,736** | — | ≈1,213 |

**No P2 rows were marked reviewed.** Recommend the PO/Data Owner authorize pulling this stratified random sample as the next executable P2 step; material-error threshold remains 2% per the operations decision record — if exceeded for a stratum, expand sampling and keep that bucket blocked from downstream use.

---

## 5. Open items requiring a named decision (blocking full completion, not blocking this pass)

1. **Branch-CR policy** (§3.3) — 9 P3 pairs need a PO ruling on same-name/different-CR (branch pattern) handling before any P3 `SEPARATE` can be safely recorded for that shape of evidence anywhere in the corpus.
2. **Escalation owner** — per the operations decision record, this is still "PO/Data Owner until a named individual is assigned." All ESCALATE/UNSURE items above (1,772 P3 + queue items) route there.
3. **P2 sampling authorization** — the stratified sample sizes above are computed and ready; pulling the actual ≈1,213-row sample is a PO go-ahead away.
4. **P3 541-item scope note** (§3.5) — worth a decision on whether it belongs in the Phase 7-A queue set at all.

---

## Final status

> **ASSISTED_REVIEW_CONDITIONAL**

Short-CR (36/36) is fully executed and independently verified against its deterministic rule. P3 (2,661) and P1/P2 (53,644) are fully analyzed from internal DB evidence with recommended next batches. Nothing was merged, no CR was promoted, no company data or Phase 6 table was touched, no production or external system was reached. Full completion of P3/P1/P2 is conditional on the three PO decisions in §5 (branch-CR policy, escalation owner, P2 sampling go-ahead) — not on any further engineering work.

**Production remains NOT APPROVED.**

---

*Non-destructive assisted-review pass. DB writes this pass: 0. All figures in this report were computed directly from `salesos_test` and `docs/data/phase6/implementation/PHASE6_P3_FULL_EVIDENCE.csv` on 2026-08-31.*
