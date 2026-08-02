import { LOOKALIKE_HONESTY, LOOKALIKE_NON_GOALS } from "../lookalikeHonesty";

describe("lookalikeHonesty — FE-S11-04", () => {
  it("states tip HTTP + fixtures + no live ML/141221 claim", () => {
    expect(LOOKALIKE_HONESTY).toMatch(/lookalikes/);
    expect(LOOKALIKE_HONESTY).toMatch(/won\/lost|Opportunity/i);
    expect(LOOKALIKE_HONESTY).toMatch(/not claimed/i);
    expect(LOOKALIKE_NON_GOALS.join(" ")).toMatch(/ML|141221/i);
  });
});
