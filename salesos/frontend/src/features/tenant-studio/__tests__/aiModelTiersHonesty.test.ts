import { AI_MODEL_TIERS_HONESTY, AI_MODEL_TIERS_NON_GOALS } from "../aiModelTiersHonesty";

describe("aiModelTiersHonesty — FE-S12-04", () => {
  it("describes owner plan writes while keeping model execution gated", () => {
    expect(AI_MODEL_TIERS_HONESTY).toMatch(/owner-only plan entitlement API/);
    expect(AI_MODEL_TIERS_HONESTY).toMatch(/feature_ai_copilot/);
    expect(AI_MODEL_TIERS_HONESTY).toMatch(/does not enable/i);
    expect(AI_MODEL_TIERS_NON_GOALS.join(" ")).toMatch(/copilot|11-07/i);
  });
});
