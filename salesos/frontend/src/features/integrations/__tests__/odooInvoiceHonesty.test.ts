import {
  CANONICAL_PAYMENT_STATES,
  CUSTOMER_MOVE_TYPES,
  DEFAULT_INVOICE_MAPPINGS,
  isInvoiceModel,
} from "../odooInvoiceHonesty";

describe("odooInvoiceHonesty — FE-S09-06", () => {
  it("mirrors tip CustomerInvoice payment states (not platform billing)", () => {
    expect(CANONICAL_PAYMENT_STATES).toContain("paid");
    expect(CANONICAL_PAYMENT_STATES).not.toContain("stripe");
    expect(CUSTOMER_MOVE_TYPES).toEqual(expect.arrayContaining(["out_invoice", "out_refund"]));
  });

  it("provides tip account.move mapping preset including payment_state", () => {
    expect(isInvoiceModel("account.move")).toBe(true);
    expect(isInvoiceModel("project.task")).toBe(false);
    expect(
      DEFAULT_INVOICE_MAPPINGS.some(
        (m) => m.external === "payment_state" && m.internal === "payment_state"
      )
    ).toBe(true);
  });
});
