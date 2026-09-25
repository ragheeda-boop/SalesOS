# 112 — Rules I/J applied (G5 split acceptance + placeholder-name blocker); G3 blocked pending PO go-ahead (2026-09-25)

**Authority:** Ragheed Almadani (PO), 25/09/2026, reply "موافق على توصياك" — approves my three recommendations from the prior turn:
- **I.** Split SRWR acceptance: accept the registry-anchored part (SFDA/multi-source), keep Apollo-only under review.
- **J.** Placeholder-name blocker for the 22 `FeedLicMigrationAccountNameAr` accounts.
- **K.** Defer the Apollo-collision (page-fetch) check.

**Scope:** code + tests only, read against `salesos_test`. No production writes, no Google Maps/Apollo/registry APIs, no merges, no adjudication of the 36 short-CR accounts.

## 1. Rule I — split SRWR gate

`app/modules/master_data/phase7/usability.py`: the single `G5:SALES_READY_WITH_REVIEW` gate is now split by identity basis:

- **`G5:SALES_READY_WITH_REVIEW`** → **CLOSED**. Applies when `apollo_only=False` (SFDA / multi-source / any other single non-Apollo source). Report 111 measured 1.2% (SFDA) / 0% (multi-source) error, n=151.
- **`G5:SALES_READY_WITH_REVIEW:APOLLO_ONLY`** → stays **OPEN**. Applies when every source row for the account is `Apollo Accounts`. Report 111 measured 7.4% error (name collisions with foreign same-name companies), n=54.

`account_blockers()` now takes `apollo_only: bool` and picks the gate key accordingly; unaffected: P1 (still G4-gated), `G5:ENRICHMENT_REQUIRED` (untouched, separate 1% stratum, no PO decision yet).

## 2. Rule J — placeholder-name blocker

`PLACEHOLDER_NAMES = {"FeedLicMigrationAccountNameAr"}` (exact match, confirmed 22 accounts in `salesos_test`, report 111 §3). New blocker `PLACEHOLDER_ACCOUNT_NAME`, applied regardless of gate state. Of the 22, **12 are SRWR/non-Apollo** — these would have silently become "usable" under rec. I alone without this rule; the other 10 are P1 (already blocked by G4 anyway).

## 3. Verification

- Unit (`tests/unit/test_phase7_sales_usability.py`): 11/11 (rewrote the stale "every gate is open" test; added split-gate and placeholder tests).
- DB integration against the real `salesos_test` (`tests/integration/test_phase7_sales_usability_db.py`, `test_phase7_sales_usability_http.py`): 4/4, using the exact live-computed figures below (obtained by running `usability_summary()` directly against `salesos_test`, not hand-derived).
- Keyword-filtered regression (`-k "phase7 or usability"`): 28/28. Full unit suite otherwise unchanged from its known pre-existing-failure baseline (frontend-page-existence checks, RAG-RLS contention against the shared live DB, and similar previously-documented environmental categories — none touch Phase 7 usability).
- Frontend: TypeScript 0 diagnostics, ESLint clean, Jest 2/2 for the `/v3/sales-usability` page (added Arabic labels for `OUT_OF_MARKET` and `PLACEHOLDER_ACCOUNT_NAME`, both previously falling back to the raw English code).
- All Docker images/containers built for this verification were removed afterward; no lasting state outside `salesos_test` itself.

### Live figures (`salesos_test`, current active version `OPTION_C_1+NCNP+DS5+LV+CR+ED`)

| | before (report 111) | after rec. I/J |
|---|---:|---:|
| ready_accounts | 21,609 | 21,609 (unchanged) |
| usable_accounts | 0 | **7,768** |
| SALES_READY (P1) usable | 0 | 0 (unchanged, G4 still open) |
| SALES_READY_WITH_REVIEW usable | 0 | **7,768** of 15,746 |
| `P2_STRATUM_NOT_ACCEPTED` (now Apollo-only only) | 15,746 | 7,807 |
| `PLACEHOLDER_ACCOUNT_NAME` (new) | — | 22 |
| `OUT_OF_MARKET` | 2,876 | 2,876 (unaffected by I/J) |
| `NON_COMMERCIAL_SEGMENT` | 164 | 164 (unaffected by I/J) |

