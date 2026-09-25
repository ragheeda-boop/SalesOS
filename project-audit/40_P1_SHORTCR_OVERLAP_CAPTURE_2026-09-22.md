# P1 Short-CR Overlap Capture — 2026-09-22

## Applied decision

The four P1 candidates whose CR conflicts were already resolved by the
Short-CR deterministic review were captured as `P1_CANDIDATE / CONFIRM`.
This is record-only evidence capture based on the existing PO decision
`PHASE7A_PO_DECISION_2026-09-09 D3`.

## Safety proof

- Database: `salesos_test`
- Targets: 4 P1 Global Company IDs
- State rows written: 4, idempotent
- Phase 6 table counts: unchanged
- `md_review_candidates`: unchanged; candidate values were not promoted
- CR values: unchanged
- Global IDs: unchanged
- Production/provider access: none

## Remaining P1 gate

P1 population is not fully approved. The remaining **6,904** candidates still
need the field-level review defined by the Phase 7 operations decision:

- 662 domain-only conflicts
- 5,753 corroboration candidates
- 489 weak-identity candidates

Fuzzy, MA-unresolved, and Short-CR escalation gates remain open. Staging is
still blocked.

**Roadmap: 75% (85/113).**
