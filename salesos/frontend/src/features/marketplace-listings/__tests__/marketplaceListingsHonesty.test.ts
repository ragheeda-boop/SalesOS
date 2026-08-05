import {
  MARKETPLACE_LISTINGS_HONESTY,
  MARKETPLACE_LISTINGS_NON_GOALS,
} from "../marketplaceListingsHonesty";

describe("marketplaceListingsHonesty — FE-S13-04", () => {
  it("states tip listings + publish pack + catalog install ≠ live ERP", () => {
    expect(MARKETPLACE_LISTINGS_HONESTY).toMatch(/marketplace\/listings/);
    expect(MARKETPLACE_LISTINGS_HONESTY).toMatch(/13-04|publish pack/i);
    expect(MARKETPLACE_LISTINGS_HONESTY).toMatch(/Catalog install/);
    expect(MARKETPLACE_LISTINGS_HONESTY).toMatch(/live HubSpot|Odoo/i);
    expect(MARKETPLACE_LISTINGS_HONESTY).toMatch(/CAP-036/);
    expect(MARKETPLACE_LISTINGS_NON_GOALS.join(" ")).toMatch(/HubSpot|Odoo|CAP-036|11-07/i);
  });
});
