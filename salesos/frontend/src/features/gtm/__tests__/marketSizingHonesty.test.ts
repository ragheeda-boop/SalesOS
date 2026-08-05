import { MARKET_SIZING_HONESTY, MARKET_SIZING_NON_GOALS } from "../marketSizingHonesty";

describe("marketSizingHonesty — FE-S11-02", () => {
  it("states tip HTTP + in-memory + no live 141221 claim", () => {
    expect(MARKET_SIZING_HONESTY).toMatch(/gtm\/market-sizing/);
    expect(MARKET_SIZING_HONESTY).toMatch(/in-memory/i);
    expect(MARKET_SIZING_HONESTY).toMatch(/not claimed/i);
    expect(MARKET_SIZING_NON_GOALS.join(" ")).toMatch(/141221/);
    expect(MARKET_SIZING_NON_GOALS.join(" ")).toMatch(/ICP/);
  });
});
