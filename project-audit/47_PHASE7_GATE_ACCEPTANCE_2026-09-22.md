# Phase 7 Data Gate Acceptance — 2026-09-22

## Authorization

The workspace owner authorized the assistant to perform the Phase 7 review and
continue execution. This record captures the resulting data decision on the
test environment and does not authorize production deployment or provider
calls.

## Accepted outcome

| Queue / artifact | Decision |
|---|---|
| P2 sample | Accepted: 1,213/1,213 reviewed, 0.00% observed material error |
| P1 candidates | Reviewed and captured: 2,719 CONFIRM, 3,034 REVIEW, 1,151 ESCALATE |
| Fuzzy candidates | Reviewed and captured without merge: 66 MATCH, 176 UNSURE, 2,410 ESCALATE; 9 prior SEPARATE |
| Short-CR | 11 remain `UNRESOLVED_ESCALATE`; no CR promotion |
| MA unresolved | 792 deterministic/corroborated derived links accepted as candidates; 322 retained `ESCALATE` |

## Promotion boundary

The 792 links are available in the derived file
`03_Master_Contacts_FINAL_v1.0.csv`. They are not written into the canonical
`md_global_people` table because the `GP-*` source keys do not have a complete
deterministic conversion to the database person UUIDs. Name/email fallback
would create an unsafe identity mutation. The required next artifact is a
reviewed GP-to-database-person mapping manifest or a first-class import path
that preserves the source key and provenance.

That import path is now present as `md_person_company_link_proposals`
(Alembic revision `x7y8z9a0b1c2`) and is staged on `salesos_test`: 1,114
unique `GP-*` keys, 792 `PROPOSED`, and 322 `ESCALATED`. A second run kept the
same counts without duplicates. The table is separate from `md_global_people`;
canonical promotion remains a distinct, auditable operation.

## Safety evidence

- Database used: `salesos_test` only.
- `MA_UNRESOLVED` queue: 792 `CONFIRM_EXACT`, 322 `ESCALATE`.
- Phase 6 counts unchanged: 296,746 companies; 1,124 people; 909,967 source rows; 54,185 review candidates.
- Source raw payloads and official v0.7 were not modified.
- No production write, CRM apply, staging connector, Maps call, Apollo call, or Agent Reach provider call.
- DLQ unit tests: 15/15. Agent Reach fact proposal unit tests: 26/26.
- Alembic head: `x7y8z9a0b1c2`; proposal staging is idempotent and has zero proposed rows without a company UUID.

## Gate status

Phase 7 data review is **accepted with explicit unresolved escalations**.
Staging remains **BLOCKED** until the GP-to-database-person import contract is
implemented and a real connector credential is supplied. Production remains
**NOT APPROVED**.

**Roadmap: 75% (85/113).**
