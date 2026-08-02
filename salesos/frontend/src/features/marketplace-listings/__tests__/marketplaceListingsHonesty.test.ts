import {
  MARKETPLACE_LISTINGS_HONESTY,
  MARKETPLACE_LISTINGS_NON_GOALS,
} from "../marketplaceListingsHonesty";

describe("marketplaceListingsHonesty — FE-S13-01b", () => {
  it("states tip listings + memory + not CAP-036 + no install", () => {
    expect(MARKETPLACE_LISTINGS_HONESTY).toMatch(/marketplace\/listings/);
    expect(MARKETPLACE_LISTINGS_HONESTY).toMatch(/memory|in-memory/i);
    expect(MARKETPLACE_LISTINGS_HONESTY).toMatch(/CAP-036/);
    expect(MARKETPLACE_LISTINGS_NON_GOALS.join(" ")).toMatch(
      /install|certify|13-02/i,
    );
  });
});
