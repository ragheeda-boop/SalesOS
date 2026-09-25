# 97 — Phase 7: sales-usability API that applies PO decisions A2/A3 in code (2026-09-25)

## Purpose

This is the first Phase 7 capability built under decision A2 (report 91),
on top of the restored `salesos_test` (reports 94/96).

A Phase 6 readiness state (`SALES_READY`, `SALES_READY_WITH_REVIEW`) is not,
on its own, permission to sell. Report 91 sets two rules:
- **A2:** anything that consumes Phase 6 output must treat the pending
  human-review populations as un-adjudicated.
- **A3:** no P2 account is sales-usable until its stratum's sample passes
  review.

Before this change, nothing in the code enforced either rule. Any consumer
reading `md_identity_classifications` would have seen 43,022 "ready"
accounts.

## Delivered

| file | purpose |
|---|---|
| `app/modules/master_data/phase7/usability.py` | Holds the rules and the gate registry (details below). |
| `review_queue.py` | Two read-only service methods, behind the existing `salesos_test`-only assertion. |
| `review_router.py` | `GET …/review-queue/sales-usability/summary` and `GET …/review-queue/sales-usability/accounts` (filters `usable`, `blocker`; paginated). Same mount, `master-data-review:READ` permission and local/test-only guard as every other Phase 7-A route. |

What `usability.py` contains:
- `account_blockers()`: the single place the rules are applied.
- `GATES`: the gate registry, recorded as reviewed code with a citation for
  each gate. An unknown gate fails closed.
- A read-only query that loads each ready account's facts: readiness,
  priority, CR class, and whether it sits in a pending P3 pair or the
  pending short-CR queue.

Rules (blocker codes are stable API values):

| rule | blocks while | source |
|---|---|---|
| `P1_REVIEW_GATE_OPEN` | the account is P1 and G4 is open | report 90 G4 |
| `P2_STRATUM_NOT_ACCEPTED` | the account is P2 and **its own** readiness stratum is not accepted | report 91 A3 |
| `PENDING_P3_FUZZY_PAIR` | the account is on either side of a pending P3 pair | A2 / G2 |
| `PENDING_SHORT_CR_ADJUDICATION` | the account is in the pending short-CR queue | A2 / G3 |
| `CR_SUSPICIOUS_MULTI` | the CR classification is a multi-value artifact | G3 |

The gates are deliberately not DB flags. Opening one requires a code change
plus a closure report citing the human decision, which is the same audit bar
as every other gate. All shipped gates are `OPEN`.

## Measured on the restored data (read-only)

| | ready | usable now | usable if G4 + G5(SRWR) closed |
|---|---:|---:|---:|
| `SALES_READY` (all P1) | 5,710 | **0** | 5,699 |
| `SALES_READY_WITH_REVIEW` (all P2) | 37,312 | **0** | 37,141 |
| **total** | 43,022 | **0** | 42,840 |

**Held back even after the priority gates close: 182 accounts.**
- 153 are in pending P3 pairs.
- 29 are short-CR accounts that are also marked as a multi-value CR
  artifact.
- 7 of the 36 short-CR accounts are not in a ready state at all.

This gives the PO a concrete answer to "what does closing G4/G5 unlock?".

## Verification

| test file | count | what it covers |
|---|---:|---|
| `tests/unit/test_phase7_sales_usability.py` | 6 | every shipped gate is open; P1 blocked by G4; P2 unlocked only by its own stratum; pending populations still block after the priority gates close; not-ready never usable; unknown gate fails closed |
| `tests/integration/test_phase7_sales_usability_db.py` | 3 | read-only transaction on `salesos_test`: exact counts; with the gates closed, every still-blocked account is blocked **only** by a pending-review reason; the listing filter |
| `tests/integration/test_phase7_sales_usability_http.py` | 1 | the real router plus the real service over ASGI: 200s, `usable_accounts == 0`, `blocker` filter returns 29, `usable=true` returns 0, `page_size=5000` rejected with 422 |

- **Red→green:** with the G4 rule disabled, 5 of the 10 tests fail.
  Restored: 10/10.
- **Regression:** Phase 7-A suite (routes, DB, unit) plus the new tests:
  39/39.
- OpenAPI lists both new paths (`app.openapi()`).
- Ruff E4/E7/E9/F/I clean on the new files.

## Deliberate non-claims

- **This opens no gate and adjudicates nothing.** The API reports blockers;
  it does not remove them. Register row 40 is unchanged.
- The query loads the 43,022 ready accounts per request and filters in
  Python, so the rules exist in exactly one place. That is acceptable for an
  internal review tool. A high-traffic consumer would need a materialised
  view.
- **No frontend yet.** The endpoints are consumable, but no V3 page shows
  them.
- Like the rest of Phase 7-A, the routes are disabled outside local/test
  environments. Production is **NOT APPROVED**.
