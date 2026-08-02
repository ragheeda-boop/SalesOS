# STORY-09-06 — CustomerInvoice via account.move (Stream A)

> **Honesty:** Not Production GO. DEC-085 untouched. No invented Odoo/Stripe secrets.  
> No new Alembic / FORCE RLS (**POLICY_COUNT unchanged at 71**).  
> Distinct from OBJ-303/323 `PlatformBillingInvoice` (Owner-plane Stripe mirror).

## Landed

| Piece | Detail |
|-------|--------|
| Projection | `CustomerInvoice` dataclass — `object_key=customer_invoice` |
| Sync | `sync_customer_invoices` from Odoo `account.move` (`out_invoice` / `out_refund`) |
| Adapter | `_INVOICE_FIELDS` + pull domain `move_type in (out_invoice, out_refund)` |
| Guard | Skips non-customer moves; rejects unmapped `payment_state`; no `stripe_invoice_id` |
| Tests | Happy path pull+sync, skip vendor bill, payment_state ACL, naming ≠ PlatformBillingInvoice |

## Acceptance

OBJ-021 CustomerInvoice populated from `account.move` and kept distinct from
`PlatformBillingInvoice` — covered by `test_account_move_customer_invoice_synced`
+ `test_customer_invoice_not_platform_billing_invoice`.

## Non-goals

- ORM `customer_invoices` table / Alembic (follow-on)
- Stripe / platform billing path changes
- Unlinked badge list API
- Production GO
