import { VERIFICATION_HONESTY, VERIFICATION_NON_GOALS } from "../verificationHonesty";

describe("verificationHonesty — FE-S11-06", () => {
  it("states tip HTTP + fake_verify + no live vendor/141221 claim", () => {
    expect(VERIFICATION_HONESTY).toMatch(/verification/);
    expect(VERIFICATION_HONESTY).toMatch(/fake_verify|swap-in/i);
    expect(VERIFICATION_HONESTY).toMatch(/not claimed/i);
    expect(VERIFICATION_NON_GOALS.join(" ")).toMatch(/NeverBounce|ZeroBounce|Twilio/i);
    expect(VERIFICATION_NON_GOALS.join(" ")).toMatch(/141221/);
  });
});
