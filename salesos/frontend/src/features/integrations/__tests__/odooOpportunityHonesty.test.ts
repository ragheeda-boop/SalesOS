import {
  CANONICAL_OPPORTUNITY_STAGES,
  DEFAULT_OPPORTUNITY_MAPPINGS,
  isOpportunityModel,
} from "../odooOpportunityHonesty";

describe("odooOpportunityHonesty — FE-S09-02", () => {
  it("mirrors tip canonical stages (no raw passthrough claim)", () => {
    expect(CANONICAL_OPPORTUNITY_STAGES).toContain("prospecting");
    expect(CANONICAL_OPPORTUNITY_STAGES).toContain("closed_won");
    expect(CANONICAL_OPPORTUNITY_STAGES).not.toContain("1");
  });

  it("provides tip crm.lead mapping preset including stage_id→stage", () => {
    expect(isOpportunityModel("crm.lead")).toBe(true);
    expect(isOpportunityModel("res.partner")).toBe(false);
    expect(
      DEFAULT_OPPORTUNITY_MAPPINGS.some((m) => m.external === "stage_id" && m.internal === "stage")
    ).toBe(true);
  });
});
