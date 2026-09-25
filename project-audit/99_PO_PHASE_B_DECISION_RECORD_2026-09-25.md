# 99 — PO Phase-B Decision Record: review-gate parameters and 5 engineering decisions (2026-09-25)

## Purpose

This record captures, verbatim in substance, the decisions the PO approved
in session on 2026-09-25. The assistant proposed each one with its
rationale, and the PO approved all of them ("كلها موافق عليها + وثق كل شي").

This document changes no code and writes no database. Implementation of
each engineering decision is recorded in its own report, which cites the
decision here.

The standing invariants of report 91 §4 are **not** changed by anything
below: never auto-merge; never auto-adjudicate a government identifier;
`salesos_test` only; no production, Apollo, or external API; source
immutability; Global-ID stability; AI honesty labels.

---

## B1 — G5 (P2 acceptance threshold): 2% material error per stratum, gated on a real-world spot check

- **Threshold:** at most **2%** material error, applied separately to
  each P2 stratum (`SALES_READY_WITH_REVIEW`, `ENRICHMENT_REQUIRED`). This
  matches the draft already used for the P1 Tier-B spot check.
- **Condition:** before either stratum is accepted, about **50 sampled
  accounts** must be verified by a human against an independent source
  (commercial register or the company's own site/contact).
- **Rationale:** the 2026-09-22 P2 review (report 37) compared the sample
  with the master file it was derived from. That is internal consistency,
  not real-world truth.
- **Gate state:** G5 stays **OPEN** in code (`phase7/usability.py`
  `GATES`) until that review is recorded and a closure report is written.
  This record sets the parameter only; it does not close the gate.

## B2 — G4 (P1 review): order and scope

1. **Tier A:** a full human review of the 666 field-conflict P1 accounts.
2. **Tier B:** a 5% random spot check of the 5,753 corroboration-review
   P1 accounts, against the same 2% threshold as B1.
3. The 489 weak-identity P1 accounts follow Tier A treatment (full
   review).
4. **Priority:** G4 comes before G5. All 5,710 `SALES_READY` accounts are
   P1, the highest-quality (multi-source) population. P2 accounts are
   single-source by definition.

## B3 — G3 (36 short-CR accounts): adjudicate now, human only

- Use the G3 workbook `docs/data/phase6/review/REVIEW_36_SUSPICIOUS_SHORT_CR.csv`.
- The earlier deterministic pass (25 `CONFIRMED_ARTIFACT` / 11
  `UNRESOLVED_ESCALATE`) may be shown as a **suggestion only**. Each
  account needs an individual human decision under the government-ID hard
  veto. No batch rule.
- Resolving G3 releases up to 29 currently-ready accounts (report 97).

## B4 — NBA feedback: one path

- Retire `NBAEngine.record_feedback()`. `POST /opportunities/{id}/nba/feedback`
  must record through the existing HITL feedback path, whose
  `nba_feedback` schema is live and was browser-proven (AGENTS.md §56).
- **Rationale:** two code paths for one concept produced report 92's
  finding 4. That finding showed the old method wrote columns that do not
  exist.

## B5 — Agent grounding sources

- **Signals:** `company_signals`, the live persisted store that Company 360
  writes (report 83).
- **Recent activity:** `activity_records` for the company, which is
  RLS-covered since DEC-157.
- **Rationale:** these are the live stores. `buying_signals` and
  `timeline_events` do not exist (reports 71, 98), and `timeline_entries`
  was shown to be the wrong store (AGENTS.md §19).

## B6 — Seller-productivity leaderboard: managers/admins only

- The per-seller leaderboard in `GET /analytics` is visible to
  manager/admin roles. Other callers see only their own figures.
- **Rationale:** individual performance data is sensitive. It is simpler
  to open it later (for example, for gamification) than to withdraw it
  once people rely on it. This closes report 88's second finding.

## B7 — Action-outcome idempotency key: required

- `POST /outcomes` rejects a request without `idempotency_key`.
- **Rationale:** the only live caller always sends one, so this costs
  nothing and closes report 87's NULL-dedup gap. Generating the key on the
  server would hide client retries instead of preventing duplicates.

## B8 — Communication Hub cross-tenant enumeration: narrow SECURITY DEFINER function

- The sync worker discovers active accounts through one `SECURITY DEFINER`
  function that returns only `(account id, tenant id)` for active
  accounts. It then processes each account in a session pinned to that
  tenant (already implemented, report 84).
- It must **not** get a `BYPASSRLS` role or an owner-engine session.
- **Rationale:** least privilege. This closes report 84's deferred gap.

## B9 — Engineering sequence (approved)

1. Prepare git commit batches for PO review. **No commit** without an
   explicit request.
2. ORM-model ↔ schema drift check, plus the SQL EXPLAIN sweep, as
   automated tests on a disposable database.
3. Implement B4–B8.
4. V3 page for the sales-usability segments (report 97).

Documentation requirement: every step gets its own numbered report and an
AGENTS.md session summary.

---

## Sign-off

| Field | Value |
|---|---|
| Decided by | Ragheb (PO) |
| Decided at | 2026-09-25 |
| Decisions | B1–B9 approved as proposed |
| Constraints | report 91 §4 invariants unchanged; G3/G4/G5 remain OPEN until their human reviews are recorded |
| Attestation | AGENT-EXECUTED per explicit user directive 2026-09-25 (verbatim: "كلها موافق عليها , + وثق كل شي") |
