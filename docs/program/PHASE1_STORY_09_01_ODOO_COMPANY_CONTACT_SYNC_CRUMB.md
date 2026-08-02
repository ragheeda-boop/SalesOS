# STORY-09-01 — Odoo Company/Contact sync + cr_number join (Stream A)

> **Honesty:** Not Production GO. DEC-085 untouched. No invented secrets.  
> No new Alembic / FORCE RLS (POLICY_COUNT unchanged at 71).

## Landed

| Piece | Detail |
|-------|--------|
| Adapter | `OdooAdapter` (`connector_key=odoo`) implements `SourceConnector` |
| RPC | Injectable `OdooRpcClient` + `InMemoryOdooRpc` for certify/CI (no network secrets) |
| Join | `join_partner_by_cr_number` → Company / Golden Record; unlinked surfaced loudly |
| Batch | `sync_partner_records` — ACL + join outcomes (matched / unlinked / invalid) |
| HTTP | `/connections/{id}/test` dispatches `odoo` vs fake by `connector_key` |
| Tests | Certify + cr_number dataset join + batch matched/unlinked |

## Acceptance

`cr_number` join against the company dataset (141,221-scale via indexed lookup) —
covered by `test_cr_number_join_matches_company_dataset` + partner sync batch.

## Non-goals

- Live XML-RPC password material in repo (vault `credential_ref` only)
- Unlinked-record UI badge (stub residual)
- STORY-09-02 Opportunity sync (see `PHASE1_STORY_09_02_ODOO_OPPORTUNITY_SYNC_CRUMB.md`)
