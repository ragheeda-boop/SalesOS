import { PROMPT_LIBRARY_HONESTY, PROMPT_LIBRARY_NON_GOALS } from "../promptLibraryHonesty";

describe("promptLibraryHonesty — FE-S12-01", () => {
  it("states tip HTTP + copilot false + no live LLM", () => {
    expect(PROMPT_LIBRARY_HONESTY).toMatch(/prompt-library/);
    expect(PROMPT_LIBRARY_HONESTY).toMatch(/feature_ai_copilot/);
    expect(PROMPT_LIBRARY_HONESTY).toMatch(/False|false/);
    expect(PROMPT_LIBRARY_NON_GOALS.join(" ")).toMatch(/LLM|copilot|RAG/i);
  });
});
