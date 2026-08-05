import { SCORING_RULES_HONESTY, SCORING_RULES_NON_GOALS } from "../scoringRulesHonesty";

describe("scoringRulesHonesty — FE-S10-04", () => {
  it("states tip HTTP + in-memory + fail-safe + not LLM", () => {
    expect(SCORING_RULES_HONESTY).toMatch(/scoring-rules/);
    expect(SCORING_RULES_HONESTY).toMatch(/in-memory/i);
    expect(SCORING_RULES_HONESTY).toMatch(/fail-safe/i);
    expect(SCORING_RULES_HONESTY).toMatch(/not LLM/i);
    expect(SCORING_RULES_NON_GOALS.join(" ")).toMatch(/Postgres/);
  });
});
