import {
  MARKETPLACE_LISTINGS_HONESTY,
  MARKETPLACE_LISTINGS_NON_GOALS,
} from "../marketplaceListingsHonesty";

describe("marketplaceListingsHonesty — FE-S13-03", () => {
  it("states tip listings + certify + memory + not CAP-036 + no live GO", () => {
    expect(MARKETPLACE_LISTINGS_HONESTY).toMatch(/marketplace\/listings/);
    expect(MARKETPLACE_LISTINGS_HONESTY).toMatch(/memory|in-memory/i);
    expect(MARKETPLACE_LISTINGS_HONESTY).toMatch(/CAP-036/);
    expect(MARKETPLACE_LISTINGS_HONESTY).toMatch(/certify|CAP-094/i);
    expect(MARKETPLACE_LISTINGS_NON_GOALS.join(" ")).toMatch(
      /HubSpot|Odoo|install|11-07/i,
    );
  });
});
