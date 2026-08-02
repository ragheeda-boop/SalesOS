/** Tip STORY-09-06 Odoo CustomerInvoice honesty constants (mirror BE).
 * Not an invented HTTP API. Unlinked badge list still BE-blocked.
 * Not Production GO / RAG GO.
 */

/** Tip CUSTOMER_MOVE_TYPES — AR only (never entry / in_invoice / platform). */
export const CUSTOMER_MOVE_TYPES = ["out_invoice", "out_refund"] as const;

/** Canonical CustomerInvoice payment states from tip customer_invoice_sync.py */
export const CANONICAL_PAYMENT_STATES = [
  "not_paid",
  "in_payment",
  "paid",
  "partial",
  "reversed",
  "cancelled",
] as const;

/** Tip DEFAULT_PAYMENT_STATE_MAP (certify/CI). */
export const DEFAULT_PAYMENT_STATE_MAP: Record<string, string> = {
  not_paid: "not_paid",
  in_payment: "in_payment",
  paid: "paid",
  partial: "partial",
  reversed: "reversed",
  cancel: "cancelled",
  cancelled: "cancelled",
};

/** Tip DEFAULT_INVOICE_MAPPINGS for Map step preset (account.move). */
export const DEFAULT_INVOICE_MAPPINGS = [
  { external: "name", internal: "name", direction: "pull" },
  { external: "amount_total", internal: "amount_total", direction: "pull" },
  {
    external: "amount_residual",
    internal: "amount_residual",
    direction: "pull",
  },
  {
    external: "payment_state",
    internal: "payment_state",
    direction: "pull",
  },
  {
    external: "partner_id",
    internal: "partner_external_id",
    direction: "pull",
  },
] as const;

export function isInvoiceModel(model: string): boolean {
  return model.trim().toLowerCase() === "account.move";
}