A methodological note surfaced during verification: `usability.py`'s `apollo_only`/`has_ncnp` detection depends on a join to `md_source_rows`, which — unlike its Master Data siblings (`md_global_companies`, `md_identity_classifications`, `md_legacy_id_mappings`, all no-RLS) — carries a real tenant-scoped RLS+FORCE policy (all 909,967 rows sit under one ingestion tenant). `review_queue.py`'s dedicated engine connects via the owner/BYPASSRLS role (`resolved_database_url`, matching how the rest of Master Data is treated as global platform data), so this is not a live gap in the shipped API — but it means a future caller that reaches this join through the tenant-restricted `app_database_url` role would need an explicit GUC pin first, or would silently under-detect `apollo_only`/`has_ncnp` exactly as this session's reports 121–141 repeatedly found elsewhere. Flagged, not changed.

## 4. G3 (5 accounts) — reviewed and captured

The permission classifier initially blocked the script call that would write these decisions (a bulk write into a CR-adjudication workbook, indistinguishable from automated adjudication without explicit authorization in-conversation). My reasoning was presented to the PO in chat instead; PO reply "يلا موافق" (2026-09-25) approved it explicitly, after which the same write succeeded.

Decisions recorded (evidence: SFDA/SOCPA 10-digit-vs-CR classification, reasoning from the established SFDA unified-national-number pattern — report 109: 96.5% of 10-digit SFDA numbers are UNN, not CR — plus per-account name/domain/source-consistency; full per-account reasoning is in the chat transcript and in `G3_HUMAN_REVIEW_5_ACCOUNTS.csv`'s `notes` column):

| MA ID | Value in question | Decision | Basis |
|---|---|---:|---|
| MA-0263479 | 7041460564 (SFDA) | NOT_A_CR | SFDA-UNN pattern; name mismatch with the attached SFDA source row noted as a separate anomaly |
| MA-0272304 | 7048819507 (SFDA) | NOT_A_CR | SFDA-UNN pattern; name/domain consistent |
| MA-0269017 | 7028654585 (SFDA) | NOT_A_CR | SFDA-UNN pattern; name/domain consistent |
| MA-0279593 | 7050371686 (SOCPA) | UNRESOLVED_ESCALATE | SOCPA numbering less established than SFDA's; genuine ambiguity, no registry access |
| MA-0279803 | 7026807060 (SOCPA) | UNRESOLVED_ESCALATE | Same SOCPA ambiguity; readiness unaffected (already multi-source corroborated via Apollo) |

Recorded via `scripts/phase7a_capture_gate_workbooks.py --apply` (dry run first, confirmed `to_record: 5`, no invalid values, G4/G5 workbooks correctly still all-incomplete since not yet reviewed). `md_review_queue_state` (`salesos_test`): 5/5 rows now `queue_type=SHORT_CR`, `status=dispositioned`, dispositions `CONFIRMED_ARTIFACT` ×3 / `UNRESOLVED_ESCALATE` ×2 — verified directly in the database. This is a record-only write per `ReviewQueueService`'s hard limits: no `md_identity_classifications` row, `cr_class`, or `sales_readiness` was touched, and nothing was merged or promoted.

This does **not** close the `G3` gate itself: `account_blockers()`'s `CR_AMBIGUOUS_MULTI` check gates on the live `G3` gate status (still `OPEN`), not on a per-account disposition, and 2 of the 5 decisions are themselves unresolved. Of the 5, only MA-0279803 falls within the current ready-accounts scope (`SALES_READY`, `cr_class=SUSPICIOUS_MULTI`) and stays blocked by `CR_AMBIGUOUS_MULTI` regardless of this disposition, matching intent (its readiness doesn't depend on this CR question either way). The separate 36-account short-CR queue (a different population, seeded by `phase7a_seed_short_cr.py`) is unaffected by this capture and remains pending.

## 5. Status

Gates: `G5:SALES_READY_WITH_REVIEW` **CLOSED** (rec. I); `G5:SALES_READY_WITH_REVIEW:APOLLO_ONLY`, `G4`, `G3`, `G2`, `G5:ENRICHMENT_REQUIRED` remain **OPEN**. All 5 G3 workbook accounts now have a recorded, evidenced disposition (3 confirmed-artifact, 2 escalated) — the G3 gate itself stays open pending the separate 36-account short-CR population. Production remains **NOT APPROVED**. No commit.
