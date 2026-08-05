import { AI_MODEL_TIERS_HONESTY, AI_MODEL_TIERS_NON_GOALS } from "../aiModelTiersHonesty";

describe("aiModelTiersHonesty — FE-S12-04", () => {
  it("states tip GET + copilot false + no invent PUT", () => {
    expect(AI_MODEL_TIERS_HONESTY).toMatch(/ai-model-tiers/);
    expect(AI_MODEL_TIERS_HONESTY).toMatch(/feature_ai_copilot/);
    expect(AI_MODEL_TIERS_HONESTY).toMatch(/False|false|Read-only|no PUT/i);
    expect(AI_MODEL_TIERS_NON_GOALS.join(" ")).toMatch(/PUT|copilot|11-07/i);
  });
});
