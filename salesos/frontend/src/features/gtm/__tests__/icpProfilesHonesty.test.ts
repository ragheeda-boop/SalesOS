import {
  ICP_PROFILES_HONESTY,
  ICP_PROFILES_NON_GOALS,
} from "../icpProfilesHonesty";

describe("icpProfilesHonesty — FE-S11-01", () => {
  it("states tip HTTP + deterministic + no ML/141221 claim", () => {
    expect(ICP_PROFILES_HONESTY).toMatch(/icp-profiles/);
    expect(ICP_PROFILES_HONESTY).toMatch(/deterministic/i);
    expect(ICP_PROFILES_HONESTY).toMatch(/not claimed/i);
    expect(ICP_PROFILES_NON_GOALS.join(" ")).toMatch(/ML|won-lost/i);
    expect(ICP_PROFILES_NON_GOALS.join(" ")).toMatch(/141221/);
  });
});
