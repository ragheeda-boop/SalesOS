import { OUTREACH_HONESTY, OUTREACH_NON_GOALS } from "../outreachHonesty";

describe("outreachHonesty — FE-S11-08", () => {
  it("states tip HTTP + draft_only + copilot false + no live send", () => {
    expect(OUTREACH_HONESTY).toMatch(/gtm\/outreach/);
    expect(OUTREACH_HONESTY).toMatch(/draft_only/);
    expect(OUTREACH_HONESTY).toMatch(/feature_ai_copilot/);
    expect(OUTREACH_HONESTY).toMatch(/False|false/);
    expect(OUTREACH_NON_GOALS.join(" ")).toMatch(/SMTP|LinkedIn|WhatsApp|copilot/i);
  });
});
