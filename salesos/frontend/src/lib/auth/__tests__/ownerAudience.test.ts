import {
  OWNER_JWT_AUDIENCE,
  TENANT_JWT_AUDIENCE,
  classifyJwtAudience,
  formatOwnerAudienceHonesty,
  getJwtAudience,
  isOwnerConsoleAudience,
} from "../ownerAudience";

function fakeJwt(payload: Record<string, unknown>): string {
  const body = Buffer.from(JSON.stringify(payload), "utf8").toString(
    "base64url",
  );
  return `hdr.${body}.sig`;
}

describe("ownerAudience — STORY-07-03", () => {
  it("classifies owner vs tenant audiences", () => {
    const owner = fakeJwt({ aud: OWNER_JWT_AUDIENCE, sub: "o1" });
    const tenant = fakeJwt({
      aud: TENANT_JWT_AUDIENCE,
      sub: "u1",
      tenant_id: "t1",
    });
    expect(getJwtAudience(owner)).toBe(OWNER_JWT_AUDIENCE);
    expect(classifyJwtAudience(owner)).toBe("owner");
    expect(isOwnerConsoleAudience(owner)).toBe(true);
    expect(classifyJwtAudience(tenant)).toBe("tenant");
    expect(isOwnerConsoleAudience(tenant)).toBe(false);
    expect(classifyJwtAudience(null)).toBe("missing");
  });

  it("formats honest gate copy without claiming Production GO", () => {
    expect(formatOwnerAudienceHonesty("owner")).toContain(OWNER_JWT_AUDIENCE);
    expect(formatOwnerAudienceHonesty("tenant")).toContain("DEC-093");
    expect(formatOwnerAudienceHonesty("tenant")).toContain("Not Production GO");
    expect(formatOwnerAudienceHonesty("missing")).toContain("No access token");
  });
});
