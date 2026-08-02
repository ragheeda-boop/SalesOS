import {
  DEFAULT_PARTNER_MAPPINGS,
  PARTNER_JOIN_OUTCOMES,
  isPartnerModel,
} from "../odooPartnerHonesty";

describe("odooPartnerHonesty — FE-S09-01", () => {
  it("mirrors tip partner mappings including cr_number join field", () => {
    expect(isPartnerModel("res.partner")).toBe(true);
    expect(isPartnerModel("company")).toBe(true);
    expect(isPartnerModel("crm.lead")).toBe(false);
    expect(
      DEFAULT_PARTNER_MAPPINGS.some(
        (m) =>
          m.external === "x_studio_cr_number" && m.internal === "cr_number",
      ),
    ).toBe(true);
  });

  it("lists tip join outcomes without inventing a badge list API", () => {
    expect(PARTNER_JOIN_OUTCOMES).toEqual([
      "matched",
      "unlinked",
      "invalid_cr",
    ]);
  });
});
