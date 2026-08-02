import { SEQUENCING_HONESTY, SEQUENCING_NON_GOALS } from "../sequencingHonesty";

describe("sequencingHonesty — FE-S11-09", () => {
  it("states tip HTTP + email-first + no live SMTP/LinkedIn/141221", () => {
    expect(SEQUENCING_HONESTY).toMatch(/sequences/);
    expect(SEQUENCING_HONESTY).toMatch(/email/i);
    expect(SEQUENCING_HONESTY).toMatch(/not claimed/i);
    expect(SEQUENCING_NON_GOALS.join(" ")).toMatch(/SMTP|LinkedIn|WhatsApp/i);
    expect(SEQUENCING_NON_GOALS.join(" ")).toMatch(/141221/);
  });
});
