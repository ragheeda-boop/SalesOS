import {
  TERRITORIES_STUDIO_HONESTY,
  TERRITORIES_STUDIO_NON_GOALS,
} from "../territoriesStudioHonesty";

describe("territoriesStudioHonesty — FE-S10-05", () => {
  it("states tip HTTP + memory + no live DB/141221 claim", () => {
    expect(TERRITORIES_STUDIO_HONESTY).toMatch(/studio\/territories/);
    expect(TERRITORIES_STUDIO_HONESTY).toMatch(/memory|CAP-017/i);
    expect(TERRITORIES_STUDIO_HONESTY).toMatch(/not claimed/i);
    expect(TERRITORIES_STUDIO_NON_GOALS.join(" ")).toMatch(/141221|Postgres/i);
  });
});
