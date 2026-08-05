import { BRANDING_STUDIO_HONESTY, BRANDING_STUDIO_NON_GOALS } from "../brandingStudioHonesty";

describe("brandingStudioHonesty — FE-S10-07", () => {
  it("states tip branding HTTP + in-memory + no upload", () => {
    expect(BRANDING_STUDIO_HONESTY).toMatch(/studio\/branding/);
    expect(BRANDING_STUDIO_HONESTY).toMatch(/in-memory/i);
    expect(BRANDING_STUDIO_HONESTY).toMatch(/no object upload/i);
    expect(BRANDING_STUDIO_HONESTY).toMatch(/FE-S10-07b|dashboard chrome/i);
    expect(BRANDING_STUDIO_NON_GOALS.join(" ")).toMatch(/Postgres/);
    expect(BRANDING_STUDIO_NON_GOALS.join(" ")).toMatch(/CDN/);
  });
});
