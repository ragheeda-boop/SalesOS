import { AI_MEMORY_HONESTY, AI_MEMORY_NON_GOALS } from "../aiMemoryHonesty";

describe("aiMemoryHonesty — FE-S12-03", () => {
  it("keeps tip honesty labels", () => {
    expect(AI_MEMORY_HONESTY).toMatch(/ai-memory/);
    expect(AI_MEMORY_HONESTY).toMatch(/feature_ai_copilot remains False/);
    expect(AI_MEMORY_HONESTY).toMatch(/STUB/);
    expect(AI_MEMORY_NON_GOALS.join(" ")).toMatch(/Cross-session/);
  });
});
