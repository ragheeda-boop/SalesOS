import { ENRICHMENT_HONESTY, ENRICHMENT_NON_GOALS } from "../enrichmentHonesty";

describe("enrichmentHonesty — FE-S11-05", () => {
  it("states tip HTTP + fake providers + no live vendor/141221 claim", () => {
    expect(ENRICHMENT_HONESTY).toMatch(/enrichment/);
    expect(ENRICHMENT_HONESTY).toMatch(/fake_a|fake_b|swappable/i);
    expect(ENRICHMENT_HONESTY).toMatch(/not claimed/i);
    expect(ENRICHMENT_NON_GOALS.join(" ")).toMatch(/Clearbit|Apollo/i);
    expect(ENRICHMENT_NON_GOALS.join(" ")).toMatch(/141221/);
  });
});
