import { WEBSITE_INTEL_HONESTY, WEBSITE_INTEL_NON_GOALS } from "../websiteIntelligenceHonesty";

describe("websiteIntelligenceHonesty — FE-S11-07", () => {
  it("states tip HTTP + fixture + copilot false + no live invent", () => {
    expect(WEBSITE_INTEL_HONESTY).toMatch(/website-intelligence/);
    expect(WEBSITE_INTEL_HONESTY).toMatch(/Fixture|fixture/i);
    expect(WEBSITE_INTEL_HONESTY).toMatch(/feature_ai_copilot/);
    expect(WEBSITE_INTEL_HONESTY).toMatch(/False|false/);
    expect(WEBSITE_INTEL_NON_GOALS.join(" ")).toMatch(/crawl|copilot|11-08|Clay/i);
  });
});
