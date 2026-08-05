import { LEAD_DISCOVERY_HONESTY, LEAD_DISCOVERY_NON_GOALS } from "../leadDiscoveryHonesty";

describe("leadDiscoveryHonesty — FE-S11-03", () => {
  it("states tip HTTP + gov-first + no live 141221 claim", () => {
    expect(LEAD_DISCOVERY_HONESTY).toMatch(/lead-discovery/);
    expect(LEAD_DISCOVERY_HONESTY).toMatch(/Government-data-first|gov/i);
    expect(LEAD_DISCOVERY_HONESTY).toMatch(/not claimed/i);
    expect(LEAD_DISCOVERY_NON_GOALS.join(" ")).toMatch(/141221/);
    expect(LEAD_DISCOVERY_NON_GOALS.join(" ")).toMatch(/ERP|Odoo/);
  });
});
