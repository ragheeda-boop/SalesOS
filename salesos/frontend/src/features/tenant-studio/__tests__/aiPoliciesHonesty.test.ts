import {
  AI_POLICIES_HONESTY,
  AI_POLICIES_NON_GOALS,
} from "../aiPoliciesHonesty";

describe("aiPoliciesHonesty — FE-S12-02", () => {
  it("keeps tip honesty labels", () => {
    expect(AI_POLICIES_HONESTY).toMatch(/ai-policies/);
    expect(AI_POLICIES_HONESTY).toMatch(/feature_ai_copilot remains False/);
    expect(AI_POLICIES_NON_GOALS.join(" ")).toMatch(/Live LLM/);
  });
});
