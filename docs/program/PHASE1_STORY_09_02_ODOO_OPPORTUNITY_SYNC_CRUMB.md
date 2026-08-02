# STORY-09-02 — Odoo Opportunity sync + translated stages (Stream A)

> **Honesty:** Not Production GO. DEC-085 untouched. No invented Odoo secrets.  
> No new Alembic / FORCE RLS (POLICY_COUNT unchanged at 71).

## Landed

| Piece | Detail |
|-------|--------|
| Pull | `OdooAdapter.pull_incremental(model="crm.lead")` — `type=opportunity` domain + opportunity fields |
| ACL | `OdooTranslator(strict_stages=True)` — unmapped Odoo stages raise `AclValidationError` (no raw passthrough) |
| Batch | `sync_opportunity_records` → canonical stages (`prospecting`…`closed_lost`) |
| Stage map | `DEFAULT_ODOO_OPPORTUNITY_STAGE_MAP` for CI/certify; tenant maps via config |
| Tests | Translated stages, many2one `stage_id`, unmapped rejection, won/lost aliases |

## Acceptance

Odoo stage semantics translated, not passed through raw — covered by
`test_opportunity_stages_translated_not_raw_passthrough` +
`test_unmapped_odoo_stage_rejected_loudly`.

## Non-goals

- Live XML-RPC / vault password material in repo
- Persist to `commercial_opportunities` ORM (orchestration-only this story)
- Unlinked cr_number badge list API for Studio Monitor (09-01 residual; land when board DoD owns it — not invented here)
- STORY-09-03 InteractionNote / PII scrubbing
